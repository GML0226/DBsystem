from fastapi import APIRouter, Depends, HTTPException
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from app.core.database import get_db
from app.models.models import Equipment as EquipmentModel, ReservationRecord as ReservationModel, StatusEnum
from app.schemas.schemas import Equipment, EquipmentCreate, EquipmentUpdate, Reservation, ReservationCreate

router = APIRouter(prefix="/equipment", tags=["Equipment"])

@router.post("/", response_model=Equipment)
async def create_equipment(equipment: EquipmentCreate, db: AsyncSession = Depends(get_db)):
    """录入新的实验设备"""
    db_equipment = EquipmentModel(**equipment.model_dump())
    db.add(db_equipment)
    await db.commit()
    await db.refresh(db_equipment)
    return db_equipment

@router.get("/", response_model=List[Equipment])
async def read_equipment(db: AsyncSession = Depends(get_db)):
    """获取所有设备列表"""
    result = await db.execute(select(EquipmentModel))
    return result.scalars().all()

@router.get("/{equipment_id}", response_model=Equipment)
async def read_equipment_by_id(equipment_id: int, db: AsyncSession = Depends(get_db)):
    """获取设备详情（包含预约情况）"""
    result = await db.execute(select(EquipmentModel).where(EquipmentModel.equipment_id == equipment_id))
    db_equipment = result.scalar_one_or_none()
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="未找到该设备")
    return db_equipment

@router.put("/{equipment_id}", response_model=Equipment)
async def update_equipment(
    equipment_id: int, 
    equipment_update: EquipmentUpdate, 
    operator_id: int = None, # 改为默认参数，避免非导师普通更新报错
    db: AsyncSession = Depends(get_db)):
    """更新设备信息：导师解锁并重置计数"""
    # 权限检查：如果涉及状态重置，仅导师可操作
    from app.models.models import LabMember as LabMemberModel
    
    update_data = equipment_update.model_dump(exclude_unset=True)
    new_status = update_data.get("status")
    
    # 如果要从维护中恢复，或者手动强行修改状态，需要鉴权
    if new_status:
        if not operator_id:
             raise HTTPException(status_code=400, detail="状态操作需要提供操作者ID")
        op_result = await db.execute(select(LabMemberModel).where(LabMemberModel.member_id == operator_id))
        operator = op_result.scalar_one_or_none()
        if not operator or operator.role.value != "Mentor":
            raise HTTPException(status_code=403, detail="权限不足：只有导师可以手动调整设备状态")

    result = await db.execute(select(EquipmentModel).where(EquipmentModel.equipment_id == equipment_id))
    db_equipment = result.scalar_one_or_none()
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="未找到该设备")
    
    update_data = equipment_update.model_dump(exclude_unset=True)
    
    # 逻辑核心：从 Maintenance 恢复 Available 时，重置计数和维保日期
    old_status = db_equipment.status
    new_status = update_data.get("status")
    
    # 修复：Pydantic 已将 status 转化为 StatusEnum 对象，应与 Enum 成员或其 .value 比较
    if old_status == StatusEnum.Maintenance and new_status == StatusEnum.Available:
        db_equipment.current_usage_count = 0
        db_equipment.last_maintenance_date = date.today()
    
    for key, value in update_data.items():
        setattr(db_equipment, key, value)
        
    await db.commit()
    await db.refresh(db_equipment)
    return db_equipment

@router.post("/reserve", response_model=Reservation)
async def reserve_equipment(reservation: ReservationCreate, db: AsyncSession = Depends(get_db)):
    """借出实验设备：状态锁定、计次自增、原子化操作"""
    # 启用事务性检查
    eq_result = await db.execute(select(EquipmentModel).where(EquipmentModel.equipment_id == reservation.equipment_id))
    db_equipment = eq_result.scalar_one_or_none()
    
    if not db_equipment:
        raise HTTPException(status_code=404, detail="未找到该设备")
    
    # 核心限制：只有 Available 状态可以借出
    if db_equipment.status == StatusEnum.Maintenance:
        raise HTTPException(status_code=403, detail="设备正处于维护锁定状态，无法预约")
    if db_equipment.status == StatusEnum.Occupied:
        raise HTTPException(status_code=400, detail="设备当前正在借用中，请勿重复操作")

    # 创建预约流水（此处即为借出动作）
    db_reservation = ReservationModel(**reservation.model_dump())
    db.add(db_reservation)
    
    # 修改设备状态为占用
    db_equipment.status = StatusEnum.Occupied
    
    # 计次自增
    db_equipment.current_usage_count += 1
    
    # 维保锁定检查
    if db_equipment.current_usage_count >= db_equipment.max_usage_limit:
        db_equipment.status = StatusEnum.Maintenance
    
    await db.commit()
    await db.refresh(db_reservation)
    return db_reservation

@router.post("/return/{reservation_id}", response_model=Reservation)
async def return_equipment(reservation_id: int, db: AsyncSession = Depends(get_db)):
    """归还实验设备：记录时间并恢复状态"""
    res_result = await db.execute(select(ReservationModel).where(ReservationModel.reservation_id == reservation_id))
    db_reservation = res_result.scalar_one_or_none()
    
    if not db_reservation:
        raise HTTPException(status_code=404, detail="未找到该预约记录")
    
    if db_reservation.actual_return_time:
        raise HTTPException(status_code=400, detail="该记录已完成归还，请勿重复操作")

    # 记录实际归还时间
    db_reservation.actual_return_time = datetime.now()
    
    # 尝试恢复设备状态
    eq_result = await db.execute(select(EquipmentModel).where(EquipmentModel.equipment_id == db_reservation.equipment_id))
    db_equipment = eq_result.scalar_one_or_none()
    
    if db_equipment:
        # 只有当前是 Occupied 且没有因为计次进入 Maintenance 时，才恢复为 Available
        if db_equipment.status == StatusEnum.Occupied:
            db_equipment.status = StatusEnum.Available
            
    await db.commit()
    await db.refresh(db_reservation)
    return db_reservation

@router.delete("/{equipment_id}")
async def delete_equipment(equipment_id: int, db: AsyncSession = Depends(get_db)):
    """删除实验室设备"""
    result = await db.execute(select(EquipmentModel).where(EquipmentModel.equipment_id == equipment_id))
    db_equipment = result.scalar_one_or_none()
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="未找到该设备")
    await db.delete(db_equipment)
    await db.commit()
    return {"message": "设备已成功删除"}

@router.get("/reservations/all", response_model=List[Reservation])
async def read_all_reservations(
    start_time: datetime = None,
    end_time: datetime = None,
    db: AsyncSession = Depends(get_db)):
    """获取所有预约记录，支持按照时间窗口筛选（过滤出与窗口重叠的记录）"""
    stmt = select(ReservationModel)
    if start_time:
        stmt = stmt.where(ReservationModel.end_time >= start_time)
    if end_time:
        stmt = stmt.where(ReservationModel.start_time <= end_time)
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.delete("/reservations/{reservation_id}")
async def delete_reservation(reservation_id: int, db: AsyncSession = Depends(get_db)):
    """删除或取消预约记录"""
    result = await db.execute(select(ReservationModel).where(ReservationModel.reservation_id == reservation_id))
    db_reservation = result.scalar_one_or_none()
    if db_reservation is None:
        raise HTTPException(status_code=404, detail="未找到该预约记录")
    await db.delete(db_reservation)
    await db.commit()
    return {"message": "预约已成功取消"}
