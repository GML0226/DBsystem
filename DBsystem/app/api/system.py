from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from datetime import date, datetime, timedelta

router = APIRouter(prefix="/api/system", tags=["System"])

@router.post("/reset")
async def reset_database(db: AsyncSession = Depends(get_db)):
    """清空数据库所有数据并重置自增 ID"""
    try:
        # 按外键依赖逆序清空
        tables = [
            "WarningLog", 
            "MaterialRequisition", 
            "ReservationRecord", 
            "Equipment", 
            "Consumable", 
            "LabMember"
        ]
        for table in tables:
            await db.execute(text(f"DELETE FROM {table}"))
            # 安全地重置 SQLite 自增 ID
            try:
                await db.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{table}'"))
            except Exception:
                # 如果 sqlite_sequence 不存在（未插入过带自增的数据），则忽略
                pass
        
        await db.commit()
        return {"message": "Database reset successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/seed")
async def seed_database(db: AsyncSession = Depends(get_db)):
    """注入预设测试数据"""
    try:
        # 1. 先清空
        await reset_database(db)
        
        # 2. 注入成员
        # mentor_id=1, student_id=2,3
        await db.execute(text("INSERT INTO LabMember (member_id, name, role, mentor_id) VALUES (1, 'TechMentor', 'Mentor', NULL)"))
        await db.execute(text("INSERT INTO LabMember (member_id, name, role, mentor_id) VALUES (2, 'StudentA', 'Student', 1)"))
        await db.execute(text("INSERT INTO LabMember (member_id, name, role, mentor_id) VALUES (3, 'StudentB', 'Student', NULL)"))
        
        # 3. 注入设备
        # 示波器(1), 焊接台(2), 显微镜(3)
        today = date.today().isoformat()
        await db.execute(text(f"INSERT INTO Equipment (equipment_id, name, status, max_usage_limit, current_usage_count, last_maintenance_date) VALUES (1, '数字示波器', 'Available', 5, 2, '{today}')"))
        await db.execute(text(f"INSERT INTO Equipment (equipment_id, name, status, max_usage_limit, current_usage_count, last_maintenance_date) VALUES (2, '高频焊接台', 'Occupied', 2, 1, '{today}')"))
        await db.execute(text(f"INSERT INTO Equipment (equipment_id, name, status, max_usage_limit, current_usage_count, last_maintenance_date) VALUES (3, '电子显微镜', 'Maintenance', 10, 10, '{today}')"))
        
        # 4. 注入耗材
        # 开发板(1), 传感器(2)
        await db.execute(text("INSERT INTO Consumable (consumable_id, name, quantity, threshold) VALUES (1, 'STM32开发板', 50, 10)"))
        await db.execute(text("INSERT INTO Consumable (consumable_id, name, quantity, threshold) VALUES (2, '超声波传感器', 5, 10)"))
        
        # 5. 注入预约历史
        # 设备1的一次历史借用（已还）
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        day_before = (datetime.now() - timedelta(days=2)).isoformat()
        await db.execute(text(f"INSERT INTO ReservationRecord (member_id, equipment_id, start_time, end_time, actual_return_time) VALUES (2, 1, '{day_before}', '{yesterday}', '{yesterday}')"))
        # 设备2的当前借用记录
        await db.execute(text(f"INSERT INTO ReservationRecord (member_id, equipment_id, start_time, end_time, actual_return_time) VALUES (2, 2, '{yesterday}', '{today}', NULL)"))
        
        # 6. 注入耗材领用
        # A 领了 10 个开发板
        await db.execute(text("INSERT INTO MaterialRequisition (member_id, consumable_id, quantity, status) VALUES (2, 1, 10, 'Approved')"))
        # B 领了 2 个开发板（待审批）
        await db.execute(text("INSERT INTO MaterialRequisition (member_id, consumable_id, quantity, status) VALUES (3, 1, 2, 'Pending')"))
        # A 领了 5 个传感器
        await db.execute(text("INSERT INTO MaterialRequisition (member_id, consumable_id, quantity, status) VALUES (2, 2, 5, 'Approved')"))
        
        # 7. 注入一条预警
        await db.execute(text("INSERT INTO WarningLog (message) VALUES ('库存预警：商品 [超声波传感器] 余量 5 已低于阈值 10')"))

        await db.commit()
        return {"message": "Seed data injected successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
