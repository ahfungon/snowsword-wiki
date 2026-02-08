# 双模式部署指南

本项目支持两种访问方式：
1. 🌐 **Streamlit 前端** - 交互式网页 (streamlit.app)
2. 🔌 **REST API** - 可用 curl 测试 (Render/Railway)

---

## 📁 部署架构

```
GitHub Repo
    ├── main分支
    │     ├── app.py → Streamlit Cloud (前端)
    │     ├── api.py → Render/Railway (API)
    │     └── .github/workflows/ → 自动测试
    │
    └── 每次 push → GitHub Actions 自动 curl 测试
```

---

## 🚀 部署步骤

### 1. 前端 (Streamlit Cloud) - 已部署 ✅
- 地址: https://snowsword-wiki.streamlit.app/
- 自动从 GitHub 部署

### 2. API 后端 (选择以下任一)

#### 方案 A: Render (推荐 ⭐)
1. 访问 https://render.com
2. 用 GitHub 登录
3. 点击 "New +" → "Web Service"
4. 选择本仓库
5. 配置:
   - **Name**: snowsword-api
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
6. 添加 Environment Variable:
   - `DEEPSEEK_API_KEY` = `sk-cdebe0...`
7. 点击 "Create Web Service"
8. 等待部署完成，记录 URL (如 `https://snowsword-api.onrender.com`)

#### 方案 B: Railway
1. 访问 https://railway.app
2. 从 GitHub 导入项目
3. 添加变量 `DEEPSEEK_API_KEY`
4. 自动部署

#### 方案 C: Heroku
```bash
heroku create snowsword-api
heroku config:set DEEPSEEK_API_KEY=sk-cdebe0...
git push heroku main
```

---

## 🔧 GitHub Secrets 配置

在 GitHub 仓库设置中添加以下 Secrets：

| Secret Name | 值 | 说明 |
|------------|-----|------|
| `API_BASE_URL` | `https://snowsword-api.onrender.com` | 你的 API 地址 |
| `DEEPSEEK_API_KEY` | `sk-cdebe0...` | DeepSeek API 密钥 |
| `RENDER_API_KEY` | `rnd_...` | Render API 密钥 (可选) |
| `RENDER_SERVICE_ID` | `srv-...` | Render 服务 ID (可选) |

---

## 🧪 手动测试 curl 命令

```bash
# 1. 测试根路径
curl https://snowsword-api.onrender.com/

# 2. 健康检查
curl https://snowsword-api.onrender.com/health

# 3. 搜索接口
curl "https://snowsword-api.onrender.com/search?q=徐凤年&top_k=3"

# 4. 问答接口 (POST)
curl -X POST https://snowsword-api.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"query":"徐凤年为什么要杀韩貂寺","top_k":5}'
```

---

## 📊 GitHub Actions 自动测试

每次提交到 `main` 分支时：
1. 自动触发部署 (如果配置了 Render API 密钥)
2. 等待 30 秒让服务启动
3. 运行 curl 命令测试所有端点
4. 生成测试报告并上传

查看测试结果:
- GitHub → Actions → 选择最新运行 → Artifacts → api-test-report

---

## 📋 API 端点文档

| 方法 | 端点 | 说明 | curl 示例 |
|------|------|------|-----------|
| GET | `/` | 服务信息 | `curl <url>/` |
| GET | `/health` | 健康检查 | `curl <url>/health` |
| GET | `/search?q=xxx` | 文本检索 | `curl "<url>/search?q=徐凤年"` |
| POST | `/query` | 智能问答 | `curl -X POST <url>/query -H "..." -d '{"query":"..."}'` |
| GET | `/stats` | 统计信息 | `curl <url>/stats` |

### POST /query 请求体
```json
{
  "query": "徐凤年是谁？",
  "top_k": 5,
  "temperature": 0.7
}
```

---

## 🔄 前端连接 API (可选)

如果想让 Streamlit 前端调用这个 API：

修改 `app.py` 中的调用方式，从本地 expert_system 改为 API 调用：

```python
import requests

API_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

# 替换本地调用为 API 调用
response = requests.post(f"{API_URL}/query", json={
    "query": user_input,
    "top_k": top_k,
    "temperature": temperature
})
result = response.json()
```

---

## 📝 部署清单

- [ ] 部署 API 到 Render/Railway/Heroku
- [ ] 记录 API URL
- [ ] 在 GitHub Secrets 添加 `API_BASE_URL`
- [ ] 在 GitHub Secrets 添加 `DEEPSEEK_API_KEY`
- [ ] 推送代码触发自动测试
- [ ] 检查 Actions 测试报告

---

## 💡 免费额度参考

| 平台 | 免费额度 | 休眠策略 |
|------|---------|---------|
| Render | 750小时/月 | 15分钟无访问休眠 |
| Railway | $5/月 等值 | 有 |
| Heroku | 550小时/月 | 30分钟无访问休眠 |
| Streamlit Cloud | 无限 | 无 |

建议：**Streamlit Cloud (前端) + Render (API)**
