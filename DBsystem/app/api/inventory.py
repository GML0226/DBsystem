from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from typing import List
from app.core.database import get_db
from app.models.models import Consumable as ConsumableModel, MaterialRequisition as RequisitionModel
from app.schemas.schemas import Consumable, ConsumableCreate, ConsumableUpdate, MaterialRequisition, MaterialRequisitionCreate, MaterialRequisitionUpdate

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.post("/consumables", response_model=Consumable)
async def create_consumable(consumable: ConsumableCreate, db: AsyncSession = Depends(get_db)):
    """录入新的消耗品"""
    db_consumable = ConsumableModel(**consumable.model_dump())
    db.add(db_consumable)
    await db.commit()
    await db.refresh(db_consumable)
    return db_consumable

@router.get("/consumables", response_model=List[Consumable])
async def read_consumables(db: AsyncSession = Depends(get_db)):
    """获取所有消耗品及库存列表"""
    result = await db.execute(select(ConsumableModel))
    return result.scalars().all()

@router.get("/consumables/{consumable_id}", response_model=Consumable)
async def read_consumable_by_id(consumable_id: int, db: AsyncSession = Depends(get_db)):
    """获取特定消耗品详情"""
    result = await db.execute(select(ConsumableModel).where(ConsumableModel.consumable_id == consumable_id))
    db_consumable = result.scalar_one_or_none()
    if db_consumable is None:
        raise HTTPException(status_code=404, detail="未找到该物品")
    return db_consumable

@router.put("/consumables/{consumable_id}", response_model=Consumable)
async def update_consumable(consumable_id: int, consumable_update: ConsumableUpdate, db: AsyncSession = Depends(get_db)):
    """更新消耗品信息"""
    result = await db.execute(select(ConsumableModel).where(ConsumableModel.consumable_id == consumable_id))
    db_consumable = result.scalar_one_or_none()
    if db_consumable is None:
        raise HTTPException(status_code=404, detail="未找到该物品")
    
    update_data = consumable_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_consumable, key, value)
        
    await db.commit()
    await db.refresh(db_consumable)
    return db_consumable

@router.post("/requisitions", response_model=MaterialRequisition)
async def create_requisition(requisition: MaterialRequisitionCreate, db: AsyncSession = Depends(get_db)):
    """提交领料申请"""
    db_requisition = RequisitionModel(**requisition.model_dump())
    db.add(db_requisition)
    await db.commit()
    await db.refresh(db_requisition)
    return db_requisition

@router.delete("/consumables/{consumable_id}")
async def delete_consumable(consumable_id: int, db: AsyncSession = Depends(get_db)):
    """删除消耗品"""
    result = await db.execute(select(ConsumableModel).where(ConsumableModel.consumable_id == consumable_id))
    db_consumable = result.scalar_one_or_none()
    if db_consumable is None:
        raise HTTPException(status_code=404, detail="未找到该物品")
    await db.delete(db_consumable)
    await db.commit()
    return {"message": "物品已成功删除"}

@router.get("/requisitions", response_model=List[MaterialRequisition])
async def read_all_requisitions(db: AsyncSession = Depends(get_db)):
    """获取所有领料申请"""
    result = await db.execute(select(RequisitionModel))
    return result.scalars().all()

@router.get("/requisitions/{requisition_id}", response_model=MaterialRequisition)
async def read_requisition_by_id(requisition_id: int, db: AsyncSession = Depends(get_db)):
    """获取领料申请详情"""
    result = await db.execute(select(RequisitionModel).where(RequisitionModel.requisition_id == requisition_id))
    db_requisition = result.scalar_one_or_none()
    if db_requisition is None:
        raise HTTPException(status_code=404, detail="未找到该领料申请")
    return db_requisition

@router.put("/requisitions/{requisition_id}", response_model=MaterialRequisition)
async def update_requisition(
    requisition_id: int, 
    requisition_update: MaterialRequisitionUpdate, 
    operator_id: int,  # 传入当前模拟的操作人员ID
    db: AsyncSession = Depends(get_db)):
    """更新领料申请（如审批通过或拒绝），仅导师可操作"""
    # 1. 查询操作人是否是导师
    from app.models.models import LabMember as LabMemberModel
    operator = await db.execute(select(LabMemberModel).where(LabMemberModel.member_id == operator_id))
    operator_user = operator.scalar_one_or_none()
    if not operator_user or operator_user.role.value != "Mentor":
        raise HTTPException(status_code=403, detail="权限不足：只有导师可以审批申请！")

    result = await db.execute(select(RequisitionModel).where(RequisitionModel.requisition_id == requisition_id))
    db_requisition = result.scalar_one_or_none()
    if db_requisition is None:
        raise HTTPException(status_code=404, detail="未找到该领料申请")
    
    update_data = requisition_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_requisition, key, value)
        
    await db.commit()
    await db.refresh(db_requisition)
    return db_requisition

@router.delete("/requisitions/{requisition_id}")
async def delete_requisition(requisition_id: int, db: AsyncSession = Depends(get_db)):
    """删除领料申请"""
    result = await db.execute(select(RequisitionModel).where(RequisitionModel.requisition_id == requisition_id))
    db_requisition = result.scalar_one_or_none()
    if db_requisition is None:
        raise HTTPException(status_code=404, detail="未找到该领料申请")
    await db.delete(db_requisition)
    await db.commit()
    return {"message": "领料申请已成功删除"}

@router.get("/reports/reservation-details")
async def get_reservation_details(db: AsyncSession = Depends(get_db)):
    """查询三表连接的复杂视图：View_ReservationDetails"""
    result = await db.execute(text("SELECT * FROM View_ReservationDetails"))
    columns = ["reservation_id", "member_name", "equipment_name", "start_time", "end_time"]
    return [dict(zip(columns, row)) for row in result.fetchall()]
