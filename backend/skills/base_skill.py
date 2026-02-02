"""
Skill 基类
定义审计引擎的通用接口
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Optional
from models.game_state import GameState


class AuditResult(BaseModel):
    """审计结果"""

    skill_name: str
    score: float = Field(ge=-100, le=100, description="审计评分 -100到100")

    # 数值影响
    delta_authority: float = 0.0
    delta_fear: float = 0.0
    delta_love: float = 0.0

    # 关系影响
    delta_trust: float = 0.0
    delta_hatred: float = 0.0

    # 审计报告
    assessment: str = ""  # 评估描述
    warnings: list[str] = Field(default_factory=list)  # 警告列表

    # 检测到的特征
    detected_keywords: list[str] = Field(default_factory=list)
    detected_intent: Optional[str] = None
    detected_tone: Optional[str] = None

    # 是否触发特殊条件
    trigger_event: bool = False
    event_type: Optional[str] = None


class BaseSkill(ABC):
    """Skill 基类"""

    name: str = "base"
    description: str = "基础审计技能"

    # 关键词库
    strong_action_keywords: list[str] = []
    weak_action_keywords: list[str] = []

    def __init__(self):
        pass

    @abstractmethod
    async def audit(
        self,
        player_input: str,
        parsed_intent: dict,
        game_state: GameState,
    ) -> AuditResult:
        """
        执行审计

        Args:
            player_input: 玩家原始输入
            parsed_intent: NLP解析后的意图结构
            game_state: 当前游戏状态

        Returns:
            AuditResult: 审计结果
        """
        pass

    def detect_keywords(self, text: str, keywords: list[str]) -> list[str]:
        """检测文本中的关键词"""
        detected = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                detected.append(keyword)
        return detected

    def calculate_keyword_score(
        self,
        text: str,
        positive_keywords: list[str],
        negative_keywords: list[str],
        positive_weight: float = 10.0,
        negative_weight: float = -10.0,
    ) -> tuple[float, list[str]]:
        """
        计算关键词得分

        Returns:
            (score, detected_keywords)
        """
        score = 0.0
        detected = []

        for kw in positive_keywords:
            if kw in text:
                score += positive_weight
                detected.append(f"+{kw}")

        for kw in negative_keywords:
            if kw in text:
                score += negative_weight
                detected.append(f"-{kw}")

        return score, detected

    @abstractmethod
    def get_character_prompt(self) -> str:
        """获取角色人设提示词"""
        pass

    @abstractmethod
    def generate_response_prompt(self, audit_result: AuditResult) -> str:
        """生成对话响应的提示词"""
        pass
