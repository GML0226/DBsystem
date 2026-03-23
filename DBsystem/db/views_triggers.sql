-- 1. 为预约记录的时间范围查询创建索引，优化性能
CREATE INDEX idx_reservation_time ON ReservationRecord(start_time, end_time);

-- 2. 创建视图：显示在未来30天内需要维护的设备
CREATE VIEW View_UpcomingMaintenance AS
SELECT 
    equipment_id, 
    name, 
    last_maintenance_date,
    DATE_ADD(last_maintenance_date, INTERVAL maintenance_interval DAY) AS next_maintenance_date
FROM Equipment
WHERE DATEDIFF(DATE_ADD(last_maintenance_date, INTERVAL maintenance_interval DAY), CURDATE()) <= 30;

-- 4. [新增] 复杂查询视图：连接三表展示完整的预约详情（人名 + 设备名）
CREATE VIEW View_ReservationDetails AS
SELECT 
    r.reservation_id,
    m.name AS member_name,
    e.name AS equipment_name,
    r.start_time,
    r.end_time
FROM ReservationRecord r
JOIN LabMember m ON r.member_id = m.member_id
JOIN Equipment e ON r.equipment_id = e.equipment_id;

-- 3. 触发器：在领料申请被批准后，自动扣减库存并检查是否触发库存预警
DELIMITER //
CREATE TRIGGER trg_after_requisition_approved
AFTER UPDATE ON MaterialRequisition
FOR EACH ROW
BEGIN
    -- 仅当状态从“非批准”转变为“已批准”时触发逻辑
    IF OLD.status != 'Approved' AND NEW.status = 'Approved' THEN
        -- 1. 从库存（Consumable）中扣减申请的数量
        UPDATE Consumable 
        SET quantity = quantity - NEW.quantity
        WHERE consumable_id = NEW.consumable_id;
        
        -- 2. 如果扣减后库存低于阈值，则向告警日志（WarningLog）插入一条记录
        INSERT INTO WarningLog (message)
        SELECT CONCAT('低库存警告：', name, ' 当前库存 (', quantity, ') 已低于阈值。')
        FROM Consumable 
        WHERE consumable_id = NEW.consumable_id AND quantity < threshold;
    END IF;
END //
DELIMITER ;
