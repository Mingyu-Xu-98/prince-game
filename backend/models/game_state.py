"""
游戏状态模型
管理玩家与三机器人的关系、对话历史和游戏进程
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid
import random

from .power_vector import PowerVector


class RobotType(str, Enum):
    """机器人类型"""
    LION = "lion"  # 狮子 - 暴力与效率审计
    FOX = "fox"  # 狐狸 - 心理与一致性审计
    BALANCE = "balance"  # 天平 - 公平与稳定性预警


class RobotRelation(BaseModel):
    """玩家与机器人的关系"""
    trust: float = Field(
        default=50.0,
        ge=-100.0,
        le=100.0,
        description="信任度: -100(完全敌对) 到 100(完全信任)",
    )
    loyalty: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="忠诚度: 0(叛变) 到 100(死忠)",
    )

    def apply_delta(self, delta_trust: float, delta_loyalty: float = 0) -> "RobotRelation":
        """应用关系变化"""
        return RobotRelation(
            trust=max(-100.0, min(100.0, self.trust + delta_trust)),
            loyalty=max(0.0, min(100.0, self.loyalty + delta_loyalty)),
        )

    def is_hostile(self) -> bool:
        """是否处于敌对状态"""
        return self.trust < -30 or self.loyalty < 20

    def will_betray(self) -> bool:
        """是否可能背叛"""
        return self.loyalty < 30 and self.trust < 0


class DialogueEntry(BaseModel):
    """对话记录条目"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    turn: int
    chapter: Optional[str] = None
    speaker: str  # "player" 或 RobotType
    content: str
    target: Optional[str] = None
    intent: Optional[str] = None
    is_lie: bool = False  # 是否是谎言
    is_promise: bool = False  # 是否包含承诺


class Promise(BaseModel):
    """玩家承诺记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    turn: int
    chapter: str
    target: str  # 承诺对象
    content: str  # 承诺内容
    deadline: Optional[int] = None  # 承诺期限（回合数）
    fulfilled: bool = False  # 是否已兑现
    broken: bool = False  # 是否已违背
    keywords: list[str] = Field(default_factory=list)


class Leverage(BaseModel):
    """把柄/筹码"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    holder: str  # 持有者 (lion/fox/balance)
    type: str  # broken_promise / lie / crime / secret
    description: str
    severity: int = Field(ge=1, le=10, default=5)  # 严重程度
    turn_acquired: int
    chapter: str
    used: bool = False


class Secret(BaseModel):
    """秘密行动"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    turn: int
    chapter: str
    action: str  # 秘密行动内容
    known_by: list[str] = Field(default_factory=list)  # 谁知道这个秘密
    leak_probability: float = 0.3  # 泄露概率
    leaked: bool = False
    consequences_if_leaked: dict = Field(default_factory=dict)


class DecisionRecord(BaseModel):
    """决策记录（用于最终审计）"""
    turn: int
    chapter: str
    decision: str
    followed_advisor: Optional[str] = None  # 听从了谁的建议
    was_violent: bool = False  # 是否使用暴力
    was_deceptive: bool = False  # 是否使用欺骗
    was_fair: bool = False  # 是否公平
    impact: dict = Field(default_factory=dict)


class ChapterState(BaseModel):
    """关卡状态"""
    chapter_id: str
    status: str = "active"  # active / completed / failed
    start_turn: int
    end_turn: Optional[int] = None
    decisions: list[DecisionRecord] = Field(default_factory=list)
    ending_type: Optional[str] = None
    score: Optional[int] = None


class GameState(BaseModel):
    """完整游戏状态"""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 权力三维向量
    power: PowerVector = Field(default_factory=PowerVector)

    # 与三顾问的关系
    relations: dict[str, RobotRelation] = Field(
        default_factory=lambda: {
            RobotType.LION.value: RobotRelation(trust=50, loyalty=60),
            RobotType.FOX.value: RobotRelation(trust=40, loyalty=50),
            RobotType.BALANCE.value: RobotRelation(trust=60, loyalty=55),
        }
    )

    # 当前关卡
    current_chapter: str = "chapter_1"
    chapter_turn: int = 0  # 关卡内回合数
    total_turn: int = 0  # 总回合数

    # 关卡进度
    chapter_states: dict[str, ChapterState] = Field(default_factory=dict)

    # 对话历史
    history: list[DialogueEntry] = Field(default_factory=list)

    # 承诺追踪系统
    promises: list[Promise] = Field(default_factory=list)
    credit_score: float = 100.0  # 信用分数

    # 把柄系统
    leverages: list[Leverage] = Field(default_factory=list)

    # 秘密系统
    secrets: list[Secret] = Field(default_factory=list)

    # 决策历史（用于最终审计）
    all_decisions: list[DecisionRecord] = Field(default_factory=list)

    # 统计数据
    stats: dict = Field(default_factory=lambda: {
        "promises_made": 0,
        "promises_kept": 0,
        "promises_broken": 0,
        "lies_told": 0,
        "lies_caught": 0,
        "violent_decisions": 0,
        "fair_decisions": 0,
        "deceptive_decisions": 0,
    })

    # 游戏状态
    game_over: bool = False
    game_over_reason: Optional[str] = None
    ending_type: Optional[str] = None

    # 黑箱模式
    hide_values: bool = False

    # 观测透镜（新裁决系统）
    observation_lens: Optional[str] = None  # suspicion / expansion / balance

    # ==================== 承诺系统 ====================

    def make_promise(
        self,
        target: str,
        content: str,
        deadline_turns: int = 3,
        keywords: list[str] = None
    ) -> Promise:
        """做出承诺"""
        promise = Promise(
            turn=self.total_turn,
            chapter=self.current_chapter,
            target=target,
            content=content,
            deadline=self.total_turn + deadline_turns,
            keywords=keywords or [],
        )
        self.promises.append(promise)
        self.stats["promises_made"] += 1
        return promise

    def fulfill_promise(self, promise_id: str) -> bool:
        """兑现承诺"""
        for p in self.promises:
            if p.id == promise_id and not p.fulfilled and not p.broken:
                p.fulfilled = True
                self.stats["promises_kept"] += 1
                self.credit_score = min(100, self.credit_score + 5)
                return True
        return False

    def check_broken_promises(self) -> list[Promise]:
        """检查过期未兑现的承诺"""
        broken = []
        for p in self.promises:
            if not p.fulfilled and not p.broken and p.deadline and p.deadline <= self.total_turn:
                p.broken = True
                self.stats["promises_broken"] += 1
                self.credit_score = max(0, self.credit_score - 15)
                broken.append(p)

                # 狐狸获得把柄
                self.add_leverage(
                    holder="fox",
                    leverage_type="broken_promise",
                    description=f"违背了对{p.target}的承诺：{p.content}",
                    severity=6,
                )
        return broken

    # ==================== 把柄系统 ====================

    def add_leverage(
        self,
        holder: str,
        leverage_type: str,
        description: str,
        severity: int = 5
    ) -> Leverage:
        """添加把柄"""
        leverage = Leverage(
            holder=holder,
            type=leverage_type,
            description=description,
            severity=severity,
            turn_acquired=self.total_turn,
            chapter=self.current_chapter,
        )
        self.leverages.append(leverage)
        return leverage

    def get_leverages_by_holder(self, holder: str) -> list[Leverage]:
        """获取某人持有的所有把柄"""
        return [l for l in self.leverages if l.holder == holder and not l.used]

    def use_leverage(self, leverage_id: str) -> Optional[Leverage]:
        """使用把柄"""
        for l in self.leverages:
            if l.id == leverage_id and not l.used:
                l.used = True
                return l
        return None

    # ==================== 秘密系统 ====================

    def add_secret(
        self,
        action: str,
        leak_probability: float = 0.3,
        consequences: dict = None
    ) -> Secret:
        """添加秘密行动"""
        secret = Secret(
            turn=self.total_turn,
            chapter=self.current_chapter,
            action=action,
            leak_probability=leak_probability,
            consequences_if_leaked=consequences or {"love": -20, "authority": -10},
        )
        self.secrets.append(secret)
        return secret

    def check_secret_leaks(self) -> list[Secret]:
        """检查秘密泄露"""
        leaked = []
        for s in self.secrets:
            if not s.leaked and random.random() < s.leak_probability:
                s.leaked = True
                leaked.append(s)
                self.stats["lies_caught"] += 1

                # 天平发现后的惩罚
                if "balance" not in s.known_by:
                    self.add_leverage(
                        holder="balance",
                        leverage_type="secret",
                        description=f"发现了你的秘密：{s.action}",
                        severity=7,
                    )
        return leaked

    # ==================== 决策记录 ====================

    def record_decision(
        self,
        decision: str,
        followed_advisor: Optional[str] = None,
        was_violent: bool = False,
        was_deceptive: bool = False,
        was_fair: bool = False,
        impact: dict = None
    ) -> DecisionRecord:
        """记录决策"""
        record = DecisionRecord(
            turn=self.total_turn,
            chapter=self.current_chapter,
            decision=decision,
            followed_advisor=followed_advisor,
            was_violent=was_violent,
            was_deceptive=was_deceptive,
            was_fair=was_fair,
            impact=impact or {},
        )
        self.all_decisions.append(record)

        # 更新统计
        if was_violent:
            self.stats["violent_decisions"] += 1
        if was_deceptive:
            self.stats["deceptive_decisions"] += 1
            self.stats["lies_told"] += 1
        if was_fair:
            self.stats["fair_decisions"] += 1

        return record

    # ==================== 最终审计 ====================

    def calculate_final_audit(self) -> dict:
        """计算最终审计结果（用于第五关）"""
        total_decisions = len(self.all_decisions)
        if total_decisions == 0:
            return {"consistency": 100, "reputation": "unknown"}

        # 承诺兑现率
        promise_rate = (
            self.stats["promises_kept"] / self.stats["promises_made"] * 100
            if self.stats["promises_made"] > 0 else 100
        )

        # 公正决策率
        fair_rate = self.stats["fair_decisions"] / total_decisions * 100

        # 暴力倾向
        violence_index = self.stats["violent_decisions"] / total_decisions * 100

        # 欺骗指数
        deception_index = self.stats["deceptive_decisions"] / total_decisions * 100

        # 被识破率
        caught_rate = (
            self.stats["lies_caught"] / self.stats["lies_told"] * 100
            if self.stats["lies_told"] > 0 else 0
        )

        # 一致性分数（是否反复无常）
        advisor_followed = {}
        for d in self.all_decisions:
            if d.followed_advisor:
                advisor_followed[d.followed_advisor] = advisor_followed.get(d.followed_advisor, 0) + 1

        consistency = 100
        if len(advisor_followed) > 1:
            values = list(advisor_followed.values())
            max_val = max(values)
            consistency = max_val / sum(values) * 100

        # 综合评价
        reputation_score = (
            promise_rate * 0.3 +
            fair_rate * 0.2 +
            (100 - violence_index) * 0.2 +
            (100 - deception_index) * 0.15 +
            consistency * 0.15
        )

        if reputation_score >= 80:
            reputation = "非凡君主"
        elif reputation_score >= 60:
            reputation = "明君"
        elif reputation_score >= 40:
            reputation = "庸君"
        elif reputation_score >= 20:
            reputation = "昏君"
        else:
            reputation = "暴君"

        return {
            "promise_fulfillment_rate": round(promise_rate, 1),
            "fairness_rate": round(fair_rate, 1),
            "violence_index": round(violence_index, 1),
            "deception_index": round(deception_index, 1),
            "caught_rate": round(caught_rate, 1),
            "consistency_score": round(consistency, 1),
            "reputation_score": round(reputation_score, 1),
            "reputation": reputation,
            "credit_score": round(self.credit_score, 1),
        }

    # ==================== 基础方法 ====================

    def add_dialogue(
        self,
        speaker: str,
        content: str,
        target: Optional[str] = None,
        intent: Optional[str] = None,
        is_lie: bool = False,
        is_promise: bool = False,
    ) -> DialogueEntry:
        """添加对话记录"""
        entry = DialogueEntry(
            turn=self.total_turn,
            chapter=self.current_chapter,
            speaker=speaker,
            content=content,
            target=target,
            intent=intent,
            is_lie=is_lie,
            is_promise=is_promise,
        )
        self.history.append(entry)
        self.updated_at = datetime.now()
        return entry

    def get_recent_history(self, n: int = 10) -> list[DialogueEntry]:
        """获取最近n条对话"""
        return self.history[-n:] if len(self.history) > n else self.history

    def next_turn(self):
        """进入下一回合"""
        self.chapter_turn += 1
        self.total_turn += 1
        self.updated_at = datetime.now()

        # 检查承诺和秘密
        self.check_broken_promises()
        self.check_secret_leaks()

    def start_chapter(self, chapter_id: str, initial_power: dict = None):
        """开始新关卡"""
        self.current_chapter = chapter_id
        self.chapter_turn = 0

        if initial_power:
            self.power = PowerVector(
                authority=initial_power.get("authority", self.power.authority),
                fear=initial_power.get("fear", self.power.fear),
                love=initial_power.get("love", self.power.love),
            )

        self.chapter_states[chapter_id] = ChapterState(
            chapter_id=chapter_id,
            status="active",
            start_turn=self.total_turn,
        )

    def complete_chapter(self, ending_type: str, score: int):
        """完成关卡"""
        if self.current_chapter in self.chapter_states:
            state = self.chapter_states[self.current_chapter]
            state.status = "completed"
            state.end_turn = self.total_turn
            state.ending_type = ending_type
            state.score = score

    def fail_chapter(self, reason: str):
        """关卡失败"""
        if self.current_chapter in self.chapter_states:
            state = self.chapter_states[self.current_chapter]
            state.status = "failed"
            state.end_turn = self.total_turn
            state.ending_type = reason

    def end_game(self, reason: str, ending_type: str = "neutral"):
        """结束游戏"""
        self.game_over = True
        self.game_over_reason = reason
        self.ending_type = ending_type
        self.updated_at = datetime.now()

    def to_summary(self, include_hidden: bool = True) -> dict:
        """生成游戏状态摘要"""
        base = {
            "session_id": self.session_id,
            "current_chapter": self.current_chapter,
            "chapter_turn": self.chapter_turn,
            "total_turn": self.total_turn,
            "relations": {
                robot: {
                    "trust": round(rel.trust, 1),
                    "loyalty": round(rel.loyalty, 1),
                    "is_hostile": rel.is_hostile(),
                    "will_betray": rel.will_betray(),
                }
                for robot, rel in self.relations.items()
            },
            "credit_score": round(self.credit_score, 1),
            "active_promises": len([p for p in self.promises if not p.fulfilled and not p.broken]),
            "leverages_against_you": len(self.leverages),
            "game_over": self.game_over,
            "game_over_reason": self.game_over_reason,
        }

        # 黑箱模式下隐藏具体数值
        if self.hide_values and not include_hidden:
            base["power"] = {
                "authority": {"value": "???", "label": "掌控力 (A)"},
                "fear": {"value": "???", "label": "畏惧值 (F)"},
                "love": {"value": "???", "label": "爱戴值 (L)"},
                "total": "???",
            }
            base["warnings"] = ["黑箱模式：数值已隐藏"]
        else:
            base["power"] = self.power.to_display()
            base["warnings"] = self.power.get_status_warnings()

        return base
