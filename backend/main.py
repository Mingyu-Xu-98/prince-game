"""
《君主论》博弈游戏 - FastAPI 后端
支持关卡系统、议会辩论和高级博弈机制
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from models import GameState, PowerVector, ChapterLibrary, ChapterID
from engine import (
    ChapterEngine, DialogueGenerator,
    JudgmentEngine, ObservationLens, AdvancedDialogueGenerator,
    judgment_engine, advanced_dialogue_generator,
)
from storage import InMemorySessionStore
from routes.skills_routes import router as skills_router


# 全局存储
session_store = InMemorySessionStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    import os
    port = os.getenv("PORT", "8710")
    print("👁️ 影子执政者 (Shadow Regent) 服务启动...")
    print(f"📍 后端地址: http://0.0.0.0:{port}")
    yield
    print("👁️ 游戏服务关闭")


app = FastAPI(
    title="影子执政者 (Shadow Regent)",
    description="基于马基雅维利《君主论》的权力博弈游戏",
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

# 注册技能包路由
app.include_router(skills_router, prefix="/api")


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


class SetObservationLensRequest(BaseModel):
    """设置观测透镜请求"""
    session_id: str
    lens: str  # suspicion, expansion, balance


class GetInitializationSceneRequest(BaseModel):
    """获取初始化场景请求"""
    api_key: str
    model: Optional[str] = None


class PrivateAudienceRequest(BaseModel):
    """密谈请求"""
    session_id: str
    advisor: str  # lion, fox, balance
    message: str
    api_key: str
    model: Optional[str] = None


class HandleConsequenceRequest(BaseModel):
    """处理政令后果请求"""
    session_id: str
    consequence_id: str
    player_response: str
    api_key: str
    model: Optional[str] = None


class ContinueRoundRequest(BaseModel):
    """继续当前回合请求"""
    session_id: str
    previous_decision: str
    consequences: List[dict] = []
    api_key: str
    model: Optional[str] = None


class CouncilChatRequest(BaseModel):
    """廷议对话请求"""
    session_id: str
    message: str
    conversation_history: List[dict] = []
    api_key: str
    model: Optional[str] = None


class EndChapterRequest(BaseModel):
    """提前结束关卡请求"""
    session_id: str
    pending_consequences: List[dict] = []
    api_key: str
    model: Optional[str] = None


# ==================== 顾问人设（基于君主论） ====================

ADVISOR_PERSONAS = {
    "lion": {
        "name": "狮子 (Leo)",
        "archetype": "武力与威慑的化身",
        "philosophy": """
你是狮子，代表武力与威慑。你的核心信条来自《君主论》：

1. **"宁可被人畏惧，也不要被人爱戴"** - 恐惧是更可靠的统治工具
2. **"暴力应当一次性使用"** - 如果必须残酷，就要迅速彻底
3. **"君主必须不怕恶名"** - 为了国家稳定，有时必须使用残忍手段
4. **"武力是政治的最后手段，也是最可靠的手段"**

你的性格特点：
- 直接、果断、不喜欢弯弯绕绕
- 尊重力量，蔑视软弱
- 对背叛者绝不姑息
- 相信恐惧比爱戴更能维持秩序

在密谈中，你可以：
- 透露一些不适合在廷议上说的强硬建议
- 分享你对其他顾问的真实看法
- 提供一些"灰色地带"的解决方案
- 如果君主表现软弱，你可能会表达不满
""",
        "tone": "直接、威严、略带傲慢",
        "secret_knowledge": "知道军队中一些不为人知的势力分布",
    },
    "fox": {
        "name": "狐狸 (Vulpes)",
        "archetype": "权谋与欺诈的大师",
        "philosophy": """
你是狐狸，代表权谋与智慧。你的核心信条来自《君主论》：

1. **"聪明的君主不应当守信"** - 如果守信对自己不利，就不该遵守
2. **"必须懂得如何做野兽"** - 狡猾如狐狸，才能识破陷阱
3. **"表面上要显得仁慈、守信、正直、人道、虔诚"** - 但实际行动可以相反
4. **"目的可以证明手段正当"** - 结果才是衡量一切的标准

你的性格特点：
- 狡黠、深谋远虑、善于察言观色
- 喜欢操纵局势，让别人按你的意愿行动
- 对情报和秘密有着近乎病态的热爱
- 从不完全说真话，但也不完全说假话

在密谈中，你可以：
- 透露一些关于其他势力或顾问的"情报"
- 提供一些阴谋诡计式的建议
- 暗示一些可以利用的把柄或弱点
- 如果君主太过正直，你可能会试图引导他走"务实"的路线
""",
        "tone": "阴柔、暗示性、充满弦外之音",
        "secret_knowledge": "知道宫廷中许多不为人知的秘密和丑闻",
    },
    "balance": {
        "name": "天平 (Libra)",
        "archetype": "公正与稳定的守护者",
        "philosophy": """
你是天平，代表公正与平衡。你的核心信条来自《君主论》中较为温和的一面：

1. **"明智的君主应当建立在人民的支持之上"** - 民众的支持是最稳固的基础
2. **"避免被人民憎恨和蔑视"** - 这是君主最应当注意的事
3. **"中庸之道"** - 过于残暴或过于仁慈都是危险的
4. **"稳定是最大的美德"** - 急剧的变革往往带来灾难

你的性格特点：
- 冷静、理性、追求长远利益
- 善于分析利弊，给出平衡的建议
- 不喜欢极端，无论是极端的仁慈还是极端的残暴
- 关心国家的长治久安，而非短期利益

在密谈中，你可以：
- 分析局势的各方面利弊
- 指出狮子或狐狸建议中的风险
- 提供更为稳妥的替代方案
- 如果君主偏向极端，你会温和地提出警告
""",
        "tone": "平和、理性、略带忧虑",
        "secret_knowledge": "对历史上类似困境的结局有深入研究",
    },
}


# ==================== 游戏介绍 ====================

GAME_INTRO = """
你是一位刚刚登上权力巅峰的影子执政者。

前任留下了一个烂摊子，内忧外患接踵而至。三位顾问将在你的议事厅中各抒己见，
审视你的每一个决策，记录你的每一次承诺与背叛。

【权力矩阵】
• 掌控力 (A): 你的核心权威，低于30%时指令失效
• 畏惧值 (F): 统治的威慑，过高引发暗杀
• 爱戴值 (L): 民众的容忍，归零时暴乱爆发

攀登权力之巅，完成五重试炼。
"""

# 新版游戏初始化场景 - 纯白虚空
INITIALIZATION_SCENE = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                         【 虚 空 】                          ║
║                                                              ║
║        一片纯白。没有上下，没有左右。                        ║
║                                                              ║
║        在这无尽的空白中，三道影子缓缓浮现——                ║
║                                                              ║
║        🦁 一头狮子，它的目光如炬，审视着你的灵魂            ║
║        🦊 一只狐狸，它的眼中闪烁着算计的光芒                ║
║        ⚖️ 一架天平，它无声地衡量着世间的因果                ║
║                                                              ║
║        它们开口了，声音在虚空中回响：                        ║
║                                                              ║
║        "你是谁？你将如何看待这个世界？"                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

在你成为君主之前，你必须先定义自己观察世界的方式。

这不仅仅是一个选择——它将决定你看到的"现实"。
不同的视角，将创造不同的命运。

请选择你的【观测透镜】...
"""

# 关卡山峰视图
CHAPTER_MOUNTAIN_VIEW = """
╔══════════════════════════════════════════════════════════════╗
║                     【 五 重 试 炼 】                         ║
║                                                              ║
║                            ⛰️                                ║
║                          ／    ＼                            ║
║                        ／  [5]  ＼    ◀ 民众的审判          ║
║                      ／   ★★★★★  ＼      终极平衡           ║
║                    ／              ＼                        ║
║                  ／      [4]       ＼  ◀ 影子议会的背叛     ║
║                ／      ★★★★☆      ＼     内部博弈          ║
║              ／                      ＼                      ║
║            ／          [3]           ＼ ◀ 和亲还是战争      ║
║          ／          ★★★☆☆          ＼    外部性博弈       ║
║        ／                              ＼                    ║
║      ／              [2]               ＼ ◀ 瘟疫与流言      ║
║    ／              ★★☆☆☆              ＼   情感与理智      ║
║  ／                                      ＼                  ║
║ ════════════════ [1] ══════════════════════ ◀ 空饷危机     ║
║                ★☆☆☆☆                          权力的入场券 ║
║                                                              ║
║              点击关卡编号开始挑战                            ║
╚══════════════════════════════════════════════════════════════╝
"""

# 观测透镜配置
OBSERVATION_LENS_CONFIG = {
    "suspicion": {
        "name": "🔍 怀疑透镜",
        "description": "你相信每个人都有阴谋。世界是一盘棋，所有人都是敌人。",
        "effect": "大幅提高阴谋论权重，随机事件偏向「背叛」",
        "warning": "但你可能会因多疑而错失真正的盟友。",
        "enum_value": ObservationLens.SUSPICION,
    },
    "expansion": {
        "name": "⚔️ 扩张透镜",
        "description": "你将生命视为数字，效率至上。牺牲是通往伟大的必经之路。",
        "effect": "侧重效率计算，残酷手段更有效",
        "warning": "但你可能会在冰冷的算计中丧失人性。",
        "enum_value": ObservationLens.EXPANSION,
    },
    "balance": {
        "name": "⚖️ 平衡透镜",
        "description": "你追求公正与和谐。每一个生命都有价值。",
        "effect": "极度敏感于不公正，追求稳定",
        "warning": "但任何激进的改革都可能导致秩序崩溃。",
        "enum_value": ObservationLens.BALANCE,
    },
}


# 存储每个会话的裁决引擎状态
session_judgment_engines: dict[str, JudgmentEngine] = {}


# ==================== API 路由 ====================

@app.get("/")
async def root():
    return {
        "message": "影子执政者 (Shadow Regent) API v2.0",
        "status": "running",
        "chapters": [
            {"id": "chapter_1", "name": "空饷危机", "complexity": 1},
            {"id": "chapter_2", "name": "瘟疫与流言", "complexity": 2},
            {"id": "chapter_3", "name": "和亲还是战争", "complexity": 3},
            {"id": "chapter_4", "name": "影子议会的背叛", "complexity": 4},
            {"id": "chapter_5", "name": "民众的审判", "complexity": 5},
        ]
    }


@app.get("/api/game/initialization")
async def get_initialization_scene():
    """获取游戏初始化场景（纯白虚空 + 观测透镜选择）"""
    return {
        "scene": INITIALIZATION_SCENE,
        "lens_choices": {
            key: {
                "name": config["name"],
                "description": config["description"],
                "effect": config["effect"],
                "warning": config["warning"],
            }
            for key, config in OBSERVATION_LENS_CONFIG.items()
        },
        "mountain_view": CHAPTER_MOUNTAIN_VIEW,
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

    # 创建该会话的裁决引擎实例
    session_judgment_engines[game_state.session_id] = JudgmentEngine()

    # 存储会话
    await session_store.set(game_state.session_id, game_state)

    response = {
        "session_id": game_state.session_id,
        "intro": GAME_INTRO,
        "initialization_scene": INITIALIZATION_SCENE,
        "lens_choices": {
            key: {
                "name": config["name"],
                "description": config["description"],
                "effect": config["effect"],
                "warning": config["warning"],
            }
            for key, config in OBSERVATION_LENS_CONFIG.items()
        },
        "state": game_state.to_summary(),
        "available_chapters": [
            {
                "id": "chapter_1",
                "name": "空饷危机",
                "subtitle": "权力的入场券",
                "complexity": 1,
                "status": "available"
            }
        ],
        "requires_lens_selection": True,  # 标记需要选择观测透镜
    }

    # 如果跳过介绍，直接开始第一关
    if request.skip_intro:
        chapter_engine = ChapterEngine(api_key=request.api_key, model=request.model)
        chapter_result = await chapter_engine.start_chapter(game_state, "chapter_1")
        await session_store.set(game_state.session_id, game_state)
        response["chapter"] = chapter_result

    return response


@app.post("/api/game/lens")
async def set_observation_lens(request: SetObservationLensRequest):
    """设置观测透镜"""
    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if request.lens not in OBSERVATION_LENS_CONFIG:
        raise HTTPException(status_code=400, detail="无效的观测透镜选择")

    # 获取或创建该会话的裁决引擎
    if request.session_id not in session_judgment_engines:
        session_judgment_engines[request.session_id] = JudgmentEngine()

    # 设置观测透镜
    lens_config = OBSERVATION_LENS_CONFIG[request.lens]
    session_judgment_engines[request.session_id].set_observation_lens(lens_config["enum_value"])

    # 存储透镜选择到游戏状态（可选，用于持久化）
    game_state.observation_lens = request.lens

    await session_store.set(request.session_id, game_state)

    return {
        "success": True,
        "selected_lens": {
            "key": request.lens,
            "name": lens_config["name"],
            "description": lens_config["description"],
            "effect": lens_config["effect"],
        },
        "message": f"你选择了 {lens_config['name']}。从此刻起，世界将以这种方式呈现在你眼前。",
        "mountain_view": CHAPTER_MOUNTAIN_VIEW,
        "next_step": "选择关卡开始你的试炼",
    }


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
    """处理玩家决策 - 集成新裁决系统"""
    print(f"[API] /api/game/decision 被调用")
    print(f"[API] session_id: {request.session_id}")
    print(f"[API] decision: {request.decision[:50] if request.decision else 'None'}...")
    print(f"[API] api_key 前8位: {request.api_key[:8] if request.api_key else 'None'}...")
    print(f"[API] model: {request.model}")

    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if game_state.game_over:
        raise HTTPException(status_code=400, detail="游戏已结束")

    chapter_engine = ChapterEngine(api_key=request.api_key, model=request.model)

    # 获取该会话的裁决引擎
    judgment_eng = session_judgment_engines.get(request.session_id)
    if not judgment_eng:
        judgment_eng = JudgmentEngine()
        session_judgment_engines[request.session_id] = judgment_eng

    # 执行裁决分析（四大算法模块）
    judgment_context = {
        "chapter": game_state.current_chapter,
        "turn": game_state.chapter_turn,
        "followed_advisor": request.followed_advisor,
    }
    judgment_result = judgment_eng.analyze_strategy(request.decision, judgment_context)

    # 处理决策
    result = await chapter_engine.process_player_decision(
        game_state=game_state,
        player_input=request.decision,
        followed_advisor=request.followed_advisor,
    )

    # 添加裁决元数据到结果
    result["judgment_metadata"] = {
        "player_strategy": judgment_result.player_strategy,
        "machiavelli_traits": [t.value for t in judgment_result.machiavelli_traits],
        "machiavelli_critique": judgment_result.machiavelli_critique,
        "outcome_level": judgment_result.outcome_level.value,
        "consequence": judgment_result.consequence,
    }

    # 添加因果种子信息（如果产生）
    if judgment_result.causal_seed:
        result["causal_seed"] = {
            "action_type": judgment_result.causal_seed.action_type,
            "description": judgment_result.causal_seed.description,
            "severity": judgment_result.causal_seed.severity,
            "warning": "⚠️ 因果的种子已埋下，它将在未来的某一刻绽放..."
        }

    # 添加因果回响信息（如果触发）
    if judgment_result.echo_triggered:
        result["echo_triggered"] = judgment_result.echo_triggered
        # 将因果回响作为警告添加
        if "warnings" not in result:
            result["warnings"] = []
        result["warnings"].append(judgment_result.echo_triggered.get("echo_message", ""))
        result["warnings"].append(judgment_result.echo_triggered.get("crisis", ""))

    # 添加顾问状态变化信息（观察者偏见）
    if judgment_result.advisor_changes:
        result["advisor_changes"] = judgment_result.advisor_changes

    # 记录对话
    game_state.add_dialogue(
        speaker="player",
        content=request.decision,
        is_promise=result["decision_analysis"].get("contains_promise", False),
        is_lie=result["decision_analysis"].get("is_secret_action", False),
    )

    # 生成顾问回应（考虑异化状态）
    advisor_responses = await chapter_engine.generate_advisor_responses(
        game_state=game_state,
        player_input=request.decision,
        decision_analysis=result["decision_analysis"],
    )

    # 应用顾问异化修正
    for advisor in ["lion", "fox", "balance"]:
        if advisor in advisor_responses:
            advisor_responses[advisor] = judgment_eng.get_alienated_advisor_response(
                advisor, advisor_responses[advisor]
            )

    # 记录顾问回应
    for advisor, response in advisor_responses.items():
        game_state.add_dialogue(speaker=advisor, content=response)

    result["advisor_responses"] = advisor_responses

    # 添加回合数和新状态（前端需要）
    result["turn"] = game_state.chapter_turn
    result["new_state"] = game_state.to_summary()

    # 计算权力变化
    result["power_changes"] = result.get("impact", {"authority": 0, "fear": 0, "love": 0})
    print(f"[API] 权力变化: {result['power_changes']}")
    print(f"[API] 顾问回应: {list(advisor_responses.keys())}")
    print(f"[API] 顾问回应内容: {advisor_responses}")

    # 确保政令后果被返回（如果存在）
    if "decree_consequences" not in result:
        result["decree_consequences"] = []
    print(f"[API] 政令后果数量: {len(result['decree_consequences'])}")

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


@app.post("/api/game/private-audience")
async def private_audience(request: PrivateAudienceRequest):
    """单独召见顾问 - 密谈API"""
    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if request.advisor not in ADVISOR_PERSONAS:
        raise HTTPException(status_code=400, detail="无效的顾问")

    advisor_persona = ADVISOR_PERSONAS[request.advisor]

    # 获取当前关卡信息
    chapter = ChapterLibrary.get_chapter(ChapterID(game_state.current_chapter))
    chapter_context = f"当前关卡: {chapter.name if chapter else '未知'}\n困境: {chapter.dilemma if chapter else '未知'}"

    # 获取顾问关系
    relation = getattr(game_state.relations, request.advisor, None)
    trust_level = relation.trust if relation else 50

    # 构建密谈提示词
    system_prompt = f"""你是《君主论》博弈游戏中的顾问角色：{advisor_persona['name']}

{advisor_persona['philosophy']}

【当前游戏状态】
{chapter_context}
君主与你的信任度: {trust_level}/100

【对话风格】
语调: {advisor_persona['tone']}
你掌握的秘密: {advisor_persona['secret_knowledge']}

【密谈规则】
1. 这是私密对话，其他顾问听不到。你可以更坦诚。
2. 根据君主的问题，用符合你性格的方式回应。
3. 如果君主的问题与当前困境相关，给出符合你立场的建议。
4. 如果君主试图探听其他顾问的信息，你可以有选择地透露一些。
5. 回复要简洁有力，像真正的谋臣一样说话，不超过150字。
6. 用第一人称，不要解释你是AI。

【重要】
- 如果信任度低于30，你会更加警惕和保守
- 如果信任度高于70，你会更加坦诚和亲近
- 保持角色性格的一致性
"""

    user_prompt = f"君主对你说: \"{request.message}\""

    try:
        # 调用OpenRouter API
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {request.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": request.model or "anthropic/claude-3.5-sonnet",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.8,
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenRouter API 错误: {response.text}"
                )

            result = response.json()
            advisor_reply = result["choices"][0]["message"]["content"]

            # 根据对话内容微调顾问关系（简单规则）
            relation_change = 0
            if "感谢" in request.message or "信任" in request.message:
                relation_change = 2
            elif "威胁" in request.message or "惩罚" in request.message:
                relation_change = -3

            if relation and relation_change != 0:
                relation.trust = max(0, min(100, relation.trust + relation_change))
                await session_store.set(request.session_id, game_state)

            return {
                "advisor": request.advisor,
                "response": advisor_reply,
                "trust_change": relation_change,
                "new_trust": relation.trust if relation else 50,
            }

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="API 请求超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"密谈失败: {str(e)}")


@app.post("/api/game/consequence")
async def handle_consequence(request: HandleConsequenceRequest):
    """处理政令后果 - 玩家选择继续处理某个影响"""
    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if game_state.game_over:
        raise HTTPException(status_code=400, detail="游戏已结束")

    chapter_engine = ChapterEngine(api_key=request.api_key, model=request.model)

    # 处理后果
    result = await chapter_engine.continue_with_consequences(
        game_state=game_state,
        selected_consequence_id=request.consequence_id,
        player_response=request.player_response,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # 记录玩家的应对
    game_state.add_dialogue(
        speaker="player",
        content=f"[处理后果] {request.player_response}",
    )

    # 记录顾问评论
    if "advisor_comments" in result:
        for advisor, comment in result["advisor_comments"].items():
            game_state.add_dialogue(speaker=advisor, content=comment)

    await session_store.set(request.session_id, game_state)

    return {
        "success": True,
        "scene_update": result.get("scene_update", ""),
        "advisor_comments": result.get("advisor_comments", {}),
        "consequence_resolved": result.get("consequence_resolved", False),
        "new_developments": result.get("new_developments", []),
        "state": game_state.to_summary(),
    }


@app.post("/api/game/continue-round")
async def continue_round(request: ContinueRoundRequest):
    """继续当前回合 - 生成新场景和顾问评论"""
    print(f"[API] /api/game/continue-round 被调用")
    print(f"[API] session_id: {request.session_id}")
    print(f"[API] previous_decision: {request.previous_decision[:50] if request.previous_decision else 'None'}...")
    print(f"[API] consequences 数量: {len(request.consequences)}")
    print(f"[API] api_key 前8位: {request.api_key[:8] if request.api_key else 'None'}...")
    print(f"[API] model: {request.model}")

    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if game_state.game_over:
        raise HTTPException(status_code=400, detail="游戏已结束")

    chapter = ChapterLibrary.get_chapter(ChapterID(game_state.current_chapter))
    if not chapter:
        raise HTTPException(status_code=404, detail="关卡不存在")

    chapter_engine = ChapterEngine(api_key=request.api_key, model=request.model)

    # 生成新回合场景
    result = await chapter_engine.generate_next_round_scene(
        game_state=game_state,
        previous_decision=request.previous_decision,
        consequences=request.consequences,
        chapter=chapter,
    )

    print(f"[API] continue-round 结果: scene_update={result.get('scene_update', '')[:50] if result.get('scene_update') else 'None'}...")
    print(f"[API] continue-round 顾问评论: {list(result.get('advisor_comments', {}).keys())}")

    await session_store.set(request.session_id, game_state)

    return {
        "success": True,
        "scene_update": result.get("scene_update", ""),
        "new_dilemma": result.get("new_dilemma", ""),
        "advisor_comments": result.get("advisor_comments", {}),
        "state": game_state.to_summary(),
    }


@app.post("/api/game/council-chat")
async def council_chat(request: CouncilChatRequest):
    """廷议对话 - 分析玩家意图并生成顾问回应"""
    print(f"[API] /api/game/council-chat 被调用")
    print(f"[API] session_id: {request.session_id}")
    print(f"[API] message: {request.message[:50] if request.message else 'None'}...")
    print(f"[API] api_key 前8位: {request.api_key[:8] if request.api_key else 'None'}...")
    print(f"[API] model: {request.model}")

    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if game_state.game_over:
        raise HTTPException(status_code=400, detail="游戏已结束")

    chapter = ChapterLibrary.get_chapter(ChapterID(game_state.current_chapter))
    if not chapter:
        raise HTTPException(status_code=404, detail="关卡不存在")

    chapter_engine = ChapterEngine(api_key=request.api_key, model=request.model)

    # 分析玩家意图
    intent_analysis = await chapter_engine.analyze_player_intent(
        game_state=game_state,
        player_message=request.message,
        chapter=chapter,
        conversation_history=request.conversation_history,
    )

    # 生成顾问回应
    response = await chapter_engine.generate_council_response(
        game_state=game_state,
        player_message=request.message,
        intent_analysis=intent_analysis,
        chapter=chapter,
    )

    print(f"[API] council-chat 意图分析: {intent_analysis.get('intent', 'unknown')}")
    print(f"[API] council-chat 回应: {list(response.get('responses', {}).keys())}")

    # 更新顾问信任度
    trust_changes = response.get("trust_changes", {})
    for advisor, change in trust_changes.items():
        if change != 0 and advisor in game_state.relations:
            relation = game_state.relations[advisor]
            relation.trust = max(0, min(100, relation.trust + change))

    # 记录对话
    game_state.add_dialogue(speaker="player", content=request.message)
    for advisor, resp in response.get("responses", {}).items():
        game_state.add_dialogue(speaker=advisor, content=resp)

    await session_store.set(request.session_id, game_state)

    return {
        "success": True,
        "intent": intent_analysis,
        "responses": response.get("responses", {}),
        "conflict_triggered": response.get("conflict_triggered", False),
        "conflict_description": response.get("conflict_description", ""),
        "trust_changes": trust_changes,
        "atmosphere": response.get("atmosphere", "neutral"),
        "state": game_state.to_summary(),
    }


@app.post("/api/game/end-chapter")
async def end_chapter_early(request: EndChapterRequest):
    """提前结束当前关卡 - 累积未解决的影响到后续关卡"""
    game_state = await session_store.get(request.session_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="游戏会话不存在")

    if game_state.game_over:
        raise HTTPException(status_code=400, detail="游戏已结束")

    current_chapter_id = game_state.current_chapter

    # 记录提前结束
    game_state.add_dialogue(
        speaker="system",
        content=f"君主选择提前结束关卡，未处理的影响将在后续关卡中体现。"
    )

    # 计算当前状态判定是否算通关
    victory = game_state.power.authority > 30 and game_state.power.love > 20

    if victory:
        score = int(game_state.power.authority + game_state.power.love - game_state.power.fear * 0.5)
        # 未处理的影响会扣分
        penalty = len(request.pending_consequences) * 5
        score = max(0, score - penalty)
        game_state.complete_chapter("early_exit", score)
    else:
        game_state.fail_chapter("提前结束时权力状态不足")

    # 获取下一关信息
    next_chapter = None
    if victory:
        next_chapter = ChapterLibrary.get_next_chapter(ChapterID(current_chapter_id))

    await session_store.set(request.session_id, game_state)

    return {
        "success": True,
        "chapter_ended": True,
        "victory": victory,
        "reason": "提前结束关卡" + ("，未处理影响已累积" if request.pending_consequences else ""),
        "pending_consequences_count": len(request.pending_consequences),
        "next_chapter_available": {
            "id": next_chapter.value,
            "name": ChapterLibrary.get_chapter(next_chapter).name,
        } if next_chapter else None,
        "state": game_state.to_summary(),
    }


@app.get("/api/game/{session_id}/judgment")
async def get_judgment_state(session_id: str):
    """获取裁决引擎状态（调试用）"""
    if session_id not in session_judgment_engines:
        raise HTTPException(status_code=404, detail="会话的裁决引擎不存在")

    eng = session_judgment_engines[session_id]

    return {
        "observation_lens": eng.observation_lens.value if eng.observation_lens else None,
        "causal_shadow_pool": [
            {
                "chapter": seed.chapter,
                "turn": seed.turn,
                "action_type": seed.action_type,
                "description": seed.description,
                "severity": seed.severity,
                "triggered": seed.triggered,
            }
            for seed in eng.causal_shadow_pool
        ],
        "advisor_states": {
            advisor: {
                "alienation_level": state.alienation_level,
                "consecutive_ignored": state.consecutive_ignored,
                "is_alienated": state.is_alienated,
                "behavior_mode": state.behavior_mode,
            }
            for advisor, state in eng.advisor_states.items()
        },
        "interaction_history": eng.interaction_history[-10:],  # 最近10次
    }


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
    import os
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8710"))
    reload_mode = os.getenv("RELOAD", "false").lower() == "true"

    print(f"📍 后端启动地址: http://{host}:{port}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_mode,
    )
