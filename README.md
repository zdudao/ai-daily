<h1 align="center">老许聊实体 · AI×实体洞察日报</h1>

<p align="center"><i>每天 13:00 自动生成，帮实体经营者看懂 AI、抓住先机</i></p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/uv-managed-DE5FE9?style=flat-square&logo=uv&logoColor=white" alt="uv managed" />
  <img src="https://img.shields.io/badge/DeepSeek-LLM-4F6DFF?style=flat-square" alt="DeepSeek" />
  <img src="https://img.shields.io/badge/GitHub%20Actions-每日自动更新-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="GitHub Actions" />
  <img src="https://img.shields.io/badge/GitHub%20Pages-在线日报-2088FF?style=flat-square&logo=githubpages&logoColor=white" alt="GitHub Pages" />
</p>

<p align="center">📅 <a href="https://zdudao.github.io/aikaifeng/"><b>每日在线日报 → https://zdudao.github.io/aikaifeng/</b></a></p>

---

## 这是什么？

一个 **AI 资讯 × 实体商业** 的每日研判系统。每天自动抓取全球 AI 新闻，用 **「实体商业观察者」视角** 打分研判，输出一份专给**餐饮、民宿、零售、文旅等实体老板**看的行动指南。

> 不堆 AI 术语，只说**这新闻对开封的实体老板意味着什么、该不该动手、怎么动手**。

### 每天 13:00 自动完成

```
抓取 400+ AI 资讯源 → LLM 实体关联度评分 → 精选 ≥60 分新闻
→ 逐条生成「顾问行动卡片」 → 渲染 HTML 日报 → 发布到 GitHub Pages
```

全自动运行（GitHub Actions 定时任务），无需人工干预，历史日报自动归档可查。

---

## 核心特色

### 1. 顾问行动卡片（每条精选新闻都有）

LLM 从"实体老板"视角强制输出四个商业结论：

| 模块 | 回答的问题 |
|------|-----------|
| 🕵️ 动机分析 | 发布这条新闻的平台/公司，到底想赚你什么钱？ |
| 📊 影响行业排序 | 对餐饮/零售/文旅/民宿哪个行业影响最大、排到第几？ |
| 🔧 落地可行性研判 | 成本门槛、消费习惯匹配度、基础设施依赖、政策风险，四维判断 |
| ⚔️ 生态位冲击 | 会干掉谁、催生什么新生意、最大阻力是什么 |

结尾固定输出：
- 🎯 **一句话核心判断** —— 这条新闻一句话说透
- 🗣️ **对老板的一句话决策建议** —— 开封话 + 明确行动指令
- 📝 **顾问备忘录** —— ≤30 字内部记录

### 2. 行动分级（一眼看懂该不该动）

每条新闻按四个等级归级，侧栏一键过滤：

| 分级 | 含义 |
|------|------|
| 🔥 立即行动 | 成熟、低门槛、强相关，现在就能用起来 |
| ✅ 小成本试用 | 可低成本试错，验证是否适合自己 |
| 👀 观望 | 有前景但不成熟 / 门槛高 / 本地不适配，先跟踪 |
| ⛔ 暂不跟进 | 与本地实体无关 / 概念太远 / 成本过高 |

### 3. 国产替代提示

每条海外 AI 新闻自动标注国内免费/可用的替代品（豆包、可灵、即梦、Kimi、Coze……），避免被"国外工具焦虑"带节奏。

### 4. 页面导航

- 左侧 **行动分级** 导航：点击只看某一分级的新闻
- 左侧 **能力分类** 导航：按 AI 能力类型（视频生成/智能体/大模型…）浏览
- 左侧 **历史日报** 导航：按月归档所有历史日报，一键回首页

---

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│  GitHub Actions（每天北京时间 13:00 自动触发）          │
│                                                     │
│  fetch → 400+ RSS 源并发抓取（24h 窗口）              │
│  score → DeepSeek 实体商业视角评分（<60 分淘汰）       │
│  deduce → 高分新闻生成顾问行动卡片                     │
│  render → HTML 日报（深色科技风）                     │
│  build_index → 更新首页 + 历史日报导航                │
│  commit & push → 触发 GitHub Pages 自动部署           │
└─────────────────────────────────────────────────────┘
```

- **语言/运行时**：Python 3.12+，[uv](https://docs.astral.sh/uv/) 管理依赖
- **LLM**：DeepSeek（OpenAI 兼容接口，结构化 JSON 输出 + 容错解析）
- **并发**：asyncio 异步抓取，LLM 调用限流（Semaphore=3）
- **部署**：GitHub Actions 定时任务 + GitHub Pages 静态托管
- **首页生成**：`scripts/build_index.py`（最新日报为首页 + 历史导航注入）

---

## 本地运行（可选）

```bash
uv sync                                   # 安装依赖
cp config.json.example config.json        # 创建配置（已 gitignore）
# .env 中配置 DEEPSEEK_API_KEY

uv run python -m src.main fetch           # 抓取 + 评分
uv run python -m src.main daily --no-deduce   # 生成 HTML 日报
uv run python scripts/build_index.py      # 更新首页 + 历史导航
```

### 目录结构

```
prompts/
  score.txt           # 实体商业视角评分 prompt
  deduce.md           # 顾问行动卡片 prompt
src/
  html_render.py      # 日报 HTML 渲染（深色科技风 + 导航）
  llm.py              # LLM 调用 + JSON 容错解析
  main.py             # 命令入口（fetch / daily / check）
scripts/
  build_index.py      # 首页生成 + 历史日报/行动分级导航注入
  retry_deduce.py     # 推演失败重试
news-data/            # 抓取数据与日报 HTML（gitignore，日报强提交）
.github/workflows/
  daily.yml           # 每日 13:00 自动运行
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.
