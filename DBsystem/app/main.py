from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import members, equipment, inventory, dashboard, system, ai, graph
from app.core.database import engine
from sqlalchemy import text
from app.models.models import Base

# 初始化 FastAPI 应用
app = FastAPI(title="Lab Management System")

# 在应用启动时自动初始化数据库表
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # 如果表不存在，则根据 SQLAlchemy 模型创建所有表
        await conn.run_sync(Base.metadata.create_all)
        
        # 建立 SQLite 触发器
        # 1. 插入时如果状态就已经是 Approved
        trigger_insert = """
        CREATE TRIGGER IF NOT EXISTS trg_material_req_insert_approved
        AFTER INSERT ON MaterialRequisition
        FOR EACH ROW
        WHEN NEW.status = 'Approved'
        BEGIN
            UPDATE Consumable SET quantity = quantity - NEW.quantity WHERE consumable_id = NEW.consumable_id;
            INSERT INTO WarningLog (message) 
            SELECT '警报：' || name || ' 库存异常/不足！当前库存：' || quantity || '，低于阈值 ' || threshold 
            FROM Consumable WHERE consumable_id = NEW.consumable_id AND quantity < threshold;
        END;
        """
        # 2. 更新时变为 Approved
        trigger_update = """
        CREATE TRIGGER IF NOT EXISTS trg_material_req_update_approved
        AFTER UPDATE OF status ON MaterialRequisition
        FOR EACH ROW
        WHEN NEW.status = 'Approved' AND OLD.status != 'Approved'
        BEGIN
            UPDATE Consumable SET quantity = quantity - NEW.quantity WHERE consumable_id = NEW.consumable_id;
            INSERT INTO WarningLog (message) 
            SELECT '警报：' || name || ' 库存异常/不足！当前库存：' || quantity || '，低于阈值 ' || threshold 
            FROM Consumable WHERE consumable_id = NEW.consumable_id AND quantity < threshold;
        END;
        """
        await conn.execute(text(trigger_insert))
        await conn.execute(text(trigger_update))

# 包含各模块的 API 路由
app.include_router(members.router)
app.include_router(equipment.router)
app.include_router(inventory.router)
app.include_router(dashboard.router)
app.include_router(system.router)
app.include_router(ai.router)
app.include_router(graph.router)

# 挂载静态文件目录 (HTML, CSS, JS)
# 放在路由最后，以确保 API 路由优先级更高
app.mount("/", StaticFiles(directory="static", html=True), name="static")
