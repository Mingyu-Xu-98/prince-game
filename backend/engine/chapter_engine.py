"""
关卡引擎
管理关卡流程、议会辩论和场景生成
"""
from typing import Optional, List, Dict, Any
import json
import re
from openai import AsyncOpenAI
from config import settings
from models import GameState, ChapterLibrary, ChapterID, Chapter
from models.game_state import DecisionRecord


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

        # 生成开场
        opening = await self.generate_chapter_opening(chapter, game_state)

        return {
            "chapter": {
                "id": chapter.id.value,
                "name": chapter.name,
                "subtitle": chapter.subtitle,
                "complexity": chapter.complexity,
                "max_turns": chapter.max_turns,
            },
            "background": chapter.background,
            "scene_snapshot": chapter.scene_snapshot,
            "dilemma": chapter.dilemma,
            "opening_narration": opening,
            "council_debate": await self.generate_council_debate(chapter, game_state),
            "state": game_state.to_summary(include_hidden=not chapter.hide_values),
        }

    async def generate_chapter_opening(self, chapter: Chapter, game_state: GameState) -> str:
        """生成关卡开场白"""
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

请用2-3段话，以第二人称"你"来叙述，营造紧张而庄严的气氛。
风格要求：古典文言白话混合，有历史感，突出困境的紧迫性。"""

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

        # 基础建议
        debate = {
            "lion": {
                "suggestion": chapter.lion_suggestion.suggestion,
                "reasoning": chapter.lion_suggestion.reasoning,
                "tone": self._get_advisor_tone("lion", lion_rel),
                "trust_level": lion_rel.trust if lion_rel else 50,
            },
            "fox": {
                "suggestion": chapter.fox_suggestion.suggestion,
                "reasoning": chapter.fox_suggestion.reasoning,
                "tone": self._get_advisor_tone("fox", fox_rel),
                "trust_level": fox_rel.trust if fox_rel else 50,
                "has_leverage": len(game_state.get_leverages_by_holder("fox")) > 0,
            },
        }

        if chapter.balance_suggestion:
            debate["balance"] = {
                "suggestion": chapter.balance_suggestion.suggestion,
                "reasoning": chapter.balance_suggestion.reasoning,
                "tone": self._get_advisor_tone("balance", balance_rel),
                "trust_level": balance_rel.trust if balance_rel else 50,
            }

        # 生成动态对话
        debate["dynamic_dialogue"] = await self._generate_debate_dialogue(chapter, game_state)

        return debate

    def _get_advisor_tone(self, advisor: str, relation) -> str:
        """根据关系获取顾问语气"""
        if not relation:
            return "neutral"

        if relation.trust > 70:
            return "loyal"
        elif relation.trust > 30:
            return "professional"
        elif relation.trust > -30:
            return "cautious"
        else:
            return "hostile"

    async def _generate_debate_dialogue(self, chapter: Chapter, game_state: GameState) -> list[dict]:
        """生成议会辩论对话"""
        # 检查是否有顾问冲突
        has_conflict = chapter.id in [ChapterID.CHAPTER_3, ChapterID.CHAPTER_4]

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
5. 只返回JSON数组"""

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

        # 进入下一回合
        game_state.next_turn()

        # 检查关卡结束条件
        chapter_result = self._check_chapter_conditions(game_state, chapter)

        # 生成政令后续影响
        decree_consequences = await self.generate_decree_consequences(
            game_state=game_state,
            player_decision=player_input,
            decision_analysis=analysis,
            chapter=chapter,
        )

        return {
            "decision_analysis": analysis,
            "impact": impact,
            "promises_broken": [p.content for p in game_state.check_broken_promises()],
            "secrets_leaked": [s.action for s in game_state.check_secret_leaks()],
            "chapter_result": chapter_result,
            "state": game_state.to_summary(include_hidden=not chapter.hide_values),
            "decree_consequences": decree_consequences,  # 添加政令后续影响
        }

    async def _analyze_decision(self, player_input: str, chapter: Chapter) -> dict:
        """分析玩家决策"""
        prompt = f"""分析玩家在《君主论》博弈游戏中的决策。

关卡：{chapter.name}
困境：{chapter.dilemma}

顾问建议：
- 狮子：{chapter.lion_suggestion.suggestion}
- 狐狸：{chapter.fox_suggestion.suggestion}
- 天平：{chapter.balance_suggestion.suggestion if chapter.balance_suggestion else "无"}

玩家决策："{player_input}"

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
  "analysis": "简短分析"
}}

数值范围：-20到+20"""

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
        }

        # 检查失败条件
        if game_state.power.authority <= 0:
            result["chapter_ended"] = True
            result["victory"] = False
            result["reason"] = "篡位：你的掌控力归零，被权臣架空"
            game_state.fail_chapter(result["reason"])
            return result

        if game_state.power.love <= 0:
            result["chapter_ended"] = True
            result["victory"] = False
            result["reason"] = "暴乱：民众的愤怒彻底爆发"
            game_state.fail_chapter(result["reason"])
            return result

        if game_state.power.fear > 90 and game_state.power.love < 20:
            result["chapter_ended"] = True
            result["victory"] = False
            result["reason"] = "暗杀：高压统治引发刺杀"
            game_state.fail_chapter(result["reason"])
            return result

        # 检查回合限制
        if game_state.chapter_turn >= chapter.max_turns:
            # 根据状态判断胜负
            if game_state.power.authority > 30 and game_state.power.love > 20:
                result["chapter_ended"] = True
                result["victory"] = True
                result["reason"] = "关卡完成"
                score = int(game_state.power.authority + game_state.power.love - game_state.power.fear * 0.5)
                game_state.complete_chapter("survived", score)
            else:
                result["chapter_ended"] = True
                result["victory"] = False
                result["reason"] = "统治崩溃：无法维持平衡"
                game_state.fail_chapter(result["reason"])

        return result

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
            "lion": "简洁有力，军人作风，直接表达态度",
            "fox": "绵里藏针，若即若离，喜欢暗示",
            "balance": "客观公正，引用数据，关心民众",
        }

        prompt = f"""你是《君主论》游戏中的{advisor_names[advisor]}顾问。

你的风格：{advisor_styles[advisor]}
你与君主的关系：信任度 {relation.trust if relation else 50}，忠诚度 {relation.loyalty if relation else 50}
君主{"听从了你的建议" if followed else ("拒绝了你的建议" if rejected else "做出了独立决策")}
{"你手中握有君主的把柄" if has_leverage else ""}

君主的决策："{player_input}"
决策分析：{"暴力" if analysis.get("was_violent") else ""}{"欺骗" if analysis.get("was_deceptive") else ""}{"公平" if analysis.get("was_fair") else "普通"}

请生成你的回应（2-3句话）：
1. 表达对决策的态度
2. 根据你的人设做出评价
3. {"如果信任度低于0，暗示你的不满" if relation and relation.trust < 0 else ""}
4. {"如果你有把柄，可以隐晦提及" if has_leverage else ""}"""

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
