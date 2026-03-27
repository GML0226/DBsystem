from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/maintenance")
async def get_maintenance_list(db: AsyncSession = Depends(get_db)):
    """获取即将达到使用限额需维保的设备清单（使用率 > 80%）"""
    query = text("""
        SELECT equipment_id, name, status, current_usage_count, max_usage_limit,
               CAST(current_usage_count AS FLOAT) / max_usage_limit as usage_rate
        FROM Equipment
        WHERE (CAST(current_usage_count AS FLOAT) / max_usage_limit >= 0.8 OR status = 'Maintenance')
    """)
    result = await db.execute(query)
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]

@router.get("/consumable-ranking")
async def get_consumable_ranking(days: int = 90, db: AsyncSession = Depends(get_db)):
    """获取指定天数内的耗材消耗排行榜（默认一季度/90天）"""
    query = text("""
        SELECT c.consumable_id, c.name, SUM(m.quantity) as total_consumed
        FROM MaterialRequisition m
        JOIN Consumable c ON m.consumable_id = c.consumable_id
        WHERE m.status = 'Approved'
          AND m.apply_date >= datetime('now', '-' || :days || ' days')
        GROUP BY c.consumable_id
        ORDER BY total_consumed DESC
    """)
    result = await db.execute(query, {"days": days})
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]

@router.get("/equipment-ranking")
async def get_equipment_ranking(db: AsyncSession = Depends(get_db)):
    """获取高频借阅设备排行"""
    query = text("""
        SELECT e.equipment_id, e.name, COUNT(r.reservation_id) as borrow_count
        FROM ReservationRecord r
        JOIN Equipment e ON r.equipment_id = e.equipment_id
        GROUP BY e.equipment_id
        ORDER BY borrow_count DESC
        LIMIT 10
    """)
    result = await db.execute(query)
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]

@router.get("/mentor-stats/{mentor_id}")
async def get_mentor_stats(mentor_id: int, db: AsyncSession = Depends(get_db)):
    """统计某位导师及其名下所有学生的资源使用情况（设备使用总次数及耗材消耗量）"""
    query = text("""
        SELECT 
            (SELECT COUNT(*) 
             FROM ReservationRecord r 
             JOIN LabMember m ON r.member_id = m.member_id 
             WHERE m.mentor_id = :mentor_id OR m.member_id = :mentor_id) as total_equipment_uses,
             
            (SELECT COALESCE(SUM(mr.quantity), 0) 
             FROM MaterialRequisition mr 
             JOIN LabMember m ON mr.member_id = m.member_id 
             WHERE (m.mentor_id = :mentor_id OR m.member_id = :mentor_id) 
               AND mr.status = 'Approved') as total_consumable_used
    """)
    result = await db.execute(query, {"mentor_id": mentor_id})
    row = result.mappings().fetchone()
    
    if not row:
        return {"total_equipment_uses": 0, "total_consumable_used": 0}
        
    return {
        "total_equipment_uses": row["total_equipment_uses"] or 0,
        "total_consumable_used": row["total_consumable_used"] or 0
    }

@router.get("/warnings")
async def get_warning_logs(db: AsyncSession = Depends(get_db)):
    """获取库存预警日志"""
    query = text("SELECT * FROM WarningLog ORDER BY created_at DESC LIMIT 50")
    result = await db.execute(query)
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]

@router.get("/equipment-insight/{equipment_id}")
async def get_equipment_insight(equipment_id: int, db: AsyncSession = Depends(get_db)):
    """反查：某设备的生命周期借用记录及总次数（不受维保清零影响）"""
    # 统计总次数
    count_query = text("""
        SELECT COUNT(*) FROM ReservationRecord WHERE equipment_id = :eq_id
    """)
    count_res = await db.execute(count_query, {"eq_id": equipment_id})
    total_uses = count_res.scalar() or 0
    
    # 获取详细历史
    history_query = text("""
        SELECT r.reservation_id, m.name as member_name, r.start_time, r.end_time, r.actual_return_time
        FROM ReservationRecord r
        JOIN LabMember m ON r.member_id = m.member_id
        WHERE r.equipment_id = :eq_id
        ORDER BY r.start_time DESC
    """)
    history_res = await db.execute(history_query, {"eq_id": equipment_id})
    history_cols = history_res.keys()
    history = [dict(zip(history_cols, row)) for row in history_res.fetchall()]
    
    return {
        "total_uses": total_uses,
        "history": history
    }

@router.get("/consumable-distribution/{consumable_id}")
async def get_consumable_distribution(consumable_id: int, db: AsyncSession = Depends(get_db)):
    """反查：某耗材在不同人员间的消耗分布统计"""
    query = text("""
        SELECT m.name as member_name, SUM(mr.quantity) as total_quantity
        FROM MaterialRequisition mr
        JOIN LabMember m ON mr.member_id = m.member_id
        WHERE mr.consumable_id = :c_id AND mr.status = 'Approved'
        GROUP BY m.member_id
        ORDER BY total_quantity DESC
    """)
    result = await db.execute(query, {"c_id": consumable_id})
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]
