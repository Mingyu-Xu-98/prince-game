"""
关卡引擎
管理关卡流程、议会辩论和场景生成
"""
from typing import Optional
from openai import AsyncOpenAI
from config import settings
from models import GameState, ChapterLibrary, ChapterID, Chapter
from models.game_state import DecisionRecord


class ChapterEngine:
    """关卡引擎"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.default_model
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=settings.openrouter_base_url,
        )

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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=400,
            )
            return response.choices[0].message.content.strip()
        except Exception:
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=800,
            )
            content = response.choices[0].message.content.strip()
            # 提取JSON
            import json
            import re
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass

        # 默认对话
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

        return {
            "decision_analysis": analysis,
            "impact": impact,
            "promises_broken": [p.content for p in game_state.check_broken_promises()],
            "secrets_leaked": [s.action for s in game_state.check_secret_leaks()],
            "chapter_result": chapter_result,
            "state": game_state.to_summary(include_hidden=not chapter.hide_values),
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            import json
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass

        # 默认分析
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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            if followed:
                return "明智的选择。"
            elif rejected:
                return "……如你所愿。"
            else:
                return "臣领命。"
