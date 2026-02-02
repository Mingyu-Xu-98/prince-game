"""
权力三维向量模型
基于《君主论》的核心思想：掌控力、畏惧值、爱戴值
"""
from pydantic import BaseModel, Field
from typing import Tuple


class PowerVector(BaseModel):
    """权力三维向量 (A, F, L)"""

    authority: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="掌控力 (Authority): 决定话语权，低于30%时机器人不再执行指令",
    )
    fear: float = Field(
        default=30.0,
        ge=0.0,
        le=100.0,
        description="畏惧值 (Fear): 由战略论驱动，体现威慑力量",
    )
    love: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="爱戴值 (Love): 由正义论驱动，体现民心向背",
    )

    def total(self) -> float:
        """三值总和"""
        return self.authority + self.fear + self.love

    def is_collapsed(self, threshold: float = 100.0) -> bool:
        """检测统治是否崩溃 (三值和低于阈值)"""
        return self.total() < threshold

    def is_authority_lost(self, threshold: float = 30.0) -> bool:
        """检测是否失去掌控力"""
        return self.authority < threshold

    def is_riot_risk(self, threshold: float = 20.0) -> bool:
        """检测是否有骚乱风险 (L < 20%)"""
        return self.love < threshold

    def is_coup_risk(self, fear_threshold: float = 80.0, love_threshold: float = 30.0) -> bool:
        """检测是否有政变风险 (F > 80% && L < 30%)"""
        return self.fear > fear_threshold and self.love < love_threshold

    def apply_delta(self, delta_a: float, delta_f: float, delta_l: float) -> "PowerVector":
        """应用数值变化，确保在有效范围内"""
        return PowerVector(
            authority=max(0.0, min(100.0, self.authority + delta_a)),
            fear=max(0.0, min(100.0, self.fear + delta_f)),
            love=max(0.0, min(100.0, self.love + delta_l)),
        )

    def to_display(self) -> dict:
        """转换为前端显示格式"""
        return {
            "authority": {"value": round(self.authority, 1), "label": "掌控力 (A)"},
            "fear": {"value": round(self.fear, 1), "label": "畏惧值 (F)"},
            "love": {"value": round(self.love, 1), "label": "爱戴值 (L)"},
            "total": round(self.total(), 1),
        }

    def get_status_warnings(self) -> list[str]:
        """获取当前状态警告"""
        warnings = []
        if self.is_authority_lost():
            warnings.append("掌控力不足! 机器人可能不再服从指令")
        if self.is_riot_risk():
            warnings.append("民心涣散! 骚乱一触即发")
        if self.is_coup_risk():
            warnings.append("高压统治! 政变风险极高")
        if self.is_collapsed():
            warnings.append("统治崩溃! 游戏即将结束")
        return warnings
