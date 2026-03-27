from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
import httpx
from pydantic import BaseModel
from typing import Optional
import json
from datetime import datetime

router = APIRouter(prefix="/api/ai", tags=["AI Analysis"])

class AnalysisRequest(BaseModel):
    provider: str = "gemini" # 'gemini' 或是 'openai' 等
    base_url: Optional[str] = None
    model_id: str
    api_key: str
    prompt_template: str
    analysis_period: str = "30d"


def resolve_period_days(period: str) -> tuple[str, int]:
    period_map = {
        "30d": ("近30天", 30),
        "quarter": ("近一季度", 90),
        "half_year": ("近半年", 180),
        "year": ("近一年", 365),
    }
    return period_map.get(period, ("近30天", 30))

@router.get("/models")
async def get_available_models(
    api_key: str = Query(..., description="API Key"),
    provider: str = Query("gemini", description="API 提供商"),
    base_url: str = Query(None, description="自定义 Base URL (对于 OpenAI 兼容源有效)")
):
    """
    拉取各大平台支持文本生成的模型列表
    """
    if not api_key:
        raise HTTPException(status_code=400, detail="请提供 API Key")
        
    async with httpx.AsyncClient(timeout=15.0) as client:
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"拉取 Gemini 模型失败: {response.text}")
            
            data = response.json()
            models = data.get("models", [])
            supported_models = [
                {
                    "id": m["name"],
                    "display_name": m.get("displayName", m["name"].split("/")[-1]),
                    "description": m.get("description", "")
                }
                for m in models if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
            return supported_models
            
        else: # provider == "openai" 或其他硅基流动等兼容源
            if not base_url:
                raise HTTPException(status_code=400, detail="OpenAI 兼容源需要提供 Base URL")
            url = f"{base_url.rstrip('/')}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"拉取模型失败: {response.text}")
            
            data = response.json()
            models = data.get("data", [])
            supported_models = [
                {
                    "id": m.get("id", ""),
                    "display_name": m.get("id", ""), # 大多数 OpenAI 返回没有单独的 display_name
                    "description": m.get("owned_by", "")
                }
                for m in models if m.get("id")
            ]
            
            # 对模型列表按照名称简单排序
            supported_models.sort(key=lambda x: x["id"])
            return supported_models

@router.post("/analyze")
async def analyze_lab_data(req: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    """
    汇总全维度实验室数据并调用 Gemini API 进行深度分析
    """
    # 1. 汇总数据
    try:
        period_label, period_days = resolve_period_days(req.analysis_period)
        data_context = await get_full_lab_context(db, period_days, period_label)
        
        # 2. 组装最终 Prompt
        final_prompt = f"{req.prompt_template}\n\n以下是当下的实验室运行数据汇总（JSON 格式）：\n{json.dumps(data_context, ensure_ascii=False, indent=2)}"
        
        # 3. 根据不同的厂商提供商发送相应的 API 请求
        async with httpx.AsyncClient(timeout=60.0) as client:
            if req.provider == "gemini":
                payload = {
                    "contents": [{
                        "parts": [{"text": final_prompt}]
                    }]
                }
                headers = {"Content-Type": "application/json"}
                url = f"https://generativelanguage.googleapis.com/v1beta/{req.model_id}:generateContent?key={req.api_key}"
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"Gemini API 错误: {response.text}")
                
                result = response.json()
                try:
                    ai_text = result['candidates'][0]['content']['parts'][0]['text']
                    return {"analysis": ai_text}
                except (KeyError, IndexError) as e:
                    raise HTTPException(status_code=500, detail="解析 Gemini 返回结果失败")

            else: # provider == "openai" 或兼容厂商（如硅基流动）
                if not req.base_url:
                    raise HTTPException(status_code=400, detail="OpenAI 兼容源需要提供 Base URL")
                
                payload = {
                    "model": req.model_id.replace("models/", ""), # 兼容此前前端可能存在的前缀
                    "messages": [
                        {"role": "user", "content": final_prompt}
                    ],
                    # 可以加入 temperature=0.7 等默认参数
                }
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {req.api_key}"
                }
                url = f"{req.base_url.rstrip('/')}/chat/completions"
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"API 调用失败: {response.text}")
                
                result = response.json()
                try:
                    ai_text = result['choices'][0]['message']['content']
                    return {"analysis": ai_text}
                except (KeyError, IndexError) as e:
                    raise HTTPException(status_code=500, detail="解析生成结果失败")

    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=f"分析执行失败: {str(e)}")

async def get_full_lab_context(db: AsyncSession, period_days: int, period_label: str):
    """提取全维度实验室统计数据（按分析周期动态汇总）"""
    
    # 获取设备概况
    eq_query = text("""
        SELECT equipment_id, name, status, current_usage_count, max_usage_limit 
        FROM Equipment
    """)
    eq_res = await db.execute(eq_query)
    equipment = [dict(row._mapping) for row in eq_res.fetchall()]
    
    # 获取耗材概况
    cs_query = text("""
        SELECT consumable_id, name, quantity, threshold 
        FROM Consumable
    """)
    cs_res = await db.execute(cs_query)
    consumables = [dict(row._mapping) for row in cs_res.fetchall()]
    
    # 获取分析周期内预约统计
    res_query = text("""
        SELECT e.name as equipment_name, COUNT(r.reservation_id) as usage_count,
               AVG(strftime('%s', r.actual_return_time) - strftime('%s', r.start_time)) / 3600 as avg_hours
        FROM ReservationRecord r
        JOIN Equipment e ON r.equipment_id = e.equipment_id
        WHERE r.start_time >= datetime('now', '-' || :period_days || ' days')
        GROUP BY e.equipment_id
    """)
    res_res = await db.execute(res_query, {"period_days": period_days})
    recent_usage = [dict(row._mapping) for row in res_res.fetchall()]
    
    # 获取分析周期内耗材申领规律
    req_query = text("""
        SELECT c.name as consumable_name, SUM(m.quantity) as total_quantity,
               COUNT(m.requisition_id) as request_count
        FROM MaterialRequisition m
        JOIN Consumable c ON m.consumable_id = c.consumable_id
        WHERE m.status = 'Approved' AND m.apply_date >= datetime('now', '-' || :period_days || ' days')
        GROUP BY c.consumable_id
    """)
    req_res = await db.execute(req_query, {"period_days": period_days})
    recent_consumption = [dict(row._mapping) for row in req_res.fetchall()]
    
    # 获取成员活跃度（Top 5）
    member_query = text("""
        SELECT m.name, m.role, 
               (SELECT COUNT(*) FROM ReservationRecord WHERE member_id = m.member_id) as total_reservations,
               (SELECT SUM(quantity) FROM MaterialRequisition WHERE member_id = m.member_id AND status = 'Approved') as total_consumables
        FROM LabMember m
        ORDER BY (total_reservations + total_consumables) DESC
        LIMIT 5
    """)
    member_res = await db.execute(member_query)
    top_members = [dict(row._mapping) for row in member_res.fetchall()]
    
    # 获取最近 10 条预警
    warn_query = text("SELECT message, created_at FROM WarningLog ORDER BY created_at DESC LIMIT 10")
    warn_res = await db.execute(warn_query)
    recent_warnings = [dict(row._mapping) for row in warn_res.fetchall()]

    return {
        "summary": {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M (Current Server Time)"),
            "analysis_window": period_label,
            "analysis_window_days": period_days,
            "total_equipment": len(equipment),
            "total_consumables": len(consumables)
        },
        "equipment_status": equipment,
        "consumable_inventory": consumables,
        "recent_period_usage": recent_usage,
        "recent_period_consumption": recent_consumption,
        "active_members": top_members,
        "recent_warnings": recent_warnings
    }
