"""
审计引擎
并发运行三个 Skill 审计，汇总结果
"""
import asyncio
from typing import Optional

from models.game_state import GameState
from skills import LionSkill, FoxSkill, BalanceSkill, AuditResult


class AuditEngine:
    """审计引擎 - 并发运行三个 Skill"""

    def __init__(self):
        self.lion = LionSkill()
        self.fox = FoxSkill()
        self.balance = BalanceSkill()

    async def run_audit(
        self,
        player_input: str,
        parsed_intent: dict,
        game_state: GameState,
    ) -> dict[str, AuditResult]:
        """
        并发运行三个 Skill 审计

        Returns:
            {
                "lion": AuditResult,
                "fox": AuditResult,
                "balance": AuditResult,
            }
        """
        # 并发执行三个审计
        results = await asyncio.gather(
            self.lion.audit(player_input, parsed_intent, game_state),
            self.fox.audit(player_input, parsed_intent, game_state),
            self.balance.audit(player_input, parsed_intent, game_state),
        )

        return {
            "lion": results[0],
            "fox": results[1],
            "balance": results[2],
        }

    def summarize_audit(self, audit_results: dict[str, AuditResult]) -> dict:
        """
        汇总审计结果

        Returns:
            {
                "total_delta": {"authority": float, "fear": float, "love": float},
                "combined_assessment": str,
                "all_warnings": list[str],
                "trigger_events": list[str],
                "skill_reports": dict,
            }
        """
        # 汇总数值变化
        total_delta = {
            "authority": 0.0,
            "fear": 0.0,
            "love": 0.0,
        }

        all_warnings = []
        trigger_events = []
        skill_reports = {}

        for skill_name, result in audit_results.items():
            # 累加数值变化
            total_delta["authority"] += result.delta_authority
            total_delta["fear"] += result.delta_fear
            total_delta["love"] += result.delta_love

            # 收集警告
            all_warnings.extend(result.warnings)

            # 检查触发事件
            if result.trigger_event and result.event_type:
                trigger_events.append(result.event_type)

            # 记录各Skill报告
            skill_reports[skill_name] = {
                "score": result.score,
                "assessment": result.assessment,
                "tone": result.detected_tone,
                "keywords": result.detected_keywords,
            }

        # 生成综合评估
        combined_assessment = self._generate_combined_assessment(skill_reports)

        return {
            "total_delta": total_delta,
            "combined_assessment": combined_assessment,
            "all_warnings": list(set(all_warnings)),  # 去重
            "trigger_events": list(set(trigger_events)),
            "skill_reports": skill_reports,
        }

    def _generate_combined_assessment(self, skill_reports: dict) -> str:
        """生成综合评估"""
        lion = skill_reports.get("lion", {})
        fox = skill_reports.get("fox", {})
        balance = skill_reports.get("balance", {})

        lines = []

        # 狮子评价
        lion_tone = lion.get("tone", "neutral")
        if lion_tone == "decisive":
            lines.append("【武力】狮子点头认可你的果断。")
        elif lion_tone == "hesitant":
            lines.append("【武力】狮子对你的软弱表示不屑。")

        # 狐狸评价
        fox_tone = fox.get("tone", "neutral")
        if fox_tone == "contradictory":
            lines.append("【权谋】狐狸嗅到了你言辞中的矛盾。")
        elif fox_tone == "cunning":
            lines.append("【权谋】狐狸欣赏你的话术技巧。")

        # 天平评价
        balance_tone = balance.get("tone", "neutral")
        if balance_tone == "unjust":
            lines.append("【正义】天平向底层倾斜，警示不公。")
        elif balance_tone == "fair":
            lines.append("【正义】天平保持平衡，政策公正。")

        if not lines:
            lines.append("三位顾问沉默以对，静待下一步行动。")

        return "\n".join(lines)

    def get_relation_deltas(self, audit_results: dict[str, AuditResult]) -> dict[str, dict]:
        """
        获取与各机器人的关系变化

        Returns:
            {
                "lion": {"trust": float, "hatred": float},
                "fox": {"trust": float, "hatred": float},
                "balance": {"trust": float, "hatred": float},
            }
        """
        return {
            skill_name: {
                "trust": result.delta_trust,
                "hatred": result.delta_hatred,
            }
            for skill_name, result in audit_results.items()
        }
