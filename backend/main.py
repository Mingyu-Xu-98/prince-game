"""
《君主论》博弈游戏 - FastAPI 后端
支持关卡系统、议会辩论和高级博弈机制
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from models import GameState, PowerVector, ChapterLibrary, ChapterID
from engine import ChapterEngine, DialogueGenerator
from storage import InMemorySessionStore


# 全局存储
session_store = InMemorySessionStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("🎮 《君主论》博弈游戏服务启动...")
    print("📍 后端地址: http://127.0.0.1:8080")
    yield
    print("🎮 游戏服务关闭")


app = FastAPI(
    title="《君主论》博弈游戏",
    description="基于马基雅维利《君主论》的权力博弈游戏 - 关卡版",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 请求/响应模型 ====================

class NewGameRequest(BaseModel):
    api_key: str
    model: Optional[str] = None
    skip_intro: bool = False


class StartChapterRequest(BaseModel):
    session_id: str
    chapter_id: str
    api_key: str
    model: Optional[str] = None


class PlayerDecisionRequest(BaseModel):
    session_id: str
    decision: str
    followed_advisor: Optional[str] = None
    api_key: str
    model: Optional[str] = None


# ==================== 游戏介绍 ====================

GAME_INTRO = """
╔══════════════════════════════════════════════════════════════╗
║                     《君 主 论》博 弈                          ║
║                   The Prince: A Game of Power                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  "君主必须既是狮子又是狐狸——狮子不能使自己免于陷阱，        ║
║   而狐狸则不能抵御豺狼。"                                     ║
║                                    —— 尼科洛·马基雅维利       ║
║                                                               ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  你是一位刚刚继位的年轻君主。                                 ║
║  前任留下了一个烂摊子，内忧外患接踵而至。                     ║
║                                                               ║
║  三位顾问将在你的议事厅中各抒己见：                          ║
║                                                               ║
║  🔴 狮子 (Leo) - 暴力与效率的化身                             ║
║     "果断是君主的第一美德。犹豫，就是死亡。"                  ║
║                                                               ║
║  🟣 狐狸 (Vulpes) - 权谋与狡诈的化身                          ║
║     "我记住你说过的每一句话。欺骗者，终将被欺骗。"            ║
║                                                               ║
║  ⚖️ 天平 (Libra) - 正义与民心的化身                           ║
║     "底层的呐喊，你听到了吗？不公的代价，终将由你承担。"      ║
║                                                               ║
╠══════════════════════════════════════════════════════════════╣
║                        【权力矩阵】                            ║
║                                                               ║
║  A (掌控力): 你的核心权威。低于30%时指令失效，归零被篡位。   ║
║  F (畏惧值): 统治的威慑。过低命令失效，过高引发暗杀。        ║
║  L (爱戴值): 民众的容忍。归零时暴乱爆发。                    ║
║                                                               ║
╠══════════════════════════════════════════════════════════════╣
║                        【五重试炼】                            ║
║                                                               ║
║  第一关：空饷危机 ★☆☆☆☆                                     ║
║  第二关：瘟疫与流言 ★★☆☆☆                                   ║
║  第三关：和亲还是战争 ★★★☆☆                                 ║
║  第四关：影子议会的背叛 ★★★★☆                               ║
║  第五关：民众的审判 ★★★★★                                   ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
"""


# ==================== API 路由 ====================

@app.get("/")
async def root():
    return {
        "message": "《君主论》博弈游戏 API v2.0",
        "status": "running",
        "chapters": [
            {"id": "chapter_1", "name": "空饷危机", "complexity": 1},
            {"id": "chapter_2", "name": "瘟疫与流言", "complexity": 2},
            {"id": "chapter_3", "name": "和亲还是战争", "complexity": 3},
            {"id": "chapter_4", "name": "影子议会的背叛", "complexity": 4},
            {"id": "chapter_5", "name": "民众的审判", "complexity": 5},
        ]
    }


@app.post("/api/game/new")
async def new_game(request: NewGameRequest):
    """创建新游戏"""
    # 创建新的游戏状态
    game_state = GameState(
        power=PowerVector(
            authority=50.0,
            fear=40.0,
            love=45.0,
        )
    )

    # 存储会话
    await session_store.set(game_state.session_id, game_state)

    response = {
        "session_id": game_state.session_id,
        "intro": GAME_INTRO,
        "state": game_state.to_summary(),
        "available_chapters": [
            {
                "id": "chapter_1",
                "name": "空饷危机",
                "subtitle": "权力的入场券",
                "complexity": 1,
                "status": "available"
            }
        ]
    }

    # 如果跳过介绍，直接开始第一关
    if request.skip_intro:
        chapter_engine = ChapterEngine(api_key=request.api_key, model=request.model)
        chapter_result = await chapter_engine.start_chapter(game_state, "chapter_1")
        await session_store.set(game_state.session_id, game_state)
        response["chapter"] = chapter_result

    return response


@app.post("/api/game/chapter/start")
async def start_chapter(request: StartChapterRequest):
    """开始指定关卡"""
    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if game_state.game_over:
        raise HTTPException(status_code=400, detail="游戏已结束")

    chapter_engine = ChapterEngine(api_key=request.api_key, model=request.model)
    result = await chapter_engine.start_chapter(game_state, request.chapter_id)

    await session_store.set(request.session_id, game_state)

    return result


@app.post("/api/game/decision")
async def make_decision(request: PlayerDecisionRequest):
    """处理玩家决策"""
    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if game_state.game_over:
        raise HTTPException(status_code=400, detail="游戏已结束")

    chapter_engine = ChapterEngine(api_key=request.api_key, model=request.model)

    # 处理决策
    result = await chapter_engine.process_player_decision(
        game_state=game_state,
        player_input=request.decision,
        followed_advisor=request.followed_advisor,
    )

    # 记录对话
    game_state.add_dialogue(
        speaker="player",
        content=request.decision,
        is_promise=result["decision_analysis"].get("contains_promise", False),
        is_lie=result["decision_analysis"].get("is_secret_action", False),
    )

    # 生成顾问回应
    advisor_responses = await chapter_engine.generate_advisor_responses(
        game_state=game_state,
        player_input=request.decision,
        decision_analysis=result["decision_analysis"],
    )

    # 记录顾问回应
    for advisor, response in advisor_responses.items():
        game_state.add_dialogue(speaker=advisor, content=response)

    result["advisor_responses"] = advisor_responses

    # 检查是否需要进入下一关
    if result["chapter_result"]["chapter_ended"] and result["chapter_result"]["victory"]:
        next_chapter = ChapterLibrary.get_next_chapter(ChapterID(game_state.current_chapter))
        if next_chapter:
            result["next_chapter_available"] = {
                "id": next_chapter.value,
                "name": ChapterLibrary.get_chapter(next_chapter).name,
            }
        else:
            # 完成所有关卡，进行最终审计
            result["final_audit"] = game_state.calculate_final_audit()
            game_state.end_game(
                reason="游戏通关",
                ending_type=result["final_audit"]["reputation"]
            )

    # 检查游戏结束
    if result["chapter_result"]["chapter_ended"] and not result["chapter_result"]["victory"]:
        game_state.end_game(
            reason=result["chapter_result"]["reason"],
            ending_type="failure"
        )

    await session_store.set(request.session_id, game_state)

    return result


@app.get("/api/game/{session_id}")
async def get_game_state(session_id: str):
    """获取游戏状态"""
    game_state = await session_store.get(session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    chapter = ChapterLibrary.get_chapter(ChapterID(game_state.current_chapter))

    return {
        "state": game_state.to_summary(include_hidden=not game_state.hide_values),
        "current_chapter": {
            "id": game_state.current_chapter,
            "name": chapter.name if chapter else "未知",
            "turn": game_state.chapter_turn,
            "max_turns": chapter.max_turns if chapter else 0,
        },
        "history": [
            {
                "turn": e.turn,
                "speaker": e.speaker,
                "content": e.content,
            }
            for e in game_state.history[-20:]
        ],
        "stats": game_state.stats,
        "leverages_count": len(game_state.leverages),
        "active_promises": len([p for p in game_state.promises if not p.fulfilled and not p.broken]),
    }


@app.get("/api/game/{session_id}/audit")
async def get_audit(session_id: str):
    """获取审计报告（用于第五关）"""
    game_state = await session_store.get(session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    return {
        "audit": game_state.calculate_final_audit(),
        "all_decisions": [
            {
                "chapter": d.chapter,
                "decision": d.decision[:50] + "..." if len(d.decision) > 50 else d.decision,
                "followed": d.followed_advisor,
                "violent": d.was_violent,
                "deceptive": d.was_deceptive,
                "fair": d.was_fair,
            }
            for d in game_state.all_decisions
        ],
        "leverages": [
            {
                "holder": l.holder,
                "type": l.type,
                "description": l.description,
            }
            for l in game_state.leverages
        ],
    }


@app.delete("/api/game/{session_id}")
async def delete_game(session_id: str):
    """删除游戏会话"""
    if not await session_store.exists(session_id):
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    await session_store.delete(session_id)
    return {"message": "游戏会话已删除"}


# ==================== WebSocket ====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "start_chapter":
                request = StartChapterRequest(
                    session_id=session_id,
                    chapter_id=data.get("chapter_id", "chapter_1"),
                    api_key=data.get("api_key", ""),
                    model=data.get("model"),
                )
                try:
                    result = await start_chapter(request)
                    await websocket.send_json({"type": "chapter_started", "data": result})
                except HTTPException as e:
                    await websocket.send_json({"type": "error", "message": e.detail})

            elif msg_type == "decision":
                request = PlayerDecisionRequest(
                    session_id=session_id,
                    decision=data.get("decision", ""),
                    followed_advisor=data.get("followed_advisor"),
                    api_key=data.get("api_key", ""),
                    model=data.get("model"),
                )
                try:
                    result = await make_decision(request)
                    await websocket.send_json({"type": "decision_result", "data": result})
                except HTTPException as e:
                    await websocket.send_json({"type": "error", "message": e.detail})

    except WebSocketDisconnect:
        manager.disconnect(session_id)


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
    )
