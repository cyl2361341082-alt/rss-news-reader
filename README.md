# rss-news-reader

`rss-news-reader` 是一个本地优先的 RSS 新闻采集与阅读系统。它把多个新闻 RSS 源拉取到本地，抓取文章正文，结构化存入 SQLite，并通过 FastAPI 提供 JSON API，再由 Next.js 14 前端渲染成一个适合长文阅读的极简网站。

项目包含两个部分：

- `backend/`：Python 3.11+ 采集管线、正文抽取、SQLite、CLI、FastAPI
- `frontend/`：Next.js 14 + TypeScript + Tailwind CSS 本地阅读站点

## 架构说明

后端职责：

- 从 `config/sources.yaml` 读取 RSS 源配置
- 使用 `feedparser` 抓取 feed 并写入 `feed_entries`
- 访问文章页，优先使用 `readability-lxml`，后备使用 `trafilatura` 和 CSS selector 抽取正文
- 通过 `SQLModel` 存储到 `data/news.db`
- 通过 `FastAPI` 暴露稳定 JSON API

前端职责：

- 从后端 API 拉取真实文章数据
- 渲染首页、搜索页、来源页、详情页
- 提供 light/dark mode、字号切换、相关文章、舒适阅读排版

## 目录结构

```text
rss-news-reader/
  README.md
  .gitignore
  .env.example
  backend/
  frontend/
```

## 后端启动方式

1. 进入后端目录：

```bash
cd backend
```

2. 安装依赖：

```bash
uv sync
```

3. 初始化数据库并写入 source：

```bash
uv run news init
```

4. 运行完整抓取流程：

```bash
uv run news run
```

5. 启动 API：

```bash
uv run news serve-api
```

默认 API 地址为 [http://localhost:8000/api](http://localhost:8000/api)。

### 一键启动

在项目根目录运行：

```bash
./start.ps1
```

Windows 也可以直接双击 `start.cmd`。

脚本会：

- 检查 `uv` 和 `npm`
- 安装后端与前端依赖
- 初始化数据库
- 默认先执行一次 `uv run news run`
- 分别启动 FastAPI 和 Next.js 开发服务器

常用参数：

```bash
./start.ps1 -SkipInstall
./start.ps1 -SkipFetch
./start.ps1 -ApiPort 8010 -FrontendPort 3010
```

## 前端启动方式

1. 进入前端目录：

```bash
cd frontend
```

2. 安装依赖：

```bash
npm install
```

3. 启动开发服务器：

```bash
npm run dev
```

默认前端地址为 [http://localhost:3000](http://localhost:3000)。

默认请求的 API 为 `http://localhost:8000/api`，也可以通过 `.env.local` 覆盖：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

## 部署到 Ubuntu 服务器

项目已经附带一套 Ubuntu 单机部署模板，位于 `deploy/ubuntu/`，包含：

- `backend.env.example`
- `frontend.env.example`
- `rss-news-reader-api.service`
- `rss-news-reader-web.service`
- `rss-news-reader-ingest.service`
- `rss-news-reader-ingest.timer`
- `rss-news-reader.nginx.conf`

推荐生产部署栈：

- Ubuntu 22.04 或更新版本
- Python 3.11+
- `uv`
- Node.js 20+
- `nginx`
- `systemd`

### 不要直接发送服务器密码

如果需要我继续协助部署，不要把服务器密码直接写到聊天里，也不要提交到仓库。

更安全的做法是：

- 使用 SSH key 登录服务器
- 或由你在终端里手动输入密码
- 或创建一个临时部署用户，而不是直接使用 root 长期密码

我可以继续帮你整理命令、检查配置、生成部署文件，但凭证应尽量只在你自己的终端会话中输入。

### 推荐部署目录

建议把仓库部署到：

```bash
/opt/rss-news-reader
```

### 服务器初始化

先在 Ubuntu 服务器安装基础依赖：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx curl git
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 拉取项目并安装依赖

```bash
cd /opt
sudo git clone <your-repo-url> rss-news-reader
sudo chown -R $USER:$USER /opt/rss-news-reader

cd /opt/rss-news-reader/backend
uv sync

cd /opt/rss-news-reader/frontend
npm ci
npm run build
```

### 配置生产环境变量

复制模板并按需修改：

```bash
cd /opt/rss-news-reader
cp deploy/ubuntu/backend.env.example deploy/ubuntu/backend.env
cp deploy/ubuntu/frontend.env.example deploy/ubuntu/frontend.env
```

常见需要修改的值：

- `deploy/ubuntu/backend.env`：
  - `RSS_NEWS_READER_ENV=production`
  - `RSS_NEWS_READER_API_HOST=127.0.0.1`
  - `RSS_NEWS_READER_API_PORT=8000`
- `deploy/ubuntu/frontend.env`：
  - `NEXT_PUBLIC_API_BASE_URL=https://your-domain.com/api`

如果你暂时没有域名，也可以先写成：

```bash
NEXT_PUBLIC_API_BASE_URL=http://<server-ip>/api
```

### 初始化数据库并首次抓取

```bash
cd /opt/rss-news-reader/backend
uv run news init
uv run news run
```

### 配置 systemd

把 `deploy/ubuntu/` 里的 service 和 timer 模板复制到系统目录前，先把文件里的 `<DEPLOY_USER>` 替换成你的部署用户名。

然后执行：

```bash
sudo cp deploy/ubuntu/rss-news-reader-api.service /etc/systemd/system/
sudo cp deploy/ubuntu/rss-news-reader-web.service /etc/systemd/system/
sudo cp deploy/ubuntu/rss-news-reader-ingest.service /etc/systemd/system/
sudo cp deploy/ubuntu/rss-news-reader-ingest.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now rss-news-reader-api.service
sudo systemctl enable --now rss-news-reader-web.service
sudo systemctl enable --now rss-news-reader-ingest.timer
```

常用检查命令：

```bash
sudo systemctl status rss-news-reader-api.service
sudo systemctl status rss-news-reader-web.service
sudo systemctl status rss-news-reader-ingest.timer
journalctl -u rss-news-reader-api.service -n 100 --no-pager
journalctl -u rss-news-reader-web.service -n 100 --no-pager
```

### 配置 Nginx

先修改 `deploy/ubuntu/rss-news-reader.nginx.conf` 中的域名，然后安装到 Nginx：

```bash
sudo cp deploy/ubuntu/rss-news-reader.nginx.conf /etc/nginx/sites-available/rss-news-reader
sudo ln -s /etc/nginx/sites-available/rss-news-reader /etc/nginx/sites-enabled/rss-news-reader
sudo nginx -t
sudo systemctl reload nginx
```

如果你使用域名，建议再配合 Certbot 开启 HTTPS。没有 HTTPS 时，也可以先用服务器 IP 访问。

### 部署后的访问路径

- 前端首页：`http://<server-ip>/` 或 `https://your-domain.com/`
- API 健康检查：`http://<server-ip>/api/health` 或 `https://your-domain.com/api/health`

### 后续更新

更新代码后的常见流程：

```bash
cd /opt/rss-news-reader
git pull

cd backend
uv sync

cd ../frontend
npm ci
npm run build

sudo systemctl restart rss-news-reader-api.service
sudo systemctl restart rss-news-reader-web.service
```

如果你修改了抓取逻辑，也可以手动补跑一次：

```bash
cd /opt/rss-news-reader/backend
uv run news run
```

## 配置说明

后端配置文件：

- `backend/config/settings.yaml`：运行参数、数据库、网络、导出、分页等
- `backend/config/sources.yaml`：RSS source 列表与抽取策略

环境变量支持：

- `RSS_NEWS_READER_ENV`
- `RSS_NEWS_READER_DATABASE_URL`
- `RSS_NEWS_READER_API_HOST`
- `RSS_NEWS_READER_API_PORT`

默认包含这些示例源：

- BBC Business
- BBC Technology
- Bloomberg Technology
- WSJ World News
- WSJ Markets
- Sample Local Feed（便于离线测试）

## CLI 使用示例

```bash
uv run news init
uv run news fetch-feeds
uv run news fetch-articles
uv run news run
uv run news export --format json
uv run news stats
uv run news retry-failures
uv run news test-source sample-local
uv run news serve-api --reload
```

## 新闻数据管理

这套项目当前采用本地 SQLite 管理新闻数据，核心数据库文件为 `backend/data/news.db`。推荐把新闻数据拆成 3 层来理解和维护：

- `sources`：新闻源配置层，负责定义抓哪些 RSS 源、是否启用、站点地址和抽取策略
- `feed_entries`：采集队列层，保存 RSS 抓回来的候选新闻和抓取状态
- `articles`：成品内容层，保存已经抽取完正文、可供前端展示和搜索的文章

日常管理时，可以按下面的职责划分：

- 管来源：编辑 `backend/config/sources.yaml`
- 管采集状态：查看 `feed_entries` 中的 `fetch_status`、`error_reason`
- 管正文成品：查看 `articles` 表中的标题、正文、摘要、分类、阅读时长等字段
- 管失败记录：查看 `backend/data/failed_requests.jsonl`
- 管导出归档：使用 `uv run news export`

### 推荐的数据管理流程

1. 初始化数据库与来源目录：

```bash
uv run news init
```

2. 抓取 RSS 条目，先把候选新闻写入 `feed_entries`：

```bash
uv run news fetch-feeds
```

3. 再抓文章正文，把成功抽取的内容写入 `articles`：

```bash
uv run news fetch-articles
```

4. 或直接运行整条流水线：

```bash
uv run news run
```

推荐把 `feed_entries` 视为“待处理和失败追踪层”，把 `articles` 视为“可读和可检索的正式内容层”。

### 常用管理命令

- 查看总体数据状态：

```bash
uv run news stats
```

- 导出文章做备份或二次处理：

```bash
uv run news export --format json
uv run news export --format md
```

- 重试失败的文章请求：

```bash
uv run news retry-failures
```

- 修复正文过短的文章：

```bash
uv run news repair-short-articles
```

- 检查单个源是否正常：

```bash
uv run news test-source <source_id>
```

### 推荐关注的管理指标

建议定期关注这些指标，避免数据越积越乱：

- `sources` 总数与启用数是否符合预期
- `feed_entries` 总量是否持续增长且长期不清理
- `feed_entries.fetch_status='failed'` 的失败数量是否偏高
- `articles` 总量与成功抽取数量是否匹配
- 是否存在正文过短、摘要为空、分类缺失的文章

如果失败数量持续偏高，优先检查：

- 源站是否仍然提供有效 RSS
- 文章页面是否能正常访问
- `sources.yaml` 中的抽取策略和 CSS selector 是否需要调整
- `backend/data/failed_requests.jsonl` 中是否出现集中错误模式

### 推荐的维护策略

为了让数据库长期可维护，建议采用下面的策略：

- 来源配置统一放在 `backend/config/sources.yaml`，不要把来源信息散落到代码里
- 候选条目和成品文章分层管理，不要把失败数据直接混进正式文章数据
- 定期导出 `articles.json` 或 `articles.md` 到 `backend/data/exports`
- 定期备份 `backend/data/news.db`
- 后续如果数据量继续增长，可以增加 SQLite FTS5 全文索引
- 后续如果候选条目积压过多，可以增加清理策略，只保留最近一段时间的 `feed_entries`

一句话说，这个项目推荐的管理方式是：

- `sources.yaml` 管来源
- `feed_entries` 管采集队列和失败状态
- `articles` 管最终可读内容
- `failed_requests.jsonl` 管异常追踪
- `export` 管导出与归档

## API 接口说明

基础接口：

- `GET /api/health`
- `GET /api/sources`
- `GET /api/articles`
- `GET /api/articles/{slug}`
- `GET /api/stats`
- `GET /api/search?q=...`

`GET /api/articles` 支持参数：

- `page`
- `page_size`
- `source`
- `category`
- `q`
- `sort`

示例：

```bash
curl "http://localhost:8000/api/articles?page=1&page_size=10&source=bbc-technology"
curl "http://localhost:8000/api/search?q=market"
```

## 阅读网站功能说明

- 首页：最近文章、来源筛选、分类筛选、分页
- 文章页：长文阅读布局、主题切换、字号切换、相关文章
- 搜索页：标题与正文关键词检索
- 来源页：查看所有 source 与对应文章

界面风格是“受 Claude 启发的阅读界面”，强调温和中性色、大量留白、克制控件和长文阅读体验，但没有复刻任何品牌专有视觉细节。

## 常见故障排查

1. `uv run news run` 没有抓到文章

- 先执行 `uv run news init`
- 检查 `config/sources.yaml` 中对应 source 是否 `enabled: true`
- 使用 `uv run news test-source <source_id>` 查看单个源诊断结果
- 离线环境下先启用 `sample-local`

2. API 无数据

- 确认 `backend/data/news.db` 已生成
- 确认已运行 `uv run news fetch-feeds` 和 `uv run news fetch-articles`
- 查看 `backend/data/failed_requests.jsonl`

3. 前端接口报错

- 确认 FastAPI 正运行于 `http://localhost:8000`
- 检查 `frontend/.env.local` 中的 `NEXT_PUBLIC_API_BASE_URL`

4. 提取正文失败

- 检查文章 HTML 是否可访问
- 查看数据库中的 `feed_entries.error_reason`
- 根据站点补充 `sources.yaml` 的 CSS selector

## 后续扩展建议

- 增加文章收藏与稍后读的前端交互
- 增加全文索引或 SQLite FTS5
- 增加站点级 selector 模板库
- 增加每日定时抓取
- 增加 OPML 导入与多语言分词搜索
- 增加正文清洗规则与摘要生成
