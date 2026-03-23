from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.core.database import get_db
from app.models.models import LabMember, Equipment, Consumable, ReservationRecord, MaterialRequisition
from typing import List, Dict, Any

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])

@router.get("/search")
async def search_graph(q: str = Query(None, description="Search keyword for nodes"), db: AsyncSession = Depends(get_db)):
    # 1. 查找匹配关键词的节点 (Core Nodes)
    nodes_map = {} # id -> node_obj
    core_ids = {"member": set(), "equipment": set(), "consumable": set()}
    
    # 成员匹配
    member_stmt = select(LabMember)
    if q:
        member_stmt = member_stmt.where(LabMember.name.contains(q))
    members = (await db.execute(member_stmt)).scalars().all()
    for m in members:
        mid = f"m_{m.member_id}"
        nodes_map[mid] = {"id": mid, "name": m.name, "type": "member", "val": 20}
        core_ids["member"].add(m.member_id)

    # 设备匹配
    equip_stmt = select(Equipment)
    if q:
        equip_stmt = equip_stmt.where(Equipment.name.contains(q))
    equips = (await db.execute(equip_stmt)).scalars().all()
    for e in equips:
        eid = f"e_{e.equipment_id}"
        nodes_map[eid] = {"id": eid, "name": e.name, "type": "equipment", "val": 15}
        core_ids["equipment"].add(e.equipment_id)

    # 耗材匹配
    consum_stmt = select(Consumable)
    if q:
        consum_stmt = consum_stmt.where(Consumable.name.contains(q))
    consums = (await db.execute(consum_stmt)).scalars().all()
    for c in consums:
        cid = f"c_{c.consumable_id}"
        nodes_map[cid] = {"id": cid, "name": c.name, "type": "consumable", "val": 10}
        core_ids["consumable"].add(c.consumable_id)

    # 2. 查找关联 (Edges) - 仅限与 Core Nodes 相连的边
    links = []
    
    # 辅助函数：按需获取并添加节点
    async def ensure_node(type_str, original_id):
        node_id = f"{type_str[0]}_{original_id}"
        if node_id in nodes_map: return True
        
        if type_str == "member":
            obj = await db.get(LabMember, original_id)
            if obj: nodes_map[node_id] = {"id": node_id, "name": obj.name, "type": "member", "val": 15}
        elif type_str == "equipment":
            obj = await db.get(Equipment, original_id)
            if obj: nodes_map[node_id] = {"id": node_id, "name": obj.name, "type": "equipment", "val": 12}
        elif type_str == "consumable":
            obj = await db.get(Consumable, original_id)
            if obj: nodes_map[node_id] = {"id": node_id, "name": obj.name, "type": "consumable", "val": 8}
        return node_id in nodes_map

    # 成员-设备关联
    res_stmt = select(
        ReservationRecord.member_id, 
        ReservationRecord.equipment_id, 
        func.count(ReservationRecord.reservation_id).label("weight")
    ).group_by(ReservationRecord.member_id, ReservationRecord.equipment_id)
    
    reservations = (await db.execute(res_stmt)).all()
    for r in reservations:
        # 核心逻辑：只有当 source 或 target 之一属于 core_ids 时，才展示该边
        if r.member_id in core_ids["member"] or r.equipment_id in core_ids["equipment"]:
            if await ensure_node("member", r.member_id) and await ensure_node("equipment", r.equipment_id):
                links.append({
                    "source": f"m_{r.member_id}", 
                    "target": f"e_{r.equipment_id}", 
                    "label": "BORROWED", 
                    "weight": r.weight
                })

    # 成员-耗材关联
    mat_stmt = select(
        MaterialRequisition.member_id, 
        MaterialRequisition.consumable_id, 
        func.sum(MaterialRequisition.quantity).label("weight")
    ).where(MaterialRequisition.status == 'Approved').group_by(MaterialRequisition.member_id, MaterialRequisition.consumable_id)
    
    requisitions = (await db.execute(mat_stmt)).all()
    for req in requisitions:
        if req.member_id in core_ids["member"] or req.consumable_id in core_ids["consumable"]:
            if await ensure_node("member", req.member_id) and await ensure_node("consumable", req.consumable_id):
                links.append({
                    "source": f"m_{req.member_id}", 
                    "target": f"c_{req.consumable_id}", 
                    "label": "CONSUMED", 
                    "weight": int(req.weight or 0) // 5 + 1
                })

    # 导师-学生关联
    mentor_stmt = select(LabMember).where(LabMember.mentor_id.isnot(None))
    mentorships = (await db.execute(mentor_stmt)).scalars().all()
    for stu in mentorships:
        if stu.mentor_id in core_ids["member"] or stu.member_id in core_ids["member"]:
            if await ensure_node("member", stu.mentor_id) and await ensure_node("member", stu.member_id):
                links.append({
                    "source": f"m_{stu.mentor_id}", 
                    "target": f"m_{stu.member_id}", 
                    "label": "MENTOR_OF", 
                    "weight": 2
                })

    return {"nodes": list(nodes_map.values()), "links": links}
