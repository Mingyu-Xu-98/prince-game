"""
数值结算引擎
应用审计结果，更新游戏状态
"""
from typing import Optional
from models.game_state import GameState, RobotType
from models.events import EventLibrary, Event
from skills import AuditResult
from config import settings


class SettlementEngine:
    """数值结算引擎"""

    def __init__(self):
        self.event_library = EventLibrary()

    def settle(
        self,
        game_state: GameState,
        audit_summary: dict,
        relation_deltas: dict[str, dict],
    ) -> dict:
        """
        执行数值结算

        Args:
            game_state: 当前游戏状态
            audit_summary: 审计汇总结果
            relation_deltas: 关系变化

        Returns:
            {
                "old_power": dict,
                "new_power": dict,
                "power_changes": dict,
                "old_relations": dict,
                "new_relations": dict,
                "triggered_event": Optional[Event],
                "game_over": bool,
                "game_over_reason": Optional[str],
            }
        """
        # 记录旧状态
        old_power = game_state.power.model_copy()
        old_relations = {
            robot: rel.model_copy()
            for robot, rel in game_state.relations.items()
        }

        # 1. 应用权力数值变化
        total_delta = audit_summary["total_delta"]
        game_state.power = game_state.power.apply_delta(
            delta_a=total_delta["authority"],
            delta_f=total_delta["fear"],
            delta_l=total_delta["love"],
        )

        # 2. 应用关系变化
        for robot, deltas in relation_deltas.items():
            if robot in game_state.relations:
                game_state.relations[robot] = game_state.relations[robot].apply_delta(
                    delta_trust=deltas["trust"],
                    delta_hatred=deltas["hatred"],
                )

        # 3. 检查事件触发
        triggered_event = None

        # 优先检查审计触发的事件
        if audit_summary.get("trigger_events"):
            event_type = audit_summary["trigger_events"][0]
            if event_type == "riot":
                triggered_event = EventLibrary.get_riot_event()
            elif event_type == "coup":
                triggered_event = EventLibrary.get_coup_event()

        # 如果没有审计触发的事件，检查数值触发
        if not triggered_event:
            triggered_event = EventLibrary.check_triggered_events(game_state.power)

        # 4. 检查游戏结束条件
        game_over = False
        game_over_reason = None

        if game_state.power.is_collapsed(settings.collapse_threshold):
            game_over = True
            game_over_reason = "统治崩溃：权力三维总值低于临界点，你的统治走向终结。"
        elif game_state.power.is_authority_lost(settings.authority_threshold):
            # 掌控力不足不直接结束，但机器人可能不服从
            pass

        if game_over:
            game_state.end_game(game_over_reason)

        # 5. 进入下一回合
        game_state.next_turn()

        return {
            "old_power": old_power.to_display(),
            "new_power": game_state.power.to_display(),
            "power_changes": {
                "authority": round(total_delta["authority"], 1),
                "fear": round(total_delta["fear"], 1),
                "love": round(total_delta["love"], 1),
            },
            "old_relations": {
                robot: {"trust": rel.trust, "hatred": rel.hatred}
                for robot, rel in old_relations.items()
            },
            "new_relations": {
                robot: {"trust": rel.trust, "hatred": rel.hatred}
                for robot, rel in game_state.relations.items()
            },
            "triggered_event": triggered_event,
            "game_over": game_over,
            "game_over_reason": game_over_reason,
            "warnings": game_state.power.get_status_warnings(),
        }

    def apply_event_choice(
        self,
        game_state: GameState,
        event: Event,
        choice_id: str,
    ) -> dict:
        """
        应用玩家对事件的选择

        Returns:
            {
                "choice_made": str,
                "impact": dict,
                "new_power": dict,
            }
        """
        impact = event.get_choice_impacts(choice_id)

        # 应用影响
        game_state.power = game_state.power.apply_delta(
            delta_a=impact.get("authority", 0),
            delta_f=impact.get("fear", 0),
            delta_l=impact.get("love", 0),
        )

        # 获取选择文本
        choice_text = ""
        for choice in event.choices:
            if choice.get("id") == choice_id:
                choice_text = choice.get("text", "")
                break

        return {
            "choice_made": choice_text,
            "impact": impact,
            "new_power": game_state.power.to_display(),
            "warnings": game_state.power.get_status_warnings(),
        }

    def check_obedience(self, game_state: GameState) -> dict:
        """
        检查机器人是否服从指令

        当掌控力低于阈值时，机器人可能不执行指令
        """
        obedience = {
            "lion": True,
            "fox": True,
            "balance": True,
        }

        if game_state.power.authority < settings.authority_threshold:
            # 根据关系决定是否服从
            for robot in ["lion", "fox", "balance"]:
                relation = game_state.relations.get(robot)
                if relation:
                    # 信任度高或仇恨度低时可能仍然服从
                    if relation.trust < 0 or relation.hatred > 50:
                        obedience[robot] = False

        return obedience
