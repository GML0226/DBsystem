import enum
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Date, TIMESTAMP, text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class RoleEnum(enum.Enum):
    """成员角色枚举"""
    Mentor = "Mentor"      # 导师
    Student = "Student"    # 学生

class StatusEnum(enum.Enum):
    """设备状态枚举"""
    Available = "Available"      # 可用
    Occupied = "Occupied"        # 占用
    Maintenance = "Maintenance"  # 维护中

class RequisitionStatusEnum(enum.Enum):
    """领料申请状态枚举"""
    Pending = "Pending"    # 待审批
    Approved = "Approved"  # 已批准
    Rejected = "Rejected"  # 已拒绝

class LabMember(Base):
    """实验室成员模型"""
    __tablename__ = "LabMember"
    
    member_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)                                # 姓名
    role = Column(Enum(RoleEnum), nullable=False)                            # 角色
    mentor_id = Column(Integer, ForeignKey("LabMember.member_id"), nullable=True) # 导师ID（自引用）
    
    # 关系映射
    mentor = relationship("LabMember", remote_side=[member_id], backref="students")
    reservations = relationship("ReservationRecord", back_populates="member")
    requisitions = relationship("MaterialRequisition", back_populates="member")

class Equipment(Base):
    """实验设备模型"""
    __tablename__ = "Equipment"
    
    equipment_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)                               # 设备名称
    status = Column(Enum(StatusEnum), default=StatusEnum.Available)         # 当前状态
    max_usage_limit = Column(Integer, nullable=False, default=10)           # 维护触发的使用次数阈值
    current_usage_count = Column(Integer, nullable=False, default=0)         # 当前累计使用次数
    last_maintenance_date = Column(Date, nullable=False)                    # 上次维护日期
    
    # 关系映射
    reservations = relationship("ReservationRecord", back_populates="equipment")

class Consumable(Base):
    """消耗品/物料模型"""
    __tablename__ = "Consumable"
    
    consumable_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)                               # 物料名称
    quantity = Column(Integer, nullable=False, default=0)                   # 现有库存数量
    threshold = Column(Integer, nullable=False, default=10)                  # 库存预警阈值
    
    # 关系映射
    requisitions = relationship("MaterialRequisition", back_populates="consumable")

class ReservationRecord(Base):
    """设备预约记录模型"""
    __tablename__ = "ReservationRecord"
    
    reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("LabMember.member_id"))           # 预约人ID
    equipment_id = Column(Integer, ForeignKey("Equipment.equipment_id"))     # 设备ID
    start_time = Column(DateTime, nullable=False, index=True)               # 借出时间/预约开始时间
    end_time = Column(DateTime, nullable=False, index=True)                 # 预期归还/结束时间
    actual_return_time = Column(DateTime, nullable=True)                    # 实际归还时间
    
    member = relationship("LabMember", back_populates="reservations")
    equipment = relationship("Equipment", back_populates="reservations")

class MaterialRequisition(Base):
    """物料领用申请模型"""
    __tablename__ = "MaterialRequisition"
    
    requisition_id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("LabMember.member_id"))           # 申请人ID
    consumable_id = Column(Integer, ForeignKey("Consumable.consumable_id"))  # 物料ID
    quantity = Column(Integer, nullable=False)                               # 申请数量
    status = Column(Enum(RequisitionStatusEnum), default=RequisitionStatusEnum.Pending) # 审批状态
    apply_date = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")) # 申请时间
    
    member = relationship("LabMember", back_populates="requisitions")
    consumable = relationship("Consumable", back_populates="requisitions")

class WarningLog(Base):
    """告警日志模型"""
    __tablename__ = "WarningLog"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String(255))                                            # 告警信息内容
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")) # 记录时间
