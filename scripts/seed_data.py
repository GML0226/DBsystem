import asyncio
import random
from datetime import datetime, timedelta, date
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.models import (
    Base, LabMember, Equipment, Consumable, 
    ReservationRecord, MaterialRequisition, 
    RoleEnum, StatusEnum, RequisitionStatusEnum, WarningLog
)

async def seed_data():
    async with SessionLocal() as session:
        print("Cleaning existing data...")
        await session.execute(text("DELETE FROM MaterialRequisition"))
        await session.execute(text("DELETE FROM ReservationRecord"))
        await session.execute(text("DELETE FROM WarningLog"))
        await session.execute(text("DELETE FROM LabMember"))
        await session.execute(text("DELETE FROM Equipment"))
        await session.execute(text("DELETE FROM Consumable"))
        await session.commit()

    async with SessionLocal() as session:
        print("Seeding LabMembers...")
        mentors = [LabMember(name=f"{n}教授", role=RoleEnum.Mentor) for n in ["张", "王", "李", "赵", "孙"]]
        session.add_all(mentors)
        await session.flush()
        students = []
        for mentor in mentors:
            for j in range(5):
                students.append(LabMember(name=f"{mentor.name[0]}门下_{j+1}", role=RoleEnum.Student, mentor_id=mentor.member_id))
        session.add_all(students)
        await session.flush()
        all_members = mentors + students

        print("Seeding Equipment...")
        equipment_data = [
            ("高分辨质谱仪 (HRMS-X1)", 50, 48, StatusEnum.Available),
            ("冷冻电镜 (Titan Krios)", 30, 10, StatusEnum.Available),
            ("激光共聚焦显微镜 (LSM 980)", 100, 95, StatusEnum.Occupied),
            ("全自动生化分析仪 (AU5800)", 200, 210, StatusEnum.Maintenance),
            ("超高速离心机 (Optima XPN)", 150, 20, StatusEnum.Available),
            ("二氧化碳培养箱 (Heracell)", 365, 300, StatusEnum.Occupied),
            ("流式细胞仪 (BD FACSAria)", 80, 75, StatusEnum.Available),
            ("PCR 扩增仪 (Mastercycler)", 500, 480, StatusEnum.Available),
            ("核磁共振波谱仪", 60, 55, StatusEnum.Available),
            ("荧光定量 PCR 仪", 300, 280, StatusEnum.Available),
        ]
        equipment_list = [Equipment(name=n, status=s, max_usage_limit=m, current_usage_count=c, last_maintenance_date=date.today()-timedelta(days=random.randint(5,300))) for n, m, c, s in equipment_data]
        session.add_all(equipment_list)

        print("Seeding Consumables...")
        consumable_configs = [
            ("1.5ml 离心管", 500, 50), ("200ul 移液吸头", 400, 80), ("1000ul 移液吸头", 300, 80),
            ("PBS 缓冲液", 50, 10), ("DMEM 培养基", 40, 10), ("胎牛血清 (FBS)", 10, 3),
            ("液氮 (100L)", 20, 5), ("无水乙醇", 100, 20), ("乳胶手套 (M)", 200, 50),
            ("封口膜 (Parafilm)", 100, 20), ("琼脂糖 (500g)", 10, 2)
        ]
        consumables = [Consumable(name=n, quantity=q, threshold=t) for n, q, t in consumable_configs]
        session.add_all(consumables)
        await session.flush()
        
        # 预设库存追踪
        stock_map = {c.consumable_id: c.quantity for c in consumables}

        print("Generating 12-month Reservations...")
        now = datetime.now()
        for _ in range(150):
            d_ago = random.randint(0, 365)
            st = now - timedelta(days=d_ago, hours=random.randint(1, 24))
            res = ReservationRecord(
                member_id=random.choice(all_members).member_id,
                equipment_id=random.choice(equipment_list).equipment_id,
                start_time=st,
                end_time=st + timedelta(hours=random.randint(1,8)),
                actual_return_time=st + timedelta(hours=random.randint(1,10)) if random.random() > 0.1 else None
            )
            session.add(res)

        print("Generating 12-month Requisitions (ensuring non-negative stock)...")
        req_dates = sorted([now - timedelta(days=random.randint(0, 365), seconds=random.randint(0, 86400)) for _ in range(120)])
        
        for r_date in req_dates:
            c = random.choice(consumables)
            req_qty = random.randint(1, 10)
            
            # 决定状态：默认为 Approved，如果库存不够则 Rejected
            status = RequisitionStatusEnum.Approved
            if stock_map[c.consumable_id] < req_qty:
                status = RequisitionStatusEnum.Rejected
            
            # 如果是 Approved，手动减去 stock_map
            # 注意：实际数据库库存会由触发器处理，所以我们不需要在 commit 之后手动 UPDATE Consumable 表
            if status == RequisitionStatusEnum.Approved:
                stock_map[c.consumable_id] -= req_qty
            
            req = MaterialRequisition(
                member_id=random.choice(all_members).member_id,
                consumable_id=c.consumable_id,
                quantity=req_qty,
                status=status,
                apply_date=r_date
            )
            session.add(req)

        # 增加一些告警日志以显示系统能力
        warning_messages = [
            "警报：1.5ml 离心管 库存极低",
            "警报：Titan Krios 即将达到 30 次维保阈值",
            "警报：全自动生化分析仪 已处于维保状态",
            "警报：PBS 缓冲液 已耗尽",
            "警报：液氮库存不足 5L",
        ]
        for msg in warning_messages:
            session.add(WarningLog(message=msg, created_at=now - timedelta(days=random.randint(0, 10))))

        await session.commit()
        print("Successfully seeded database with consistent data!")

if __name__ == "__main__":
    asyncio.run(seed_data())
