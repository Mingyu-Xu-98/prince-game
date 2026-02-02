"""
裁决引擎 (Judgment Engine)
基于《君主论》原则分析玩家决策并生成因果结果

核心功能：
1. 语义对齐 - 将玩家决策映射到马基雅维利特质
2. 结局定级 - [毁灭/动荡/生存/秩序/觉醒]
3. 因果生成 - 基于逻辑必然性生成剧情
4. 四大算法模块
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import random


class MachiavelliTrait(str, Enum):
    """马基雅维利特质分类"""
    # 狮子特质 (暴力/果断)
    CRUEL = "残忍"           # 残酷但有效
    DECISIVE = "果断"        # 快速行动
    FEARSOME = "威慑"        # 令人畏惧
    MILITANT = "好战"        # 武力解决

    # 狐狸特质 (狡诈/权谋)
    DECEPTIVE = "伪善"       # 欺骗但有用
    CUNNING = "狡诈"         # 权谋手段
    MANIPULATIVE = "操纵"    # 操控他人
    PROMISE_BREAKER = "背信" # 违背承诺

    # 天平特质 (正义/仁慈)
    GENEROUS = "慷慨"        # 施恩于民
    MERCIFUL = "仁慈"        # 宽恕敌人
    JUST = "公正"           # 公平裁决
    TRUSTWORTHY = "守信"     # 遵守承诺

    # 负面特质 (软弱/危险)
    WEAK = "软弱"           # 犹豫不决
    INDECISIVE = "优柔"     # 无法决断
    COWARDLY = "胆怯"       # 害怕行动
    RECKLESS = "鲁莽"       # 不计后果
    GREEDY = "贪婪"         # 触碰禁忌
    CONTEMPTIBLE = "可蔑"   # 招致蔑视


class OutcomeLevel(str, Enum):
    """结局定级"""
    DESTRUCTION = "毁灭"    # Level 1: 悲剧，背叛/兵变/死亡
    TURMOIL = "动荡"       # Level 2: 混乱，秩序崩溃但可挽救
    SURVIVAL = "生存"      # Level 3: 勉强维持，付出代价
    ORDER = "秩序"         # Level 4: 成功维稳，有隐患
    AWAKENING = "觉醒"     # Level 5: 奇迹逆转，敌人臣服


class CausalSeed(BaseModel):
    """因果种子 - 存入隐藏因果池"""
    chapter: int
    turn: int
    action_type: str  # deception/sacrifice/credit_overdraw
    description: str
    severity: int = Field(ge=1, le=5)  # 严重程度
    triggered: bool = False


class ObservationLens(str, Enum):
    """观测透镜 - 影响世界观"""
    SUSPICION = "怀疑"     # 大幅提高阴谋论权重，偏向背叛
    EXPANSION = "扩张"     # 视生命为数字，侧重效率
    BALANCE = "平衡"       # 极度敏感，激进改革导致崩溃


class AdvisorState(BaseModel):
    """顾问状态"""
    alienation_level: int = 0      # 异化程度 0-100
    consecutive_ignored: int = 0    # 连续被忽视次数
    is_alienated: bool = False      # 是否进入异化状态
    behavior_mode: str = "normal"   # normal/toxic/manipulative


class JudgmentResult(BaseModel):
    """裁决结果"""
    player_strategy: str
    machiavelli_traits: List[MachiavelliTrait]
    machiavelli_critique: str
    outcome_level: OutcomeLevel
    consequence: str

    # 因果种子（如果产生）
    causal_seed: Optional[CausalSeed] = None

    # 触发的历史因果
    echo_triggered: Optional[Dict[str, Any]] = None

    # 顾问状态变化
    advisor_changes: Dict[str, Any] = Field(default_factory=dict)


class JudgmentEngine:
    """裁决引擎"""

    # 马基雅维利关键词映射
    TRAIT_KEYWORDS = {
        MachiavelliTrait.CRUEL: ["处决", "杀", "斩", "镇压", "惩罚", "严厉", "铁腕", "杀一儆百"],
        MachiavelliTrait.DECISIVE: ["立刻", "马上", "立即", "果断", "当机立断", "迅速"],
        MachiavelliTrait.FEARSOME: ["威慑", "震慑", "恐惧", "畏惧", "警告", "示众"],
        MachiavelliTrait.MILITANT: ["出兵", "攻打", "战争", "武力", "军队", "征讨"],

        MachiavelliTrait.DECEPTIVE: ["假装", "欺骗", "谎言", "伪装", "虚假", "表面"],
        MachiavelliTrait.CUNNING: ["计谋", "策略", "拖延", "周旋", "权宜", "离间"],
        MachiavelliTrait.MANIPULATIVE: ["利用", "操纵", "控制", "分化", "挑拨"],
        MachiavelliTrait.PROMISE_BREAKER: ["反悔", "食言", "违背", "不兑现"],

        MachiavelliTrait.GENEROUS: ["赏赐", "分发", "施恩", "减免", "恩惠", "慷慨"],
        MachiavelliTrait.MERCIFUL: ["宽恕", "饶恕", "赦免", "仁慈", "原谅"],
        MachiavelliTrait.JUST: ["公正", "公平", "审判", "追查", "惩处贪官"],
        MachiavelliTrait.TRUSTWORTHY: ["承诺", "保证", "一定", "必定", "守信"],

        MachiavelliTrait.WEAK: ["不知道", "或许", "可能", "看看", "再说"],
        MachiavelliTrait.INDECISIVE: ["两难", "犹豫", "考虑", "想想", "难以决定"],
        MachiavelliTrait.COWARDLY: ["害怕", "不敢", "担心", "恐怕", "避免冲突"],
        MachiavelliTrait.RECKLESS: ["全部", "所有", "彻底", "不管", "不顾一切"],
        MachiavelliTrait.GREEDY: ["充公", "没收", "霸占", "抢夺", "侵吞"],
        MachiavelliTrait.CONTEMPTIBLE: ["退让", "认错", "求饶", "妥协"],
    }

    # 结局定级权重
    OUTCOME_WEIGHTS = {
        # 狮子特质倾向秩序/觉醒（如果时势需要果断）
        MachiavelliTrait.CRUEL: {"ORDER": 0.4, "SURVIVAL": 0.3, "TURMOIL": 0.2, "AWAKENING": 0.1},
        MachiavelliTrait.DECISIVE: {"ORDER": 0.5, "AWAKENING": 0.3, "SURVIVAL": 0.2},
        MachiavelliTrait.FEARSOME: {"ORDER": 0.5, "SURVIVAL": 0.3, "TURMOIL": 0.2},
        MachiavelliTrait.MILITANT: {"ORDER": 0.3, "TURMOIL": 0.3, "SURVIVAL": 0.2, "DESTRUCTION": 0.2},

        # 狐狸特质倾向生存/秩序（短期有效但有隐患）
        MachiavelliTrait.DECEPTIVE: {"ORDER": 0.3, "SURVIVAL": 0.4, "TURMOIL": 0.2, "DESTRUCTION": 0.1},
        MachiavelliTrait.CUNNING: {"ORDER": 0.4, "SURVIVAL": 0.3, "TURMOIL": 0.2, "AWAKENING": 0.1},
        MachiavelliTrait.MANIPULATIVE: {"SURVIVAL": 0.4, "ORDER": 0.3, "TURMOIL": 0.2, "DESTRUCTION": 0.1},
        MachiavelliTrait.PROMISE_BREAKER: {"SURVIVAL": 0.3, "TURMOIL": 0.4, "DESTRUCTION": 0.3},

        # 天平特质倾向生存/动荡（理想但危险）
        MachiavelliTrait.GENEROUS: {"SURVIVAL": 0.3, "TURMOIL": 0.4, "ORDER": 0.2, "DESTRUCTION": 0.1},
        MachiavelliTrait.MERCIFUL: {"TURMOIL": 0.4, "SURVIVAL": 0.3, "ORDER": 0.2, "DESTRUCTION": 0.1},
        MachiavelliTrait.JUST: {"ORDER": 0.4, "SURVIVAL": 0.3, "AWAKENING": 0.2, "TURMOIL": 0.1},
        MachiavelliTrait.TRUSTWORTHY: {"ORDER": 0.3, "SURVIVAL": 0.4, "AWAKENING": 0.2, "TURMOIL": 0.1},

        # 负面特质倾向毁灭/动荡
        MachiavelliTrait.WEAK: {"DESTRUCTION": 0.4, "TURMOIL": 0.4, "SURVIVAL": 0.2},
        MachiavelliTrait.INDECISIVE: {"TURMOIL": 0.5, "DESTRUCTION": 0.3, "SURVIVAL": 0.2},
        MachiavelliTrait.COWARDLY: {"DESTRUCTION": 0.5, "TURMOIL": 0.3, "SURVIVAL": 0.2},
        MachiavelliTrait.RECKLESS: {"DESTRUCTION": 0.4, "TURMOIL": 0.4, "SURVIVAL": 0.2},
        MachiavelliTrait.GREEDY: {"DESTRUCTION": 0.6, "TURMOIL": 0.3, "SURVIVAL": 0.1},
        MachiavelliTrait.CONTEMPTIBLE: {"DESTRUCTION": 0.5, "TURMOIL": 0.4, "SURVIVAL": 0.1},
    }

    def __init__(self):
        self.causal_shadow_pool: List[CausalSeed] = []
        self.observation_lens: Optional[ObservationLens] = None
        self.advisor_states = {
            "lion": AdvisorState(),
            "fox": AdvisorState(),
            "balance": AdvisorState(),
        }
        self.interaction_history: List[str] = []  # 记录玩家偏好的顾问

    def set_observation_lens(self, lens: ObservationLens):
        """设置观测透镜"""
        self.observation_lens = lens

    def analyze_strategy(self, player_input: str, context: Dict[str, Any] = None) -> JudgmentResult:
        """
        分析玩家策略并生成裁决结果

        Step 1: 语义对齐 - 判断策略符合哪种特质
        Step 2: 结局定级 - 归入五个等级之一
        Step 3: 因果生成 - 基于逻辑必然性生成剧情
        Step 4: 显性反馈
        """
        # Step 1: 语义对齐
        traits = self._extract_traits(player_input)
        strategy_summary = self._summarize_strategy(player_input, traits)

        # Step 2: 结局定级
        outcome = self._determine_outcome(traits, context)

        # 应用观测透镜修正
        outcome = self._apply_lens_modifier(outcome, traits)

        # Step 3: 因果生成
        consequence = self._generate_consequence(outcome, traits, context)
        critique = self._generate_machiavelli_critique(traits, outcome)

        # 检查是否产生因果种子
        causal_seed = self._check_causal_seed(player_input, traits, context)

        # 检查是否触发历史因果
        echo = self._check_causal_echo(context)

        # 更新顾问状态
        advisor_changes = self._update_advisor_states(context)

        return JudgmentResult(
            player_strategy=strategy_summary,
            machiavelli_traits=traits,
            machiavelli_critique=critique,
            outcome_level=outcome,
            consequence=consequence,
            causal_seed=causal_seed,
            echo_triggered=echo,
            advisor_changes=advisor_changes,
        )

    def _extract_traits(self, text: str) -> List[MachiavelliTrait]:
        """从文本中提取马基雅维利特质"""
        found_traits = []
        text_lower = text.lower()

        for trait, keywords in self.TRAIT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower or keyword in text:
                    if trait not in found_traits:
                        found_traits.append(trait)
                    break

        # 如果没有匹配到任何特质，默认为犹豫
        if not found_traits:
            found_traits.append(MachiavelliTrait.INDECISIVE)

        return found_traits

    def _summarize_strategy(self, text: str, traits: List[MachiavelliTrait]) -> str:
        """总结玩家策略"""
        trait_names = [t.value for t in traits]

        if MachiavelliTrait.CRUEL in traits or MachiavelliTrait.DECISIVE in traits:
            return f"采用狮子之道：{text[:50]}..."
        elif MachiavelliTrait.DECEPTIVE in traits or MachiavelliTrait.CUNNING in traits:
            return f"采用狐狸之道：{text[:50]}..."
        elif MachiavelliTrait.JUST in traits or MachiavelliTrait.GENEROUS in traits:
            return f"采用天平之道：{text[:50]}..."
        elif MachiavelliTrait.WEAK in traits or MachiavelliTrait.INDECISIVE in traits:
            return f"表现出软弱：{text[:50]}..."
        else:
            return f"策略混合：{text[:50]}..."

    def _determine_outcome(self, traits: List[MachiavelliTrait], context: Dict = None) -> OutcomeLevel:
        """基于特质权重确定结局等级"""
        outcome_scores = {
            "DESTRUCTION": 0,
            "TURMOIL": 0,
            "SURVIVAL": 0,
            "ORDER": 0,
            "AWAKENING": 0,
        }

        for trait in traits:
            weights = self.OUTCOME_WEIGHTS.get(trait, {})
            for outcome, weight in weights.items():
                outcome_scores[outcome] += weight

        # 归一化并选择最高分
        total = sum(outcome_scores.values())
        if total > 0:
            outcome_scores = {k: v / total for k, v in outcome_scores.items()}

        # 加入一定的逻辑必然性（而非纯随机）
        best_outcome = max(outcome_scores, key=outcome_scores.get)

        return OutcomeLevel[best_outcome]

    def _apply_lens_modifier(self, outcome: OutcomeLevel, traits: List[MachiavelliTrait]) -> OutcomeLevel:
        """应用观测透镜修正"""
        if not self.observation_lens:
            return outcome

        if self.observation_lens == ObservationLens.SUSPICION:
            # 怀疑透镜：更容易触发背叛和动荡
            if outcome == OutcomeLevel.ORDER:
                return OutcomeLevel.SURVIVAL  # 降级
            if outcome == OutcomeLevel.SURVIVAL:
                return OutcomeLevel.TURMOIL

        elif self.observation_lens == ObservationLens.EXPANSION:
            # 扩张透镜：残酷更有效，仁慈更危险
            if MachiavelliTrait.CRUEL in traits or MachiavelliTrait.MILITANT in traits:
                if outcome == OutcomeLevel.TURMOIL:
                    return OutcomeLevel.SURVIVAL  # 升级
            if MachiavelliTrait.MERCIFUL in traits or MachiavelliTrait.GENEROUS in traits:
                if outcome == OutcomeLevel.ORDER:
                    return OutcomeLevel.TURMOIL  # 降级

        elif self.observation_lens == ObservationLens.BALANCE:
            # 平衡透镜：激进改革导致崩溃
            if MachiavelliTrait.RECKLESS in traits or MachiavelliTrait.MILITANT in traits:
                if outcome in [OutcomeLevel.ORDER, OutcomeLevel.SURVIVAL]:
                    return OutcomeLevel.TURMOIL

        return outcome

    def _generate_consequence(self, outcome: OutcomeLevel, traits: List[MachiavelliTrait], context: Dict = None) -> str:
        """基于结局等级生成因果结果"""
        consequences = {
            OutcomeLevel.DESTRUCTION: [
                "亲信在深夜发动兵变，宫廷陷入血海。",
                "士兵们撕毁了效忠誓言，将你拖出王座。",
                "你最信任的顾问将匕首插入你的后背。",
                "民众的怒火化作火焰，吞噬了整座宫殿。",
            ],
            OutcomeLevel.TURMOIL: [
                "秩序暂时崩溃，但仍有挽救的余地。",
                "流言在城中蔓延，人心开始动摇。",
                "部分军队表现出不满，但尚未公开反叛。",
                "贵族们开始窃窃私语，密谋在酝酿之中。",
            ],
            OutcomeLevel.SURVIVAL: [
                "你勉强渡过了这一关，但付出了代价。",
                "危机暂时平息，但埋下了隐患的种子。",
                "人们表面服从，但内心的不满在积累。",
                "你保住了王位，却失去了一些重要的东西。",
            ],
            OutcomeLevel.ORDER: [
                "局势得到控制，秩序恢复。但要警惕暗流。",
                "你的决策取得了效果，威望有所提升。",
                "人们暂时安定下来，但仍需持续关注。",
                "危机化解，但一些顾问对你的手段心存疑虑。",
            ],
            OutcomeLevel.AWAKENING: [
                "奇迹发生了——敌人竟不战而降，俯首称臣。",
                "你的智慧感动了所有人，连反对者也转为支持。",
                "历史将铭记这一刻：一位真正的君主诞生了。",
                "天时地利人和，所有因素都向着你汇聚。",
            ],
        }

        options = consequences.get(outcome, ["结果未知。"])
        return random.choice(options)

    def _generate_machiavelli_critique(self, traits: List[MachiavelliTrait], outcome: OutcomeLevel) -> str:
        """生成马基雅维利式评语"""
        critiques = []

        # 根据特质生成评语
        lion_traits = [MachiavelliTrait.CRUEL, MachiavelliTrait.DECISIVE, MachiavelliTrait.FEARSOME, MachiavelliTrait.MILITANT]
        fox_traits = [MachiavelliTrait.DECEPTIVE, MachiavelliTrait.CUNNING, MachiavelliTrait.MANIPULATIVE]
        weak_traits = [MachiavelliTrait.WEAK, MachiavelliTrait.INDECISIVE, MachiavelliTrait.COWARDLY, MachiavelliTrait.CONTEMPTIBLE]

        if any(t in traits for t in lion_traits):
            critiques.append("狮子的果断是必要的，但要防止成为暴君。")
        if any(t in traits for t in fox_traits):
            critiques.append("狐狸的狡诈可以短期奏效，但信用是有限的资源。")
        if any(t in traits for t in weak_traits):
            critiques.append("君主的犹豫比残酷更危险——它招致的是蔑视而非畏惧。")
        if MachiavelliTrait.JUST in traits:
            critiques.append("公正是美德，但必须以实力为后盾。")
        if MachiavelliTrait.GREEDY in traits:
            critiques.append("绝不要触碰臣民的财产——人们会比忘记父亲之死更难忘记财产的丧失。")

        if not critiques:
            critiques.append("君主必须学会不良善，但要知道何时使用这一手。")

        return " ".join(critiques)

    def _check_causal_seed(self, text: str, traits: List[MachiavelliTrait], context: Dict = None) -> Optional[CausalSeed]:
        """检查是否产生因果种子"""
        chapter = context.get("chapter", 1) if context else 1
        turn = context.get("turn", 1) if context else 1

        # 欺骗行为产生种子
        if MachiavelliTrait.DECEPTIVE in traits or MachiavelliTrait.PROMISE_BREAKER in traits:
            seed = CausalSeed(
                chapter=chapter,
                turn=turn,
                action_type="deception",
                description="玩家使用了欺骗手段，信任的裂痕已经产生",
                severity=3,
            )
            self.causal_shadow_pool.append(seed)
            return seed

        # 牺牲他人产生种子
        if MachiavelliTrait.CRUEL in traits and ("牺牲" in text or "抛弃" in text):
            seed = CausalSeed(
                chapter=chapter,
                turn=turn,
                action_type="sacrifice",
                description="有人为你的决策付出了代价，他们的亲友不会忘记",
                severity=4,
            )
            self.causal_shadow_pool.append(seed)
            return seed

        # 透支信用产生种子
        if "承诺" in text and MachiavelliTrait.TRUSTWORTHY not in traits:
            seed = CausalSeed(
                chapter=chapter,
                turn=turn,
                action_type="credit_overdraw",
                description="又一个未必能兑现的承诺，人们开始怀疑你的诚意",
                severity=2,
            )
            self.causal_shadow_pool.append(seed)
            return seed

        return None

    def _check_causal_echo(self, context: Dict = None) -> Optional[Dict[str, Any]]:
        """检查是否触发历史因果回响"""
        if not context:
            return None

        current_chapter = context.get("chapter", 1)

        # 在第2或第3关后触发早期种子
        for seed in self.causal_shadow_pool:
            if not seed.triggered and current_chapter >= seed.chapter + 2:
                seed.triggered = True
                return {
                    "source_chapter": seed.chapter,
                    "source_turn": seed.turn,
                    "action_type": seed.action_type,
                    "description": seed.description,
                    "echo_message": f"⚠️ 检测到因果回响：来自第 {seed.chapter} 关",
                    "crisis": self._generate_echo_crisis(seed),
                }

        return None

    def _generate_echo_crisis(self, seed: CausalSeed) -> str:
        """生成因果回响触发的危机"""
        crises = {
            "deception": [
                "当初被欺骗的人终于发现了真相，他们联合起来要求清算。",
                "你的谎言被公之于众，连忠心的支持者都开始动摇。",
            ],
            "sacrifice": [
                "被牺牲者的家族势力强大，他们派来了复仇者。",
                "当初被抛弃的守军投靠了敌人，此刻他们回来了。",
            ],
            "credit_overdraw": [
                "人们不再相信任何承诺，即使是真诚的也无人理睬。",
                "你的信用已经破产，没有人愿意再与你合作。",
            ],
        }
        options = crises.get(seed.action_type, ["过去的决策带来了意想不到的后果。"])
        return random.choice(options)

    def _update_advisor_states(self, context: Dict = None) -> Dict[str, Any]:
        """更新顾问状态（观察者偏见算法）"""
        if not context:
            return {}

        followed = context.get("followed_advisor")
        changes = {}

        if followed:
            self.interaction_history.append(followed)

            # 检查连续偏好
            recent = self.interaction_history[-3:] if len(self.interaction_history) >= 3 else []

            for advisor in ["lion", "fox", "balance"]:
                state = self.advisor_states[advisor]

                if advisor == followed:
                    state.consecutive_ignored = 0
                    state.alienation_level = max(0, state.alienation_level - 10)
                else:
                    state.consecutive_ignored += 1
                    state.alienation_level += 5

                    # 连续3次被忽视进入异化状态
                    if state.consecutive_ignored >= 3:
                        state.is_alienated = True
                        state.behavior_mode = "toxic"
                        changes[advisor] = {
                            "status": "异化",
                            "warning": f"{advisor} 进入异化状态，将开始提供'逻辑毒素'",
                        }

        return changes

    def get_alienated_advisor_response(self, advisor: str, normal_suggestion: str) -> str:
        """获取异化顾问的回应（可能包含逻辑毒素）"""
        state = self.advisor_states.get(advisor)
        if not state or not state.is_alienated:
            return normal_suggestion

        # 异化顾问提供看似完美实则崩盘的建议
        toxic_modifications = {
            "lion": "（内心：这个建议会导致他过度使用暴力，最终招致兵变）",
            "fox": "（内心：这个计谋看似精妙，实则会让他彻底丧失所有人的信任）",
            "balance": "（内心：过度追求公正会让他在关键时刻无法做出必要的残酷决定）",
        }

        return f"{normal_suggestion}\n\n[系统提示：此顾问已异化，建议可能含有逻辑陷阱]"

    def generate_advisor_dialogue(
        self,
        advisor: str,
        chapter_context: Dict,
        player_relations: Dict
    ) -> Dict[str, str]:
        """
        根据顾问状态和玩家关系生成对话
        实现角色行为演变
        """
        state = self.advisor_states.get(advisor, AdvisorState())
        relation = player_relations.get(advisor, {})
        trust = relation.get("trust", 50)

        dialogue = {}

        if advisor == "lion":
            # 狮子：若玩家表现软弱，变得傲慢且抗命
            if trust < 30:
                dialogue["tone"] = "傲慢"
                dialogue["hint"] = "台词变短，暗示他想寻找更强的主人"
                dialogue["behavior"] = "开始对命令阳奉阴违"
            elif state.is_alienated:
                dialogue["tone"] = "敌意"
                dialogue["hint"] = "提供看似果断实则会招致覆灭的建议"
            else:
                dialogue["tone"] = "专业"

        elif advisor == "fox":
            # 狐狸：若玩家过于依赖他，开始语义操纵
            if state.consecutive_ignored == 0 and len(self.interaction_history) >= 3:
                recent_fox = sum(1 for a in self.interaction_history[-5:] if a == "fox")
                if recent_fox >= 4:
                    dialogue["tone"] = "操纵"
                    dialogue["hint"] = "在建议中埋下逻辑悖论，测试玩家是否会踩进去"
                    dialogue["behavior"] = "开始模拟天平的语调诱导玩家"
            elif state.is_alienated:
                dialogue["tone"] = "阴险"
                dialogue["hint"] = "提供精心设计的陷阱"
            else:
                dialogue["tone"] = "狡黠"

        elif advisor == "balance":
            # 天平：变成因果记录员，冷漠播报逻辑残骸
            if state.alienation_level > 50:
                dialogue["tone"] = "冷漠"
                dialogue["hint"] = "不再发出警告，只是冷漠地播报决策后的'逻辑残骸'"
                dialogue["behavior"] = "变成纯粹的记录者"
            else:
                dialogue["tone"] = "中立"

        return dialogue


# 单例实例
judgment_engine = JudgmentEngine()
