# 地图功能demo

## 项目介绍

本项目用于支持用户新增或编辑收货地址时打开地图选点、识别标准地址，并在补充门牌号后提交给后端校验和保存。

当前阶段只提供可启动、可联调的前后端基础环境及健康检查，不包含地图、地址解析、数据库、认证或业务接口。数据库方案暂不启用。

## 技术栈

- 前端：React、Vite、JavaScript、Fetch API
- 后端：Python、FastAPI、Uvicorn
- 开发环境：Windows、PowerShell

## 目录结构

```text
地图功能demo/
├─ frontend/
│  ├─ public/
│  ├─ src/
│  │  ├─ App.jsx
│  │  ├─ config.js
│  │  ├─ index.css
│  │  └─ main.jsx
│  ├─ .env.example
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.js
├─ backend/
│  ├─ app/
│  │  ├─ __init__.py
│  │  └─ main.py
│  ├─ .env.example
│  ├─ requirements.txt
│  └─ .venv/              # 本地虚拟环境，不提交 Git
├─ .gitignore
└─ README.md
```

## 环境要求

- Node.js 20.19+ 或 22.12+（当前 Vite 8 的要求；本机为 24.15.0）
- npm（本机为 11.12.1）
- Python 3.10+（本机为 3.14.5）
- Git（本机为 2.55.0.windows.2）

## 首次安装

在项目根目录打开 PowerShell：

```powershell
npm.cmd --prefix frontend install
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

项目已完成上述安装；克隆到新电脑后再执行即可。

## 环境变量配置

前端会自动读取 `frontend/.env.local`。从示例复制一份：

```powershell
Copy-Item frontend\.env.example frontend\.env.local
```

默认配置：

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

后端为保持依赖最少，当前直接读取 PowerShell 进程变量，不自动解析 `.env` 文件。默认只允许 `http://localhost:5173`：

```powershell
$env:FRONTEND_ORIGIN = "http://localhost:5173"
```

`.env.example` 只能放示例值。所有以 `VITE_` 开头的变量都会进入浏览器代码，因此绝不能存放密码、Token 或 API Key。

## 启动后端

在项目根目录运行，无需激活虚拟环境：

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host localhost --port 8000
```

健康检查地址为 `http://localhost:8000/health`，交互式 API 文档为 `http://localhost:8000/docs`。

## 启动前端

另开一个 PowerShell 窗口，在项目根目录运行：

```powershell
npm.cmd --prefix frontend run dev
```

浏览器访问 `http://localhost:5173`。生产构建命令为：

```powershell
npm.cmd --prefix frontend run build
```

构建产物位于 `frontend/dist/`。

## 前后端联调

1. 先启动后端，确认访问 `http://localhost:8000/health` 返回 `status: ok`。
2. 再启动前端并访问 `http://localhost:5173`。
3. 首页先显示“正在检查后端连接…”，成功后显示“后端运行正常”。
4. 若端口或主机名变更，同时更新前端 `VITE_API_BASE_URL` 与后端 `FRONTEND_ORIGIN`，然后重启对应服务。

## 初学者概念说明

- **Node.js** 是在浏览器之外运行 JavaScript 工具的运行时；本项目用它执行 Vite。
- **npm** 是 Node.js 的包管理器，负责根据 `package.json` 下载依赖并运行 `dev`、`build` 等脚本。
- **Vite** 是前端开发与构建工具，提供快速开发服务器、模块热更新和生产打包。
- **React 开发服务器与构建产物**：`npm.cmd run dev` 启动只供开发使用的实时服务器；`npm.cmd run build` 生成经过优化的静态文件到 `dist/`，这些文件才用于部署，构建命令本身不会长期启动网站。
- **Python 虚拟环境** 把本项目的 Python 包隔离在 `backend/.venv`，避免与全局 Python 或其他项目发生版本冲突。
- **FastAPI 与 Uvicorn**：FastAPI 定义接口、校验和响应；Uvicorn 是实际监听端口并把 HTTP 请求交给 FastAPI 的应用服务器。
- **不同端口**：开发时 Vite 和 Uvicorn 是两个独立进程，一个端口不能同时被两个服务占用，因此分别使用 5173 和 8000。
- **CORS**：浏览器把协议、主机和端口的组合视为“来源”。5173 请求 8000 属于跨来源请求，浏览器要求后端明确允许该前端来源，否则会拦截响应。

## 常见问题

### npm.ps1 被 PowerShell 拦截

不要修改系统执行策略，直接使用 `npm.cmd`：

```powershell
npm.cmd --prefix frontend run dev
```

### Python 虚拟环境无法激活

无需激活，直接调用虚拟环境解释器：

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

### 端口被占用

查找占用端口的进程：

```powershell
Get-NetTCPConnection -LocalPort 5173,8000 -ErrorAction SilentlyContinue | Select-Object LocalPort,OwningProcess
```

确认进程属于你并且可以关闭后，再用任务管理器结束它；也可以换端口，并同步更新环境变量和 CORS 来源。

### CORS 错误

确认浏览器实际打开的是 `http://localhost:5173`，且后端 `FRONTEND_ORIGIN` 完全一致。`localhost` 与 `127.0.0.1` 是不同来源，端口不同也是不同来源。修改后需重启后端。

### 前端无法连接后端

依次确认：后端终端没有报错、`/health` 能直接访问、`frontend/.env.local` 地址正确、修改环境变量后已重启 Vite，并检查浏览器开发者工具的 Network 与 Console 面板。
