# pppet Backend

pppet 的后端服务基于 FastAPI + SQLAlchemy Async + MySQL，当前阶段提供项目骨架、数据库配置和 Alembic 迁移能力。

## 目录结构

```text
backend/
├── app/
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── alembic/
│   └── versions/
├── scripts/
├── uploads/
│   ├── images/
│   └── reports/
├── .env.example
├── alembic.ini
└── requirements.txt
```

## 首次使用

以下命令均在 `backend/` 目录下执行：

1. 复制环境变量文件并填写 MySQL 密码等配置：

   ```powershell
   Copy-Item .env.example .env
   ```

2. 安装依赖：

   ```powershell
   pip install -r requirements.txt
   ```

3. 首次初始化数据库时，先创建项目专用数据库 `pppet`：

   ```powershell
   python -m scripts.create_database
   ```

4. 然后执行 Alembic 迁移创建表结构：

   ```powershell
   alembic upgrade head
   ```

5. 启动开发服务：

   ```powershell
   uvicorn app.main:app --reload
   ```

6. 验证迁移状态：

   ```powershell
   alembic current
   ```

7. 插入默认开发数据：

   ```powershell
   python -m scripts.init_db
   ```

8. 如需完全重置数据库并恢复默认数据：

   ```powershell
   python -m scripts.reset_db
   ```

## 数据库隔离说明

- `.env.example` 中的数据库名固定为 `pppet`。
- `scripts/create_database.py` 只连接 MySQL 服务本身，不会连接或修改其他数据库。
- `DATABASE_URL` 与 `DATABASE_URL_SYNC` 必须指向 `pppet`，配置校验会阻止误连到同一实例中的其他数据库。
- 所有 Alembic 迁移和后续表结构都只会落在 `pppet` 数据库中。

## 本地开发提示

- CORS 已允许 `localhost:*` 和 `127.0.0.1:*`，便于本地 uni-app 开发服务器跨域调试。
- 当前各业务模块路由均为占位接口，访问 `/docs` 可直接看到已注册的模块入口。
- `scripts/init_db.py` 可重复执行，不会重复插入默认管理员、测试用户和测试宠物。
