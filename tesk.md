

这是一份非常详尽的要求。我来完整输出开发任务清单和全局提示词。

---

# pppet v1.0 开发任务清单

> **使用说明**：按任务编号顺序执行。标注 `[设计检查点]` 的任务需要先完成UI原型设计再进入开发。每个任务对应一次独立的AI对话或一个commit。

---

## 阶段一：项目初始化与基础架构

---


---

## 任务 1.1：后端项目初始化（修改版）

**内容**：创建 FastAPI 后端项目骨架，包括目录结构、入口文件、配置管理、数据库连接、依赖文件、Alembic 迁移工具初始化。

**目的**：搭建后端基础框架和数据库迁移能力，后续所有任务在此骨架上扩展。

**注意细节**：
- 目录结构按模块划分：auth、pets、records、reminders、health、chat、community、admin、user
- 数据库使用 MySQL，ORM 使用 SQLAlchemy（async 模式）
- 所有配置项（数据库连接串、API Key 等）走 .env 文件，使用 pydantic-settings 读取
- 需要 requirements.txt 列出所有依赖
- 包含 CORS 中间件配置（允许本地 uni-app 开发服务器跨域）
- 初始化 Alembic 迁移工具，后续每次模型变更通过 Alembic 管理

**AI提示词**：
```
你是一个 Python 后端架构师。请为项目 "pppet" 创建 FastAPI 后端项目骨架。

要求：
1. 目录结构如下：
   backend/
   ├── app/
   │   ├── main.py              # FastAPI 入口
   │   ├── config.py            # 配置管理，使用 pydantic-settings 读取 .env
   │   ├── database.py          # 数据库连接（MySQL + SQLAlchemy async）
   │   ├── models/              # 数据库模型目录（先创建 __init__.py）
   │   ├── schemas/             # Pydantic 请求/响应模型目录
   │   ├── routers/             # 路由目录，按模块划分：auth, pets, records, reminders, health, chat, community, admin, user
   │   ├── services/            # 业务逻辑层目录
   │   └── utils/               # 工具函数目录
   ├── alembic/                 # Alembic 迁移目录
   │   ├── versions/            # 迁移脚本存放
   │   └── env.py               # Alembic 环境配置
   ├── alembic.ini              # Alembic 配置文件
   ├── scripts/                 # 脚本目录
   ├── uploads/                 # 文件上传目录（images/ 和 reports/）
   ├── .env.example             # 环境变量示例
   ├── requirements.txt         # 依赖列表
   └── README.md

2. main.py 中配置 CORS 中间件，允许 localhost:* 跨域
3. config.py 使用 pydantic-settings 的 BaseSettings，读取以下变量：
   DATABASE_URL, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, COZE_API_KEY, SECRET_KEY
4. database.py 使用 SQLAlchemy async engine + async session
5. 每个 routers/ 下的模块文件先创建空路由蓝图（APIRouter），在 main.py 中注册
6. requirements.txt 包含：fastapi, uvicorn, sqlalchemy, aiomysql, pydantic-settings,
   python-dotenv, python-jose, passlib, bcrypt, python-multipart, httpx,
   sse-starlette, alembic, jinja2, aiofiles
7. 初始化 Alembic：
   - alembic.ini 中 sqlalchemy.url 留空（从 env.py 动态读取）
   - alembic/env.py 中：
     a. 从 app.config 读取 DATABASE_URL
     b. 导入 app.models 中的 Base.metadata 作为 target_metadata
     c. 使用同步连接执行迁移（Alembic 不支持 async，需配置同步 URL）
   - 在 .env.example 中同时提供 DATABASE_URL（async）和 DATABASE_URL_SYNC（sync）
8. 不要硬编码任何密钥，全部走 .env
9. 每个文件顶部写一行 docstring 说明用途
```

**核验方式**：
1. 执行 `pip install -r requirements.txt` 无报错
2. 创建 `.env` 文件填入测试数据库连接串
3. 执行 `uvicorn app.main:app --reload` 服务启动成功
4. 访问 `http://localhost:8000/docs` 能看到 Swagger 文档页面，所有空路由模块已注册
5. 执行 `alembic current` 无报错，能正确连接数据库

---

### 任务 1.2：数据库模型 — 用户与宠物

**内容**：创建 users 表和 pets 表的 SQLAlchemy 模型，以及对应的 Pydantic schema。

**目的**：完成用户和宠物档案的数据层，后续所有模块依赖这两张核心表。

**注意细节**：
- users 表字段：id, openid, nickname, avatar_url, user_type（默认"normal"，可选"vip"）, vip_expire_time, ai_analysis_used_count（普通用户永久计数）, created_at, updated_at
- pets 表字段：id, user_id（外键）, avatar, nickname, species, breed, gender, birthday, approximate_age, weight, is_neutered, fur_color, adoption_date, allergy_history, chronic_disease, current_food_brand, created_at, updated_at
- birthday 和 approximate_age 二选一，用两个可空字段实现
- pets 表需要软删除字段 is_deleted + deleted_at
- 所有时间字段使用 UTC 时间

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请在 app/models/ 下创建用户和宠物的数据库模型。

具体要求：

1. 创建 app/models/user.py — User 模型：
   - id: 主键，自增整数
   - openid: 微信openid，字符串，唯一索引，可空（本地开发阶段）
   - nickname: 昵称，字符串
   - avatar_url: 头像URL，字符串，可空
   - user_type: 用户类型，字符串，默认 "normal"，可选 "vip"
   - vip_expire_time: 会员到期时间，DateTime，可空
   - ai_analysis_used_count: AI分析已使用次数（普通用户永久计数），整数，默认0
   - created_at, updated_at: 时间戳

2. 创建 app/models/pet.py — Pet 模型：
   - id: 主键，自增整数
   - user_id: 外键关联 users.id
   - avatar: 头像文件路径，字符串，可空
   - nickname: 昵称，字符串，非空
   - species: 物种，字符串，非空（猫/狗/仓鼠/兔子/鸟/爬行类/其他）
   - breed: 品种，字符串，非空
   - gender: 性别，字符串，可空（公/母/未知）
   - birthday: 精确生日，Date，可空
   - approximate_age: 大约年龄，字符串，可空（如"大约2岁"）
   - weight: 体重kg，Float，可空
   - is_neutered: 绝育状态，Boolean，可空
   - fur_color: 毛色，字符串，可空
   - adoption_date: 领养日期，Date，可空
   - allergy_history: 过敏史，Text，可空
   - chronic_disease: 慢性病，Text，可空
   - current_food_brand: 当前主粮品牌，字符串，可空
   - is_deleted: 软删除标记，Boolean，默认False
   - deleted_at: 删除时间，DateTime，可空
   - created_at, updated_at: 时间戳

3. 创建 app/models/__init__.py，导出所有模型

4. 创建对应的 Pydantic schema：
   - app/schemas/user.py: UserCreate, UserResponse, UserUpdate
   - app/schemas/pet.py: PetCreate, PetResponse, PetUpdate, PetListResponse

5. PetCreate 中 nickname, species, breed 为必填，其余选填
6. PetResponse 中 birthday 和 approximate_age 都返回，前端根据哪个有值来展示

保持已有代码的导入风格和目录风格一致。每个文件顶部写 docstring。
```

**核验方式**：
1. 启动服务无报错
2. 使用 SQLAlchemy 的 `create_all` 或 Alembic 初始化数据库，确认 users 和 pets 表在 MySQL 中创建成功
3. 字段类型、可空性、默认值与需求一致

---

### 任务 1.3：数据库模型 — 记录与提醒

**内容**：创建 pet_records 表、record_images 表、reminders 表的 SQLAlchemy 模型和 schema。

**目的**：完成数据记录模块的数据层。

**注意细节**：
- pet_records 字段：id, pet_id（外键）, record_date, category（健康/日常护理/消费/医疗）, sub_type（子分类如体内驱虫、洗澡等）, note, amount（消费金额，可空）, weight_value（体重值，可空）, created_at, updated_at
- record_images 字段：id, record_id（外键）, image_path, created_at
- reminders 字段：id, record_id（外键）, pet_id（外键）, reminder_type, cycle_days（周期天数）, reminder_time, next_reminder_date, is_active, created_at, updated_at
- category 和 sub_type 使用字符串存储，不用枚举类型，方便后续扩展

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请在 app/models/ 下创建记录和提醒相关的数据库模型。

已有模型：app/models/user.py (User), app/models/pet.py (Pet)。
请先阅读已有代码的风格，保持一致。

具体要求：

1. 创建 app/models/record.py — PetRecord 模型：
   - id: 主键自增
   - pet_id: 外键关联 pets.id
   - record_date: 记录日期，Date，非空
   - category: 分类，字符串，非空（健康/日常护理/消费/医疗）
   - sub_type: 子分类，字符串，非空（如：体内驱虫、体外驱虫、疫苗接种、体重记录、异常症状、洗澡、美容、剪指甲、主粮、零食、玩具、日用品、其他、门诊就诊、住院、用药记录）
   - note: 备注，Text，可空
   - amount: 金额（元），Float，可空，仅消费类使用
   - weight_value: 体重值（kg），Float，可空，仅体重记录使用
   - created_at, updated_at

2. 创建 app/models/record_image.py — RecordImage 模型：
   - id: 主键自增
   - record_id: 外键关联 pet_records.id
   - image_path: 图片文件路径，字符串
   - created_at

3. 创建 app/models/reminder.py — Reminder 模型：
   - id: 主键自增
   - record_id: 外键关联 pet_records.id，可空
   - pet_id: 外键关联 pets.id
   - reminder_type: 提醒类型，字符串（如"体内驱虫""疫苗接种"）
   - cycle_days: 周期天数，整数
   - reminder_time: 提醒时间，Time
   - next_reminder_date: 下次提醒日期，Date
   - is_active: 是否启用，Boolean，默认True
   - created_at, updated_at

4. 创建对应的 Pydantic schema：
   - app/schemas/record.py: RecordCreate, RecordResponse, RecordUpdate, RecordListResponse
   - app/schemas/reminder.py: ReminderCreate, ReminderResponse, ReminderUpdate

5. 更新 app/models/__init__.py 导出新模型
```

**核验方式**：
1. 数据库迁移后 pet_records、record_images、reminders 三张表创建成功
2. 外键关系正确，字段类型无误

---

### 任务 1.4：数据库模型 — AI分析与对话

**内容**：创建 health_reports 表、chat_sessions 表、chat_messages 表的模型和 schema。

**目的**：完成 AI 体检分析和 AI 对话的数据层。

**注意细节**：
- health_reports 字段：id, pet_id, original_file_path, file_type（image/pdf）, ocr_result_json（Text，存OCR原始结果）, parsed_indicators_json（Text，存结构化指标数据）, ai_interpretation（Text，AI解读文字）, status（pending/processing/completed/failed）, created_at, updated_at
- chat_sessions 字段：id, pet_id, user_id, title（会话标题，可空，默认取第一条消息的前20字）, created_at, updated_at
- chat_messages 字段：id, session_id, role（user/assistant）, content（Text）, created_at

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请在 app/models/ 下创建 AI 分析和对话相关的数据库模型。

请先阅读已有 app/models/ 下所有文件的代码风格，保持一致。

具体要求：

1. 创建 app/models/health_report.py — HealthReport 模型：
   - id: 主键自增
   - pet_id: 外键关联 pets.id
   - original_file_path: 原始文件路径，字符串
   - file_type: 文件类型，字符串（"image" 或 "pdf"）
   - ocr_result_json: OCR 原始结果，Text，可空
   - parsed_indicators_json: 结构化指标数据JSON，Text，可空
   - ai_interpretation: AI 通俗解读文本，Text，可空
   - status: 处理状态，字符串，默认 "pending"（pending/processing/completed/failed）
   - created_at, updated_at

2. 创建 app/models/chat_session.py — ChatSession 模型：
   - id: 主键自增
   - pet_id: 外键关联 pets.id
   - user_id: 外键关联 users.id
   - title: 会话标题，字符串，可空
   - created_at, updated_at

3. 创建 app/models/chat_message.py — ChatMessage 模型：
   - id: 主键自增
   - session_id: 外键关联 chat_sessions.id
   - role: 角色，字符串（"user" 或 "assistant"）
   - content: 消息内容，Text
   - created_at

4. 创建对应 schema：
   - app/schemas/health_report.py: HealthReportCreate, HealthReportResponse, HealthReportListResponse, IndicatorItem（指标条目：name, value, reference_range, status）
   - app/schemas/chat.py: ChatSessionCreate, ChatSessionResponse, ChatMessageCreate, ChatMessageResponse, ChatSessionListResponse

5. 更新 app/models/__init__.py
```

**核验方式**：
1. 数据库迁移后三张表创建成功
2. 外键关系正确
3. status 字段默认值为 "pending"

---

## 任务 1.5：数据库模型 — 社区、管理与反馈（修改版）

**内容**：创建 articles 表、comments 表、user_favorites 表、user_likes 表、admin_users 表、payment_records 预留表、user_daily_quota 表、feedback 表，以及对应的 Pydantic schema。

**目的**：完成社区模块、后台管理的数据层，补全会员额度管理表和用户反馈表。

**注意细节**：
- articles 字段：id, title, cover_image, category, content（富文本）, author, view_count, like_count, favorite_count, is_published, created_at, updated_at
- comments 字段：id, article_id, user_id, content, created_at
- user_favorites / user_likes：联合唯一索引（user_id + article_id）
- admin_users：独立的管理员表，id, username, password_hash, created_at
- user_daily_quota：id, user_id, quota_date, chat_count, created_at。user_id + quota_date 联合唯一索引
- payment_records：id, user_id, payment_type, amount, status, created_at（预留，字段可简化）
- feedback：id, user_id, type, content, contact, created_at

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请在 app/models/ 下创建社区、管理后台、会员额度和用户反馈相关的数据库模型。

请先阅读已有 app/models/ 下所有文件的代码风格，保持一致。

具体要求：

1. app/models/article.py — Article 模型：
   - id, title（字符串非空）, cover_image（字符串可空）, category（字符串非空，
     五个分类：生活类/训化类/医疗类/饮食营养类/新手入门类）
   - content: 正文富文本，Text
   - author: 作者名，字符串
   - view_count, like_count, favorite_count: 整数，默认0
   - is_published: 是否发布，Boolean，默认True
   - created_at, updated_at

2. app/models/comment.py — Comment 模型：
   - id, article_id（外键）, user_id（外键）, content（Text）, created_at

3. app/models/user_interaction.py — UserFavorite 和 UserLike 模型：
   - 都包含 id, user_id, article_id, created_at
   - user_id + article_id 建联合唯一索引

4. app/models/admin_user.py — AdminUser 模型：
   - id, username（唯一）, password_hash, created_at

5. app/models/user_daily_quota.py — UserDailyQuota 模型：
   - id, user_id（外键）, quota_date（Date）, chat_count（整数，默认0）, created_at
   - user_id + quota_date 建联合唯一索引

6. app/models/payment_record.py — PaymentRecord 模型（预留）：
   - id, user_id（外键）, payment_type（字符串）, amount（Float）, status（字符串）, created_at

7. app/models/feedback.py — Feedback 模型：
   - id: 主键自增
   - user_id: 外键关联 users.id
   - type: 反馈类型，字符串，非空（功能建议/Bug反馈/其他）
   - content: 反馈内容，Text，非空
   - contact: 联系方式，字符串，可空
   - created_at: 时间戳

8. 创建对应的 Pydantic schema 文件：
   - app/schemas/article.py
   - app/schemas/comment.py
   - app/schemas/feedback.py: FeedbackCreate, FeedbackResponse

9. 更新 app/models/__init__.py 导出所有新模型
```

**核验方式**：
1. 执行 `alembic revision --autogenerate -m "add community admin feedback tables"` 生成迁移脚本
2. 执行 `alembic upgrade head` 所有表创建成功
3. 共计16张表：users, pets, pet_records, record_images, reminders, health_reports, chat_sessions, chat_messages, articles, comments, user_favorites, user_likes, admin_users, user_daily_quota, payment_records, feedback
4. 联合唯一索引生效
5. `python -c "from app.models import *"` 无报错

---

## 任务 1.6：数据库迁移与初始数据脚本（修改版）

**内容**：通过 Alembic 生成初始迁移并建表，创建初始数据插入脚本。

**目的**：一键初始化开发环境数据库，方便重置环境和协作。

**注意细节**：
- 建表统一通过 Alembic 迁移完成，不再使用 `create_all`
- `scripts/init_db.py` 只负责插入初始数据
- 插入一个默认管理员账号（admin/admin123，密码用 bcrypt 加密）
- 插入一个测试用户和一只测试宠物，方便后续开发调试
- 脚本可重复执行，已有数据不重复插入

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端，使用 Alembic 管理数据库迁移。
请完成数据库迁移和初始数据插入。

要求：
1. 确保所有 models 已在 app/models/__init__.py 中导出
2. 执行命令生成初始迁移脚本（给出具体命令）
3. 执行命令应用迁移，在 MySQL 中创建所有表（给出具体命令）

4. 创建 scripts/init_db.py — 初始数据插入脚本：
   - 读取 .env 中的 DATABASE_URL 配置
   - 插入初始数据：
     a. 管理员账号：username="admin", password="admin123"（使用 bcrypt 加密存储）
     b. 测试用户：nickname="测试用户", user_type="normal"
     c. 测试宠物：nickname="小橘", species="猫", breed="中华田园猫", weight=4.5，关联测试用户
   - 先检查数据是否已存在，避免重复插入
   - 执行方式：python -m scripts.init_db

5. 创建 scripts/reset_db.py — 数据库重置脚本（开发用）：
   - 执行 alembic downgrade base（清除所有表）
   - 执行 alembic upgrade head（重新建表）
   - 调用 init_db 逻辑插入初始数据
   - 执行方式：python -m scripts.reset_db

请先阅读 app/config.py 和 app/database.py 的已有代码，保持一致。
```

**核验方式**：
1. 先在 MySQL 中创建空数据库 `pppet`
2. 执行 `alembic upgrade head` 所有表创建成功
3. 执行 `python -m scripts.init_db` 无报错，初始数据插入成功
4. 重复执行 `python -m scripts.init_db` 不报错、不重复插入
5. 执行 `python -m scripts.reset_db` 数据库完全重置并恢复初始数据
6. 用数据库客户端查看，管理员、测试用户、测试宠物数据存在

---


## 任务 1.7：认证模块与用户接口（修改版）

**内容**：实现用户登录注册接口（本地模拟登录 + 预留微信登录）、JWT token 管理、用户信息查询修改接口、用户反馈接口。

**目的**：打通认证链路和用户基础能力，后续所有接口依赖 token 鉴权。

**注意细节**：
- 本地开发阶段提供模拟登录接口：POST `/api/auth/mock-login`，传入 nickname 即可返回 token
- 预留微信登录接口：POST `/api/auth/wx-login`，接收 code 参数，第一版内部直接走模拟逻辑
- JWT token 使用 python-jose 生成，密钥从 .env 读取，过期时间7天
- 实现 `get_current_user` 依赖项，从 Authorization header 解析 token 获取 user_id
- 实现用户信息查询和修改接口
- 实现用户反馈提交接口
- 所有后续业务接口通过 `Depends(get_current_user)` 注入当前用户

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请实现认证模块和用户基础接口。

请先阅读已有代码结构，保持风格一致。

要求：

【Part 1：认证】
1. 创建 app/services/auth_service.py：
   - create_access_token(user_id): 生成 JWT token，过期时间7天，密钥从 config 读取
   - verify_token(token): 验证并解析 token，返回 user_id

2. 创建 app/utils/deps.py：
   - get_current_user: FastAPI 依赖项，从 Authorization: Bearer <token> 中提取 token，
     解析出 user_id，查询数据库返回 User 对象。token 无效返回 401。
   - get_optional_user: 可选鉴权依赖项，有 token 则返回用户，无 token 返回 None。
     用于社区浏览等不强制登录的接口。

3. 实现 app/routers/auth.py：
   - POST /api/auth/mock-login：
     请求体：{"nickname": "string", "avatar_url": "string"(可选)}
     逻辑：根据 nickname 查找用户，不存在则创建，返回 {"access_token": "xxx", "user": {...}}
   - POST /api/auth/wx-login：
     请求体：{"code": "string"}
     逻辑：第一版内部直接用 code 作为模拟 openid，其余同上
     预留注释说明后续对接微信真实登录的位置

【Part 2：用户接口】
4. 创建 app/services/user_service.py：
   - get_user_profile(user_id) -> User
   - update_user_profile(user_id, data) -> User（支持修改 nickname, avatar_url）
   - get_user_quota_summary(user_id) -> dict
     返回：{
       "ai_analysis_remaining": int,     # AI分析剩余次数
       "chat_daily_remaining": int|None,  # 今日对话剩余（None表示不限）
       "user_type": str,                  # 用户类型
       "vip_expire_time": datetime|None   # 会员到期时间
     }
   - create_feedback(user_id, feedback_data) -> Feedback

5. 实现 app/routers/user.py：
   - GET  /api/user/profile          获取当前用户信息
   - PUT  /api/user/profile          修改用户信息（昵称、头像）
   - GET  /api/user/quota            获取当前用户所有额度汇总
   - POST /api/user/feedback         提交用户反馈

6. 所有路由前缀 /api/auth 和 /api/user
7. 不要硬编码密钥
```

**核验方式**：
1. 调用 `POST /api/auth/mock-login {"nickname": "测试用户"}` 返回 token
2. 使用返回的 token 调用 `GET /api/user/profile` 返回用户信息
3. 调用 `PUT /api/user/profile {"nickname": "新昵称"}` 修改成功
4. 调用 `GET /api/user/quota` 返回额度信息，普通用户 ai_analysis_remaining 为 3
5. 调用 `POST /api/user/feedback` 提交反馈成功，数据库有记录
6. 使用无效 token 调用返回 401
7. 重复登录同一 nickname 不会创建重复用户


---

## 阶段二：宠物档案模块

---

### 任务 2.1：宠物档案 CRUD 接口

**内容**：实现宠物档案的创建、查询、编辑、删除（软删除）接口。

**目的**：完成宠物档案的后端逻辑，供前端调用。

**注意细节**：
- 所有接口需要登录鉴权，只能操作自己的宠物
- 查询列表自动过滤 is_deleted=True 的记录
- 删除为软删除，设置 is_deleted=True 和 deleted_at
- 创建时 nickname/species/breed 必填校验
- 上传头像接口单独做（任务2.2），这里 avatar 字段先传文件路径字符串

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请实现宠物档案的 CRUD 接口。

请先阅读已有代码（特别是 models/pet.py, schemas/pet.py, utils/deps.py），保持风格一致。

要求：
1. 创建 app/services/pet_service.py，包含：
   - create_pet(user_id, pet_data) -> Pet
   - get_pets_by_user(user_id) -> List[Pet]（过滤已软删除）
   - get_pet_by_id(pet_id, user_id) -> Pet（校验归属权）
   - update_pet(pet_id, user_id, pet_data) -> Pet
   - delete_pet(pet_id, user_id) -> None（软删除）

2. 实现 app/routers/pets.py：
   - POST   /api/pets          创建宠物
   - GET    /api/pets          获取当前用户所有宠物列表
   - GET    /api/pets/{pet_id} 获取单只宠物详情
   - PUT    /api/pets/{pet_id} 编辑宠物信息
   - DELETE /api/pets/{pet_id} 软删除宠物

3. 所有接口通过 Depends(get_current_user) 鉴权
4. 操作非自己的宠物返回 403
5. 操作不存在的宠物返回 404
6. 创建时校验 nickname, species, breed 非空
```

**核验方式**：
1. 用 Swagger 或 Postman 完成完整的 CRUD 流程测试
2. 创建宠物 → 查询列表能看到 → 编辑后字段更新 → 删除后列表中消失
3. 用另一个用户的 token 操作返回 403
4. 缺少必填字段返回 422

---

### 任务 2.2：文件上传接口

**内容**：实现通用的文件上传接口，支持图片和 PDF，本地文件系统存储。

**目的**：为宠物头像、记录图片、体检报告上传提供统一的文件处理能力。

**注意细节**：
- 统一上传接口 POST `/api/upload`，返回文件访问路径
- 本地存储目录：`uploads/images/`、`uploads/reports/`，按日期子目录组织
- 文件名使用 UUID 重命名防冲突
- 限制文件大小（图片最大10MB，PDF最大20MB）
- 限制文件类型（图片：jpg/jpeg/png/webp，PDF：pdf）
- 配置 FastAPI 静态文件服务，让上传的文件可通过 URL 访问

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请实现通用文件上传接口。

要求：
1. 创建 app/services/file_service.py：
   - save_file(file: UploadFile, file_category: str) -> str
   - file_category 分为 "image" 和 "report"
   - 存储目录：uploads/images/YYYY-MM-DD/ 或 uploads/reports/YYYY-MM-DD/
   - 文件名用 UUID 重命名，保留原始扩展名
   - 校验文件大小：图片 ≤10MB，PDF ≤20MB
   - 校验文件类型：图片仅 jpg/jpeg/png/webp，报告额外支持 pdf
   - 返回相对路径如 "uploads/images/2026-03-20/uuid.jpg"

2. 实现 app/routers/upload.py：
   - POST /api/upload/image  上传图片
   - POST /api/upload/report 上传体检报告（图片或PDF）
   - 返回 {"file_path": "xxx", "file_url": "http://localhost:8000/static/xxx"}

3. 在 app/main.py 中挂载静态文件服务：
   app.mount("/static", StaticFiles(directory="uploads"), name="static")

4. 需要登录鉴权
5. 文件类型或大小不合规返回 400 错误
```

**核验方式**：
1. 上传一张 jpg 图片成功，返回 file_path 和 file_url
2. 通过返回的 file_url 能在浏览器中访问到图片
3. 上传超过 10MB 的图片返回 400
4. 上传 .exe 文件返回 400

---

### `[设计检查点]` 任务 2.3：前端 — 宠物档案页面

> **暂停开发，先进行UI设计。**
>
> **需要设计的页面**：
>
> **页面1：添加/编辑宠物页面**
> - 目的：用户创建新宠物或修改已有宠物信息
> - 需展示字段：宠物头像上传区、昵称（必填）、物种选择器（必填，选项：猫/狗/仓鼠/兔子/鸟/爬行类/其他）、品种选择器+手动输入（必填，根据物种联动）、性别选择器（选填）、生日/大约年龄切换输入（选填）、体重输入（选填）、绝育状态（选填）、毛色（选填）、领养日期（选填）、过敏史（选填）、慢性病（选填）、当前主粮品牌（选填）
> - 交互：必填字段标红星号，底部保存按钮，保存前校验必填项
>
> **页面2：宠物管理列表页（"我的"Tab 进入）**
> - 目的：查看和管理所有宠物
> - 展示内容：宠物卡片列表（头像+昵称+品种+物种），底部添加宠物按钮，左滑卡片出现删除按钮
>
> **请完成以上页面的UI原型设计，确认后继续开发。**



---


## 新增任务 2.3.5：前端全局样式与公共组件

> 此任务插在 **任务 2.3（设计检查点）之后、任务 2.4（前端开发）之前** 执行。

**内容**：定义全局 CSS 变量、全局样式基类、基础公共组件，建立整个项目的前端视觉基础设施。

**目的**：确保后续所有前端页面使用统一的色彩、字号、圆角、间距，避免各页面各自定义导致风格不一致。

**注意细节**：
- 全局色彩变量需覆盖：主色、辅助色、背景色、卡片色、文字色（标题/正文/辅助）、状态色（正常绿/偏高红/偏低黄/禁用灰）
- 全局基础样式：页面背景渐变、卡片圆角投影、按钮主样式/次样式/禁用样式、输入框样式
- 公共组件：PetSwitcher（宠物切换栏）、EmptyState（空状态）、LoadingOverlay（全局加载遮罩）
- 所有颜色通过 CSS 变量引用，后续如果做主题切换（会员专属皮肤）可直接替换变量

**AI提示词**：
```
当前项目是 pppet，使用 uni-app (Vue3 Composition API) 开发。
请建立项目的全局样式基础设施和公共组件。

【设计规范】
- 风格：温暖治愈，参考 Suki app
- 主色调：粉色渐变到浅蓝
- 背景色：米白到浅粉渐变
- 卡片：白色底，圆角16-24rpx，浅色投影
- 图标风格：萌宠风格，圆润线条
- 字体规范：标题32rpx加粗，正文28rpx，辅助文字24rpx灰色

要求：

1. 修改 uni.scss — 全局 SCSS 变量：
   // 主色
   $color-primary: #FF8BA7;        // 粉色（主按钮、高亮）
   $color-primary-light: #FFC6D3;  // 浅粉（背景点缀）
   $color-secondary: #A8D8EA;      // 浅蓝（辅助色）
   $color-secondary-light: #D4F0F7;// 更浅蓝

   // 背景
   $bg-page: linear-gradient(180deg, #FFF5F5 0%, #FFFFFF 100%);  // 页面背景
   $bg-card: #FFFFFF;              // 卡片背景

   // 文字
   $text-primary: #333333;         // 主文字
   $text-secondary: #888888;       // 辅助文字
   $text-placeholder: #CCCCCC;     // 占位文字

   // 状态色
   $color-success: #7EC699;        // 正常/绿
   $color-warning: #F5C842;        // 偏低/黄
   $color-danger: #FF6B6B;         // 偏高/红
   $color-disabled: #D9D9D9;       // 禁用/灰

   // 圆角
   $radius-sm: 12rpx;
   $radius-md: 20rpx;
   $radius-lg: 32rpx;
   $radius-full: 50%;

   // 投影
   $shadow-card: 0 4rpx 16rpx rgba(255, 139, 167, 0.1);

   // 字号
   $font-title: 32rpx;
   $font-body: 28rpx;
   $font-caption: 24rpx;
   $font-mini: 20rpx;

2. 修改 App.vue <style> — 全局基础样式：
   - page 默认背景
   - .card 通用卡片样式（背景白、圆角、投影、内边距）
   - .btn-primary 主按钮样式（粉色渐变背景、白色文字、圆角）
   - .btn-secondary 次按钮样式（白色背景、粉色边框和文字）
   - .btn-disabled 禁用状态
   - .input-field 通用输入框样式
   - .section-title 区域标题样式
   - .divider 分隔线

3. 创建 components/PetSwitcher.vue — 宠物切换组件：
   - props: petList (宠物数组), currentPetId (当前选中)
   - emit: change(petId) 切换事件
   - 横向滚动展示宠物头像+昵称，当前选中项高亮（粉色边框）
   - 无宠物时显示"+"添加按钮

4. 创建 components/EmptyState.vue — 空状态组件：
   - props: icon (图标名), text (提示文字), buttonText (可选按钮文字)
   - emit: action (按钮点击事件)
   - 居中展示图标+文字，可选底部按钮
   - 图标使用柔和灰色，文字使用辅助色

5. 创建 components/LoadingOverlay.vue — 全局加载遮罩：
   - props: visible (是否显示), text (加载提示文字，默认"加载中...")
   - 半透明遮罩 + 居中加载动画 + 提示文字
   - 加载动画用 CSS 实现（旋转的萌宠爪印图标或圆形loading）

6. 创建 static/tabbar/ 目录 — TabBar 图标：
   - 需要5组图标（选中/未选中）：首页、记录、AI、社区、我的
   - 先用占位文字说明需要什么图标，我会后续替换实际图标文件

7. 配置 pages.json 的 tabBar：
   - 5个Tab：首页(pages/home/index)、记录(pages/record/index)、
     AI(pages/ai/index)、社区(pages/community/index)、我的(pages/mine/index)
   - 选中颜色使用主色 #FF8BA7，未选中颜色 #CCCCCC
   - 先创建5个空的Tab页面文件占位
```

**核验方式**：
1. 运行 uni-app 项目，底部 TabBar 正确显示5个Tab并可切换
2. 在任意页面中使用 `$color-primary` 等变量可正确引用
3. 使用 `.card` 类的元素展示为白色圆角投影卡片
4. PetSwitcher 组件传入测试数据正常渲染，切换触发 change 事件
5. EmptyState 组件显示居中的图标和文字
6. LoadingOverlay 显示/隐藏正常
---


### 任务 2.4：前端 — 宠物档案页面开发

**内容**：基于确认的UI原型，使用 uni-app 开发宠物档案相关页面（添加/编辑宠物、宠物管理列表）。

**目的**：完成宠物档案前端，打通前后端数据流。

**注意细节**：
- uni-app 项目使用 Vue3 + Composition API
- 封装统一的请求工具（utils/request.js），自动携带 token，处理错误
- 物种和品种的联动数据先用前端本地 JSON 维护
- 头像上传调用 `/api/upload/image` 接口
- 页面风格参考 Suki 温暖治愈风：粉嫩渐变背景、圆角卡片、柔和配色

**AI提示词**：
```
当前项目是 pppet，使用 uni-app (Vue3 Composition API) 开发。
请根据以下已确认的 UI 原型和设计规范开发宠物档案相关页面。

【UI风格规范】
- 整体风格：温暖治愈，参考 Suki app
- 主色调：粉色渐变到浅蓝，背景米白/浅粉
- 卡片：圆角（16rpx-24rpx），浅色投影
- 图标：萌宠风格，圆润线条
- 字体：标题16号加粗，正文14号，辅助文字12号灰色

【已确认的 UI 原型】
（此处粘贴你确认的原型图描述或截图）

要求：
1. 创建 utils/request.js — 统一请求封装：
   - 基于 uni.request 封装
   - baseURL 从配置读取
   - 自动从本地存储读取 token 附加到 Authorization header
   - 统一处理 401（跳转登录）、网络错误等
   - 暴露 get, post, put, del 方法

2. 创建 pages/pet/add.vue — 添加/编辑宠物页面：
   - 根据 UI 原型还原页面布局
   - 接收页面参数 petId，有则为编辑模式（加载已有数据），无则为添加模式
   - 物种选择后联动品种列表（从本地 JSON 数据读取）
   - 品种支持手动输入（选择列表末尾加"其他"选项，选择后出现输入框）
   - 生日/大约年龄提供切换Tab，二选一输入
   - 头像点击调用 uni.chooseImage + 上传接口
   - 保存按钮校验必填项，调用创建/更新 API

3. 创建 pages/pet/list.vue — 宠物管理列表页：
   - 宠物卡片列表展示
   - 左滑出现删除按钮，删除前二次确认弹窗
   - 底部"添加宠物"按钮，跳转到 add 页面
   - 点击卡片跳转到编辑页面

4. 创建 data/pet-breeds.json — 品种数据：
   - 按物种分类，每个物种下列出常见品种
   - 猫：英短、美短、布偶、暹罗、中华田园猫、波斯、缅因、加菲、折耳、无毛 等
   - 狗：金毛、拉布拉多、哈士奇、柯基、泰迪、边牧、柴犬、萨摩耶、德牧、博美 等
   - 其他物种各提供5-10个常见品种
   - 每个物种最后一项为"其他"

5. 在 pages.json 中注册新页面
```

**核验方式**：
1. 添加宠物页面所有字段可正常输入
2. 物种切换后品种列表正确联动
3. 头像上传成功并显示预览
4. 保存后数据库中新增记录，字段值正确
5. 列表页展示所有宠物，删除后刷新消失

---

## 阶段三：数据记录模块

---

### 任务 3.1：记录 CRUD 接口

**内容**：实现宠物日常记录的创建、查询、编辑、删除接口，包含图片关联。

**目的**：完成数据记录模块的后端逻辑。

**注意细节**：
- 创建记录时可同时传入多张图片路径（已通过上传接口获得）
- 查询支持按宠物ID、日期范围、分类筛选
- 体重记录创建/更新时同步更新 pets 表的 weight 字段
- 删除记录时同时删除关联的 record_images 和 reminders

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请实现数据记录模块的 CRUD 接口。

请先阅读已有代码，保持风格一致。

要求：
1. 创建 app/services/record_service.py：
   - create_record(pet_id, user_id, record_data, image_paths: List[str]) -> PetRecord
     创建记录并关联图片。如果 sub_type 为"体重记录"且 weight_value 不为空，
     同步更新 pets 表的 weight 字段。
   - get_records(pet_id, user_id, date_from, date_to, category) -> List[PetRecord]
     按条件查询，所有参数均可选，返回结果包含关联的图片列表
   - get_record_by_id(record_id, user_id) -> PetRecord（含图片）
   - update_record(record_id, user_id, record_data) -> PetRecord
   - delete_record(record_id, user_id) -> None（真删除，级联删除图片和提醒）

2. 实现 app/routers/records.py：
   - POST   /api/records                创建记录
   - GET    /api/records?pet_id=&date_from=&date_to=&category=   查询记录列表
   - GET    /api/records/{record_id}     获取单条记录详情
   - PUT    /api/records/{record_id}     编辑记录
   - DELETE /api/records/{record_id}     删除记录

3. 请求体中 image_paths 为字符串数组（文件已通过 /api/upload/image 上传）
4. 校验 pet_id 对应的宠物属于当前用户
5. 所有接口需要登录鉴权
```

**核验方式**：
1. 创建一条体重记录，pets 表的 weight 字段同步更新
2. 创建带图片的记录，查询详情时图片列表正确返回
3. 按日期和分类筛选查询结果正确
4. 删除记录后关联的图片记录和提醒也被删除

---

### 任务 3.2：提醒功能接口

**内容**：实现提醒的创建、查询、编辑、删除接口，以及获取即将到期提醒的接口（供首页展示）。

**目的**：完成提醒功能后端，为首页待办提醒提供数据支撑。

**注意细节**：
- 创建提醒时根据关联记录的日期 + cycle_days 自动计算 next_reminder_date
- 提供查询"即将到期"的接口：返回 next_reminder_date 在未来7天内的提醒
- 提醒完成后用户可标记完成，系统自动计算下一次提醒日期（next_reminder_date += cycle_days）

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请实现提醒功能接口。

请先阅读已有代码，保持风格一致。

要求：
1. 创建 app/services/reminder_service.py：
   - create_reminder(pet_id, user_id, reminder_data) -> Reminder
     根据 reminder_data 中的起始日期和 cycle_days 计算 next_reminder_date
   - get_reminders(pet_id, user_id) -> List[Reminder]
   - get_upcoming_reminders(user_id, days=7) -> List[Reminder]
     返回当前用户所有宠物中，next_reminder_date 在今天到未来 days 天内的活跃提醒
     结果需包含关联的宠物昵称
   - complete_reminder(reminder_id, user_id) -> Reminder
     标记完成：next_reminder_date += cycle_days（推到下一周期）
   - update_reminder(reminder_id, user_id, data) -> Reminder
   - delete_reminder(reminder_id, user_id) -> None

2. 实现 app/routers/reminders.py：
   - POST   /api/reminders                     创建提醒
   - GET    /api/reminders?pet_id=              查询某宠物的所有提醒
   - GET    /api/reminders/upcoming             获取即将到期提醒（首页用）
   - POST   /api/reminders/{reminder_id}/complete  标记完成
   - PUT    /api/reminders/{reminder_id}        编辑提醒
   - DELETE /api/reminders/{reminder_id}        删除提醒

3. 所有接口需要登录鉴权，校验数据归属权
```

**核验方式**：
1. 创建提醒，next_reminder_date 自动计算正确
2. 调用 upcoming 接口返回未来7天内的提醒
3. 标记完成后 next_reminder_date 推进一个周期
4. 过期的提醒不在 upcoming 中出现

---

### 任务 3.3：数据统计接口

**内容**：实现体重趋势数据查询接口和消费统计数据查询接口。

**目的**：为前端图表展示提供数据支持。

**注意细节**：
- 体重趋势：返回时间序列数据点（date, weight），支持按时间范围筛选
- 消费统计：支持月度和年度两个维度，返回总金额和按 sub_type 分组的明细

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请实现数据统计接口。

请先阅读已有代码，保持风格一致。

要求：
1. 在 app/services/record_service.py 中新增：
   - get_weight_trend(pet_id, user_id, period) -> List[{date, weight}]
     period 可选：1m/3m/6m/1y/all，筛选 sub_type 为"体重记录"的数据
     按日期正序排列
   - get_expense_stats(pet_id, user_id, year, month=None) -> {total, details: [{sub_type, amount}]}
     month 有值时返回月度统计，无值时返回年度统计
     details 按 sub_type 分组汇总金额

2. 在 app/routers/records.py 中新增：
   - GET /api/records/stats/weight?pet_id=&period=1m    体重趋势
   - GET /api/records/stats/expense?pet_id=&year=&month= 消费统计

3. 返回数据格式清晰，前端可直接用于 echarts/ucharts 渑染图表
4. 注意路由注册顺序，stats 路由要放在 {record_id} 路由之前，避免路径冲突
```

**核验方式**：
1. 插入5条不同日期的体重记录，调用体重趋势接口返回5个数据点，日期正序
2. 插入多条不同 sub_type 的消费记录，月度统计总金额和分类金额正确
3. 年度统计汇总12个月数据正确

---

---

## 任务 3.4 设计检查点（修改版）

### `[设计检查点]` 任务 3.4：前端 — 记录模块页面

> **暂停开发，先进行UI设计。**
>
> **需要设计的页面**：
>
> **页面1：记录主页面（Tab：记录）**
> - 目的：用户查看和管理宠物日常记录
> - 展示内容：顶部宠物切换栏（头像横滑）、日历视图（标记有记录的日期）、选中日期的记录列表（每条显示分类图标+子类型+备注摘要+时间）、右下角悬浮"+"添加按钮
>
> **页面2：添加/编辑记录页面**
> - 目的：填写一条新记录或修改已有记录
> - 展示内容：日期选择器（默认今天）、分类选择（四大类，选中后展开子分类）、子分类选择、备注输入框、图片上传区（最多9张）、金额输入（仅消费类显示）、体重输入（仅体重记录显示）、开启提醒开关+周期设置+提醒时间
>
> **页面3：记录详情页（只读）**
> - 目的：查看单条记录的完整信息
> - 展示内容：日期、分类图标+子分类名称、备注文字完整内容、图片列表（可点击放大查看）、金额（消费类显示）、体重值（体重记录显示）、关联提醒信息（如有，展示周期和下次提醒日期）
> - 底部操作栏：编辑按钮（跳转编辑页）、删除按钮（二次确认弹窗）
>
> **页面4：体重趋势图页面**
> - 目的：可视化展示宠物体重变化
> - 展示内容：顶部时间范围选择（近1月/3月/6月/1年/全部）、折线图（横轴日期纵轴体重）、当前体重和变化值
>
> **页面5：消费统计页面**
> - 目的：了解养宠消费情况
> - 展示内容：月度/年度切换、年月选择器、总金额展示、分类占比饼图或柱状图、分类明细列表
>
> **请完成以上页面的UI原型设计，确认后继续开发。**

---

## 任务 3.5：前端 — 记录模块页面开发（修改版）

**内容**：基于确认的UI原型，开发记录主页面、添加/编辑记录页、记录详情页（只读）、体重趋势图页、消费统计页。

**目的**：完成记录模块前端，打通数据记录全流程。

**注意细节**：
- 日历组件可使用 uni-app 插件市场的日历组件或自行实现
- 图表使用 ucharts 或 lime-echart 插件
- 分类和子分类选择使用两级联动选择器
- 图片上传调用已实现的 `/api/upload/image` 接口
- 提醒设置与记录创建在同一个表单中提交
- 记录列表点击跳转详情页（非编辑页），详情页中再提供编辑入口
- 详情页图片可点击放大预览（uni.previewImage）

**AI提示词**：
```
当前项目是 pppet，使用 uni-app (Vue3 Composition API) 开发。
请根据已确认的 UI 原型开发记录模块相关页面。

【UI风格规范】参考 uni.scss 中已定义的全局变量和 App.vue 中的全局样式。
使用已有的公共组件：PetSwitcher, EmptyState, LoadingOverlay。

【已确认的 UI 原型】
（此处粘贴你确认的原型图描述或截图）

要求：
1. pages/record/index.vue — 记录主页面（Tab页）：
   - 使用 PetSwitcher 组件切换宠物
   - 日历视图：展示当月日历，有记录的日期标记圆点，可切换月份
   - 点击日期加载该日记录列表
   - 每条记录显示：分类图标、子类型、备注摘要（超出一行省略）、时间
   - 点击某条记录跳转 **详情页**（非编辑页）
   - 右下角悬浮"+"按钮，点击跳转添加页
   - 无记录时使用 EmptyState 组件

2. pages/record/add.vue — 添加/编辑记录页面：
   - 接收参数 recordId（有则编辑模式，加载已有数据）和 petId
   - 日期选择器，默认今天
   - 分类选择：点击展开四大类（健康/日常护理/消费/医疗），选中后展开子分类列表
   - 备注 textarea
   - 图片上传区：最多9张，点击调用 uni.chooseImage 后上传
   - 条件字段：选择消费类时显示金额输入框，选择体重记录时显示体重输入框
   - 提醒开关：开启后展开周期天数输入和提醒时间选择器
   - 底部保存按钮

3. pages/record/detail.vue — 记录详情页（只读）：
   - 接收参数 recordId
   - 顶部显示日期和分类信息（分类图标 + 子分类名称）
   - 备注文字完整展示
   - 图片列表：网格布局展示，点击调用 uni.previewImage 放大查看
   - 消费类记录显示金额字段
   - 体重记录显示体重值字段
   - 如果有关联提醒，显示提醒信息卡片（提醒周期、下次提醒日期）
   - 底部固定操作栏：
     "编辑"按钮：跳转到 add.vue 并传 recordId（编辑模式）
     "删除"按钮：点击弹出二次确认弹窗，确认后调用删除 API，删除成功返回上一页

4. pages/record/weight-trend.vue — 体重趋势图：
   - 使用 ucharts 或 lime-echart 绘制折线图
   - 顶部时间范围Tab切换（近1月/3月/6月/1年/全部）
   - 图表下方显示当前体重和与上次记录的对比变化值

5. pages/record/expense-stats.vue — 消费统计：
   - 月度/年度切换Tab
   - 年月滚动选择器
   - 总金额大字展示
   - 饼图展示分类占比
   - 下方分类明细列表（图标+分类名+金额+占比百分比）

6. 注册所有新页面到 pages.json
```

**核验方式**：
1. 日历标记有记录的日期，点击展示记录列表
2. 点击记录卡片跳转到详情页，详情信息完整展示
3. 详情页图片可点击放大预览
4. 详情页点击"编辑"跳转编辑页，数据预填充正确
5. 详情页点击"删除"弹出确认框，确认后记录删除成功并返回上一页
6. 添加记录后返回日历页，数据刷新正确
7. 体重趋势图根据时间范围正确渲染
8. 消费统计金额和占比计算正确
9. 宠物切换后数据正确刷新
10. 无记录时展示空状态组件


## 阶段四：AI 体检报告分析模块

---

### 任务 4.1：AI 服务层 — DeepSeek 集成

**内容**：封装 DeepSeek API 调用服务，支持体检报告解读和对话问答两种调用模式。

**目的**：建立统一的 AI 服务层，后续体检分析和对话模块共用。

**注意细节**：
- 使用 httpx 的 async client 调用 DeepSeek API
- DeepSeek API 兼容 OpenAI 接口格式
- 体检解读：普通请求，等待完整响应
- 对话问答：流式请求（SSE），逐 token 返回
- API Key 和 Base URL 从环境变量读取
- 做好异常处理：超时、API 报错、额度不足等

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请封装 DeepSeek API 调用服务。

请先阅读 app/config.py 获取配置方式，保持风格一致。

要求：
1. 创建 app/services/deepseek_service.py：

   class DeepSeekService:
       """DeepSeek API 调用服务，兼容 OpenAI 接口格式"""

       async def interpret_health_report(self, ocr_data: str, pet_info: dict) -> str:
           """
           体检报告解读。
           - ocr_data: OCR 识别出的文本数据
           - pet_info: 宠物档案信息（品种、年龄、体重等）
           - 返回通俗化解读文本
           - 使用精心设计的 system prompt，角色为专业宠物健康顾问
           """

       async def chat_stream(self, messages: list, pet_info: dict):
           """
           对话问答，流式输出。
           - messages: 对话历史 [{"role": "user/assistant", "content": "..."}]
           - pet_info: 当前宠物档案信息
           - yield 每个 token 文本片段
           - system prompt 包含宠物档案信息，角色为该宠物的专属健康顾问
           """

2. system prompt 设计要点：
   - 体检解读 prompt：你是一位专业的宠物健康顾问，请用通俗易懂的语言解读以下体检报告数据。
     对每项指标说明：指标含义、当前数值是否正常、可能的影响、建议。
     最后给出整体健康评估和注意事项。宠物信息：{pet_info}
   - 对话 prompt：你是{pet_name}（{species}/{breed}/{age}）的专属健康顾问。
     基于以下健康档案信息回答问题：{pet_info}。回答要通俗易懂，紧急情况建议就医。

3. 使用 httpx.AsyncClient，超时设置30秒
4. 流式请求使用 stream=True，逐行解析 SSE 数据
5. 异常处理：连接超时、API Key 无效、速率限制等，抛出自定义异常
6. API Key 和 Base URL 从 config 读取，不硬编码
```

**核验方式**：
1. 编写测试脚本调用 interpret_health_report，传入模拟 OCR 数据，成功返回解读文本
2. 调用 chat_stream，能逐 token 接收到流式响应
3. 传入无效 API Key 能正确捕获异常并返回有意义的错误信息

---

### 任务 4.2：Coze OCR 服务集成

**内容**：封装 Coze 工作流 API 调用，实现体检报告图片/PDF 的 OCR 识别。

**目的**：将体检报告文件转换为结构化文本数据，供 DeepSeek 解读。

**注意细节**：
- 具体接口格式以业务方提供的 Coze 官方文档为准
- 封装为独立 service，与 DeepSeek service 解耦
- 需要处理图片和 PDF 两种格式
- 返回结构化的指标数据（尽可能解析为 JSON 格式）

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请封装 Coze 工作流 OCR 服务。

【Coze API 对接文档】
（此处粘贴你提供的 Coze 官方对接文档内容）

要求：
1. 创建 app/services/coze_ocr_service.py：

   class CozeOCRService:
       """Coze 工作流 OCR 服务，用于识别宠物体检报告"""

       async def recognize_report(self, file_path: str, file_type: str) -> dict:
           """
           调用 Coze 工作流识别体检报告。
           - file_path: 本地文件路径
           - file_type: "image" 或 "pdf"
           - 返回：{"raw_text": "OCR原始文本", "indicators": [{"name": "白细胞", "value": "12.5", "unit": "10^9/L", "reference_range": "6-17"}]}
           """

2. 根据 Coze 文档实现具体的 API 调用逻辑
3. 图片需要 base64 编码后传输（或按 Coze 文档要求的方式）
4. 做好异常处理和重试逻辑（最多重试2次）
5. API Key 从环境变量读取
```

**核验方式**：
1. 使用一张宠物体检报告图片调用接口，成功返回识别结果
2. 返回的 indicators 列表结构正确
3. 网络超时时正确重试并最终返回错误

---
---

## 任务 4.3：体检报告分析接口（修改版）

**内容**：实现体检报告上传、OCR 识别、AI 解读、归档的完整接口链路，包含额度管理和重新分析能力。

**目的**：打通体检报告分析的后端全流程。

**注意细节**：
- 整体流程：上传文件 → 创建 health_report 记录（status=pending）→ 调用 Coze OCR → 调用 DeepSeek 解读 → 更新记录（status=completed）
- 分析前检查用户额度（普通用户永久3次，会员每月10次）
- 额度不足返回 403 并提示
- 提供查询历史分析记录列表和单条详情接口
- 支持用户修改 OCR 识别结果（不消耗额度，仅更新数据）
- 支持基于修改后的数据重新触发 AI 解读（消耗1次额度）
- 分析失败时不扣减额度

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请实现体检报告分析的完整接口。

请先阅读已有的 deepseek_service.py, coze_ocr_service.py, models/health_report.py,
models/user.py 中的额度相关字段，保持风格一致。

要求：
1. 创建 app/services/quota_service.py：
   """用户 AI 使用额度管理"""
   - check_analysis_quota(user: User) -> bool
     普通用户：检查 ai_analysis_used_count < 3
     会员用户：检查当月已分析次数 < 10（通过查询 health_reports 表中当月 status=completed 的记录数）
   - consume_analysis_quota(user: User) -> None
     普通用户：ai_analysis_used_count += 1
     会员：无需操作（按月统计查询即可）
   - get_analysis_remaining(user: User) -> int
     返回剩余可用次数

2. 创建 app/services/health_service.py：
   - analyze_report(pet_id, user_id, file_path, file_type) -> HealthReport
     完整流程：检查额度 → 创建记录(status=pending) → 更新status=processing →
     调用OCR → 调用DeepSeek → 更新记录(status=completed) → 扣减额度
     任何步骤失败则更新 status=failed，不扣减额度
   - get_report_list(pet_id, user_id) -> List[HealthReport]
     按时间倒序排列
   - get_report_detail(report_id, user_id) -> HealthReport
   - update_report_indicators(report_id, user_id, indicators_json) -> HealthReport
     用户手动修改指标数据，仅更新 parsed_indicators_json 字段，不重新AI解读，不消耗额度
   - reanalyze_report(report_id, user_id) -> HealthReport
     基于当前 parsed_indicators_json 重新调用 DeepSeek 生成解读
     需要检查并扣减额度，流程：检查额度 → 调用DeepSeek → 更新ai_interpretation → 扣减额度

3. 实现 app/routers/health.py：
   - POST /api/health/analyze                       上传并分析（接收 pet_id + file_path + file_type）
   - GET  /api/health/reports?pet_id=                查询分析历史列表
   - GET  /api/health/reports/{id}                   查询单条详情
   - PUT  /api/health/reports/{id}/indicators        修改指标数据（不消耗额度）
   - POST /api/health/reports/{id}/reanalyze         重新AI解读（消耗1次额度）
   - GET  /api/health/quota                          查询当前用户剩余分析次数

4. 分析接口和重新分析接口，额度不足时返回 403 {"detail": "AI分析次数已用完", "remaining": 0}
5. 分析过程中如果 OCR 或 DeepSeek 调用失败，更新 status 为 "failed"，不扣减额度
6. 所有接口需要登录鉴权，校验数据归属权
```

**核验方式**：
1. 上传一张体检报告图片，分析完成后查询详情，三个区域数据完整（原始文件、指标列表、解读文本）
2. 普通用户分析3次后第4次返回 403
3. 分析失败时 status 为 failed，额度未扣减
4. 修改指标数据接口不消耗额度，数据更新成功
5. 调用重新分析接口，AI解读文本更新，额度扣减1次
6. 重新分析时额度不足返回 403
7. 查询剩余次数接口返回正确

---


### `[设计检查点]` 任务 4.4：前端 — AI分析模块页面

> **暂停开发，先进行UI设计。**
>
> **需要设计的页面**：
>
> **页面1：AI Tab 主页面**
> - 目的：AI 功能的入口页，分为体检分析和AI对话两个区域
> - 展示内容：顶部区域"体检报告分析"（上传入口按钮 + 历史分析记录列表缩略）、下方区域"AI宠物顾问"（每只宠物一个对话入口卡片，显示头像+昵称，未开通的显示锁定状态）、剩余额度提示文字
>
> **页面2：上传体检报告页面**
> - 目的：选择宠物并上传体检报告
> - 展示内容：宠物选择器、上传区域（支持拍照/相册/文件）、剩余分析次数提示、开始分析按钮、分析中的加载动画
>
> **页面3：分析结果详情页**
> - 目的：查看体检报告的AI解读结果
> - 展示内容：顶部原始报告图片（可点击放大）、中部指标数据卡片列表（每项：名称、数值、参考范围、状态标签红绿黄）、底部AI通俗解读文字区域、右上角编辑按钮（可修改指标数据）
>
> **页面4：历史分析记录列表页**
> - 目的：查看该宠物所有历史体检分析
> - 展示内容：按时间倒序的记录卡片（日期+状态标签+指标概要）
>
> **请完成以上页面的UI原型设计，确认后继续开发。**

---

### 任务 4.5：前端 — AI分析模块页面开发

**内容**：基于确认的UI原型，开发 AI Tab 主页面、上传报告页、分析结果页、历史记录页。

**目的**：完成体检报告分析模块的前端。

**注意细节**：
- 上传支持拍照（uni.chooseImage source=camera）、相册、文件（uni.chooseMessageFile）
- 分析过程中展示加载动画，轮询或等待分析结果
- 指标状态用颜色区分：正常绿色、偏高红色、偏低黄色
- 剩余次数不足时上传按钮置灰并提示

**AI提示词**：
```
当前项目是 pppet，使用 uni-app (Vue3 Composition API) 开发。
请根据已确认的 UI 原型开发 AI 体检分析相关页面。

【UI风格规范】同前（省略）

【已确认的 UI 原型】
（此处粘贴确认的原型图描述）

要求：
1. pages/ai/index.vue — AI Tab 主页面：
   - 上半区"体检报告分析"：上传入口按钮 + 剩余次数显示 + 最近3条分析记录
   - 下半区"AI宠物顾问"：宠物对话入口卡片列表
   - 锁定状态的宠物卡片点击后弹出会员引导弹窗

2. pages/ai/upload-report.vue — 上传体检报告：
   - 宠物选择（如果从某个宠物详情进来则预选）
   - 上传区：支持拍照、相册选图、选择PDF文件
   - 上传后显示文件预览缩略图
   - 剩余分析次数提示
   - "开始分析"按钮，点击后调用分析 API
   - 分析中显示加载动画（可用 Lottie 或 CSS 动画），禁止重复点击
   - 分析完成后自动跳转结果详情页

3. pages/ai/report-detail.vue — 分析结果详情：
   - 接收参数 reportId
   - 原始报告图片展示（点击调用 uni.previewImage 放大）
   - 指标数据卡片列表，每项包含：
     指标名称、数值、参考范围、状态色块（绿/红/黄）
   - AI 解读文本区域
   - 右上角编辑按钮：进入编辑模式，指标数值变为可编辑输入框，保存后调用修改 API

4. pages/ai/report-history.vue — 历史分析记录列表：
   - 宠物筛选栏
   - 记录卡片列表（按时间倒序）：日期、处理状态（已完成/失败/处理中）、概要
   - 点击跳转详情页

5. 注册页面到 pages.json
```

**核验方式**：
1. 上传图片并分析，加载动画正常显示，分析完成跳转结果页
2. 结果页三个区域内容正确展示
3. 指标状态颜色区分正确
4. 编辑指标数据保存成功
5. 历史列表正确展示，点击跳转正常
6. 剩余次数为0时按钮置灰

---

## 阶段五：AI 对话模块

---
## 任务 5.1：AI 对话接口（修改版）

**内容**：实现 AI 对话的会话管理（含创建、查询、删除）、消息发送（SSE流式）、历史查询接口。

**目的**：完成 AI 对话智能体的后端逻辑。

**注意细节**：
- 消息发送接口使用 SSE（Server-Sent Events）流式返回
- 每次发送消息前检查每日对话额度
- System prompt 注入该宠物的完整档案 + 健康档案
- 携带最近10条对话历史作为上下文
- 会话标题自动取用户第一条消息的前20个字符
- 支持删除会话（级联删除该会话下所有消息）

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请实现 AI 对话智能体接口。

请先阅读已有的 deepseek_service.py（chat_stream 方法）、
models/chat_session.py、models/chat_message.py、services/quota_service.py，保持风格一致。

要求：
1. 在 app/services/quota_service.py 中新增：
   - check_chat_quota(user: User) -> bool
     普通用户：查询 user_daily_quota 表今天的 chat_count < 10
     会员：直接返回 True
   - consume_chat_quota(user: User) -> None
     普通用户：今天的 chat_count += 1（不存在则创建记录）
     会员：无操作
   - get_chat_remaining(user: User) -> int | None
     普通用户返回今日剩余次数，会员返回 None（表示不限）

2. 创建 app/services/chat_service.py：
   - create_session(pet_id, user_id) -> ChatSession
   - get_sessions(pet_id, user_id) -> List[ChatSession]
     按更新时间倒序，每个会话附带最后一条消息摘要和消息总数
   - get_session_messages(session_id, user_id, page, page_size) -> {total, list}
     分页查询消息，按时间正序排列
   - delete_session(session_id, user_id) -> None
     删除会话及其所有关联消息（真删除）
   - send_message(session_id, user_id, content: str) -> AsyncGenerator
     流程：
     a. 校验会话归属权
     b. 检查每日对话额度
     c. 保存用户消息到 chat_messages
     d. 如果是该会话第一条消息，自动设置会话标题（取前20字符）
     e. 加载宠物档案信息 + 近期健康档案摘要
     f. 加载该会话最近10条消息作为上下文
     g. 构造 messages 列表（system + history + current）
     h. 调用 deepseek_service.chat_stream
     i. 逐 token yield，同时拼接完整回复
     j. 流结束后保存 assistant 消息到 chat_messages
     k. 扣减每日额度
     l. 更新会话的 updated_at 时间
   - check_pet_chat_permission(pet_id, user_id) -> bool
     检查该宠物是否可使用对话。
     逻辑：查询用户已创建对话的宠物数量，
     普通用户 ≤1 只，会员 ≤3 只。
     如果该宠物已有会话则直接放行（不重复计数）。

3. 实现 app/routers/chat.py：
   - POST   /api/chat/sessions              创建会话（传 pet_id）
   - GET    /api/chat/sessions?pet_id=       获取会话列表
   - GET    /api/chat/sessions/{id}/messages?page=&page_size=  获取会话消息历史
   - DELETE /api/chat/sessions/{id}          删除会话（级联删除所有消息）
   - POST   /api/chat/sessions/{id}/send     发送消息（SSE流式响应）
   - GET    /api/chat/quota                  查询今日剩余对话次数
   - GET    /api/chat/permissions            查询用户可对话的宠物列表和锁定状态

4. 发送消息接口使用 sse-starlette 的 EventSourceResponse
5. 额度不足返回 403
6. 未开通对话权限的宠物返回 403
7. 删除不存在的会话或非本人会话返回 404/403
```

**核验方式**：
1. 创建会话 → 发送消息 → 收到流式响应 → 消息保存到数据库
2. 查询消息历史包含用户消息和 AI 回复，分页正确
3. 普通用户发送第11条消息返回 403
4. 第二只宠物创建对话返回 403（普通用户）
5. 会话标题在第一条消息后自动生成
6. 删除会话后查询返回 404，关联消息全部清除
7. 查询 permissions 接口正确返回每只宠物的锁定/解锁状态

---


### `[设计检查点]` 任务 5.2：前端 — AI对话页面

> **暂停开发，先进行UI设计。**
>
> **需要设计的页面**：
>
> **页面1：AI对话主页面**
> - 目的：与宠物专属AI顾问对话
> - 展示内容：顶部显示宠物头像+昵称+"的专属顾问"、免责声明提示条（常驻）、对话消息气泡列表（用户消息右侧、AI回复左侧）、底部输入框+发送按钮、左上角返回和历史会话入口、今日剩余次数提示
>
> **页面2：历史会话列表页**
> - 目的：查看和切换历史对话会话
> - 展示内容：会话卡片列表（标题+最后消息时间+消息条数），右上角"新建对话"按钮
>
> **请完成以上页面的UI原型设计，确认后继续开发。**

---

### 任务 5.3：前端 — AI对话页面开发

**内容**：基于确认的UI原型，开发 AI 对话页面和历史会话列表页。

**目的**：完成 AI 对话智能体的前端。

**注意细节**：
- SSE 流式接收需要使用 uni-app 兼容的方案（uni.request 不支持 SSE，需用 requestTask 或第三方方案）
- 消息气泡逐字显示效果
- 对话列表自动滚动到底部
- 输入框发送后清空，发送中禁用重复发送

**AI提示词**：
```
当前项目是 pppet，使用 uni-app (Vue3 Composition API) 开发。
请根据已确认的 UI 原型开发 AI 对话相关页面。

【UI风格规范】同前

【已确认的 UI 原型】
（此处粘贴确认的原型图描述）

要求：
1. pages/ai/chat.vue — AI 对话主页面：
   - 接收参数 petId 和可选的 sessionId
   - 无 sessionId 时自动创建新会话或加载最近会话
   - 顶部导航栏：返回按钮、宠物头像+昵称+"的专属顾问"、历史会话图标
   - 导航栏下方固定免责声明条：
     "AI建议仅供参考，不能替代专业兽医诊断，紧急情况请立即就医。"
     浅黄色背景，小字展示
   - 对话区域：
     用户消息：右侧气泡，配用户头像
     AI消息：左侧气泡，配AI头像（萌宠机器人图标），支持逐字显示效果
   - 新消息自动滚动到底部
   - 底部输入区域：
     输入框 + 发送按钮
     发送中按钮变为loading状态，禁止重复发送
     输入框上方显示"今日剩余 X 次"（会员显示"不限"）
     次数为0时输入框禁用，显示提示文字

2. SSE 流式接收方案：
   - 由于 uni-app 的 uni.request 不支持 SSE
   - 方案A：使用 plus.net.XMLHttpRequest（App端）处理流式响应
   - 方案B：使用轮询方案作为降级（每500ms请求一次最新消息）
   - 优先实现方案A，保留方案B作为降级

3. pages/ai/chat-history.vue — 历史会话列表：
   - 接收参数 petId
   - 会话卡片列表：标题、最后对话时间、消息数
   - 点击跳转到 chat 页面并传 sessionId
   - 右上角"新建对话"按钮

4. 注册页面到 pages.json
```

**核验方式**：
1. 进入对话页，发送消息后收到AI流式回复，逐字显示
2. 对话记录保存，退出重新进入可查看历史
3. 切换历史会话正确加载对应消息
4. 次数用尽后输入框正确禁用
5. 免责声明常驻显示

---

## 阶段六：社区与首页

---

### 任务 6.1：社区文章接口（前台）

**内容**：实现文章列表查询、详情查询、点赞、收藏、评论接口。

**目的**：完成社区模块的前台后端逻辑。

**注意细节**：
- 文章列表支持按分类筛选、分页查询
- 点赞和收藏为 toggle 操作（再次调用则取消）
- 浏览详情时自动 +1 浏览量
- 评论按时间正序排列，返回评论者昵称和头像

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请实现社区文章的前台接口。

请先阅读已有模型和代码风格，保持一致。

要求：
1. 创建 app/services/community_service.py：
   - get_articles(category, page, page_size) -> {total, list}
     支持分类筛选，分页查询，仅返回 is_published=True 的文章
   - get_article_detail(article_id, user_id) -> Article + is_liked + is_favorited
     浏览量自动 +1，返回当前用户是否已点赞/收藏
   - toggle_like(article_id, user_id) -> bool（返回当前状态）
   - toggle_favorite(article_id, user_id) -> bool
   - create_comment(article_id, user_id, content) -> Comment
   - get_comments(article_id, page, page_size) -> {total, list}
     按时间正序，每条包含用户昵称和头像
   - get_user_favorites(user_id, page, page_size) -> {total, list}

2. 实现 app/routers/community.py：
   - GET    /api/community/articles?category=&page=&page_size=
   - GET    /api/community/articles/{id}
   - POST   /api/community/articles/{id}/like
   - POST   /api/community/articles/{id}/favorite
   - POST   /api/community/articles/{id}/comments
   - GET    /api/community/articles/{id}/comments?page=&page_size=
   - GET    /api/community/favorites（我的收藏）

3. 查看文章详情和浏览列表不需要登录（可选鉴权：有token则返回点赞/收藏状态，无token也可查看）
4. 点赞、收藏、评论需要登录
```

**核验方式**：
1. 查询文章列表分页正确，分类筛选有效
2. 查看详情后浏览量 +1
3. 点赞两次后恢复未点赞状态，like_count 正确增减
4. 评论创建后出现在评论列表中
5. 我的收藏列表正确

---

### 任务 6.2：管理后台

**内容**：开发简易 Web 管理后台，支持管理员登录、文章增删改查、评论管理。

**目的**：为运营人员提供内容管理能力。

**注意细节**：
- 使用 FastAPI + Jinja2 模板渲染简易页面，或使用独立的 Vue 单页面
- 管理员账号独立于前端用户，使用 admin_users 表
- 富文本编辑器用于文章正文编辑
- 支持文章的草稿/发布状态切换

**AI提示词**：
```
当前项目是 pppet，FastAPI 后端。请开发一个简易的 Web 管理后台。

要求：
1. 使用 FastAPI + Jinja2 模板渲染（不引入额外前端框架，保持简单）

2. 创建 app/admin/ 目录：
   - app/admin/router.py — 管理后台路由
   - app/admin/templates/ — Jinja2 模板目录
   - app/admin/static/ — 管理后台静态资源

3. 页面列表：
   - /admin/login — 登录页（用户名+密码）
   - /admin/ — 仪表盘（显示文章数、用户数、评论数统计）
   - /admin/articles — 文章列表（表格展示：标题、分类、状态、浏览量、操作按钮）
   - /admin/articles/create — 创建文章（表单：标题、封面图上传、分类选择、作者、正文富文本编辑器）
   - /admin/articles/{id}/edit — 编辑文章
   - /admin/comments — 评论管理（列表展示，支持删除）

4. 富文本编辑器使用 wangEditor 5（CDN引入）
5. 封面图上传复用已有的 /api/upload/image 接口
6. 管理员登录使用 session（存 cookie），与前端 JWT 体系隔离
7. 所有管理后台页面需要登录校验中间件
8. 使用 Bootstrap 5（CDN引入）快速构建页面样式
```

**核验方式**：
1. 访问 `/admin/login` 显示登录页面
2. 使用 admin/admin123 登录成功跳转仪表盘
3. 创建一篇文章（含富文本正文和封面图），前台接口能查询到
4. 编辑文章内容并保存，前台查询更新
5. 删除评论后前台不再显示

---

### `[设计检查点]` 任务 6.3：前端 — 社区与首页页面

> **暂停开发，先进行UI设计。**
>
> **需要设计的页面**：
>
> **页面1：首页（Tab：首页）**
> - 目的：宠物信息概览和快捷入口
> - 展示内容：顶部宠物切换栏（头像横滑）、当前宠物信息卡片（大头像+昵称+品种+年龄+体重）、近期待办提醒列表（如"3天后体内驱虫"）、快捷入口按钮组（快速记录、AI分析、AI对话、知识社区）
>
> **页面2：社区主页面（Tab：社区）**
> - 目的：浏览养宠知识文章
> - 展示内容：顶部分类标签横滑栏（全部/生活类/训化类/医疗类/饮食营养类/新手入门类）、文章卡片列表（封面图+标题+分类标签+浏览量+点赞数），下拉刷新，上拉加载更多
>
> **页面3：文章详情页**
> - 目的：查看文章完整内容
> - 展示内容：标题、作者+发布时间、正文富文本内容、底部操作栏（点赞按钮+收藏按钮+浏览量）、评论区域（评论列表+输入框）
>
> **页面4：我的页面（Tab：我的）**
> - 目的：个人中心
> - 展示内容：用户头像+昵称、功能列表入口（宠物管理、我的收藏、会员中心、设置）、会员中心显示当前身份和权益概要
>
> **请完成以上页面的UI原型设计，确认后继续开发。**

---

## 任务 6.4：前端 — 首页、社区、我的页面开发（修改版）

**内容**：基于确认的UI原型，开发首页、社区页面、文章详情页、我的页面（含宠物管理、收藏、会员中心、设置、意见反馈）。

**目的**：完成所有 Tab 页面和"我的"子页面，产品功能闭环。

**注意细节**：
- 首页是用户打开应用的第一个页面，加载速度优先
- 社区文章列表需要分页加载（上拉加载更多）
- 富文本内容使用 rich-text 组件渲染
- 评论输入使用底部弹出的输入框
- 我的页面预留会员中心入口，点击后展示权益对照表
- 意见反馈页面需要类型选择和内容提交功能

**AI提示词**：
```
当前项目是 pppet，使用 uni-app (Vue3 Composition API) 开发。
请根据已确认的 UI 原型开发首页、社区和个人中心页面。

【UI风格规范】参考 uni.scss 全局变量和 App.vue 全局样式，使用已有公共组件。

【已确认的 UI 原型】
（此处粘贴确认的原型图描述）

要求：
1. pages/home/index.vue — 首页（Tab页）：
   - 使用 PetSwitcher 组件切换宠物
   - 当前宠物信息卡片：大圆形头像 + 昵称 + 品种 + 年龄 + 体重
     年龄根据 birthday 计算，或显示 approximate_age
   - 近期待办提醒列表：调用 /api/reminders/upcoming
     每条显示：宠物昵称 + 提醒类型 + 距离天数（如"3天后"）
     点击可跳转到对应记录
   - 快捷入口按钮组（2x2 网格）：
     快速记录（跳转添加记录页）、AI分析（跳转上传报告页）、
     AI对话（跳转对话页）、知识社区（切换到社区Tab）
   - 无宠物时使用 EmptyState 组件显示引导创建

2. pages/community/index.vue — 社区主页（Tab页）：
   - 顶部分类标签横滑栏，"全部"默认选中
   - 文章卡片列表，每个卡片：
     左侧封面图缩略（圆角）+ 右侧标题+分类标签+底部浏览量和点赞数
   - 下拉刷新（onPullDownRefresh）
   - 上拉加载更多（onReachBottom），分页每页10条
   - 点击卡片跳转详情页

3. pages/community/detail.vue — 文章详情页：
   - 标题（大字加粗）
   - 作者 + 发布时间
   - 正文使用 rich-text 组件渲染 HTML
   - 底部固定操作栏：点赞按钮（已赞变红）、收藏按钮（已收藏变黄）、浏览量
   - 评论区域：
     评论列表（头像+昵称+内容+时间）
     底部固定"写评论"按钮，点击弹出输入框

4. pages/mine/index.vue — 我的页面（Tab页）：
   - 顶部用户信息区：头像 + 昵称
   - 功能列表（圆角卡片内的 cell 列表）：
     宠物管理（跳转 pet/list）
     我的收藏（跳转收藏列表页）
     会员中心（跳转会员页面）
     设置（跳转设置页面）

5. pages/mine/favorites.vue — 我的收藏列表：
   - 复用社区文章卡片组件
   - 调用 /api/community/favorites 接口
   - 空收藏时使用 EmptyState 组件

6. pages/mine/membership.vue — 会员中心：
   - 显示当前身份（普通用户/会员）
   - 权益对照表展示（参照 PRD 中的会员权益表格）
   - 当前各项额度使用情况（调用 /api/user/quota 展示）
   - 预留"开通会员"按钮（第一版点击提示"即将上线"）

7. pages/mine/settings.vue — 设置页面：
   - 关于我们（弹窗或跳转页面展示应用信息和版本号）
   - 意见反馈（跳转 feedback 页面）
   - 清除缓存（调用 uni.getStorageInfo 展示缓存大小，点击清除）
   - 退出登录（清除 token，跳转登录页）

8. pages/mine/feedback.vue — 意见反馈页面：
   - 反馈类型选择器：功能建议 / Bug反馈 / 其他（单选按钮或选择器）
   - 反馈内容 textarea（必填，限制500字，显示字数统计）
   - 联系方式输入框（选填，placeholder 提示"手机号或邮箱，方便我们联系你"）
   - 提交按钮，调用 POST /api/user/feedback
   - 提交成功后 toast 提示"感谢反馈，我们会认真处理"并返回上一页
   - 提交中按钮显示 loading 状态，防重复提交

9. 注册所有新页面到 pages.json
10. 配置 pages.json 的 tabBar（如未在 2.3.5 中完成，则在此配置）
```

**核验方式**：
1. 首页宠物信息展示正确，切换宠物数据刷新
2. 待办提醒列表展示即将到期的提醒
3. 无宠物时首页展示引导创建空状态
4. 社区文章列表分页加载正常，分类筛选有效
5. 文章详情富文本渲染正确，点赞收藏交互正常
6. 评论发送后立即显示在列表中
7. 我的页面各入口跳转正确
8. 会员中心正确展示权益表和当前额度使用情况
9. 意见反馈提交成功，数据库有对应记录
10. 退出登录后跳转登录页，重新打开应用需要重新登录
11. 底部 TabBar 5个Tab切换正常


---

## 阶段七：登录与全局联调

---

### `[设计检查点]` 任务 7.1：前端 — 登录和引导页面

> **暂停开发，先进行UI设计。**
>
> **需要设计的页面**：
>
> **页面1：登录页面**
> - 目的：用户进入应用的第一个页面
> - 展示内容：应用 Logo + 名称"pppet"、温暖治愈风的欢迎插画或动画、微信一键登录按钮（本地开发阶段显示为"快速体验"按钮，输入昵称即可登录）
>
> **页面2：新用户引导页**
> - 目的：首次登录的用户引导创建第一只宠物
> - 展示内容：温馨文案"先来添加你的小可爱吧"、简化版创建宠物表单（仅昵称+物种+品种三个必填字段）、跳过按钮（跳过后进入首页，首页提示创建宠物）
>
> **请完成以上页面的UI原型设计，确认后继续开发。**

---

### 任务 7.2：前端 — 登录与引导页面开发

**内容**：基于确认的UI原型，开发登录页面和新用户引导页面。

**目的**：完成应用入口流程。

**AI提示词**：
```
当前项目是 pppet，使用 uni-app (Vue3 Composition API) 开发。
请根据已确认的 UI 原型开发登录和引导页面。

【已确认的 UI 原型】
（此处粘贴）

要求：
1. pages/login/index.vue — 登录页面：
   - 应用 Logo 和名称展示
   - 本地开发模式：显示昵称输入框 + "快速体验"按钮
     调用 /api/auth/mock-login，成功后存储 token 到本地（uni.setStorageSync）
   - 预留微信登录按钮（button open-type="getPhoneNumber" 或自定义）
   - 登录成功后检查用户是否有宠物：
     有 → 跳转首页
     无 → 跳转引导页

2. pages/login/guide.vue — 新用户引导页：
   - 温馨插画/动画
   - 文案："先来添加你的小可爱吧 🐾"
   - 简化创建表单：昵称、物种选择、品种选择
   - 创建按钮，成功后跳转首页
   - 右上角"跳过"按钮，跳过后直接进首页

3. 全局路由拦截逻辑：
   - 在 App.vue 或 utils/request.js 中：
     每次启动检查本地是否有 token
     无 token → 跳转登录页
     有 token → 验证有效性，失效则跳转登录页

4. 注册页面到 pages.json，登录页设为非 tabBar 页面
```

**核验方式**：
1. 首次打开应用跳转登录页
2. 输入昵称登录成功，跳转引导页
3. 创建宠物后进入首页
4. 退出应用重新打开，token 有效直接进首页
5. token 过期后自动跳转登录页

---

### 任务 7.3：全局联调与Bug修复

**内容**：全流程测试所有功能模块，修复前后端联调中发现的问题。

**目的**：确保各模块联通，核心流程跑通。

**注意细节**：
- 按以下核心流程逐一测试并记录问题
- 修复的每个 Bug 单独一个 commit

**AI提示词**：
```
当前项目是 pppet，已完成所有模块开发。请协助我进行全局联调。

我会逐个描述遇到的问题，请你分析原因并给出修复方案。

修复规则：
1. 每次只修复一个问题
2. 先说明问题原因
3. 列出需要修改的文件
4. 给出修改代码
5. 说明如何验证修复结果
```

**核验方式（全流程检查清单）**：

1. **登录流程**：打开应用 → 登录 → 引导创建宠物 → 进入首页 ✓
2. **宠物管理**：添加第二只宠物 → 编辑宠物 → 切换宠物 → 删除宠物 ✓
3. **数据记录**：添加健康记录 → 添加消费记录 → 添加体重记录 → 日历标记 → 编辑记录 → 删除记录 ✓
4. **提醒功能**：创建带提醒的记录 → 首页显示待办 → 标记完成 → 日期推进 ✓
5. **数据可视化**：体重趋势图渲染 → 切换时间范围 → 消费月度统计 → 消费年度统计 ✓
6. **体检分析**：上传报告 → 等待分析 → 查看结果 → 修改指标 → 查看历史 → 额度扣减正确 ✓
7. **AI对话**：进入对话 → 发送消息 → 收到流式回复 → 查看历史会话 → 新建会话 → 每日额度正确 ✓
8. **社区模块**：浏览文章 → 分类筛选 → 查看详情 → 点赞 → 收藏 → 评论 → 我的收藏 ✓
9. **管理后台**：管理员登录 → 创建文章 → 编辑文章 → 前台可见 → 删除评论 
10. **我的页面**：宠物管理入口 → 收藏列表 → 会员中心 → 设置 → 退出登录 ✓

---

## 阶段八：优化与收尾

---

### 任务 8.1：全局 Loading 和错误处理

**内容**：统一全局加载状态展示和错误提示交互。

**目的**：提升用户体验，避免接口异常时白屏或无反馈。

**AI提示词**：
```
当前项目是 pppet，uni-app 前端。请优化全局加载和错误处理。

要求：
1. 在 utils/request.js 中完善：
   - 请求发送时自动显示 loading（可配置某些接口不显示）
   - 请求成功自动隐藏 loading
   - 网络错误统一 toast 提示"网络异常，请稍后重试"
   - 401 错误清除 token 并跳转登录页
   - 403 错误 toast 提示具体原因（从 response.detail 读取）
   - 422 校验错误 toast 提示"请检查输入内容"
   - 500 错误 toast 提示"服务器繁忙"

2. 创建 components/EmptyState.vue — 空状态组件：
   - 接收 props: icon, text
   - 用于列表为空时展示（如无记录、无文章、无宠物等场景）

3. 在所有列表页面中，数据为空时使用 EmptyState 组件

保持已有代码风格一致。
```

**核验方式**：
1. 接口请求时出现 loading
2. 断网情况下操作出现友好提示
3. 空列表展示空状态组件

---

### 任务 8.2：前端样式走查与适配

**内容**：检查所有页面在不同屏幕尺寸下的显示效果，统一样式细节。

**目的**：确保视觉一致性和多端适配。

**AI提示词**：
```
当前项目是 pppet，uni-app 前端。请协助进行样式走查。

我会截图标注问题区域，请你给出 CSS 修复方案。

修复规则：
1. 只修改样式相关代码
2. 使用 rpx 单位保证多屏适配
3. 保持温暖治愈的设计风格
4. 颜色统一使用全局 CSS 变量
```

**核验方式**：
1. 在 iPhone SE（小屏）和 iPhone 14 Pro Max（大屏）模拟器上分别查看
2. 所有页面布局不错位，文字不溢出
3. 颜色和圆角风格全局一致

---

### 任务 8.3：README 与部署文档

**内容**：编写项目 README 和本地部署文档。

**目的**：方便后续维护和协作。

**AI提示词**：
```
当前项目是 pppet。请编写完整的 README.md 和部署文档。

要求：
1. README.md 包含：
   - 项目介绍
   - 技术栈
   - 项目目录结构说明
   - 本地开发环境搭建步骤（后端 + 前端）
   - 环境变量说明（.env 各字段含义）
   - 管理后台访问方式
   - API 文档访问方式（Swagger）

2. 文档要详细到一个新人按步骤操作就能跑起来
3. 保持简洁，不废话
```

**核验方式**：
1. 一个新环境按照文档操作能成功启动前后端
2. 文档中的所有链接和命令有效

---

以上就是完整的开发任务清单，总计 **8个阶段、23个任务**（含5个设计检查点）。建议你按编号顺序执行，每完成一个阶段做一次整体回归测试。遇到设计检查点时停下来做原型设计，确认后再继续，这样能避免返工。
