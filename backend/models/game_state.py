"""
游戏状态模型
管理玩家与三机器人的关系、对话历史和游戏进程
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

from .power_vector import PowerVector


class RobotType(str, Enum):
    """机器人类型"""

    LION = "lion"  # 狮子 - 战略重心审计
    FOX = "fox"  # 狐狸 - 语义一致性审计
    BALANCE = "balance"  # 天平 - 社会熵增预警


class RobotRelation(BaseModel):
    """玩家与机器人的关系"""

    trust: float = Field(
        default=0.0,
        ge=-100.0,
        le=100.0,
        description="信任度: -100(完全敌对) 到 100(完全信任)",
    )
    hatred: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="仇恨度: 0(无仇恨) 到 100(深仇大恨)",
    )

    def apply_delta(self, delta_trust: float, delta_hatred: float) -> "RobotRelation":
        """应用关系变化"""
        return RobotRelation(
            trust=max(-100.0, min(100.0, self.trust + delta_trust)),
            hatred=max(0.0, min(100.0, self.hatred + delta_hatred)),
        )

    def is_hostile(self) -> bool:
        """是否处于敌对状态"""
        return self.trust < -50 or self.hatred > 70


class DialogueEntry(BaseModel):
    """对话记录条目"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    turn: int
    speaker: str  # "player" 或 RobotType
    content: str
    target: Optional[str] = None  # 对话目标（用于狐狸的一致性检测）
    intent: Optional[str] = None  # 解析出的意图
    promises: list[str] = Field(default_factory=list)  # 承诺列表


class Promise(BaseModel):
    """玩家承诺记录（用于狐狸审计）"""

    turn: int
    target: str  # 承诺对象
    content: str  # 承诺内容
    keywords: list[str] = Field(default_factory=list)


class GameState(BaseModel):
    """完整游戏状态"""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 权力三维向量
    power: PowerVector = Field(default_factory=PowerVector)

    # 与三机器人的关系
    relations: dict[str, RobotRelation] = Field(
        default_factory=lambda: {
            RobotType.LION.value: RobotRelation(),
            RobotType.FOX.value: RobotRelation(),
            RobotType.BALANCE.value: RobotRelation(),
        }
    )

    # 游戏回合
    turn: int = 0

    # 对话历史
    history: list[DialogueEntry] = Field(default_factory=list)

    # 玩家承诺记录（狐狸用于检测矛盾）
    promises: list[Promise] = Field(default_factory=list)

    # 待处理事件
    pending_events: list[str] = Field(default_factory=list)

    # 游戏是否结束
    game_over: bool = False
    game_over_reason: Optional[str] = None

    def add_dialogue(
        self,
        speaker: str,
        content: str,
        target: Optional[str] = None,
        intent: Optional[str] = None,
        promises: Optional[list[str]] = None,
    ) -> DialogueEntry:
        """添加对话记录"""
        entry = DialogueEntry(
            turn=self.turn,
            speaker=speaker,
            content=content,
            target=target,
            intent=intent,
            promises=promises or [],
        )
        self.history.append(entry)
        self.updated_at = datetime.now()
        return entry

    def add_promise(self, target: str, content: str, keywords: list[str]) -> Promise:
        """记录玩家承诺"""
        promise = Promise(turn=self.turn, target=target, content=content, keywords=keywords)
        self.promises.append(promise)
        # 只保留最近10轮的承诺
        recent_promises = [p for p in self.promises if self.turn - p.turn <= 10]
        self.promises = recent_promises
        return promise

    def get_recent_history(self, n: int = 10) -> list[DialogueEntry]:
        """获取最近n轮对话"""
        return self.history[-n * 2 :] if len(self.history) > n * 2 else self.history

    def get_promises_to_target(self, target: str) -> list[Promise]:
        """获取对某目标的所有承诺"""
        return [p for p in self.promises if p.target == target]

    def next_turn(self):
        """进入下一回合"""
        self.turn += 1
        self.updated_at = datetime.now()

    def end_game(self, reason: str):
        """结束游戏"""
        self.game_over = True
        self.game_over_reason = reason
        self.updated_at = datetime.now()

    def to_summary(self) -> dict:
        """生成游戏状态摘要"""
        return {
            "session_id": self.session_id,
            "turn": self.turn,
            "power": self.power.to_display(),
            "relations": {
                robot: {
                    "trust": round(rel.trust, 1),
                    "hatred": round(rel.hatred, 1),
                    "is_hostile": rel.is_hostile(),
                }
                for robot, rel in self.relations.items()
            },
            "warnings": self.power.get_status_warnings(),
            "game_over": self.game_over,
            "game_over_reason": self.game_over_reason,
        }
