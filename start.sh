#!/bin/bash

# 《君主论》博弈游戏 - 启动脚本

echo "🎮 《君主论》博弈游戏启动中..."
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python"
    exit 1
fi

# 检查 Node.js
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm，请先安装 Node.js"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 安装后端依赖
echo "📦 检查后端依赖..."
cd backend
if [ ! -d "venv" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "  创建 .env 配置文件..."
    cp .env.example .env
    echo "  ⚠️  请编辑 backend/.env 文件配置 OpenRouter API Key"
fi

# 安装前端依赖
echo "📦 检查前端依赖..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "  安装 npm 依赖..."
    npm install --silent
fi

cd ..

echo ""
echo "✅ 依赖安装完成!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🚀 启动方式:"
echo ""
echo "  1. 启动后端服务 (新终端窗口):"
echo "     cd backend && source venv/bin/activate && python main.py"
echo ""
echo "  2. 启动前端服务 (新终端窗口):"
echo "     cd frontend && npm run dev"
echo ""
echo "  3. 打开浏览器访问: http://localhost:3000"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📝 注意事项:"
echo "  - 需要 OpenRouter API Key (https://openrouter.ai/keys)"
echo "  - 可以在游戏界面中输入 API Key"
echo "  - 后端运行在 http://localhost:8000"
echo "  - 前端运行在 http://localhost:3000"
echo ""
