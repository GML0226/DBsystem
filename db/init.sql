-- 1. LabMember 表（实验室成员，支持自引用的层级结构）
CREATE TABLE LabMember (
    member_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,                        -- 成员姓名
    role ENUM('Mentor', 'Student') NOT NULL,          -- 角色：导师或学生
    mentor_id INT DEFAULT NULL,                       -- 导师ID（外键，指向自身）
    FOREIGN KEY (mentor_id) REFERENCES LabMember(member_id)
);

-- 2. Equipment 表（实验设备）
CREATE TABLE Equipment (
    equipment_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,                       -- 设备名称
    status ENUM('Available', 'Occupied', 'Maintenance') DEFAULT 'Available', -- 状态：可用、占用、维护中
    maintenance_interval INT NOT NULL,                -- 维护间隔（天）
    last_maintenance_date DATE NOT NULL               -- 上次维护日期
);

-- 3. Consumable 表（消耗品/库存）
CREATE TABLE Consumable (
    consumable_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,                       -- 消耗品名称
    quantity INT NOT NULL DEFAULT 0,                  -- 当前库存数量
    threshold INT NOT NULL DEFAULT 10                 -- 低库存阈值提示
);

-- 4. ReservationRecord 表（设备预约记录）
CREATE TABLE ReservationRecord (
    reservation_id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT,                                    -- 预约成员ID
    equipment_id INT,                                 -- 预约设备ID
    start_time DATETIME NOT NULL,                     -- 开始时间
    end_time DATETIME NOT NULL,                       -- 结束时间
    FOREIGN KEY (member_id) REFERENCES LabMember(member_id),
    FOREIGN KEY (equipment_id) REFERENCES Equipment(equipment_id)
);

-- 5. MaterialRequisition 表（物料领用申请）
CREATE TABLE MaterialRequisition (
    requisition_id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT,                                    -- 申请人ID
    consumable_id INT,                                -- 消耗品ID
    quantity INT NOT NULL,                            -- 申请数量
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending', -- 状态：待审批、已批准、已拒绝
    apply_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- 申请日期
    FOREIGN KEY (member_id) REFERENCES LabMember(member_id),
    FOREIGN KEY (consumable_id) REFERENCES Consumable(consumable_id)
);

-- 6. WarningLog 表（告警日志，用于库存预警等）
CREATE TABLE WarningLog (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    message VARCHAR(255),                             -- 告警信息内容
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP     -- 创建时间
);
