# 版权管理系统

一个基于 Flask + Vue.js 的出版社版权管理系统。

## 功能模块

### 核心模块
| 模块 | 功能说明 |
|------|----------|
| 数据看板 | 统计卡片、图表可视化、待办提醒 |
| 外版图书档案 | 图书信息管理、状态流转、样书上传 |
| 合同管理 | 合同存档、版税配置、到期提醒 |
| 外商库 | 国外出版社信息、联系人管理 |
| 译者库 | 译者信息、简历合同上传 |
| 意向选题库 | 选题意向管理、超时提醒 |
| 版税管理 | 版税支付记录、阶梯版税支持 |

### 已实现功能
- ✅ 所有模块的增删改查 (CRUD)
- ✅ 状态管理和流转
- ✅ 数据统计看板 + 图表可视化
- ✅ **文件上传**（合同扫描件、电子样书、译者简历）
- ✅ **到期提醒**（合同30天内到期、意向选题超时）
- ✅ **阶梯版税配置**（支持多档位版税率）
- ✅ 搜索筛选功能
- ✅ 表单验证
- ✅ 响应式布局

## 技术栈

| 类型 | 技术 |
|------|------|
| 前端 | Vue.js 3 + ECharts 5 |
| 后端 | Python Flask |
| 数据库 | SQLite |
| 文件存储 | 本地文件系统 |

## 项目结构

```
copyright-manager/
├── app.py              # Flask 后端主文件
├── database.py         # 数据库操作模块
├── requirements.txt    # Python 依赖
├── Procfile            # Railway 部署配置
├── static/
│   ├── index.html      # 主页面
│   ├── css/style.css   # 样式文件
│   └── js/app.js       # 前端逻辑
└── uploads/            # 上传文件目录 (自动创建)
```

## 快速启动

### 方式一：直接运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py

# 3. 访问系统
# 本地: http://localhost:5001
```

### 方式二：生产环境部署

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 使用 systemd 托管（推荐）
# 创建服务文件 /etc/systemd/system/copyright-manager.service
# 内容见下方"生产环境配置"

# 3. 启动服务
sudo systemctl start copyright-manager
sudo systemctl enable copyright-manager  # 开机自启
```

### 生产环境配置

创建 `/etc/systemd/system/copyright-manager.service`：

```ini
[Unit]
Description=Copyright Manager System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/copyright-manager
ExecStart=/usr/bin/python3 /path/to/copyright-manager/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 数据库

- 使用 SQLite 数据库，文件 `copyright_manager.db` 首次运行自动创建
- **重要**：更新代码时请保留此文件，否则数据会丢失
- **备份建议**：定期备份 `.db` 文件和 `uploads/` 文件夹

## 文件上传

- 支持格式：PDF、图片（PNG/JPG）、Word文档
- 大小限制：10MB
- 存储位置：`uploads/` 目录

## 提醒功能

| 提醒类型 | 规则 |
|----------|------|
| 合同到期提醒 | 30天内到期 + 状态为"执行中" |
| 意向选题紧急 | 超过90天未洽谈 |
| 意向选题初级 | 30-90天未洽谈 |

## 阶梯版税配置

选择"阶梯版税率"时支持多档位配置：

```
第1档: 1-5000册 → 7%
第2档: 5001-10000册 → 8%
第3档: 10001册及以上 → 9%
```

## 状态枚举

### 意向选题状态
待洽谈 → 洽谈中 → 已签约 / 已放弃

### 图书状态
意向阶段 → 合同签约阶段 → 翻译中 → 编辑中 → 已出版
（特殊情况：近期需续约、已过期、已废弃）

### 合同状态
草稿 → 已签约 → 执行中 → 已到期 / 已作废

## 更新维护

```bash
# 更新代码
git pull

# 重启服务
sudo systemctl restart copyright-manager

# 注意：不要删除 .db 文件和 uploads/ 文件夹
```

## 后续开发规划

- [ ] AI 合同信息提取（本地大模型）
- [ ] 批量报表导出（Excel）
- [ ] 用户权限管理
- [ ] 编辑系统对接
- [ ] 老系统数据迁移

## License

MIT License
