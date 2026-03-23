from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from app.core.database import get_db
from app.models.models import LabMember as LabMemberModel
from app.schemas.schemas import LabMember, LabMemberCreate, LabMemberUpdate

router = APIRouter(prefix="/members", tags=["Members"])

@router.post("/", response_model=LabMember)
async def create_member(member: LabMemberCreate, db: AsyncSession = Depends(get_db)):
    """创建新的实验室成员"""
    db_member = LabMemberModel(**member.model_dump())
    db.add(db_member)
    await db.flush()
    member_id = db_member.member_id
    await db.commit()
    
    # 重新查询以包含完整的 selectinload 结构，避免 Pydantic 发生 Lazy-load 相关错误
    result = await db.execute(
        select(LabMemberModel)
        .where(LabMemberModel.member_id == member_id)
        .options(selectinload(LabMemberModel.reservations), selectinload(LabMemberModel.requisitions))
    )
    return result.scalar_one()

@router.get("/", response_model=List[LabMember])
async def read_members(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """分页获取所有实验室成员列表（包含其关联的预约和领料记录）"""
    # 使用 selectinload 预加载关联关系，体现数据库的“一对多”关系
    result = await db.execute(
        select(LabMemberModel)
        .options(selectinload(LabMemberModel.reservations), selectinload(LabMemberModel.requisitions))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/{member_id}", response_model=LabMember)
async def read_member(member_id: int, db: AsyncSession = Depends(get_db)):
    """根据 ID 获取特定成员详情（包含其关联的预约和领料记录）"""
    result = await db.execute(
        select(LabMemberModel)
        .where(LabMemberModel.member_id == member_id)
        .options(selectinload(LabMemberModel.reservations), selectinload(LabMemberModel.requisitions))
    )
    db_member = result.scalar_one_or_none()
    if db_member is None:
        raise HTTPException(status_code=404, detail="未找到该成员")
    return db_member

@router.put("/{member_id}", response_model=LabMember)
async def update_member(member_id: int, member_update: LabMemberUpdate, db: AsyncSession = Depends(get_db)):
    """更新实验室成员信息"""
    result = await db.execute(
        select(LabMemberModel)
        .where(LabMemberModel.member_id == member_id)
        .options(selectinload(LabMemberModel.reservations), selectinload(LabMemberModel.requisitions))
    )
    db_member = result.scalar_one_or_none()
    if db_member is None:
        raise HTTPException(status_code=404, detail="未找到该成员")
    
    update_data = member_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_member, key, value)
        
    await db.commit()
    await db.refresh(db_member)
    return db_member

@router.delete("/{member_id}")
async def delete_member(member_id: int, db: AsyncSession = Depends(get_db)):
    """删除实验室成员"""
    result = await db.execute(select(LabMemberModel).where(LabMemberModel.member_id == member_id))
    db_member = result.scalar_one_or_none()
    if db_member is None:
        raise HTTPException(status_code=404, detail="未找到该成员")
    await db.delete(db_member)
    await db.commit()
    return {"message": "成员已成功删除"}
