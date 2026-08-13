# 地图功能 Demo

## 项目介绍

本项目用于支持用户新增或编辑收货地址时打开地图选点、识别规范地址，并在补充门牌号后提交给后端校验和保存。

当前后端已经实现收货地址新增、查询、部分更新、软删除、高德地址校验、MongoDB 持久化、默认地址维护、并发版本冲突检测和统一异常响应。认证系统尚未接入，目前所有地址接口使用固定测试用户 ID。

## 技术栈

- 前端：React 19、Vite 8、JavaScript、Fetch API
- 后端：Python 3.10+、uv、FastAPI、Uvicorn、Pydantic
- 数据库：MongoDB、PyMongo 异步 API
- 外部服务：高德地图 Web 服务 API
- 开发环境：Windows、PowerShell

## 目录结构

```text
地图功能demo/
├─ frontend/
│  ├─ src/
│  │  ├─ App.jsx
│  │  ├─ config.js
│  │  ├─ index.css
│  │  └─ main.jsx
│  ├─ .env.example
│  ├─ package.json
│  └─ vite.config.js
├─ backend/
│  ├─ app/
│  │  ├─ amap/                 # 高德客户端、模型与异常
│  │  ├─ core/                 # 配置、依赖、日志及生命周期
│  │  ├─ repository/           # MongoDB 数据访问层
│  │  ├─ routers/              # FastAPI 路由
│  │  ├─ schema/               # Pydantic 请求与响应模型
│  │  ├─ service/              # 地址业务逻辑与真实性校验
│  │  └─ main.py               # 后端入口
│  ├─ tests/                   # 后端单元测试
│  ├─ .env.example
│  ├─ pyproject.toml            # 后端项目与直接依赖声明
│  └─ uv.lock                   # uv 生成的完整依赖锁文件
├─ .gitignore
└─ README.md
```

## 环境要求

- Node.js 20.19+ 或 22.12+
- npm
- Python 3.10+
- uv
- MongoDB
- 可调用高德 Web 服务 API 的 Key

如果需要使用“创建默认地址”或“设为默认地址”，MongoDB 必须支持事务，开发环境通常应配置为副本集，而不是普通 standalone 实例。

## 首次安装

在项目根目录打开 PowerShell：

```powershell
npm.cmd --prefix frontend install
uv sync --project backend --locked
```

`uv sync` 会根据 `backend/pyproject.toml` 和 `backend/uv.lock` 自动创建或更新
`backend/.venv`，不需要手动执行 `pip install` 或激活虚拟环境。

后端依赖统一通过 uv 管理：

```powershell
# 添加运行时依赖
uv add --project backend package-name

# 添加开发依赖
uv add --project backend --dev package-name

# 删除依赖
uv remove --project backend package-name

# 按锁文件同步环境
uv sync --project backend --locked
```

提交依赖变更时，应同时提交 `backend/pyproject.toml` 和 `backend/uv.lock`。

## 环境变量配置

### 前端

复制示例配置：

```powershell
Copy-Item frontend\.env.example frontend\.env.local
```

默认值：

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

所有以 `VITE_` 开头的变量都会进入浏览器代码，不得存放密码、Token 或 API Key。

### 后端

复制示例配置：

```powershell
Copy-Item backend\.env.example backend\.env
```

配置项：

```dotenv
FRONTEND_ORIGIN=http://localhost:5173

AMAP_API_KEY=replace-with-your-amap-api-key
AMAP_POI_DETAIL_URL=https://restapi.amap.com/v5/place/detail
AMAP_REVERSE_GEOCODE_URL=https://restapi.amap.com/v3/geocode/regeo

MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=map_feature_demo
MONGODB_SERVER_SELECTION_TIMEOUT_MS=5000
```

说明：

- `AMAP_API_KEY`、两个高德接口地址和 `MONGODB_DATABASE` 为必填项。
- 系统环境变量优先于 `backend/.env`。
- `FRONTEND_ORIGIN` 支持用英文逗号分隔多个明确来源，不允许使用 `*`。
- 应用启动时会立即连接并 ping MongoDB；连接失败时后端不会完成启动。
- `.env.example` 只能保存示例值，不得写入真实密钥。

## 启动项目

### 启动后端

先启动 MongoDB，再在项目根目录运行：

```powershell
uv run --project backend uvicorn app.main:app --app-dir backend --reload --host localhost --port 8000
```

常用地址：

- 健康检查：`http://localhost:8000/health`
- Swagger API 文档：`http://localhost:8000/docs`
- OpenAPI JSON：`http://localhost:8000/openapi.json`

健康检查响应：

```json
{
  "status": "ok",
  "message": "backend is running"
}
```

### 启动前端

另开一个 PowerShell 窗口，在项目根目录运行：

```powershell
npm.cmd --prefix frontend run dev
```

浏览器访问 `http://localhost:5173`。

生产构建：

```powershell
npm.cmd --prefix frontend run build
```

构建产物位于 `frontend/dist/`。

## 前后端联调

1. 启动 MongoDB。
2. 启动后端，确认 `/health` 返回 `status: ok`。
3. 启动前端并访问 `http://localhost:5173`。
4. 若端口或主机名发生变化，同时修改前端 `VITE_API_BASE_URL` 和后端 `FRONTEND_ORIGIN`。
5. 修改环境变量后重启对应服务。

## 后端架构

一次地址请求的主要调用流程如下：

```text
HTTP 请求
  → routers/address_routers.py
  → core/depedencies.py
  → service/address_service.py
  ├─ service/address_validation.py
  │    → amap/client.py → 高德 Web 服务
  └─ repository/address_repository.py → MongoDB
```

- Router 负责 HTTP 参数和响应模型。
- Service 负责地址校验、状态判断、事务和异常转换。
- Repository 负责 MongoDB 查询及原子更新。
- AmapClient 负责高德请求、响应解析和上游异常分类。
- 全局异常处理器负责输出稳定且不泄漏内部信息的错误响应。

## 地址 API

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/addresses/get?address_id={uuid}` | 查询一条有效地址 |
| GET | `/addresses/status?address_id={uuid}` | 查询地址状态 |
| POST | `/addresses/add` | 新增地址 |
| PATCH | `/addresses/update` | 部分更新地址 |
| DELETE | `/addresses/{address_id}` | 软删除地址 |

当前还没有地址列表、分页或搜索接口。

### 新增地址

```http
POST /addresses/add
Content-Type: application/json
```

POI 选点请求示例：

```json
{
  "receiver_name": "张三",
  "phone_number": "13800138000",
  "display_address": "科技园",
  "detail_address": "某某大厦 10 楼 1001 室",
  "location": {
    "source": "poi",
    "coordinate": "113.934528,22.540503",
    "adcode": "440305",
    "amap_poi_id": "B0XXXXXX"
  },
  "is_default": false
}
```

成功响应：

```json
{
  "code": 200,
  "message": "地址添加成功",
  "data": {
    "address_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

地图拖拽选点时，`source` 使用 `position`，POI ID 可以省略：

```json
{
  "source": "position",
  "coordinate": "113.934528,22.540503",
  "adcode": "440305"
}
```

也可以携带附近 POI：

```json
{
  "source": "position",
  "coordinate": "113.934528,22.540503",
  "adcode": "440305",
  "amap_poi_id": "B0XXXXXX"
}
```

### 部分更新

```http
PATCH /addresses/update
Content-Type: application/json
```

```json
{
  "address_id": "550e8400-e29b-41d4-a716-446655440000",
  "detail_address": "某某大厦 12 楼 1201 室",
  "is_default": true
}
```

至少要提供一个可更新字段。允许更新：

- `receiver_name`
- `phone_number`
- `display_address`
- `detail_address`
- `location`
- `is_default`

如果更新 `location`，后端会重新调用高德服务，并更新规范地址和行政区划编码。更新响应只包含地址 ID 和本次提交的字段，不是完整的最新地址记录。

### 查询地址

```http
GET /addresses/get?address_id=550e8400-e29b-41d4-a716-446655440000
```

该接口只查询 `status=active` 的地址。已删除地址会按地址不存在处理。

### 查询状态

```http
GET /addresses/status?address_id=550e8400-e29b-41d4-a716-446655440000
```

响应为 JSON 字符串，可能值是 `"active"` 或 `"deleted"`：

```json
"active"
```

### 删除地址

```http
DELETE /addresses/550e8400-e29b-41d4-a716-446655440000
```

删除采用软删除：

- 将 `status` 改为 `deleted`。
- `version` 加一。
- 写入 `deleted_at` 和 `updated_at`。
- 重复删除同一地址仍返回成功。
- 删除默认地址后不会自动选择新的默认地址。

## 地址校验规则

基础字段规则：

- 手机号必须符合中国大陆 11 位手机号格式：`1[3-9]xxxxxxxxx`。
- `adcode` 必须是 6 位数字。
- 坐标格式为 `longitude,latitude`，经纬度最多保留 6 位小数。
- 经度范围是 `-180～180`，纬度范围是 `-90～90`。
- POI 选点必须提供长度为 1～64 的 `amap_poi_id`。
- 请求出现未知字段时返回 422。
- `canonical_address`、最终 `adcode` 等服务端字段不能由客户端直接指定。

高德真实性校验：

- POI 的行政区划编码必须与客户端提交值一致。
- POI 返回坐标与提交坐标的距离不得超过 200 米。
- 地图拖拽位置通过逆地理编码校验行政区划。
- 拖拽位置携带 POI 时，两者距离不得超过 500 米。
- `canonical_address` 始终以后端调用高德得到的结果为准。

## MongoDB 数据设计

集合名称为 `addresses`，主要字段如下：

```text
address_id
user_id
receiver_name
phone_number
display_address
detail_address
location
canonical_address
adcode
is_default
status
version
deleted_at
created_at
updated_at
```

应用启动时自动创建：

- `address_id` 唯一索引。
- 针对 active 默认地址的 `user_id` 部分唯一索引。

同一用户最多只能有一个有效默认地址，但允许没有默认地址。创建或切换默认地址时，会在 MongoDB 事务中取消旧默认地址并写入新默认地址。

更新和删除使用 `version` 与 `is_default` 作为原子更新条件。如果读取状态后记录被并发修改，接口会返回 `409 address_version_conflict`。

## 异常响应

业务异常统一返回：

```json
{
  "code": "error_code",
  "detail": "面向用户的安全消息"
}
```

主要错误：

| HTTP | code | 含义 |
|---:|---|---|
| 404 | `address_not_found` | 地址不存在 |
| 409 | `address_state_conflict` | 地址已删除或状态冲突 |
| 409 | `address_version_conflict` | 地址被并发修改 |
| 422 | `address_validation_failed` | 地址数据或高德校验不一致 |
| 422 | `address_provider_location_not_found` | 高德未找到地址 |
| 500 | `address_create_failed` | 创建地址失败 |
| 500 | `address_update_failed` | 更新地址失败 |
| 500 | `address_delete_failed` | 删除地址失败 |
| 500 | `address_data_integrity_error` | MongoDB 数据结构异常 |
| 500 | `address_provider_configuration_error` | 高德 Key 或权限配置错误 |
| 502 | `address_provider_bad_response` | 高德响应异常 |
| 503 | `address_provider_unavailable` | 高德限流、配额或服务不可用 |
| 504 | `address_provider_timeout` | 高德请求超时 |

高德 HTTP 请求的超时时间为 5 秒。日志中的高德 `key` 和 `sig` 查询参数会替换为 `<redacted>`，500 级错误不会把内部异常消息直接返回给客户端。

## 认证与当前限制

- 目前没有真实认证和授权。
- 所有地址接口使用固定用户 ID：`7c2c3dc3-2577-4d85-b6a8-03f3d8c21d83`。
- 没有地址列表、分页、搜索和恢复已删除地址的接口。
- 删除默认地址不会自动指定替代地址。
- 更新响应不包含新的 `version` 或完整数据库快照。
- 地址写入依赖高德服务，健康检查本身不检查高德服务状态。

## 运行测试

在项目根目录执行：

```powershell
Set-Location backend
uv run --locked python -m unittest discover -s tests -v
```

当前测试覆盖地址模型、Router、Service、Repository、高德异常转换、CORS、MongoDB 生命周期、软删除、默认地址和并发冲突等行为。

最近一次验证结果：

```text
Ran 85 tests
OK
```

测试运行时可能出现 FastAPI/Starlette `TestClient` 关于 HTTPX 的弃用警告，目前不影响测试结果。

## 常见问题

### 后端启动失败

依次检查：

- `backend/.env` 是否存在且包含所有必填项。
- MongoDB 是否正在运行。
- `MONGODB_URI` 和数据库名是否正确。
- 高德 Key 是否为 Web 服务类型且具有所需接口权限。

### 默认地址操作报 MongoDB 事务错误

默认地址的创建和切换使用事务。请确认 MongoDB 运行在支持事务的副本集或分片集群模式。

### CORS 错误

确认浏览器实际来源与 `FRONTEND_ORIGIN` 完全一致。`localhost` 与 `127.0.0.1` 属于不同来源，端口不同也属于不同来源。修改后需要重启后端。

### PowerShell 拦截 npm.ps1

无需修改系统执行策略，直接使用：

```powershell
npm.cmd --prefix frontend run dev
```

### Python 虚拟环境无法激活

uv 不要求激活虚拟环境，直接通过 `uv run` 启动：

```powershell
uv run --project backend uvicorn app.main:app --app-dir backend --reload --port 8000
```

### 端口被占用

```powershell
Get-NetTCPConnection -LocalPort 5173,8000 -ErrorAction SilentlyContinue | Select-Object LocalPort,OwningProcess
```

确认进程可以关闭后再结束它，或者修改端口并同步更新前端 API 地址和后端 CORS 来源。
