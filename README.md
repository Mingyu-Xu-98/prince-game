# 君主论博弈游戏 (The Prince: A Game of Power)

基于马基雅维利《君主论》核心思想的权力博弈游戏。

## 游戏简介

作为新登基的君主，你将面对内忧外患。三位顾问将评判你的每一个决定：

- 🦁 **狮子** - 代表武力与威慑，崇尚"宁可被人畏惧，也不要被人爱戴"
- 🦊 **狐狸** - 代表权谋与智慧，信奉"目的可以证明手段正当"
- ⚖️ **天平** - 代表公正与稳定，追求"明智的君主应当建立在人民的支持之上"

## 核心机制

### 权力三维向量
- **A (掌控力)** - 你的核心权威，低于30%时指令失效
- **F (畏惧值)** - 统治的威慑，过高引发暗杀
- **L (爱戴值)** - 民众的容忍，归零时暴乱爆发

### 观测透镜系统
游戏开始时选择你观察世界的方式：
- 🔍 **怀疑透镜** - 相信每个人都有阴谋，世界是一盘棋
- ⚔️ **扩张透镜** - 将生命视为数字，效率至上
- ⚖️ **平衡透镜** - 追求公正与和谐，每一个生命都有价值

### 关卡系统
五重试炼，攀登权力之巅：
1. **空饷危机** - 权力的入场券
2. **瘟疫与流言** - 情感与理智
3. **和亲还是战争** - 外部性博弈
4. **影子议会的背叛** - 内部博弈
5. **民众的审判** - 终极平衡

### 政令后果系统
每个政令都会产生连锁反应：
- AI 基于《君主论》原则分析决策后果
- 可选择继续处理影响或跳过进入下一关
- 跳过的影响会累积，可能在后续关卡中爆发

## 特性

- 🎭 **沉浸式叙事** - 基于《君主论》的深度权谋剧情
- 🤖 **AI 驱动** - 顾问对话和决策分析由 AI 实时生成
- 💾 **进度持久化** - 游戏进度自动保存，刷新页面不丢失
- 🎨 **优雅界面** - 浅色米色主题，古典与现代结合
- 📱 **响应式设计** - 支持桌面和移动端

## 技术栈

- **后端**: Python + FastAPI
- **前端**: React + TypeScript + Vite
- **AI**: OpenRouter API (支持 Claude、GPT-4 等多种模型)

## 本地运行

### 1. 克隆项目
```bash
git clone https://github.com/Mingyu-Xu-98/prince-game.git
cd prince-game
```

### 2. 启动后端
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
后端将运行在 http://127.0.0.1:8080

### 3. 启动前端
```bash
cd frontend
npm install
npm run dev
```
前端将运行在 http://127.0.0.1:5173

### 4. 访问游戏
打开浏览器访问 http://127.0.0.1:5173

## 云端部署

推荐部署方案：
- **后端**: [Railway](https://railway.app) / [Render](https://render.com)
- **前端**: [Vercel](https://vercel.com) / [Netlify](https://netlify.com)

## 配置

需要 OpenRouter API Key，可从 https://openrouter.ai/keys 获取。

在游戏界面的设置中输入 API Key 即可开始游戏。

支持的模型包括：
- Claude 3.5 Sonnet
- Claude Sonnet 4
- GPT-4 Turbo
- GPT-4o
- Gemini 2.0 Flash

## 项目结构

```
prince-game/
├── backend/
│   ├── engine/           # 游戏引擎
│   │   ├── chapter_engine.py    # 关卡引擎
│   │   ├── judgment_engine.py   # 裁决引擎
│   │   └── ...
│   ├── models/           # 数据模型
│   ├── main.py           # FastAPI 入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React 组件
│   │   ├── hooks/        # 自定义 Hooks
│   │   ├── api/          # API 客户端
│   │   └── types/        # TypeScript 类型
│   └── package.json
└── README.md
```

## License

MIT
