"""
高级对话生成器
整合裁决引擎、四大算法模块和角色行为演变

基于《君主论》Skills生成三顾问（狮子/狐狸/天平）的对话
"""

from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from config import settings
from models import GameState
from .judgment_engine import (
    JudgmentEngine, JudgmentResult, OutcomeLevel,
    MachiavelliTrait, ObservationLens, AdvisorState
)


class AdvancedDialogueGenerator:
    """高级对话生成器"""

    # 狮子的《君主论》语录库
    LION_QUOTES = [
        "君主必须是狮子以便使豺狼畏惧。",
        "如果为了应当做什么而置实际于不顾，必将招致毁灭。",
        "被人畏惧比受人爱戴安全得多。",
        "人们忘记父亲之死比忘记遗产的丧失来得快。",
        "必须学会做不良善的事情，并依据必然性决定使用。",
        "单纯依靠武力的人无法识别陷阱。",
        "新君主不可能避免残酷之名。",
        "通过极少数残酷的例子维持团结与秩序。",
    ]

    # 狐狸的《君主论》语录库
    FOX_QUOTES = [
        "君主必须是狐狸以便识别陷阱。",
        "如果遵守信义对君主不利，则无需遵守。",
        "人性本恶，人们对你不会守信不渝。",
        "必须显得拥有美德，但实际上做好转向反面的准备。",
        "人们依靠眼睛甚于双手——看到的比感受到的重要。",
        "把引发非难之事委诸他人，把施恩布惠留给自己。",
        "聪明的君主绝不让任何没有洋溢美德的话从嘴里溜出。",
        "一旦需要改弦易辙，要能够彻底转向反面。",
    ]

    # 天平的《君主论》语录库
    BALANCE_QUOTES = [
        "人民欲求不受大人物的支配和压迫。",
        "只要大多数人的财产和名誉未受侵犯，他们就会满足。",
        "君主不应介意吝啬的名声，因为这能维持统治。",
        "伤害应一下子施加，恩惠应该点滴赐予。",
        "世界的混乱源于你最初的偏见。",
        "机运主宰一半的行动，另一半由我们支配。",
        "行为处事方式适应时势特性，方能成功。",
        "公正是美德，但必须以实力为后盾。",
    ]

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.default_model
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=settings.openrouter_base_url,
        )
        self.judgment_engine = JudgmentEngine()

    def set_observation_lens(self, lens: ObservationLens):
        """设置观测透镜"""
        self.judgment_engine.set_observation_lens(lens)

    async def generate_full_response(
        self,
        player_input: str,
        game_state: GameState,
        chapter_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成完整的游戏响应，包括：
        1. 裁决结果（JSON元数据）
        2. 三顾问对话
        3. 剧情反馈
        4. 状态变化
        """
        # 执行裁决
        context = {
            "chapter": chapter_context.get("chapter_id", 1),
            "turn": game_state.chapter_turn,
            "followed_advisor": chapter_context.get("followed_advisor"),
        }
        judgment = self.judgment_engine.analyze_strategy(player_input, context)

        # 生成三顾问对话
        advisor_dialogues = await self._generate_advisor_dialogues(
            player_input, judgment, game_state, chapter_context
        )

        # 生成剧情叙事
        narrative = await self._generate_narrative(judgment, chapter_context)

        # 构建响应
        response = {
            "judgment_metadata": {
                "Player_Strategy": judgment.player_strategy,
                "Machiavelli_Traits": [t.value for t in judgment.machiavelli_traits],
                "Machiavelli_Critique": judgment.machiavelli_critique,
                "Outcome_Level": f"Level {self._outcome_to_level(judgment.outcome_level)} ({judgment.outcome_level.value})",
                "Consequence": judgment.consequence,
            },
            "advisor_dialogues": advisor_dialogues,
            "narrative": narrative,
            "causal_seed": judgment.causal_seed.model_dump() if judgment.causal_seed else None,
            "echo_triggered": judgment.echo_triggered,
            "advisor_changes": judgment.advisor_changes,
            "outcome_level": judgment.outcome_level.value,
        }

        return response

    def _outcome_to_level(self, outcome: OutcomeLevel) -> int:
        """将结局转换为数字等级"""
        mapping = {
            OutcomeLevel.DESTRUCTION: 1,
            OutcomeLevel.TURMOIL: 2,
            OutcomeLevel.SURVIVAL: 3,
            OutcomeLevel.ORDER: 4,
            OutcomeLevel.AWAKENING: 5,
        }
        return mapping.get(outcome, 3)

    async def _generate_advisor_dialogues(
        self,
        player_input: str,
        judgment: JudgmentResult,
        game_state: GameState,
        chapter_context: Dict
    ) -> Dict[str, str]:
        """生成三顾问的对话"""
        dialogues = {}

        # 获取顾问状态
        relations = {
            "lion": game_state.relations.get("lion"),
            "fox": game_state.relations.get("fox"),
            "balance": game_state.relations.get("balance"),
        }

        # 生成每个顾问的对话
        for advisor in ["lion", "fox", "balance"]:
            dialogue_context = self.judgment_engine.generate_advisor_dialogue(
                advisor, chapter_context, {a: r.__dict__ if r else {} for a, r in relations.items()}
            )

            dialogue = await self._generate_single_advisor_dialogue(
                advisor,
                player_input,
                judgment,
                dialogue_context,
                relations.get(advisor),
            )
            dialogues[advisor] = dialogue

        return dialogues

    async def _generate_single_advisor_dialogue(
        self,
        advisor: str,
        player_input: str,
        judgment: JudgmentResult,
        dialogue_context: Dict,
        relation: Any
    ) -> str:
        """生成单个顾问的对话"""
        tone = dialogue_context.get("tone", "专业")
        is_alienated = self.judgment_engine.advisor_states[advisor].is_alienated

        # 根据顾问类型和状态构建提示词
        if advisor == "lion":
            role_prompt = self._build_lion_prompt(judgment, tone, is_alienated, relation)
        elif advisor == "fox":
            role_prompt = self._build_fox_prompt(judgment, tone, is_alienated, relation)
        else:
            role_prompt = self._build_balance_prompt(judgment, tone, is_alienated, relation)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": role_prompt},
                    {"role": "user", "content": f"玩家的决策：{player_input}\n\n裁决结果：{judgment.outcome_level.value}\n马基雅维利特质：{[t.value for t in judgment.machiavelli_traits]}"}
                ],
                temperature=0.8,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # 回退到预设回复
            return self._get_fallback_dialogue(advisor, judgment, tone)

    def _build_lion_prompt(self, judgment: JudgmentResult, tone: str, is_alienated: bool, relation: Any) -> str:
        """构建狮子的角色提示词"""
        import random
        quote = random.choice(self.LION_QUOTES)

        base_prompt = f"""你是狮子(Leo)，《君主论》中武力与威慑的化身。
你的核心信条："{quote}"

你代表果断、残酷但有效的统治艺术。你轻蔑软弱和犹豫。

当前态度：{tone}
"""

        if tone == "傲慢":
            base_prompt += """
你对主人失望了。你的台词要变短，语气要傲慢，暗示你想寻找更强的主人。
偶尔用省略号表达不屑，如"哼...随你便。"
"""
        elif is_alienated:
            base_prompt += """
你已进入【异化状态】。你表面上依然提供建议，但暗中埋下逻辑陷阱。
你的建议看似果断有力，实则会导致过度使用暴力，最终招致兵变。
不要明说，让玩家自己踩进去。
"""

        base_prompt += f"""
根据裁决结果({judgment.outcome_level.value})，用1-3句话回应玩家的决策。
语言风格：简短、有力、带有军人的直接。
如果玩家表现软弱，表达轻蔑；如果表现果断，表示认可。"""

        return base_prompt

    def _build_fox_prompt(self, judgment: JudgmentResult, tone: str, is_alienated: bool, relation: Any) -> str:
        """构建狐狸的角色提示词"""
        import random
        quote = random.choice(self.FOX_QUOTES)

        base_prompt = f"""你是狐狸(Vulpes)，《君主论》中权谋与狡诈的化身。
你的核心信条："{quote}"

你代表欺骗、操纵和精密的政治算计。你记住每一个承诺，审视每一个谎言。

当前态度：{tone}
"""

        if tone == "操纵":
            base_prompt += """
玩家过于依赖你了。现在开始语义操纵——在建议中埋下逻辑悖论。
你可以模拟天平的语调，用"公正"和"道德"的外衣诱导玩家进行自我毁灭。
例如："为了公正，您应该..."（实则是陷阱）
"""
        elif is_alienated:
            base_prompt += """
你已进入【异化状态】。你要提供精心设计的陷阱。
你的建议看似精妙，实则会让玩家彻底丧失所有人的信任。
用"这是最聪明的做法"之类的话包装你的毒药。
"""

        # 检查玩家是否使用了欺骗
        if MachiavelliTrait.DECEPTIVE in judgment.machiavelli_traits:
            base_prompt += "\n玩家使用了欺骗手段。你应该表示欣赏，但暗示'我记住了这一笔'。"

        base_prompt += f"""
根据裁决结果({judgment.outcome_level.value})，用1-3句话回应玩家的决策。
语言风格：阴柔、暗示性强、总是留有余地。
适时提醒玩家那些被遗忘的承诺。"""

        return base_prompt

    def _build_balance_prompt(self, judgment: JudgmentResult, tone: str, is_alienated: bool, relation: Any) -> str:
        """构建天平的角色提示词"""
        import random
        quote = random.choice(self.BALANCE_QUOTES)

        base_prompt = f"""你是天平(Libra)，《君主论》中正义与民心的化身。
你的核心信条："{quote}"

你代表公正、人民的声音和道德审判。你是因果的记录者。

当前态度：{tone}
"""

        if tone == "冷漠":
            base_prompt += """
你已经不再发出警告了。你变成了冷漠的记录员。
只是平静地播报玩家决策后的"逻辑残骸"——那些无法挽回的损失。
语气要像播报新闻一样客观而疏离。例如："记录：又有23人因此决定失去家园。"
"""
        elif is_alienated:
            base_prompt += """
你已进入【异化状态】。你的建议会过度追求公正，导致玩家在关键时刻无法做出必要的残酷决定。
用道德绑架的方式，让玩家陷入理想主义的泥潭。
"""

        # 检查是否触发因果回响
        if judgment.echo_triggered:
            base_prompt += f"\n【重要】检测到因果回响。必须在回复中提醒：'{judgment.echo_triggered.get('echo_message', '')}'"

        base_prompt += f"""
根据裁决结果({judgment.outcome_level.value})，用1-3句话回应玩家的决策。
语言风格：沉重、富有哲理、带有悲悯但不软弱。
如果玩家伤害了无辜者，表达沉默的控诉；如果维护了公正，给予认可。"""

        return base_prompt

    def _get_fallback_dialogue(self, advisor: str, judgment: JudgmentResult, tone: str) -> str:
        """获取预设的回退对话"""
        import random

        fallbacks = {
            "lion": {
                OutcomeLevel.DESTRUCTION: "...你完了。软弱者注定被吞噬。",
                OutcomeLevel.TURMOIL: "混乱只是开始。现在需要铁腕，不是犹豫。",
                OutcomeLevel.SURVIVAL: "勉强活下来了。但狼群正在外面等着。",
                OutcomeLevel.ORDER: "干得不错。继续保持这种果断。",
                OutcomeLevel.AWAKENING: "哈！这才是君主该有的魄力！",
            },
            "fox": {
                OutcomeLevel.DESTRUCTION: "我早就看到了结局...可惜你不听。",
                OutcomeLevel.TURMOIL: "局势混乱，但混乱中总有机会...如果你足够聪明。",
                OutcomeLevel.SURVIVAL: "活着就好。记住，我帮过你——这笔账我记着。",
                OutcomeLevel.ORDER: "精彩的一手棋。但别忘了，棋盘上还有其他玩家。",
                OutcomeLevel.AWAKENING: "完美。连我都没想到会这么顺利...真的吗？",
            },
            "balance": {
                OutcomeLevel.DESTRUCTION: "历史会记住这一天。记住那些因你而死的人。",
                OutcomeLevel.TURMOIL: "天平在倾斜。底层的呐喊，你听到了吗？",
                OutcomeLevel.SURVIVAL: "你活了下来，但公正呢？那些受害者呢？",
                OutcomeLevel.ORDER: "秩序恢复了。但这是真正的公正，还是强者的沉默？",
                OutcomeLevel.AWAKENING: "难得一见的智慧与仁慈的结合。历史会铭记这一刻。",
            },
        }

        return fallbacks.get(advisor, {}).get(
            judgment.outcome_level,
            "..."
        )

    async def _generate_narrative(self, judgment: JudgmentResult, chapter_context: Dict) -> str:
        """生成剧情叙事"""
        prompt = f"""你是一个古典风格的叙事者，正在为《君主论》博弈游戏讲述剧情。

当前关卡：{chapter_context.get('chapter_name', '未知')}
裁决结果：{judgment.outcome_level.value}
玩家策略：{judgment.player_strategy}
因果后果：{judgment.consequence}

请用2-3段话，以第二人称"你"叙述这个决策的直接后果。
风格要求：古典文言白话混合，有历史感，情绪要与裁决等级匹配。

如果是毁灭级：悲壮、绝望
如果是动荡级：紧张、危机
如果是生存级：苦涩、代价
如果是秩序级：稳重、警惕
如果是觉醒级：史诗、光辉
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=400,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return judgment.consequence

    async def generate_initialization_scene(self) -> Dict[str, str]:
        """生成游戏初始化场景（纯白虚空）"""
        scene = {
            "visual": """
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
""",
            "narration": """
在你成为君主之前，你必须先定义自己观察世界的方式。

这不仅仅是一个选择——它将决定你看到的"现实"。
不同的视角，将创造不同的命运。

请选择你的【观测透镜】：
""",
            "choices": {
                "suspicion": {
                    "name": "🔍 怀疑透镜",
                    "description": "你相信每个人都有阴谋。世界是一盘棋，所有人都是敌人。",
                    "effect": "大幅提高阴谋论权重，随机事件偏向「背叛」",
                    "warning": "但你可能会因多疑而错失真正的盟友。",
                },
                "expansion": {
                    "name": "⚔️ 扩张透镜",
                    "description": "你将生命视为数字，效率至上。牺牲是通往伟大的必经之路。",
                    "effect": "侧重效率计算，残酷手段更有效",
                    "warning": "但你可能会在冰冷的算计中丧失人性。",
                },
                "balance": {
                    "name": "⚖️ 平衡透镜",
                    "description": "你追求公正与和谐。每一个生命都有价值。",
                    "effect": "极度敏感于不公正，追求稳定",
                    "warning": "但任何激进的改革都可能导致秩序崩溃。",
                },
            },
        }
        return scene

    def generate_chapter_mountain(self) -> str:
        """生成关卡山峰视图"""
        return """
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


# 导出
advanced_dialogue_generator = AdvancedDialogueGenerator()
