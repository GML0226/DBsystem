# 实验室智能管理与辅助决策系统 (Lab Nexus)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-05998b.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg?style=flat)](https://www.sqlalchemy.org/)
[![Visual-Polish](https://img.shields.io/badge/UI-Apple--Style-blue.svg)](https://developer.apple.com/design/human-interface-guidelines/)
[![AI-Powered](https://img.shields.io/badge/AI-Enhanced-brightgreen.svg)](https://ai.google.dev/)

**Lab Nexus** 是一款专为科研院校设计的高级实验室综合管理平台。它不仅解决了基础的**设备借还**与**耗材调拨**，更通过**知识图谱**挖掘资源关联，利用 **LLM (大语言模型)** 实现自动化运营分析，并以**极致的苹果系视觉美学**重新定义了科研管理软件的交互体验。

---

## 💎 高级业务特性

### 1. 知识图谱 (Knowledge Graph Search)
系统内置基于 ECharts 力引导布局的关系探索引擎，跨越成员、设备、耗材的物理堆叠，将孤立的数据转化为知识网。
- **关联脉络分析**: 一键检索关键词，动态展示“人-机-料-导师”的级联关系。
- **关联强度加权**: 连线粗细代表了真实的交互频次（如借跃次数、领用规模）。
- **上帝视角**: 辅助管理者快速理清核心资源的使用归属与流动规律。

### 2. AI 智能辅助决策 (AI Analytical Suite)
集成底层 LLM 能力（Gemini/OpenAI 兼容），将枯燥的数据库记录转化为直观的管理建议。
- **全维度上下文感知**: AI 自动提取近期的预约分布、库存损耗速度及预警记录。
- **预测性洞察**: 自动分析耗材损耗周期，预测未来可能出现的缺口，并提供采购建议。
- **自然语言交互**: 通过 Markdown 格式渲染深度实验室状态报告。

### 3. 极致视觉系统 (Apple-Style Visual Polish)
放弃平庸的工业软件风格，采用现代 Human Interface 设计语言：
- **深度玻璃拟态 (Glassmorphism)**: 错落有致的层叠阴影与 `backdrop-filter` 带来的通透质感。
- **流体交互**: 列表项错位入场动画 (`SlideUpFade`)、平滑的响应式汉堡菜单及动态背景梯度。
- **隐藏式美学**: 定制 Apple 风格极简滚动条，全系统 60FPS 丝滑体验。

---

## 🛠️ 核心模块功能解析 (Module Deep-Dive)

### 1. 资产全生命周期管理 (Equipment & Assets)
系统对高价值实验仪器进行数字孪生式的状态追踪：
- **智能排期预约**: 动态过滤 `Occupied` 状态设备，精确到秒级的时间冲突校验。
- **维保阈值锁定 (Hard-Locking)**: 数据库底层记录每台设备的累计使用次数。当达到 `max_usage_limit` 时，状态**自动硬切换**为 `Maintenance`，从物理层禁止任何新的预约申请。
- **生命周期追溯**: 支持“反向穿透”查询，即由单台设备追溯其自入库以来所有的借用轨迹、故障频率与维保记录。

### 2. 原子化耗材调拨闭环 (Smart Inventory)
基于事务完整性的库存管理方案：
- **审批权杖流**: 成员提交申请 -> 导师/管理员异步审批。
- **数据库原生触发器 (DB Triggers)**: 在审批状态变为 `Approved` 的瞬间，由 DB 原生触发器执行原子扣减。这种设计确保了在高并发申请场景下，库存扣减的绝对准确，彻底杜绝逻辑层的计算漂移。
- **库存熔断与预警**: 一旦库存触碰安全阈值，触发器自动联动 `WarningLog` 写入告警，并由前端看板实时进行边缘闪烁动画推送。

### 3. 知识图谱关联挖掘 (Nexus Knowledge Graph)
将实验室建模为一个多维拓扑网络：
- **一度拓扑检索**: 搜索关键词时，系统以该节点为中心，智能拉取其一度关联关系（如：借阅过该设备的成员、该成员所属的导师、导师名下的其他耗材领用）。
- **关系加权可视化**: 线条粗细动态对应交互频次。师生关系、借阅关系、消耗关系在图谱中具备不同的视觉语义。
- **交互聚焦与磁吸**: 节点具备真实的物理特性（引力与斥力），支持拖拽重布，点击任意节点可瞬间过滤无关背景，强化特定资源链路。

### 4. AI 智能辅助决策 (AI Laboratory Analyst)
利用 LLM 构建实验室的“超级大脑”：
- **多维度数据喂入**: AI 助手在执行分析前，会自动从数据库聚合：设备利用率排名、耗材周转天数、成员活跃负载、系统告警烈度等全维度 JSON 格式上下文。
- **多层级建议生成**: AI 不仅仅是报表展示，它会基于数据给出具体的管理策略（例如：某耗材消耗过快建议增加库存、某设备利用率低建议考虑跨部门共享）。
- **Markdown 报告生成**: 自动生成具备专业排版、表格与分段建议的深度运行报告。

---

## 📐 技术架构深度

### 数据库层 (High-Performance DB Design)
- **3rd Normal Form (3NF)**: 严格解耦实体关系，消除数据冗余。
- **复合索引策略**: 针对 `ReservationRecord` 的时间范围查询进行 B-Tree 索引优化。
- **物化视图思想**: 简化 API 层的复杂 Join 操作。

### 后端层 (Asynchronous Backend)
- **完全异步 IO**: 基于 FastAPI 与 SQLAlchemy 2.0 Async 实现高并发处理能力。
- **数据反查能力 (Reverse Lookup)**: 支持由耗材追溯人员分布，或由设备追溯全生命周期轨迹。

---

## 🚀 部署与启动

### 1. 环境安装
```bash
pip install -r requirements.txt
```

### 2. 服务启动
```bash
uvicorn app.main:app --reload
```

### 3. 数据灌入
    http://127.0.0.1:8000
访问 `http://127.0.0.1:8000/docs`，执行 `POST /api/system/seed` 接口。系统将自动化生成：
- **12个月**的模拟预约流水。
- **复杂师生层级关系**数据。
- 预设的**低库存预警**与**维保锁定**记录。

---

## 📊 模块导览
- **主大屏**: 可视化看板、维保监控、耗材排行。
- **关系图谱**: 力引导关系链交互。
- **AI 助手**: 全自动运行状态报告。
- **资产中心**: 设备预约与领料流程。

---
*Developed with ❤️ by Google Deepmind - Antigravity Team*
