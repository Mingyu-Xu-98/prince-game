# 君主论博弈游戏 (The Prince: A Game of Power)

基于马基雅维利《君主论》核心思想的权力博弈游戏。

## 游戏简介

作为新登基的君主，你将面对内忧外患。三位顾问将评判你的每一个决定：

- 🦁 **狮子** - 评估你的决策是否果断有力（战略重心审计）
- 🦊 **狐狸** - 检验你言行的一致性（语义一致性审计）
- ⚖️ **天平** - 衡量政策对各阶层的影响（社会熵增预警）

## 核心机制

**权力三维向量：**
- **A (掌控力)** - 你的话语权，低于30%时顾问不再服从
- **F (畏惧值)** - 臣民对你的恐惧，过高可能导致政变
- **L (爱戴值)** - 臣民对你的爱戴，过低将引发骚乱

**胜负条件：**
- 若 A + F + L < 100，统治崩溃，游戏结束

## 技术栈

- **后端**: Python + FastAPI
- **前端**: React + TypeScript + Vite
- **AI**: OpenRouter API (支持多种模型)

## 本地运行

### 1. 克隆项目
```bash
git clone https://github.com/YOUR_USERNAME/prince-game.git
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

### 3. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 4. 访问游戏
打开浏览器访问 http://127.0.0.1:5173

## 云端部署

推荐部署方案：
- **后端**: [Railway](https://railway.app) / [Render](https://render.com)
- **前端**: [Vercel](https://vercel.com) / [Netlify](https://netlify.com)

## 配置

需要 OpenRouter API Key，可从 https://openrouter.ai/keys 获取。

在游戏界面中输入 API Key 即可开始游戏。

## License

MIT
