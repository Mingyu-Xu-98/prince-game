"""
《君主论》博弈游戏 - FastAPI 后端
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from models import GameState, PowerVector, Event
from models.events import EventLibrary
from engine import NLPParser, AuditEngine, SettlementEngine, DialogueGenerator
from storage import InMemorySessionStore
from prompts.system_prompts import GAME_INTRO


# 全局存储
session_store = InMemorySessionStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("🎮 《君主论》博弈游戏服务启动...")
    yield
    print("🎮 游戏服务关闭")


app = FastAPI(
    title="《君主论》博弈游戏",
    description="基于马基雅维利《君主论》的权力博弈游戏",
    version="1.0.0",
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


class NewGameResponse(BaseModel):
    session_id: str
    intro: str
    state: dict


class PlayerInputRequest(BaseModel):
    session_id: str
    input: str
    api_key: str
    model: Optional[str] = None


class EventChoiceRequest(BaseModel):
    session_id: str
    event_id: str
    choice_id: str
    api_key: str
    model: Optional[str] = None


class TurnResponse(BaseModel):
    turn: int
    player_input: str
    parsed_intent: dict
    robot_responses: dict
    audit_summary: dict
    settlement: dict
    state: dict
    event: Optional[dict] = None


# ==================== API 路由 ====================

@app.get("/")
async def root():
    return {"message": "《君主论》博弈游戏 API", "status": "running"}


@app.post("/api/game/new", response_model=NewGameResponse)
async def new_game(request: NewGameRequest):
    """创建新游戏"""
    # 创建新的游戏状态
    game_state = GameState(
        power=PowerVector(
            authority=settings.initial_authority,
            fear=settings.initial_fear,
            love=settings.initial_love,
        )
    )

    # 存储会话
    await session_store.set(game_state.session_id, game_state)

    return NewGameResponse(
        session_id=game_state.session_id,
        intro=GAME_INTRO,
        state=game_state.to_summary(),
    )


@app.post("/api/game/turn", response_model=TurnResponse)
async def process_turn(request: PlayerInputRequest):
    """处理一个回合"""
    # 获取游戏状态
    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if game_state.game_over:
        raise HTTPException(status_code=400, detail="游戏已结束")

    # 初始化引擎
    nlp_parser = NLPParser(api_key=request.api_key, model=request.model)
    audit_engine = AuditEngine()
    settlement_engine = SettlementEngine()
    dialogue_gen = DialogueGenerator(api_key=request.api_key, model=request.model)

    # 1. NLP 解析
    parsed_intent = await nlp_parser.parse(request.input)

    # 2. 记录玩家输入
    game_state.add_dialogue(
        speaker="player",
        content=request.input,
        intent=parsed_intent.get("intent"),
    )

    # 3. 运行三 Skill 审计
    audit_results = await audit_engine.run_audit(
        player_input=request.input,
        parsed_intent=parsed_intent,
        game_state=game_state,
    )

    # 4. 汇总审计结果
    audit_summary = audit_engine.summarize_audit(audit_results)
    relation_deltas = audit_engine.get_relation_deltas(audit_results)

    # 5. 数值结算
    settlement = settlement_engine.settle(game_state, audit_summary, relation_deltas)

    # 6. 生成机器人回应
    context = [
        {"speaker": e.speaker, "content": e.content}
        for e in game_state.get_recent_history(5)
    ]
    robot_responses = await dialogue_gen.generate_all_responses(
        audit_results=audit_results,
        player_input=request.input,
        context=context,
    )

    # 记录机器人回应
    for robot, response in robot_responses.items():
        game_state.add_dialogue(speaker=robot, content=response)

    # 7. 处理触发的事件
    event_data = None
    if settlement.get("triggered_event"):
        event: Event = settlement["triggered_event"]
        narration = await dialogue_gen.generate_event_narration(event)
        event_data = {
            "id": event.id,
            "type": event.type.value,
            "title": event.title,
            "narration": narration,
            "choices": event.choices,
        }
        game_state.pending_events.append(event.id)

    # 8. 保存状态
    await session_store.set(request.session_id, game_state)

    return TurnResponse(
        turn=game_state.turn,
        player_input=request.input,
        parsed_intent=parsed_intent,
        robot_responses=robot_responses,
        audit_summary=audit_summary,
        settlement=settlement,
        state=game_state.to_summary(),
        event=event_data,
    )


@app.post("/api/game/event")
async def handle_event(request: EventChoiceRequest):
    """处理事件选择"""
    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    # 获取事件
    events = EventLibrary.get_all_events()
    event = events.get(request.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    # 应用选择
    settlement_engine = SettlementEngine()
    result = settlement_engine.apply_event_choice(game_state, event, request.choice_id)

    # 从待处理列表移除
    if request.event_id in game_state.pending_events:
        game_state.pending_events.remove(request.event_id)

    # 生成回应
    dialogue_gen = DialogueGenerator(api_key=request.api_key, model=request.model)

    # 检查游戏结束
    if game_state.power.is_collapsed():
        game_state.end_game("统治崩溃")
        narration = await dialogue_gen.generate_game_over_narration(
            "统治崩溃",
            game_state.power.to_display(),
        )
        result["game_over"] = True
        result["game_over_narration"] = narration

    await session_store.set(request.session_id, game_state)

    return {
        "event_id": request.event_id,
        "result": result,
        "state": game_state.to_summary(),
    }


@app.get("/api/game/{session_id}")
async def get_game_state(session_id: str):
    """获取游戏状态"""
    game_state = await session_store.get(session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    return {
        "state": game_state.to_summary(),
        "history": [
            {
                "turn": e.turn,
                "speaker": e.speaker,
                "content": e.content,
            }
            for e in game_state.history[-20:]
        ],
        "pending_events": game_state.pending_events,
    }


@app.delete("/api/game/{session_id}")
async def delete_game(session_id: str):
    """删除游戏会话"""
    if not await session_store.exists(session_id):
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    await session_store.delete(session_id)
    return {"message": "游戏会话已删除"}


# ==================== WebSocket 实时通信 ====================

class ConnectionManager:
    """WebSocket 连接管理器"""

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
    """WebSocket 实时游戏通信"""
    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "turn":
                # 处理回合
                request = PlayerInputRequest(
                    session_id=session_id,
                    input=data.get("input", ""),
                    api_key=data.get("api_key", ""),
                    model=data.get("model"),
                )

                try:
                    result = await process_turn(request)
                    await websocket.send_json({
                        "type": "turn_result",
                        "data": result.model_dump(),
                    })
                except HTTPException as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": e.detail,
                    })

            elif data.get("type") == "event_choice":
                # 处理事件选择
                request = EventChoiceRequest(
                    session_id=session_id,
                    event_id=data.get("event_id", ""),
                    choice_id=data.get("choice_id", ""),
                    api_key=data.get("api_key", ""),
                    model=data.get("model"),
                )

                try:
                    result = await handle_event(request)
                    await websocket.send_json({
                        "type": "event_result",
                        "data": result,
                    })
                except HTTPException as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": e.detail,
                    })

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
