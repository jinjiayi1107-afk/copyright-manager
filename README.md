# SMPH外版图书管理系统

一个基于 Flask + Vue.js 的出版社外版图书版权管理系统。

## 功能模块

### 核心模块
| 模块 | 功能说明 |
|------|----------|
| 数据看板 | 统计卡片、图表可视化、全局检索、待办提醒 |
| 外版图书档案 | 图书信息管理、状态流转、样书上传、合同关联 |
| 合同管理 | 合同存档、阶梯版税配置、到期提醒、外商关联 |
| 外商库 | 国外出版社信息、联系人管理 |
| 译者库 | 译者信息、简历合同上传 |
| 意向选题库 | 选题意向管理、超时提醒 |
| 版税管理 | 版税支付记录、阶梯版税支持 |

### 已实现功能

#### 基础功能
- ✅ 所有模块的增删改查 (CRUD)
- ✅ 状态管理和流转
- ✅ 数据统计看板 + 图表可视化
- ✅ 表单验证
- ✅ 响应式布局

#### 检索功能
- ✅ **全局检索**（数据看板一键搜索所有模块）
- ✅ **模块独立检索**（图书/合同/译者/外商各自搜索）
- ✅ **可搜索下拉框**（关联选择时实时过滤）

#### 文件管理
- ✅ **文件上传**（合同扫描件、电子样书、译者简历）
- ✅ **文件下载**（通过接口下载，不暴露真实路径）
- ✅ **文件删除**（支持误上传删除和合同更新）
- ✅ 支持格式：PDF、Word(doc/docx)、图片(png/jpg)
- ✅ 大小限制：10MB
- ✅ 安全措施：UUID重命名、类型白名单、路径遍历防护

#### 提醒功能
- ✅ **合同到期提醒**（30天内到期 + 状态为"执行中"）
- ✅ **意向选题紧急提醒**（超过90天未洽谈）
- ✅ **意向选题初级提醒**（30-90天未洽谈）

#### 图书档案
- ✅ 原文名/中文名（必填字段）
- ✅ 合同关联（下拉选择已有关同）
- ✅ 译者关联

#### 合同管理
- ✅ **阶梯版税配置**（支持多档位版税率）
- ✅ 外商关联
- ✅ 译者关联

#### 界面交互
- ✅ **双击展开详情**（表格行双击显示完整信息）
- ✅ **ID格式化**（Book_0001、Contract_0001等）
- ✅ **修改记录追踪**（显示创建/修改时间）
- ✅ 浅蓝色主题UI

## 技术栈

| 类型 | 技术 |
|------|------|
| 前端 | Vue.js 3 + ECharts 5 |
| 后端 | Python Flask + Gunicorn |
| 数据库 | MySQL 8.0 |
| 文件存储 | 本地文件系统 |

## 项目结构

```
copyright-manager/
├── app.py                 # Flask 后端主文件
├── database.py            # 数据库操作模块
├── backup.sh              # 自动备份脚本
├── requirements.txt       # Python 依赖
├── gunicorn.conf.py       # Gunicorn配置文件
├── copyright-manager.service  # systemd服务文件
├── .env.example           # 环境变量示例
├── Procfile               # Railway 部署配置
├── static/
│   ├── index.html         # 主页面
│   ├── css/style.css      # 样式文件
│   ├── js/app.js          # 前端逻辑
│   └── logo.png           # 系统Logo
└── /data/
    ├── uploads/           # 上传文件目录
    └── backups/           # 备份文件目录
```

## 文件上传说明

### 存储路径
- 上传文件存储在 `/data/uploads/` 目录（独立于项目目录）
- 系统启动时自动创建该目录

### 文件命名
- 使用UUID重命名（32位十六进制字符）
- 保留原始扩展名
- 示例：`a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.pdf`

### 文件类型限制
仅支持以下类型：
- PDF文档：`.pdf`
- Word文档：`.doc`, `.docx`
- 图片：`.png`, `.jpg`

### 文件大小限制
- 最大10MB
- 由Flask配置 `MAX_CONTENT_LENGTH` 控制

### 文件访问方式
- **不能**通过URL直接访问（如 `/uploads/xxx`）
- **必须**通过下载接口：`GET /api/file/download?id={文件ID}`
- 文件ID为32位UUID，不含扩展名

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

### 方式二：生产环境部署（Gunicorn）

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件，填写实际的数据库密码和ADMIN_TOKEN

# 3. 使用 systemd 托管（推荐）
sudo cp copyright-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start copyright-manager
sudo systemctl enable copyright-manager  # 开机自启

# 4. 查看状态
sudo systemctl status copyright-manager
```

### Gunicorn vs Flask开发服务器

| 特性 | Flask开发服务器 | Gunicorn |
|-----|---------------|----------|
| 并发处理 | 单线程，一次一个请求 | 多Worker，支持并发 |
| 稳定性 | 可能内存泄漏 | 自动重启Worker |
| 性能 | 适合开发测试 | 生产级性能 |
| 适用场景 | 开发调试 | 生产部署 |

### 生产环境配置文件

**gunicorn.conf.py**（已包含，无需修改）：
- 自动根据CPU核心数设置Worker数量
- 30秒超时，1000请求后重启Worker
- 日志输出到stdout/stderr

**copyright-manager.service**（需要修改路径）：
- `WorkingDirectory`: 改为实际项目路径
- `User/Group`: 改为实际运行用户
- `EnvironmentFile`: 指向.env文件路径

## 数据库

- 使用 MySQL 8.0 数据库
- 数据库名称：`copyright_manager`
- 使用pymysql连接，每次操作后自动关闭连接
- 支持事务和异常处理
- **SQL注入防护**：表名白名单+参数化查询

### 数据库配置（环境变量）

系统通过环境变量读取数据库配置，支持不同部署环境：

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `DB_HOST` | localhost | MySQL服务器地址 |
| `DB_PORT` | 3306 | MySQL端口 |
| `DB_USER` | copyright_user | 数据库用户名 |
| `DB_PASSWORD` | copyright123 | 数据库密码 |
| `DB_NAME` | copyright_manager | 数据库名称 |
| `ADMIN_TOKEN` | 无（必填） | **管理员访问令牌** |

### 连接与事务

- **连接管理**：每次数据库操作独立获取连接，操作完成后自动关闭
- **事务支持**：写操作（增删改）使用事务，出错自动回滚
- **异常处理**：所有操作捕获异常并打印错误日志，不会导致程序崩溃

### 首次部署 - 创建数据库

```sql
-- 1. 创建数据库
CREATE DATABASE copyright_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 创建用户并授权
CREATE USER 'copyright_user'@'localhost' IDENTIFIED BY 'copyright123';
GRANT ALL PRIVILEGES ON copyright_manager.* TO 'copyright_user'@'localhost';
FLUSH PRIVILEGES;
```

## 接口安全

系统使用Token验证机制保护写接口和文件接口。

### Token配置

```bash
# 设置管理员令牌（必须设置，否则写接口无法使用）
export ADMIN_TOKEN=your_secure_token_here
```

### 需要Token的接口

以下接口必须在请求头中携带 `X-ADMIN-TOKEN`：

| 接口类型 | 接口路径 |
|---------|---------|
| 所有删除 | `/api/*/DELETE` |
| 所有更新 | `/api/*/PUT` |
| 所有创建 | `/api/*/POST` |
| 文件上传 | `/api/upload` |
| 文件下载 | `/api/file/download` |
| 文件删除 | `/api/file/delete` |

### 前端配置示例

```javascript
// 在请求头中添加Token
fetch('/api/upload', {
    method: 'POST',
    headers: {
        'X-ADMIN-TOKEN': 'your_secure_token_here'
    },
    body: formData
})
```

### 删除策略

系统使用外键约束，删除时会检查关联数据：

| 被删数据 | 关联检查 | 失败提示 |
|---------|---------|---------|
| 外商 | 合同引用 | "该外商有关联合同，无法删除" |
| 译者 | 合同引用 | "该译者有关联合同，无法删除" |
| 合同 | 图书/版税引用 | "该合同有关联图书或版税，无法删除" |
| 图书 | 版税引用 | "该图书有关联版税，无法删除" |

### 环境变量配置示例

**Linux/Mac（开发环境）**：
```bash
# 设置环境变量
export DB_HOST=localhost
export DB_USER=your_user
export DB_PASSWORD=your_password
export ADMIN_TOKEN=your_token

# 启动开发服务器
python app.py
```

**Linux/Mac（生产环境）**：
```bash
# 创建.env文件
cp .env.example .env
# 编辑.env填写实际配置

# 使用Gunicorn启动
gunicorn -c gunicorn.conf.py app:app
```

**Windows**：
```cmd
set DB_HOST=localhost
set DB_USER=your_user
set DB_PASSWORD=your_password
set ADMIN_TOKEN=your_token
python app.py
```

**Docker / Railway**：
在平台后台的环境变量配置中添加上述变量。

## ID格式说明

各模块ID自动生成并格式化显示：

| 模块 | ID格式 | 示例 |
|------|--------|------|
| 图书档案 | Book_XXXX | Book_0001 |
| 合同管理 | Contract_XXXX | Contract_0001 |
| 译者库 | Translator_XXXX | Translator_0001 |
| 外商库 | Publisher_XXXX | Publisher_0001 |
| 意向选题 | Topic_XXXX | Topic_0001 |
| 版税管理 | Royalty_XXXX | Royalty_0001 |

## 阶梯版税配置

选择"阶梯版税率"时支持多档位配置：

```
第1档: 1-5000册 → 7%
第2档: 5001-10000册 → 8%
第3档: 10001册及以上 → 9%
```

支持动态添加/删除档位。

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

# 注意：数据库和 uploads/ 文件夹需要定期备份
```

## 自动备份

系统提供自动备份脚本 `backup.sh`，支持备份MySQL数据库和上传文件。

### 备份内容

- MySQL数据库（使用mysqldump导出为.sql.gz文件）
- 上传文件目录 `/data/uploads/`（打包为.tar.gz文件）

### 手动执行备份

```bash
# 添加执行权限
chmod +x backup.sh

# 执行备份
./backup.sh
```

### 定时自动备份（crontab）

```bash
# 编辑定时任务
crontab -e

# 添加以下内容（每天凌晨2点执行备份）
# 注意：需要设置数据库密码环境变量
0 2 * * * export DB_PASSWORD=your_password && /path/to/backup.sh >> /data/backups/cron.log 2>&1
```

### 备份文件存储

- 存储目录：`/data/backups/`
- 命名格式：`2024-01-01_020000/`（日期_时间）
- 自动清理：保留最近30天的备份

### 配置修改

备份脚本从环境变量读取数据库密码（与database.py一致），无需修改脚本：

```bash
# 必须设置的环境变量
export DB_PASSWORD=your_password

# 可选的环境变量（有默认值）
export DB_HOST=localhost
export DB_USER=copyright_user
export DB_NAME=copyright_manager
export BACKUP_ROOT=/data/backups
export UPLOAD_DIR=/data/uploads
```

### 恢复数据

**恢复数据库**：
```bash
# 解压备份文件
gunzip database_2024-01-01_020000.sql.gz

# 导入数据库
mysql -u copyright_user -p copyright_manager < database_2024-01-01_020000.sql
```

**恢复上传文件**：
```bash
# 解压到上传目录
tar -xzf uploads_2024-01-01_020000.tar.gz -C /data/uploads/
```

## 数据关联说明

- **图书 ↔ 合同**：多对一关系，一本书对应一个合同，一个合同可对应多本书
- **合同 ↔ 外商**：多对一关系
- **合同/图书 ↔ 译者**：关联译者库

## 后续开发规划

- [ ] AI 合同信息提取（本地大模型）
- [ ] 批量报表导出（Excel）
- [ ] 用户权限管理
- [ ] 编辑系统对接
- [ ] 老系统数据迁移

## License

MIT License
