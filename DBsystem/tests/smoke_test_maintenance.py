
import asyncio
import httpx
from datetime import date
from app.main import app

async def smoke_test():
    # 确保数据库表已创建
    from app.core.database import engine
    from app.models.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        # 1. Create Mentor
        mentor_resp = await client.post("/members/", json={"name": "TechMentor", "role": "Mentor"})
        mentor_id = mentor_resp.json()["member_id"]
        
        # 2. Create Student
        student_resp = await client.post("/members/", json={"name": "JuniorStudent", "role": "Student"})
        student_id = student_resp.json()["member_id"]
        
        # 3. Create Equipment (Limit 1)
        equip_resp = await client.post("/equipment/", json={
            "name": "TestScope", 
            "max_usage_limit": 1,
            "last_maintenance_date": date.today().isoformat()
        })
        equip_id = equip_resp.json()["equipment_id"]
        print(f"Created Equipment #{equip_id}")
        
        # 4. 预约该设备 (借出)
        # 这一步应该会使设备状态变为 Occupied (因为 max_usage_limit=1 会直接切到 Maintenance)
        # 我们测试一个限额为 2 的，这样第一次借出是 Occupied，第二次是 Maintenance
        eq_resp2 = await client.post("/equipment/", json={
            "name": "FlowTest",
            "max_usage_limit": 2,
            "last_maintenance_date": date.today().isoformat()
        })
        eq_id_flow = eq_resp2.json()["equipment_id"]
        
        print(f"Testing Flow with Equipment #{eq_id_flow}")
        
        # 第一次借出
        res_resp = await client.post("/equipment/reserve", json={
            "member_id": student_id,
            "equipment_id": eq_id_flow,
            "start_time": "2026-03-17T10:00:00",
            "end_time": "2026-03-17T11:00:00"
        })
        res_data = res_resp.json()
        reservation_id = res_data["reservation_id"]
        print(f"Borrow Status: {res_resp.status_code}")
        
        # 检查设备状态应为 Occupied
        status_resp = await client.get(f"/equipment/{eq_id_flow}")
        print(f"Status after borrow: {status_resp.json()['status']}")
        assert status_resp.json()["status"] == "Occupied"

        # 执行归还
        ret_resp = await client.post(f"/equipment/return/{reservation_id}")
        print(f"Return Status: {ret_resp.status_code}")
        
        # 检查设备状态应恢复为 Available
        status_resp_after = await client.get(f"/equipment/{eq_id_flow}")
        print(f"Status after return: {status_resp_after.json()['status']}")
        assert status_resp_after.json()["status"] == "Available"

        # 第二次借出 -> 此时累计次数达到 2，应触发 Maintenance
        await client.post("/equipment/reserve", json={
            "member_id": student_id,
            "equipment_id": eq_id_flow,
            "start_time": "2026-03-18T10:00:00",
            "end_time": "2026-03-18T11:00:00"
        })
        status_resp_maint = await client.get(f"/equipment/{eq_id_flow}")
        print(f"Status after 2nd borrow (Limit 2): {status_resp_maint.json()['status']}")
        assert status_resp_maint.json()["status"] == "Maintenance"

        # 验证手动更新错误修复 (不传 operator_id 应报错或 422，此处因定义了可选应允许普通字段修改，但状态修改需 operator_id)
        # 我们测试：导师手动恢复 Maintenance 设备
        reset_resp = await client.put(f"/equipment/{eq_id_flow}?operator_id={mentor_id}", json={
            "status": "Available"
        })
        print(f"Mentor Reset Status: {reset_resp.status_code}")
        assert reset_resp.status_code == 200
        assert reset_resp.json()["status"] == "Available"
        assert reset_resp.json()["current_usage_count"] == 0

        print("--- Flow Test Passed ---")

if __name__ == "__main__":
    asyncio.run(smoke_test())
