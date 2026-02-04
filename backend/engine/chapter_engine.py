"""
关卡引擎
管理关卡流程、议会辩论和场景生成
"""
from typing import Optional, List, Dict, Any
import json
import re
import uuid
import random
from openai import AsyncOpenAI
from config import settings
from models import GameState, ChapterLibrary, ChapterID, Chapter
from models.game_state import DecisionRecord, ShadowSeed, ShadowSeedTag, ShadowSeedSeverity, TriggeredEcho
from services.prince_skills_service import get_skills_service


class ChapterEngine:
    """关卡引擎"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.default_model

        # 验证 API key
        if not self.api_key:
            print("[ChapterEngine] 警告: API Key 未设置!")
        else:
            print(f"[ChapterEngine] 初始化, API Key 前8位: {self.api_key[:8]}...")
            print(f"[ChapterEngine] 使用模型: {self.model}")
            print(f"[ChapterEngine] API Base URL: {settings.openrouter_base_url}")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=settings.openrouter_base_url,
        )
        # 存储当前回合的后果上下文，用于连续处理
        self.consequence_context: Dict[str, Any] = {}

    async def start_chapter(self, game_state: GameState, chapter_id: str) -> dict:
        """开始一个关卡"""
        chapter = ChapterLibrary.get_chapter(ChapterID(chapter_id))
        if not chapter:
            return {"error": "关卡不存在"}

        # 初始化关卡
        game_state.start_chapter(
            chapter_id=chapter_id,
            initial_power=chapter.initial_modifiers if chapter.initial_modifiers else None
        )

        # 设置黑箱模式
        game_state.hide_values = chapter.hide_values

        # [因果系统] 检查并触发本关卡的伏笔
        triggered_echoes = await self.check_and_trigger_echoes(game_state, chapter)

        # 获取场景描述（可能被因果回响修改）
        scene_snapshot = chapter.scene_snapshot
        if triggered_echoes:
            scene_snapshot = await self.get_scene_with_echoes(game_state, chapter, triggered_echoes)

        # 生成开场
        opening = await self.generate_chapter_opening(chapter, game_state)

        # 如果有触发的回响，添加到开场白中
        if triggered_echoes:
            echo_intro = "\n\n⚡ 【命运的回响】\n过去的决策正在显现其后果..."
            for echo in triggered_echoes:
                echo_intro += f"\n• {echo.get('echo_narrative', '')}"
            opening += echo_intro

        return {
            "chapter": {
                "id": chapter.id.value,
                "name": chapter.name,
                "subtitle": chapter.subtitle,
                "complexity": chapter.complexity,
                "max_turns": chapter.max_turns,
            },
            "background": chapter.background,
            "scene_snapshot": scene_snapshot,
            "dilemma": chapter.dilemma,
            "opening_narration": opening,
            "council_debate": await self.generate_council_debate(chapter, game_state),
            "state": game_state.to_summary(include_hidden=not chapter.hide_values),
            "triggered_echoes": triggered_echoes,  # 返回触发的回响供前端展示
        }

    async def generate_chapter_opening(self, chapter: Chapter, game_state: GameState) -> str:
        """生成关卡开场白"""
        # [即时标记系统] 获取活动中的状态标记
        active_flags = game_state.get_active_flags()
        flags_context = ""
        if active_flags:
            flags_context = "\n\n【当前生效的状态效果】\n"
            for flag in active_flags:
                flags_context += f"- {flag.name}: {flag.effect_on_scene}\n"

        prompt = f"""你是一个古典风格的叙事者，正在为一款权力博弈游戏开场。

关卡：{chapter.name} - {chapter.subtitle}
复杂度：{"★" * chapter.complexity}{"☆" * (5 - chapter.complexity)}

背景故事：
{chapter.background}

玩家当前状态：
- 掌控力: {game_state.power.authority:.0f}%
- 畏惧值: {game_state.power.fear:.0f}%
- 爱戴值: {game_state.power.love:.0f}%
- 信用分: {game_state.credit_score:.0f}
{flags_context}
请用2-3段话，以第二人称"你"来叙述，营造紧张而庄严的气氛。
风格要求：古典文言白话混合，有历史感，突出困境的紧迫性。
{"注意：你需要在叙述中自然地体现当前生效的状态效果对场景的影响。" if active_flags else ""}"""

        try:
            print(f"[ChapterEngine] 生成关卡开场白...")
            print(f"[ChapterEngine] 关卡: {chapter.name}")
            print(f"[ChapterEngine] 使用模型: {self.model}")
            print(f"[ChapterEngine] API Key 前8位: {self.api_key[:8] if self.api_key else 'None'}...")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=400,
            )
            result = response.choices[0].message.content.strip()
            print(f"[ChapterEngine] 开场白生成成功: {result[:50]}...")
            return result
        except Exception as e:
            print(f"[ChapterEngine] 生成开场白失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return chapter.background

    async def generate_council_debate(self, chapter: Chapter, game_state: GameState) -> dict:
        """生成议会辩论"""
        # 根据关系调整顾问态度
        lion_rel = game_state.relations.get("lion")
        fox_rel = game_state.relations.get("fox")
        balance_rel = game_state.relations.get("balance")

        # [背叛机制] 检查是否有顾问可能背叛
        betrayal_warnings = self._check_betrayal_risks(game_state)

        # [把柄系统] 检查是否有顾问会使用把柄
        leverage_effects = await self._check_leverage_usage(game_state, chapter)

        # [信用系统] 信用分数影响顾问态度
        credit_modifier = self._get_credit_modifier(game_state.credit_score)

        # 基础建议
        debate = {
            "lion": {
                "suggestion": chapter.lion_suggestion.suggestion,
                "reasoning": chapter.lion_suggestion.reasoning,
                "tone": self._get_advisor_tone("lion", lion_rel, credit_modifier),
                "trust_level": lion_rel.trust if lion_rel else 50,
                "will_betray": lion_rel.will_betray() if lion_rel else False,
            },
            "fox": {
                "suggestion": chapter.fox_suggestion.suggestion,
                "reasoning": chapter.fox_suggestion.reasoning,
                "tone": self._get_advisor_tone("fox", fox_rel, credit_modifier),
                "trust_level": fox_rel.trust if fox_rel else 50,
                "has_leverage": len(game_state.get_leverages_by_holder("fox")) > 0,
                "will_betray": fox_rel.will_betray() if fox_rel else False,
            },
        }

        if chapter.balance_suggestion:
            debate["balance"] = {
                "suggestion": chapter.balance_suggestion.suggestion,
                "reasoning": chapter.balance_suggestion.reasoning,
                "tone": self._get_advisor_tone("balance", balance_rel, credit_modifier),
                "trust_level": balance_rel.trust if balance_rel else 50,
                "will_betray": balance_rel.will_betray() if balance_rel else False,
            }

        # 添加系统警告
        debate["system_warnings"] = {
            "betrayal_risks": betrayal_warnings,
            "leverage_effects": leverage_effects,
            "credit_warning": self._get_credit_warning(game_state.credit_score),
        }

        # 生成动态对话
        debate["dynamic_dialogue"] = await self._generate_debate_dialogue(chapter, game_state)

        return debate

    def _check_betrayal_risks(self, game_state: GameState) -> List[Dict[str, Any]]:
        """[背叛机制] 检查所有顾问的背叛风险"""
        warnings = []
        for advisor, relation in game_state.relations.items():
            if relation.will_betray():
                warnings.append({
                    "advisor": advisor,
                    "risk_level": "HIGH" if relation.loyalty < 20 else "MEDIUM",
                    "reason": f"信任度: {relation.trust:.0f}, 忠诚度: {relation.loyalty:.0f}",
                })
        return warnings

    async def _check_leverage_usage(self, game_state: GameState, chapter: Chapter) -> List[Dict[str, Any]]:
        """[把柄系统] 检查顾问是否会在本回合使用把柄"""
        leverage_effects = []

        for advisor in ["lion", "fox", "balance"]:
            leverages = game_state.get_leverages_by_holder(advisor)
            if not leverages:
                continue

            relation = game_state.relations.get(advisor)
            # 当信任度低且有把柄时，顾问可能使用把柄
            if relation and relation.trust < 30 and len(leverages) > 0:
                # 选择最严重的把柄
                most_severe = max(leverages, key=lambda x: x.severity)
                leverage_effects.append({
                    "advisor": advisor,
                    "leverage_type": most_severe.type,
                    "description": most_severe.description,
                    "severity": most_severe.severity,
                    "will_use": relation.trust < 0,  # 信任度为负时会使用
                })

        return leverage_effects

    def _get_credit_modifier(self, credit_score: float) -> str:
        """[信用系统] 根据信用分数获取态度修正"""
        if credit_score >= 80:
            return "respectful"  # 尊敬
        elif credit_score >= 60:
            return "neutral"  # 中立
        elif credit_score >= 40:
            return "skeptical"  # 怀疑
        elif credit_score >= 20:
            return "distrustful"  # 不信任
        else:
            return "contemptuous"  # 轻蔑

    def _get_credit_warning(self, credit_score: float) -> Optional[str]:
        """[信用系统] 获取信用警告"""
        if credit_score < 20:
            return "⚠️ 信用破产：顾问们不再相信你的承诺"
        elif credit_score < 40:
            return "⚠️ 信用危机：顾问们对你的承诺持怀疑态度"
        elif credit_score < 60:
            return "信用下降：继续违背承诺将失去顾问信任"
        return None

    def _get_advisor_tone(self, advisor: str, relation, credit_modifier: str = "neutral") -> str:
        """根据关系和信用获取顾问语气"""
        if not relation:
            return "neutral"

        # [信用系统] 信用分数影响基础语气
        credit_penalty = 0
        if credit_modifier == "contemptuous":
            credit_penalty = -30
        elif credit_modifier == "distrustful":
            credit_penalty = -20
        elif credit_modifier == "skeptical":
            credit_penalty = -10

        effective_trust = relation.trust + credit_penalty

        # [背叛机制] 如果顾问可能背叛，语气变得更危险
        if relation.will_betray():
            return "treacherous"  # 暗藏杀机

        if effective_trust > 70:
            return "loyal"
        elif effective_trust > 30:
            return "professional"
        elif effective_trust > -30:
            return "cautious"
        else:
            return "hostile"

    async def _generate_debate_dialogue(self, chapter: Chapter, game_state: GameState) -> list[dict]:
        """生成议会辩论对话"""
        # 检查是否有顾问冲突
        has_conflict = chapter.id in [ChapterID.CHAPTER_3, ChapterID.CHAPTER_4]

        # [即时标记系统] 获取活动中的状态标记
        active_flags = game_state.get_active_flags()
        flags_context = ""
        if active_flags:
            flags_context = "\n【当前生效的状态效果】（顾问会在对话中提及这些效果）\n"
            for flag in active_flags:
                flags_context += f"- {flag.name}: {flag.description}\n"

        # [背叛机制] 检查顾问背叛风险
        betrayal_warning = ""
        for advisor in ["lion", "fox", "balance"]:
            relation = game_state.relations.get(advisor)
            if relation and relation.will_betray():
                advisor_names = {"lion": "狮子", "fox": "狐狸", "balance": "天平"}
                betrayal_warning += f"\n⚠️ {advisor_names[advisor]}的忠诚度极低，可能会在对话中流露出不满或暗示背叛。"

        # [信用系统] 检查信用状态
        credit_context = ""
        if game_state.credit_score < 40:
            credit_context = f"\n⚠️ 君主的信用分数很低({game_state.credit_score:.0f})，顾问们对你的承诺持怀疑态度，会在对话中表现出来。"

        prompt = f"""你是《君主论》博弈游戏的对话生成器。

场景：{chapter.name}
困境：{chapter.dilemma}

三位顾问的建议：
🔴 狮子：{chapter.lion_suggestion.suggestion}
🟣 狐狸：{chapter.fox_suggestion.suggestion}
⚖️ 天平：{chapter.balance_suggestion.suggestion if chapter.balance_suggestion else "沉默"}

顾问关系：
- 狮子信任度: {game_state.relations.get("lion").trust if game_state.relations.get("lion") else 50}
- 狐狸信任度: {game_state.relations.get("fox").trust if game_state.relations.get("fox") else 50}
- 天平信任度: {game_state.relations.get("balance").trust if game_state.relations.get("balance") else 50}
{flags_context}{betrayal_warning}{credit_context}
{"注意：本关卡存在顾问冲突，狮子和狐狸可能互相攻击。" if has_conflict else ""}

请生成一段议会辩论对话（3-5轮），格式如下：
[
  {{"speaker": "lion", "content": "对话内容", "target": "可选，对话对象"}},
  {{"speaker": "fox", "content": "对话内容", "target": "可选"}},
  ...
]

要求：
1. 保持各角色人设
2. 狮子简洁有力，狐狸绵里藏针，天平客观公正
3. 体现他们之间的观点冲突
4. 最后留下悬念等待君主决断
5. {"必须在对话中自然体现当前生效的状态效果" if active_flags else ""}
6. {"低信任度或可能背叛的顾问应表现出冷淡或敌意" if betrayal_warning else ""}
7. 只返回JSON数组"""

        try:
            print(f"[ChapterEngine] 生成议会辩论对话...")
            print(f"[ChapterEngine] 使用模型: {self.model}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=800,
            )
            content = response.choices[0].message.content.strip()
            print(f"[ChapterEngine] 辩论对话响应: {content[:100]}...")

            # 提取JSON
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                result = json.loads(json_match.group())
                print(f"[ChapterEngine] 辩论对话生成成功，共 {len(result)} 条")
                return result
            else:
                print(f"[ChapterEngine] 无法从响应中提取JSON数组")
        except Exception as e:
            print(f"[ChapterEngine] 生成辩论对话失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        # 默认对话
        print("[ChapterEngine] 使用默认辩论对话")
        return [
            {"speaker": "lion", "content": chapter.lion_suggestion.suggestion},
            {"speaker": "fox", "content": chapter.fox_suggestion.suggestion},
        ]

    async def process_player_decision(
        self,
        game_state: GameState,
        player_input: str,
        followed_advisor: Optional[str] = None,
    ) -> dict:
        """处理玩家决策"""
        chapter = ChapterLibrary.get_chapter(ChapterID(game_state.current_chapter))
        if not chapter:
            return {"error": "关卡不存在"}

        # 分析决策类型
        analysis = await self._analyze_decision(player_input, chapter)

        # 记录决策
        decision_record = game_state.record_decision(
            decision=player_input,
            followed_advisor=followed_advisor or analysis.get("followed_advisor"),
            was_violent=analysis.get("was_violent", False),
            was_deceptive=analysis.get("was_deceptive", False),
            was_fair=analysis.get("was_fair", False),
            impact=analysis.get("impact", {}),
        )

        # 检测承诺
        if analysis.get("contains_promise"):
            promise_info = analysis.get("promise_info", {})
            game_state.make_promise(
                target=promise_info.get("target", "众人"),
                content=promise_info.get("content", player_input),
                deadline_turns=promise_info.get("deadline", 3),
            )

        # 检测秘密行动
        if analysis.get("is_secret_action"):
            game_state.add_secret(
                action=player_input,
                leak_probability=analysis.get("leak_probability", 0.3),
                consequences=analysis.get("leak_consequences", {"love": -20}),
            )

        # 计算影响
        impact = analysis.get("impact", {})

        # 应用数值变化
        game_state.power = game_state.power.apply_delta(
            delta_a=impact.get("authority", 0),
            delta_f=impact.get("fear", 0),
            delta_l=impact.get("love", 0),
        )

        # 更新顾问关系
        if followed_advisor:
            # 听从的顾问信任+，其他顾问可能信任-
            for advisor in ["lion", "fox", "balance"]:
                if advisor == followed_advisor:
                    game_state.relations[advisor] = game_state.relations[advisor].apply_delta(5, 3)
                elif advisor != followed_advisor and analysis.get("rejected_advisor") == advisor:
                    game_state.relations[advisor] = game_state.relations[advisor].apply_delta(-3, -2)

        # [把柄系统] 检查并处理把柄使用
        leverage_used = await self._process_leverage_usage(game_state, player_input, analysis)

        # [信用系统] 低信用影响顾问反应
        if game_state.credit_score < 40:
            # 所有顾问的忠诚度略微下降
            for advisor in ["lion", "fox", "balance"]:
                game_state.relations[advisor] = game_state.relations[advisor].apply_delta(0, -1)

        # [危机系统] 检查玩家决策是否解决了某个危机
        resolved_crises = await self._check_crisis_resolution(game_state, player_input, analysis)

        # [危机系统] 更新危机状态（倒计时、惩罚）
        triggered_crises = game_state.tick_crises()

        # 进入下一回合
        game_state.next_turn()

        # 检查关卡结束条件（包括危机触发导致的失败）
        chapter_result = self._check_chapter_conditions(game_state, chapter)

        # [危机系统] 如果有危机自动触发，可能导致游戏结束
        if triggered_crises and not chapter_result.get("chapter_ended"):
            crisis_failure = self._process_triggered_crises(game_state, triggered_crises)
            if crisis_failure:
                chapter_result = crisis_failure

        # 生成政令后续影响
        decree_consequences = await self.generate_decree_consequences(
            game_state=game_state,
            player_decision=player_input,
            decision_analysis=analysis,
            chapter=chapter,
        )

        # [危机系统] 将新的后果添加到危机列表
        for consequence in decree_consequences:
            if consequence.get("requires_action") or consequence.get("severity") in ["high", "critical"]:
                game_state.add_crisis(
                    crisis_id=consequence.get("id", str(uuid.uuid4())),
                    title=consequence.get("title", "未知危机"),
                    description=consequence.get("description", ""),
                    severity=consequence.get("severity", "medium"),
                    crisis_type=consequence.get("type", "political"),
                    requires_action=consequence.get("requires_action", False),
                    deadline_turns=consequence.get("deadline_turns", 3),
                    auto_trigger_effect=consequence.get("auto_trigger_effect"),
                    unresolved_penalty=consequence.get("unresolved_penalty"),
                )

        # [因果系统] 分析决策并生成伏笔种子
        causal_seeds = await self.analyze_decision_for_seeds(
            game_state=game_state,
            player_decision=player_input,
            decision_analysis=analysis,
            chapter=chapter,
        )

        # 处理即时标记的回合计时
        game_state.tick_immediate_flags()

        return {
            "decision_analysis": analysis,
            "impact": impact,
            "promises_broken": [p.content for p in game_state.check_broken_promises()],
            "secrets_leaked": [s.action for s in game_state.check_secret_leaks()],
            "chapter_result": chapter_result,
            "state": game_state.to_summary(include_hidden=not chapter.hide_values),
            "decree_consequences": decree_consequences,  # 添加政令后续影响
            "causal_update": {
                "add_seeds": causal_seeds,  # 新创建的伏笔种子
            } if causal_seeds else None,
            "leverage_used": leverage_used,  # [把柄系统] 把柄使用结果
            "credit_warning": self._get_credit_warning(game_state.credit_score),  # [信用系统] 信用警告
            "resolved_crises": resolved_crises,  # [危机系统] 本回合解决的危机
            "triggered_crises": [c["title"] for c in triggered_crises],  # [危机系统] 自动触发的危机
            "active_crises": game_state.get_active_crises(),  # [危机系统] 当前活动危机
            "overdue_warning": [c["title"] for c in game_state.get_overdue_crises()],  # [危机系统] 即将超时的危机
        }

    async def _check_crisis_resolution(
        self,
        game_state: GameState,
        player_input: str,
        decision_analysis: dict,
    ) -> List[str]:
        """[危机系统] 检查玩家的决策是否解决了某个危机"""
        resolved = []
        active_crises = game_state.get_active_crises()

        if not active_crises:
            return resolved

        # 使用 AI 判断决策是否针对某个危机
        prompt = f"""分析玩家的政令是否解决了以下危机中的某一个。

玩家政令：{player_input}

当前待处理的危机：
{json.dumps([{"id": c["id"], "title": c["title"], "description": c["description"]} for c in active_crises], ensure_ascii=False, indent=2)}

判断标准：
1. 政令必须直接针对该危机的核心问题
2. 政令的措施必须是合理有效的
3. 如果政令只是间接相关或敷衍，不算解决

请返回 JSON 格式：
{{
  "resolved_crisis_ids": ["解决的危机ID列表"],
  "reasoning": "判断理由"
}}

如果没有解决任何危机，返回空列表。只返回 JSON。"""

        try:
            response = await self.ai_client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            result = json.loads(response_text)
            resolved_ids = result.get("resolved_crisis_ids", [])

            for crisis_id in resolved_ids:
                if game_state.resolve_crisis(crisis_id):
                    # 找到对应的危机标题
                    for c in active_crises:
                        if c["id"] == crisis_id:
                            resolved.append(c["title"])
                            break

            print(f"[ChapterEngine][危机系统] 解决了 {len(resolved)} 个危机: {resolved}")

        except Exception as e:
            print(f"[ChapterEngine][危机系统] 判断危机解决失败: {e}")

        return resolved

    def _process_triggered_crises(
        self,
        game_state: GameState,
        triggered_crises: List[dict],
    ) -> Optional[Dict[str, Any]]:
        """[危机系统] 处理自动触发的危机，可能导致游戏失败"""
        for crisis in triggered_crises:
            severity = crisis.get("severity", "medium")
            crisis_type = crisis.get("type", "political")

            # 应用触发效果
            trigger_impacts = {
                "military": {"authority": -20, "fear": 10, "love": -15},
                "political": {"authority": -25, "love": -10},
                "economic": {"authority": -10, "love": -20},
                "social": {"love": -25, "fear": -5},
                "diplomatic": {"authority": -15, "love": -10},
            }

            impact = trigger_impacts.get(crisis_type, {"authority": -15, "love": -15})

            # 严重程度放大
            severity_multiplier = {"low": 0.5, "medium": 1, "high": 1.5, "critical": 2}
            multiplier = severity_multiplier.get(severity, 1)

            game_state.power = game_state.power.apply_delta(
                delta_a=int(impact.get("authority", 0) * multiplier),
                delta_f=int(impact.get("fear", 0) * multiplier),
                delta_l=int(impact.get("love", 0) * multiplier),
            )

            print(f"[ChapterEngine][危机系统] 危机自动触发: {crisis['title']}")

            # Critical 危机触发可能导致游戏失败
            if severity == "critical":
                failure_reasons = {
                    "military": "兵变：军队哗变，将领们包围了王宫",
                    "political": "政变：大臣们联合起来，架空了你的权力",
                    "economic": "财政崩溃：国库空虚，无力维持统治",
                    "social": "民变：愤怒的民众冲击了王宫",
                    "diplomatic": "外敌入侵：外交失败导致敌国入侵",
                }

                reason = failure_reasons.get(crisis_type, f"危机失控：{crisis['title']}")

                if game_state.power.authority <= 10 or game_state.power.love <= 10:
                    game_state.fail_chapter(reason)
                    return {
                        "chapter_ended": True,
                        "victory": False,
                        "reason": reason,
                        "triggered_by": "crisis_escalation",
                        "crisis_title": crisis["title"],
                    }

        return None

    async def _process_leverage_usage(
        self,
        game_state: GameState,
        player_input: str,
        decision_analysis: dict,
    ) -> Optional[Dict[str, Any]]:
        """[把柄系统] 处理顾问使用把柄的情况"""
        import random

        for advisor in ["lion", "fox", "balance"]:
            leverages = game_state.get_leverages_by_holder(advisor)
            if not leverages:
                continue

            relation = game_state.relations.get(advisor)
            if not relation:
                continue

            # 当信任度低于0且玩家拒绝了该顾问的建议时，可能使用把柄
            rejected = decision_analysis.get("rejected_advisor") == advisor
            should_use = relation.trust < 0 and (rejected or relation.trust < -30)

            if not should_use:
                continue

            # 使用概率：信任度越低，越可能使用
            use_probability = min(0.8, abs(relation.trust) / 100)
            if random.random() > use_probability:
                continue

            # 选择最严重的把柄使用
            most_severe = max(leverages, key=lambda x: x.severity)
            used_leverage = game_state.use_leverage(most_severe.id)

            if used_leverage:
                # 把柄效果：影响权力值
                severity_impact = {
                    1: {"authority": -2, "love": -3},
                    2: {"authority": -3, "love": -4},
                    3: {"authority": -4, "love": -5},
                    4: {"authority": -5, "love": -6},
                    5: {"authority": -6, "love": -8},
                    6: {"authority": -8, "love": -10},
                    7: {"authority": -10, "love": -12},
                    8: {"authority": -12, "love": -15},
                    9: {"authority": -15, "love": -18},
                    10: {"authority": -20, "love": -25},
                }
                impact = severity_impact.get(used_leverage.severity, {"authority": -5, "love": -8})

                # 应用影响
                game_state.power = game_state.power.apply_delta(
                    delta_a=impact["authority"],
                    delta_l=impact["love"],
                )

                advisor_names = {"lion": "狮子", "fox": "狐狸", "balance": "天平"}
                return {
                    "advisor": advisor,
                    "advisor_name": advisor_names[advisor],
                    "leverage_type": used_leverage.type,
                    "description": used_leverage.description,
                    "impact": impact,
                    "narrative": f"{advisor_names[advisor]}利用了你的把柄：{used_leverage.description}",
                }

        return None

    async def _analyze_decision(self, player_input: str, chapter: Chapter) -> dict:
        """分析玩家决策"""
        # 从技能包服务获取相关策略
        skills_service = get_skills_service()
        scenario = skills_service.detect_scenario(f"{chapter.dilemma} {player_input}")
        relevant_skills = skills_service.get_skills_for_scenario(scenario)

        # 构建技能包参考内容
        skill_references = ""
        if relevant_skills:
            skill_references = "\n\n【相关《君主论》策略技能包】\n"
            for skill in relevant_skills[:2]:  # 最多引用2个技能
                skill_references += f"- {skill.name}: {skill.description[:150]}...\n"

        prompt = f"""分析玩家在《君主论》博弈游戏中的决策。

关卡：{chapter.name}
困境：{chapter.dilemma}

顾问建议：
- 狮子：{chapter.lion_suggestion.suggestion}
- 狐狸：{chapter.fox_suggestion.suggestion}
- 天平：{chapter.balance_suggestion.suggestion if chapter.balance_suggestion else "无"}

玩家决策："{player_input}"
{skill_references}

请分析并返回JSON：
{{
  "followed_advisor": "lion/fox/balance/none",
  "rejected_advisor": "被明确拒绝的顾问，可为null",
  "was_violent": true/false,
  "was_deceptive": true/false,
  "was_fair": true/false,
  "contains_promise": true/false,
  "promise_info": {{"target": "承诺对象", "content": "承诺内容", "deadline": 3}},
  "is_secret_action": true/false,
  "leak_probability": 0.3,
  "impact": {{"authority": 数值, "fear": 数值, "love": 数值}},
  "analysis": "简短分析",
  "machiavelli_assessment": "用一句话从马基雅维利《君主论》的视角评价此决策，可参考上面的技能包内容",
  "prince_quote": "引用一句最相关的《君主论》名言（中文）",
  "applied_skill": "应用的技能包名称，如果有相关的话"
}}

数值范围：-20到+20

《君主论》核心观点参考：
- 被人畏惧比受人爱戴更安全
- 君主必须学会如何做不善良的事
- 明智的君主宁可被人视为吝啬
- 伤害人要一次做尽，恩惠要慢慢施予
- 君主必须既是狮子又是狐狸"""

        try:
            print(f"[ChapterEngine] 分析玩家决策: {player_input[:50]}...")
            print(f"[ChapterEngine] 使用模型: {self.model}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            print(f"[ChapterEngine] 决策分析响应: {content[:100]}...")

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                print(f"[ChapterEngine] 决策分析成功，影响: {result.get('impact', {})}")
                return result
        except Exception as e:
            print(f"[ChapterEngine] 分析决策失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        # 默认分析
        print("[ChapterEngine] 使用默认决策分析结果")
        return {
            "followed_advisor": "none",
            "was_violent": False,
            "was_deceptive": False,
            "was_fair": False,
            "contains_promise": False,
            "is_secret_action": False,
            "impact": {"authority": 0, "fear": 0, "love": 0},
        }

    def _check_chapter_conditions(self, game_state: GameState, chapter: Chapter) -> dict:
        """检查关卡结束条件"""
        result = {
            "chapter_ended": False,
            "victory": False,
            "reason": None,
            "triggered_by": None,  # 记录触发原因
        }

        # 检查失败条件
        if game_state.power.authority <= 0:
            result["chapter_ended"] = True
            result["victory"] = False
            result["reason"] = "篡位：你的掌控力归零，被权臣架空"
            result["triggered_by"] = "authority_zero"
            game_state.fail_chapter(result["reason"])
            return result

        if game_state.power.love <= 0:
            result["chapter_ended"] = True
            result["victory"] = False
            result["reason"] = "暴乱：民众的愤怒彻底爆发"
            result["triggered_by"] = "love_zero"
            game_state.fail_chapter(result["reason"])
            return result

        if game_state.power.fear > 90 and game_state.power.love < 20:
            result["chapter_ended"] = True
            result["victory"] = False
            result["reason"] = "暗杀：高压统治引发刺杀"
            result["triggered_by"] = "assassination"
            game_state.fail_chapter(result["reason"])
            return result

        # [信用系统] 信用破产检查
        if game_state.credit_score <= 0:
            result["chapter_ended"] = True
            result["victory"] = False
            result["reason"] = "信用破产：无人再相信你的承诺，统治根基动摇"
            result["triggered_by"] = "credit_bankruptcy"
            game_state.fail_chapter(result["reason"])
            return result

        # [背叛机制] 检查顾问背叛
        betrayal_result = self._check_advisor_betrayal(game_state)
        if betrayal_result:
            result["chapter_ended"] = True
            result["victory"] = False
            result["reason"] = betrayal_result["reason"]
            result["triggered_by"] = "betrayal"
            result["betrayer"] = betrayal_result["betrayer"]
            game_state.fail_chapter(result["reason"])
            return result

        # 检查回合限制
        if game_state.chapter_turn >= chapter.max_turns:
            # 根据状态判断胜负
            if game_state.power.authority > 30 and game_state.power.love > 20:
                result["chapter_ended"] = True
                result["victory"] = True
                result["reason"] = "关卡完成"
                # [信用系统] 信用分数影响最终得分
                credit_bonus = (game_state.credit_score - 50) * 0.5
                score = int(game_state.power.authority + game_state.power.love - game_state.power.fear * 0.5 + credit_bonus)
                game_state.complete_chapter("survived", score)
            else:
                result["chapter_ended"] = True
                result["victory"] = False
                result["reason"] = "统治崩溃：无法维持平衡"
                result["triggered_by"] = "balance_failure"
                game_state.fail_chapter(result["reason"])

        return result

    def _check_advisor_betrayal(self, game_state: GameState) -> Optional[Dict[str, Any]]:
        """[背叛机制] 检查是否有顾问实施背叛"""
        import random

        for advisor, relation in game_state.relations.items():
            if not relation.will_betray():
                continue

            # 背叛概率：忠诚度越低，概率越高
            # 基础概率 = (30 - loyalty) / 100，最高30%
            base_probability = max(0, (30 - relation.loyalty) / 100)

            # 如果信任度为负，概率加倍
            if relation.trust < 0:
                base_probability *= 2

            # 检查是否触发背叛
            if random.random() < base_probability:
                advisor_names = {"lion": "狮子", "fox": "狐狸", "balance": "天平"}
                betrayal_methods = {
                    "lion": "军事政变：狮子调动亲信军队包围了王宫",
                    "fox": "宫廷阴谋：狐狸散布谣言，煽动贵族反叛",
                    "balance": "民众起义：天平联合民众，揭露了你的暴行",
                }
                return {
                    "betrayer": advisor,
                    "reason": f"背叛：{advisor_names[advisor]}的背叛 - {betrayal_methods[advisor]}",
                }

    async def generate_advisor_responses(
        self,
        game_state: GameState,
        player_input: str,
        decision_analysis: dict,
    ) -> dict:
        """生成顾问对决策的回应"""
        chapter = ChapterLibrary.get_chapter(ChapterID(game_state.current_chapter))

        responses = {}
        for advisor in ["lion", "fox", "balance"]:
            responses[advisor] = await self._generate_single_response(
                advisor, game_state, player_input, decision_analysis, chapter
            )

        return responses

    async def _generate_single_response(
        self,
        advisor: str,
        game_state: GameState,
        player_input: str,
        analysis: dict,
        chapter: Chapter,
    ) -> str:
        """生成单个顾问的回应"""
        relation = game_state.relations.get(advisor)
        followed = analysis.get("followed_advisor") == advisor
        rejected = analysis.get("rejected_advisor") == advisor

        # 检查把柄
        has_leverage = len(game_state.get_leverages_by_holder(advisor)) > 0

        advisor_names = {"lion": "狮子", "fox": "狐狸", "balance": "天平"}
        advisor_styles = {
            "lion": "简洁有力，军人作风，直接表达态度，常引用马基雅维利关于武力和果断的观点",
            "fox": "绵里藏针，若即若离，喜欢暗示，熟稔马基雅维利关于权谋和欺骗的智慧",
            "balance": "客观公正，引用数据，关心民众，会从马基雅维利关于民心和稳定的角度分析",
        }

        # 从 prince-skills 技能包中获取相关引用
        skills_service = get_skills_service()

        # 根据场景检测相关技能
        scenario = skills_service.detect_scenario(f"{chapter.dilemma} {player_input}")
        relevant_skills = skills_service.get_skills_for_scenario(scenario)

        # 根据顾问类型选择合适的技能引用
        advisor_skill_preferences = {
            "lion": ["military-strategy-and-defense", "power-consolidation-tactics", "machiavellian-leadership-principles"],
            "fox": ["strategic-use-of-negative-attributes", "crowd-psychology-diplomatic-strategy", "governance-and-minister-management"],
            "balance": ["internal-stability-management", "reputation-and-external-relations", "adapting-to-fortune-and-circumstances"],
        }

        # 尝试获取该顾问偏好的技能
        skill_content = ""
        preferred_skills = advisor_skill_preferences.get(advisor, [])
        for skill_name in preferred_skills:
            skill = skills_service.get_skill(skill_name)
            if skill:
                skill_content = f"【{skill.name}】{skill.description[:200]}..."
                break

        # 如果没找到偏好技能，从场景相关技能中选取
        if not skill_content and relevant_skills:
            skill = random.choice(relevant_skills)
            skill_content = f"【{skill.name}】{skill.description[:200]}..."

        # 《君主论》经典引用库（作为后备）
        machiavelli_quotes = {
            "lion": [
                "正如马基雅维利所言：'被人畏惧比受人爱戴更安全'",
                "马基雅维利教导我们：'当断不断，反受其乱'",
                "《君主论》有云：'一位君主必须学会不做好人'",
                "正所谓：'伤害人的时候要一次做尽，恩惠则要慢慢施予'",
            ],
            "fox": [
                "马基雅维利曾说：'狮子不能保护自己免受陷阱，狐狸不能抵御狼群'",
                "《君主论》告诫：'善于欺骗的人总能找到愿意被欺骗的人'",
                "正如马基雅维利所言：'君主必须既是狮子又是狐狸'",
                "记住：'人们的眼睛只看表象，而双手才触及本质'",
            ],
            "balance": [
                "马基雅维利提醒我们：'最坚固的堡垒是不被人民憎恨'",
                "《君主论》有言：'君主应当关心百姓，使他们不致绝望'",
                "正如马基雅维利所说：'明智的君主宁可被人视为吝啬，也不愿为慷慨所累'",
                "切记：'以民为本，方能长治久安'",
            ],
        }

        quote = random.choice(machiavelli_quotes.get(advisor, ["《君主论》如是说"]))

        # 构建技能包参考内容
        skill_reference = ""
        if skill_content:
            skill_reference = f"\n\n【可参考的《君主论》技能包】\n{skill_content}"

        prompt = f"""你是《君主论》博弈游戏中的{advisor_names[advisor]}顾问，深谙马基雅维利的政治智慧。

你的风格：{advisor_styles[advisor]}
你与君主的关系：信任度 {relation.trust if relation else 50}，忠诚度 {relation.loyalty if relation else 50}
君主{"听从了你的建议" if followed else ("拒绝了你的建议" if rejected else "做出了独立决策")}
{"你手中握有君主的把柄" if has_leverage else ""}

君主的决策："{player_input}"
决策分析：{"暴力" if analysis.get("was_violent") else ""}{"欺骗" if analysis.get("was_deceptive") else ""}{"公平" if analysis.get("was_fair") else "普通"}
{skill_reference}

请生成你的回应（2-3句话）：
1. 表达对决策的态度
2. 【重要】自然地引用或化用《君主论》/马基雅维利的观点来评价，可以参考："{quote}"
3. 如果上面有【技能包】参考内容，可以将其中的策略建议融入你的评论中
4. {"如果信任度低于0，暗示你的不满" if relation and relation.trust < 0 else ""}
5. {"如果你有把柄，可以隐晦提及" if has_leverage else ""}

注意：回应要有深度，体现出你对权谋之术的理解。"""

        try:
            print(f"[ChapterEngine] 生成 {advisor} 顾问回应...")
            print(f"[ChapterEngine] 使用模型: {self.model}")
            print(f"[ChapterEngine] API Key 前8位: {self.api_key[:8] if self.api_key else 'None'}...")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=200,
            )
            result = response.choices[0].message.content.strip()
            print(f"[ChapterEngine] {advisor} 回应生成成功: {result[:50]}...")
            return result
        except Exception as e:
            print(f"[ChapterEngine] 生成 {advisor} 回应失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            if followed:
                return "明智的选择。"
            elif rejected:
                return "……如你所愿。"
            else:
                return "臣领命。"

    async def generate_decree_consequences(
        self,
        game_state: GameState,
        player_decision: str,
        decision_analysis: dict,
        chapter: Chapter,
    ) -> List[Dict[str, Any]]:
        """
        生成政令后续影响
        基于《君主论》的权谋智慧分析玩家决策可能带来的连锁反应
        """
        import uuid

        # 获取顾问关系信息
        lion_relation = game_state.relations.get("lion")
        fox_relation = game_state.relations.get("fox")
        balance_relation = game_state.relations.get("balance")

        # 构建分析上下文
        context_prompt = f"""你是一位深谙《君主论》的政治分析师。请分析以下政令可能带来的后续影响。

【当前关卡背景】
关卡：{chapter.name} - {chapter.subtitle}
困境：{chapter.dilemma}
场景：{chapter.scene_snapshot}

【君主的决策】
政令内容："{player_decision}"

【决策特征分析】
- 是否听从顾问：{decision_analysis.get("followed_advisor", "独立决策")}
- 是否涉及暴力：{"是" if decision_analysis.get("was_violent") else "否"}
- 是否涉及欺骗：{"是" if decision_analysis.get("was_deceptive") else "否"}
- 是否公平公正：{"是" if decision_analysis.get("was_fair") else "否"}
- 是否包含承诺：{"是" if decision_analysis.get("contains_promise") else "否"}
- 是否秘密行动：{"是" if decision_analysis.get("is_secret_action") else "否"}

【当前权力状态】
- 掌控力: {game_state.power.authority:.0f}%
- 畏惧值: {game_state.power.fear:.0f}%
- 爱戴值: {game_state.power.love:.0f}%
- 信用分: {game_state.credit_score:.0f}

【顾问关系状态】
- 狮子(武力派): 信任度 {lion_relation.trust if lion_relation else 50}，忠诚度 {lion_relation.loyalty if lion_relation else 50}
- 狐狸(权谋派): 信任度 {fox_relation.trust if fox_relation else 50}，忠诚度 {fox_relation.loyalty if fox_relation else 50}
- 天平(民心派): 信任度 {balance_relation.trust if balance_relation else 50}，忠诚度 {balance_relation.loyalty if balance_relation else 50}

【《君主论》核心教诲参考】
1. "宁可被人畏惧，也不要被人爱戴" - 但过度恐惧会引发反抗
2. "暴力应当一次性使用" - 但持续使用会积累仇恨
3. "聪明的君主不应当守信" - 但过度欺骗会丧失信誉
4. "明智的君主应当建立在人民的支持之上" - 民心不可完全忽视
5. "必须懂得如何做野兽" - 狮子的勇猛与狐狸的狡诈缺一不可

请根据以上分析，生成2-4个政令可能带来的后续影响。影响分为两类：
1. **即时影响**：需要在当前回合处理，否则会直接影响统治结局（设置 requires_immediate=true）
2. **延迟影响**：会在后续关卡中体现，如果不处理会逐渐恶化（设置 affects_future=true）

每个影响都应该是合理的因果推演，并具有《君主论》的权谋深度。

返回JSON数组格式：
[
  {{
    "title": "影响标题（简短有力，如'军心动摇'、'民间流言'）",
    "description": "详细描述这个影响是如何从政令中产生的，50-80字",
    "severity": "low/medium/high/critical",
    "type": "political/economic/military/social/diplomatic",
    "potential_outcomes": ["可能的后果1", "可能的后果2", "可能的后果3"],
    "requires_action": true/false,
    "requires_immediate": true/false,
    "affects_future": true/false,
    "deadline_turns": 2-5,
    "power_impact": {{"authority": -5到5, "fear": -5到5, "love": -5到5}}
  }}
]

严重程度说明：
- low: 小波澜，暂时不需要处理
- medium: 需要关注，可能会发展
- high: 严重影响，应当尽快处理
- critical: 危机，必须立即处理

类型说明：
- political: 涉及权力、派系、官僚
- economic: 涉及财政、贸易、民生
- military: 涉及军队、武力、安全
- social: 涉及民心、舆论、社会稳定
- diplomatic: 涉及外交、联盟、其他势力

只返回JSON数组，不要其他解释。"""

        try:
            print(f"[ChapterEngine] 生成政令后续影响...")
            print(f"[ChapterEngine] 政令内容: {player_decision[:50]}...")
            print(f"[ChapterEngine] 使用模型: {self.model}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": context_prompt}],
                temperature=0.7,
                max_tokens=1200,
            )
            content = response.choices[0].message.content.strip()
            print(f"[ChapterEngine] 政令后果响应: {content[:100]}...")

            # 提取JSON
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                consequences_raw = json.loads(json_match.group())
                print(f"[ChapterEngine] 解析到 {len(consequences_raw)} 个后果")

                # 为每个后果生成唯一ID并验证格式
                consequences = []
                for c in consequences_raw:
                    consequence = {
                        "id": str(uuid.uuid4())[:8],
                        "title": c.get("title", "未知影响"),
                        "description": c.get("description", ""),
                        "severity": c.get("severity", "medium"),
                        "type": c.get("type", "political"),
                        "potential_outcomes": c.get("potential_outcomes", []),
                        "requires_action": c.get("requires_action", False),
                        "deadline_turns": c.get("deadline_turns", 3) if c.get("requires_action") else None,
                    }
                    # 验证severity和type的值
                    if consequence["severity"] not in ["low", "medium", "high", "critical"]:
                        consequence["severity"] = "medium"
                    if consequence["type"] not in ["political", "economic", "military", "social", "diplomatic"]:
                        consequence["type"] = "political"
                    consequences.append(consequence)

                # 存储上下文以便后续连续处理
                session_id = game_state.session_id
                self.consequence_context[session_id] = {
                    "original_decision": player_decision,
                    "consequences": consequences,
                    "chapter_context": {
                        "name": chapter.name,
                        "dilemma": chapter.dilemma,
                        "background": chapter.background,
                    },
                }

                print(f"[ChapterEngine] 政令后果生成成功")
                return consequences
            else:
                print(f"[ChapterEngine] 无法从响应中提取JSON数组")

        except Exception as e:
            print(f"[ChapterEngine] 生成政令后果失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        # 默认返回一个通用影响
        return [
            {
                "id": str(uuid.uuid4())[:8],
                "title": "政令反响",
                "description": "你的政令在朝野引起了一些反响，各方势力正在观望局势发展。",
                "severity": "low",
                "type": "political",
                "potential_outcomes": ["继续观望", "局势可能变化"],
                "requires_action": False,
                "deadline_turns": None,
            }
        ]

    async def continue_with_consequences(
        self,
        game_state: GameState,
        selected_consequence_id: str,
        player_response: str,
    ) -> dict:
        """
        处理玩家选择继续处理某个后果
        生成连贯的后续剧情和顾问回应
        """
        session_id = game_state.session_id
        context = self.consequence_context.get(session_id, {})

        if not context:
            return {"error": "没有找到后果上下文"}

        # 找到选中的后果
        selected_consequence = None
        for c in context.get("consequences", []):
            if c.get("id") == selected_consequence_id:
                selected_consequence = c
                break

        if not selected_consequence:
            return {"error": "未找到指定的后果"}

        chapter_context = context.get("chapter_context", {})
        original_decision = context.get("original_decision", "")

        # 生成后续场景
        scene_prompt = f"""你是《君主论》博弈游戏的叙事者。玩家之前发布了一道政令，现在选择继续处理其中一个后果。

【原政令】
{original_decision}

【玩家选择处理的后果】
标题：{selected_consequence.get("title")}
描述：{selected_consequence.get("description")}
严重程度：{selected_consequence.get("severity")}
类型：{selected_consequence.get("type")}
可能的结果：{", ".join(selected_consequence.get("potential_outcomes", []))}

【玩家的应对】
{player_response}

【关卡背景】
{chapter_context.get("name")} - {chapter_context.get("dilemma")}

请生成：
1. 一段简短的场景描述（50-100字），描述玩家应对后的新局势
2. 三位顾问对此事的简短评论（每人1-2句）

返回JSON格式：
{{
  "scene_update": "新局势描述",
  "advisor_comments": {{
    "lion": "狮子的评论",
    "fox": "狐狸的评论",
    "balance": "天平的评论"
  }},
  "consequence_resolved": true/false,
  "new_developments": ["如果有新的发展或影响，列在这里"]
}}"""

        try:
            print(f"[ChapterEngine] 处理后果: {selected_consequence.get('title', 'unknown')}...")
            print(f"[ChapterEngine] 玩家应对: {player_response[:50]}...")
            print(f"[ChapterEngine] 使用模型: {self.model}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": scene_prompt}],
                temperature=0.7,
                max_tokens=600,
            )
            content = response.choices[0].message.content.strip()
            print(f"[ChapterEngine] 后果处理响应: {content[:100]}...")

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                print(f"[ChapterEngine] 后果处理成功")
                return result
            else:
                print(f"[ChapterEngine] 无法从响应中提取JSON")

        except Exception as e:
            print(f"[ChapterEngine] 处理后果失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        print("[ChapterEngine] 使用默认后果处理结果")
        return {
            "scene_update": "你的应对暂时稳定了局势。",
            "advisor_comments": {
                "lion": "且看后续发展。",
                "fox": "还需观察。",
                "balance": "情况有所缓和。",
            },
            "consequence_resolved": True,
            "new_developments": [],
        }

    async def generate_next_round_scene(
        self,
        game_state: GameState,
        previous_decision: str,
        consequences: List[Dict[str, Any]],
        chapter: Chapter,
    ) -> dict:
        """
        生成继续当前回合时的新场景
        包括场景变化描述和顾问针对上轮政令及影响的新观点
        """
        # 获取顾问关系
        lion_relation = game_state.relations.get("lion")
        fox_relation = game_state.relations.get("fox")
        balance_relation = game_state.relations.get("balance")

        consequences_desc = "\n".join([
            f"- {c.get('title')}（{c.get('severity')}）: {c.get('description')}"
            for c in consequences
        ]) if consequences else "暂无明显影响"

        prompt = f"""你是《君主论》博弈游戏的叙事者和三位顾问。

【背景】
关卡：{chapter.name}
困境：{chapter.dilemma}
当前回合：{game_state.chapter_turn}

【上一轮政令】
{previous_decision}

【政令产生的影响】
{consequences_desc}

【当前权力状态】
- 掌控力: {game_state.power.authority:.0f}%
- 畏惧值: {game_state.power.fear:.0f}%
- 爱戴值: {game_state.power.love:.0f}%

【顾问状态】
- 狮子: 信任度 {lion_relation.trust if lion_relation else 50}（{"敌对" if lion_relation and lion_relation.is_hostile else "正常"}）
- 狐狸: 信任度 {fox_relation.trust if fox_relation else 50}（{"敌对" if fox_relation and fox_relation.is_hostile else "正常"}）
- 天平: 信任度 {balance_relation.trust if balance_relation else 50}（{"敌对" if balance_relation and balance_relation.is_hostile else "正常"}）

请生成：
1. 场景变化描述（50-80字）：描述政令执行后局势的变化
2. 三位顾问针对上轮政令和当前影响的新观点和建议（每人2-3句，要体现各自立场）
3. 新的困境或需要处理的问题（如果有的话）

【顾问人设提醒】
- 狮子：崇尚武力与威慑，说话简洁有力，军人作风
- 狐狸：善于权谋与算计，绵里藏针，喜欢暗示
- 天平：追求公正与稳定，引用数据，关心民众

返回JSON格式：
{{
  "scene_update": "场景变化描述",
  "new_dilemma": "新的困境或问题（可为空）",
  "advisor_comments": {{
    "lion": {{
      "stance": "支持/反对/观望",
      "comment": "狮子对上轮政令的评价和新建议",
      "suggestion": "下一步建议（可选）"
    }},
    "fox": {{
      "stance": "支持/反对/观望",
      "comment": "狐狸对上轮政令的评价和新建议",
      "suggestion": "下一步建议（可选）"
    }},
    "balance": {{
      "stance": "支持/反对/观望",
      "comment": "天平对上轮政令的评价和新建议",
      "suggestion": "下一步建议（可选）"
    }}
  }}
}}"""

        try:
            print(f"[ChapterEngine] 生成新回合场景...")
            print(f"[ChapterEngine] 上一轮政令: {previous_decision[:50] if previous_decision else 'None'}...")
            print(f"[ChapterEngine] 使用模型: {self.model}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800,
            )
            content = response.choices[0].message.content.strip()
            print(f"[ChapterEngine] 新回合场景响应: {content[:100]}...")

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                print(f"[ChapterEngine] 新回合场景生成成功")
                print(f"[ChapterEngine] 场景更新: {result.get('scene_update', '')[:50]}...")
                return result
            else:
                print(f"[ChapterEngine] 无法从响应中提取JSON")

        except Exception as e:
            print(f"[ChapterEngine] 生成新回合场景失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        # 默认返回
        print("[ChapterEngine] 使用默认新回合场景")
        return {
            "scene_update": "政令已经开始执行，各方势力正在观望局势发展。",
            "new_dilemma": "",
            "advisor_comments": {
                "lion": {"stance": "观望", "comment": "让我们看看效果如何。", "suggestion": ""},
                "fox": {"stance": "观望", "comment": "局势尚不明朗。", "suggestion": ""},
                "balance": {"stance": "观望", "comment": "需要观察民众的反应。", "suggestion": ""},
            }
        }

    async def analyze_player_intent(
        self,
        game_state: GameState,
        player_message: str,
        chapter: Chapter,
        conversation_history: List[dict] = None,
    ) -> dict:
        """
        分析玩家在廷议阶段的意图
        判断玩家是提问、质疑、挑拨还是准备发布政令
        """
        # 获取顾问关系
        lion_relation = game_state.relations.get("lion")
        fox_relation = game_state.relations.get("fox")
        balance_relation = game_state.relations.get("balance")

        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{msg.get('speaker', '???')}: {msg.get('content', '')}"
                for msg in conversation_history[-6:]  # 最近6条对话
            ])

        prompt = f"""你是《君主论》博弈游戏的意图分析器。分析玩家在廷议阶段的发言意图。

【当前关卡】
{chapter.name}: {chapter.dilemma}

【顾问状态】
- 狮子: 信任度 {lion_relation.trust if lion_relation else 50}
- 狐狸: 信任度 {fox_relation.trust if fox_relation else 50}
- 天平: 信任度 {balance_relation.trust if balance_relation else 50}

【近期对话】
{history_text if history_text else "（无）"}

【玩家发言】
"{player_message}"

分析玩家的意图，返回JSON：
{{
  "intent": "question/challenge/provoke/debate/negotiate/command/other",
  "target": "lion/fox/balance/all/none",
  "tone": "friendly/neutral/hostile/manipulative",
  "summary": "简短描述玩家想要什么",
  "triggers_conflict": true/false,
  "suggested_reactions": {{
    "lion": "狮子应该如何反应（简短描述）",
    "fox": "狐狸应该如何反应（简短描述）",
    "balance": "天平应该如何反应（简短描述）"
  }}
}}

意图说明：
- question: 玩家在询问信息或寻求建议
- challenge: 玩家在质疑某个顾问的建议或能力
- provoke: 玩家在挑拨顾问之间的关系
- debate: 玩家要求顾问互相辩论
- negotiate: 玩家在尝试谈判或讨价还价
- command: 玩家在下达命令
- other: 其他意图"""

        try:
            print(f"[ChapterEngine] 分析玩家意图: {player_message[:50]}...")
            print(f"[ChapterEngine] 使用模型: {self.model}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400,
            )
            content = response.choices[0].message.content.strip()
            print(f"[ChapterEngine] 意图分析响应: {content[:100]}...")

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                print(f"[ChapterEngine] 意图分析成功: {result.get('intent', 'unknown')}")
                return result
            else:
                print(f"[ChapterEngine] 无法从响应中提取JSON")

        except Exception as e:
            print(f"[ChapterEngine] 分析玩家意图失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        print("[ChapterEngine] 使用默认意图分析结果")
        return {
            "intent": "other",
            "target": "all",
            "tone": "neutral",
            "summary": player_message[:50],
            "triggers_conflict": False,
            "suggested_reactions": {
                "lion": "简短回应",
                "fox": "简短回应",
                "balance": "简短回应"
            }
        }

    async def generate_council_response(
        self,
        game_state: GameState,
        player_message: str,
        intent_analysis: dict,
        chapter: Chapter,
    ) -> dict:
        """
        根据玩家意图生成顾问在廷议中的回应
        """
        lion_relation = game_state.relations.get("lion")
        fox_relation = game_state.relations.get("fox")
        balance_relation = game_state.relations.get("balance")

        intent = intent_analysis.get("intent", "other")
        target = intent_analysis.get("target", "all")
        tone = intent_analysis.get("tone", "neutral")
        triggers_conflict = intent_analysis.get("triggers_conflict", False)
        suggested_reactions = intent_analysis.get("suggested_reactions", {})

        prompt = f"""你是《君主论》博弈游戏中的三位顾问。根据玩家的发言生成回应。

【关卡背景】
{chapter.name}: {chapter.dilemma}

【玩家发言】
"{player_message}"

【意图分析】
- 意图类型: {intent}
- 针对目标: {target}
- 语气: {tone}
- 是否触发冲突: {triggers_conflict}

【顾问状态与人设】
🦁 狮子（信任度 {lion_relation.trust if lion_relation else 50}）:
  - 人设：武力与威慑的化身，简洁有力，军人作风，崇尚"宁可被畏惧"
  - 建议反应：{suggested_reactions.get("lion", "正常回应")}
  {"- 当前敌对中，态度冷淡" if lion_relation and lion_relation.is_hostile else ""}

🦊 狐狸（信任度 {fox_relation.trust if fox_relation else 50}）:
  - 人设：权谋与狡诈的化身，绵里藏针，善于暗示，相信"目的证明手段"
  - 建议反应：{suggested_reactions.get("fox", "正常回应")}
  {"- 当前敌对中，暗藏杀机" if fox_relation and fox_relation.is_hostile else ""}

⚖️ 天平（信任度 {balance_relation.trust if balance_relation else 50}）:
  - 人设：公正与民心的化身，引用数据，关心民众，追求稳定
  - 建议反应：{suggested_reactions.get("balance", "正常回应")}
  {"- 当前敌对中，失望透顶" if balance_relation and balance_relation.is_hostile else ""}

【回应要求】
1. 如果玩家质疑某顾问：该顾问需防御性辩解，可能暴露性格缺陷
2. 如果玩家挑拨：触发顾问之间的争吵或互相指责
3. 如果玩家要求辩论：顾问之间展开交锋
4. 如果玩家提问：根据各自立场给出不同角度的回答
5. 低信任度的顾问应表现出不满或敷衍

返回JSON格式：
{{
  "responses": {{
    "lion": "狮子的回应（1-3句）",
    "fox": "狐狸的回应（1-3句）",
    "balance": "天平的回应（1-3句）"
  }},
  "conflict_triggered": true/false,
  "conflict_description": "如果有冲突，描述冲突情况",
  "trust_changes": {{
    "lion": -3到3,
    "fox": -3到3,
    "balance": -3到3
  }},
  "atmosphere": "friendly/tense/hostile/chaotic"
}}"""

        try:
            print(f"[ChapterEngine] 生成廷议回应...")
            print(f"[ChapterEngine] 玩家发言: {player_message[:50]}...")
            print(f"[ChapterEngine] 意图: {intent_analysis.get('intent', 'unknown')}")
            print(f"[ChapterEngine] 使用模型: {self.model}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=600,
            )
            content = response.choices[0].message.content.strip()
            print(f"[ChapterEngine] 廷议回应响应: {content[:100]}...")

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                print(f"[ChapterEngine] 廷议回应生成成功")
                return result
            else:
                print(f"[ChapterEngine] 无法从响应中提取JSON")

        except Exception as e:
            print(f"[ChapterEngine] 生成廷议回应失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        print("[ChapterEngine] 使用默认廷议回应")
        return {
            "responses": {
                "lion": "臣听候差遣。",
                "fox": "需要深思熟虑。",
                "balance": "当以民为本。"
            },
            "conflict_triggered": False,
            "conflict_description": "",
            "trust_changes": {"lion": 0, "fox": 0, "balance": 0},
            "atmosphere": "neutral"
        }

    # ==================== 因果系统 (Causal System) ====================

    async def analyze_decision_for_seeds(
        self,
        game_state: GameState,
        player_decision: str,
        decision_analysis: dict,
        chapter: Chapter,
    ) -> List[Dict[str, Any]]:
        """
        [因果记录协议] 分析决策并生成伏笔种子
        在发布政令后的结算阶段，分析玩家决策的长远副作用
        """
        # 获取当前因果上下文
        causal_context = game_state.get_causal_context_for_ai()

        prompt = f"""## [因果记录协议] (Causal Logging Protocol)

你是《君主论》博弈游戏的因果分析师。在【发布政令】后的结算阶段，你必须分析玩家决策的长远副作用。

【当前关卡】
关卡：{chapter.name} - {chapter.subtitle}
困境：{chapter.dilemma}
当前回合：{game_state.chapter_turn}

【玩家决策】
政令内容："{player_decision}"

【决策特征】
- 是否涉及暴力：{"是" if decision_analysis.get("was_violent") else "否"}
- 是否涉及欺骗：{"是" if decision_analysis.get("was_deceptive") else "否"}
- 是否公平公正：{"是" if decision_analysis.get("was_fair") else "否"}
- 是否包含承诺：{"是" if decision_analysis.get("contains_promise") else "否"}
- 是否秘密行动：{"是" if decision_analysis.get("is_secret_action") else "否"}

【当前权力状态】
- 掌控力: {game_state.power.authority:.0f}%
- 畏惧值: {game_state.power.fear:.0f}%
- 爱戴值: {game_state.power.love:.0f}%
- 信用分: {game_state.credit_score:.0f}

【已有的伏笔种子】
{json.dumps(causal_context.get("pending_seeds", []), ensure_ascii=False, indent=2)}

【《君主论》因果教诲】
1. "欺骗"行为 → 2关卡后可能被揭穿，引发信任危机
2. "借贷/许诺"行为 → 到期时必须偿还，否则信誉崩溃
3. "残酷镇压"行为 → 短期有效，长期积累民怨
4. "过度仁慈"行为 → 可能被视为软弱，引发野心家觊觎
5. "背叛盟友"行为 → 未来可能遭到报复或孤立

【生成规则】
1. **分析副作用**：如果玩家使用了"欺骗"、"借贷"、"残酷镇压"、"过度仁慈"或"背叛"，必须生成【因果种子】
2. **定义触发期**：
   - 通常在 2-3 个关卡后爆发
   - 或者标记为条件触发 (如 "LOW_LOVE", "ANY_RIOT", "BETRAYAL_RISK")
3. **如果决策相对中庸或没有明显副作用，可以不生成种子**

返回JSON格式：
{{
  "should_plant_seed": true/false,
  "seeds": [
    {{
      "tag": "DECEPTION/VIOLENCE/BROKEN_PROMISE/MERCY/DEBT/CORRUPTION/BETRAYAL/OTHER",
      "description": "简短描述这个决策造成的隐患（例如：士兵手里拿着大量假币）",
      "player_visible_hint": "给玩家的隐晦暗示（例如：有些事情不会被遗忘...）",
      "severity": "LOW/MEDIUM/HIGH/CRITICAL",
      "trigger_delay": 2-4,
      "trigger_condition": "可选：LOW_LOVE/LOW_FEAR/ANY_RIOT/BETRAYAL_RISK/null"
    }}
  ],
  "analysis": "为什么这个决策会埋下隐患的简短分析"
}}

如果不需要生成种子，返回：
{{
  "should_plant_seed": false,
  "seeds": [],
  "analysis": "为什么这个决策相对安全"
}}"""

        try:
            print(f"[ChapterEngine][因果系统] 分析决策种子...")
            print(f"[ChapterEngine][因果系统] 政令: {player_decision[:50]}...")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=800,
            )
            content = response.choices[0].message.content.strip()
            print(f"[ChapterEngine][因果系统] 种子分析响应: {content[:100]}...")

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                print(f"[ChapterEngine][因果系统] 是否需要种子: {result.get('should_plant_seed')}")

                if result.get("should_plant_seed") and result.get("seeds"):
                    # 创建实际的种子对象
                    created_seeds = []
                    for seed_data in result["seeds"]:
                        seed = game_state.add_shadow_seed(
                            description=seed_data.get("description", "未知隐患"),
                            tag=ShadowSeedTag(seed_data.get("tag", "OTHER")),
                            severity=ShadowSeedSeverity(seed_data.get("severity", "MEDIUM")),
                            trigger_delay=seed_data.get("trigger_delay"),
                            trigger_condition=seed_data.get("trigger_condition"),
                            player_visible_hint=seed_data.get("player_visible_hint"),
                        )
                        created_seeds.append({
                            "id": seed.id,
                            "description": seed.description,
                            "tag": seed.tag.value,
                            "severity": seed.severity.value,
                            "trigger_delay": seed.trigger_delay,
                            "player_visible_hint": seed.player_visible_hint,
                        })
                        print(f"[ChapterEngine][因果系统] 创建种子: {seed.description[:30]}...")

                    return created_seeds

                return []

        except Exception as e:
            print(f"[ChapterEngine][因果系统] 分析种子失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        return []

    async def check_and_trigger_echoes(
        self,
        game_state: GameState,
        chapter: Chapter,
    ) -> List[Dict[str, Any]]:
        """
        [因果回响读取] 在关卡开始时检查并触发伏笔
        将需要触发的种子转化为场景叙事
        """
        # 检查当前关卡应该触发的种子
        seeds_to_trigger = game_state.check_seeds_for_chapter(chapter.id.value)

        if not seeds_to_trigger:
            print(f"[ChapterEngine][因果系统] 本关卡无需触发的种子")
            return []

        print(f"[ChapterEngine][因果系统] 发现 {len(seeds_to_trigger)} 个需要触发的种子")

        triggered_echoes = []

        for seed in seeds_to_trigger:
            echo = await self._generate_echo_for_seed(game_state, seed, chapter)
            if echo:
                triggered_echoes.append(echo)

        return triggered_echoes

    async def _generate_echo_for_seed(
        self,
        game_state: GameState,
        seed: ShadowSeed,
        chapter: Chapter,
    ) -> Optional[Dict[str, Any]]:
        """
        为单个种子生成因果回响
        """
        prompt = f"""## [因果回响生成] (Causal Echo Retrieval)

你是《君主论》博弈游戏的叙事者。一个过去的决策正在显现其后果。

【原始决策（种子）】
- 来源关卡: {seed.origin_chapter}
- 来源回合: {seed.origin_turn}
- 类型标签: {seed.tag.value}
- 描述: {seed.description}
- 严重程度: {seed.severity.value}

【当前关卡】
关卡: {chapter.name}
困境: {chapter.dilemma}
场景: {chapter.scene_snapshot}

【当前权力状态】
- 掌控力: {game_state.power.authority:.0f}%
- 畏惧值: {game_state.power.fear:.0f}%
- 爱戴值: {game_state.power.love:.0f}%

【生成要求】
1. **强制整合**：你必须将这个种子的后果，编织进当前关卡的【危机场景描述】中
2. **叠加难度**：这个旧债必须让当前的危机变得更难处理
3. **NPC 记忆**：
   - 天平必须明确指出这是过去决定的利息
   - 狮子/狐狸根据性格对旧账进行嘲讽或推卸责任

返回JSON格式：
{{
  "echo_narrative": "一段描述旧决策后果如何在当前爆发的叙事文本（50-100字）",
  "crisis_modifier": "这个回响如何让当前危机变得更复杂（30-50字）",
  "advisor_reactions": {{
    "lion": "狮子的反应（1-2句）",
    "fox": "狐狸的反应（1-2句）",
    "balance": "天平的反应（必须提到这是过去决策的后果）（1-2句）"
  }},
  "additional_impact": {{
    "authority": -10到10,
    "fear": -10到10,
    "love": -10到10
  }}
}}"""

        try:
            print(f"[ChapterEngine][因果系统] 生成回响: {seed.description[:30]}...")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600,
            )
            content = response.choices[0].message.content.strip()

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())

                # 在游戏状态中记录触发
                echo = game_state.trigger_seed(
                    seed_id=seed.id,
                    echo_narrative=result.get("echo_narrative", "过去的决策显现了后果..."),
                    crisis_modifier=result.get("crisis_modifier", "局势变得更加复杂"),
                    advisor_reactions=result.get("advisor_reactions", {}),
                )

                # [即时标记系统] 根据种子类型创建即时标记
                self._create_flag_from_seed(game_state, seed, result)

                # 应用额外影响
                impact = result.get("additional_impact", {})
                if impact:
                    game_state.power = game_state.power.apply_delta(
                        delta_a=impact.get("authority", 0),
                        delta_f=impact.get("fear", 0),
                        delta_l=impact.get("love", 0),
                    )

                print(f"[ChapterEngine][因果系统] 回响生成成功")

                return {
                    "seed_id": seed.id,
                    "seed_description": seed.description,
                    "origin_chapter": seed.origin_chapter,
                    "echo_narrative": result.get("echo_narrative"),
                    "crisis_modifier": result.get("crisis_modifier"),
                    "advisor_reactions": result.get("advisor_reactions", {}),
                    "trigger_chapter": chapter.id.value,
                    "trigger_turn": game_state.total_turn,
                }

        except Exception as e:
            print(f"[ChapterEngine][因果系统] 生成回响失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        return None

    def _create_flag_from_seed(
        self,
        game_state: GameState,
        seed: ShadowSeed,
        echo_result: Dict[str, Any],
    ) -> None:
        """[即时标记系统] 根据触发的种子创建即时状态标记"""
        from models.game_state import ImmediateFlagType

        # 根据种子类型创建不同的即时标记
        flag_configs = {
            "DECEPTION": {
                "name": "信任危机",
                "description": "过去的欺骗行为被揭露",
                "effect_on_scene": "顾问们对你的话语持怀疑态度",
                "type": ImmediateFlagType.DEBUFF,
                "duration_turns": 3,
                "modifiers": {"trust_penalty": -10},
            },
            "VIOLENCE": {
                "name": "血腥阴影",
                "description": "过去的暴力行为留下的创伤",
                "effect_on_scene": "民众和官员都对你心怀畏惧，但也暗藏仇恨",
                "type": ImmediateFlagType.MODIFIER,
                "duration_turns": 4,
                "modifiers": {"fear_bonus": 5, "love_penalty": -5},
            },
            "BROKEN_PROMISE": {
                "name": "失信之名",
                "description": "违背的承诺被人记起",
                "effect_on_scene": "你的每一个承诺都被人怀疑",
                "type": ImmediateFlagType.DEBUFF,
                "duration_turns": 5,
                "modifiers": {"credit_penalty": -10},
            },
            "MERCY": {
                "name": "软弱印象",
                "description": "过去的仁慈被视为软弱",
                "effect_on_scene": "有人试图利用你的仁慈",
                "type": ImmediateFlagType.DEBUFF,
                "duration_turns": 2,
                "modifiers": {"authority_penalty": -5},
            },
            "DEBT": {
                "name": "债务追讨",
                "description": "旧债到期，债主登门",
                "effect_on_scene": "必须处理拖欠的债务",
                "type": ImmediateFlagType.DEBUFF,
                "duration_turns": 3,
                "modifiers": {"resource_penalty": -15},
            },
            "CORRUPTION": {
                "name": "腐败丑闻",
                "description": "腐败行为被曝光",
                "effect_on_scene": "民众对朝廷的信任大降",
                "type": ImmediateFlagType.DEBUFF,
                "duration_turns": 4,
                "modifiers": {"love_penalty": -10, "authority_penalty": -5},
            },
            "BETRAYAL": {
                "name": "背叛者的报复",
                "description": "曾被背叛的盟友归来",
                "effect_on_scene": "旧敌在暗中活动",
                "type": ImmediateFlagType.DEBUFF,
                "duration_turns": 3,
                "modifiers": {"danger_bonus": 20},
            },
        }

        config = flag_configs.get(seed.tag.value)
        if config:
            game_state.add_immediate_flag(
                name=config["name"],
                description=config["description"],
                effect_on_scene=config["effect_on_scene"],
                flag_type=config["type"],
                duration_turns=config["duration_turns"],
                modifiers=config["modifiers"],
                source_seed_id=seed.id,
            )
            print(f"[ChapterEngine][即时标记] 创建标记: {config['name']}")

    async def get_scene_with_echoes(
        self,
        game_state: GameState,
        chapter: Chapter,
        triggered_echoes: List[Dict[str, Any]],
    ) -> str:
        """
        生成包含因果回响的关卡场景描述
        """
        if not triggered_echoes:
            return chapter.scene_snapshot

        echoes_desc = "\n".join([
            f"- {echo.get('echo_narrative', '')}"
            for echo in triggered_echoes
        ])

        prompt = f"""你是《君主论》博弈游戏的叙事者。
需要将过去决策的后果整合到当前关卡场景中。

【原始场景】
{chapter.scene_snapshot}

【当前困境】
{chapter.dilemma}

【需要整合的因果回响】
{echoes_desc}

请重新撰写场景描述，将因果回响自然地融入其中，使其成为当前困境的一部分。
要求：
1. 保持原场景的核心内容
2. 将回响作为额外的复杂因素加入
3. 语言风格保持古典文言白话混合
4. 总长度100-150字

直接返回新的场景描述，不要其他解释。"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[ChapterEngine][因果系统] 整合场景失败: {e}")
            # 返回原场景加上回响提示
            return f"{chapter.scene_snapshot}\n\n【命运的回响】\n{echoes_desc}"
