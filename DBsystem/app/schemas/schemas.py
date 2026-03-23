from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.models import RoleEnum, StatusEnum, RequisitionStatusEnum

# --- 实验室成员 Schema ---
class LabMemberBase(BaseModel):
    """实验室成员基础模型"""
    name: str                   # 姓名
    role: RoleEnum              # 角色
    mentor_id: Optional[int] = None # 导师ID

class LabMemberCreate(LabMemberBase):
    """用于创建成员的 Schema"""
    pass

class LabMemberUpdate(BaseModel):
    """用于更新成员的 Schema"""
    name: Optional[str] = None
    role: Optional[RoleEnum] = None
    mentor_id: Optional[int] = None

class LabMember(LabMemberBase):
    """用于展示/返回成员信息的 Schema"""
    member_id: int
    # 增加关联关系展示
    reservations: List["Reservation"] = []
    requisitions: List["MaterialRequisition"] = []
    model_config = ConfigDict(from_attributes=True)

# --- 设备 Schema ---
class EquipmentBase(BaseModel):
    """设备基础模型"""
    name: str                                # 设备名称
    status: StatusEnum = StatusEnum.Available # 状态
    max_usage_limit: int = 10                # 维护次数限制
    last_maintenance_date: date              # 上次维护日期

class EquipmentCreate(EquipmentBase):
    """用于创建设备的 Schema"""
    pass

class EquipmentUpdate(BaseModel):
    """用于更新设备的 Schema"""
    name: Optional[str] = None
    status: Optional[StatusEnum] = None
    max_usage_limit: Optional[int] = None
    current_usage_count: Optional[int] = None
    last_maintenance_date: Optional[date] = None

class Equipment(EquipmentBase):
    """用于展示设备信息的 Schema"""
    equipment_id: int
    current_usage_count: int
    model_config = ConfigDict(from_attributes=True)

# --- 消耗品 Schema ---
class ConsumableBase(BaseModel):
    """消耗品基础模型"""
    name: str                # 名称
    quantity: int = 0        # 数量
    threshold: int = 10      # 预警阈值

class ConsumableCreate(ConsumableBase):
    """用于创建消耗品的 Schema"""
    pass

class ConsumableUpdate(BaseModel):
    """用于更新消耗品的 Schema"""
    name: Optional[str] = None
    quantity: Optional[int] = None
    threshold: Optional[int] = None

class Consumable(ConsumableBase):
    """用于展示消耗品信息的 Schema"""
    consumable_id: int
    model_config = ConfigDict(from_attributes=True)

# --- 预约 Schema ---
class ReservationBase(BaseModel):
    """预约基础模型"""
    member_id: int           # 成员ID
    equipment_id: int        # 设备ID
    start_time: datetime     # 开始时间
    end_time: datetime       # 结束时间

class ReservationCreate(ReservationBase):
    """用于创建预约的 Schema"""
    pass

class ReservationUpdate(BaseModel):
    """用于更新预约的 Schema"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class Reservation(ReservationBase):
    """用于展示预约详情的 Schema"""
    reservation_id: int
    actual_return_time: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# --- 领料申请 Schema ---
class MaterialRequisitionBase(BaseModel):
    """领料申请基础模型"""
    member_id: int           # 申请人ID
    consumable_id: int       # 消耗品ID
    quantity: int            # 数量
    status: RequisitionStatusEnum = RequisitionStatusEnum.Pending # 申请状态

class MaterialRequisitionCreate(MaterialRequisitionBase):
    """用于创建领料申请的 Schema"""
    pass

class MaterialRequisitionUpdate(BaseModel):
    """用于更新领料申请的 Schema"""
    quantity: Optional[int] = None
    status: Optional[RequisitionStatusEnum] = None

class MaterialRequisition(MaterialRequisitionBase):
    """用于展示领料申请详情的 Schema"""
    requisition_id: int
    apply_date: datetime     # 申请时间
    model_config = ConfigDict(from_attributes=True)
