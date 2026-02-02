"""
狐狸 Skill - 语义一致性与影响力审计
基于《君主论》中的权谋与欺诈原则，以及《影响力》六原则
"君主必须知道如何善于使用野兽的方式...必须同时是狐狸和狮子"
"""
from .base_skill import BaseSkill, AuditResult
from models.game_state import GameState, Promise
from difflib import SequenceMatcher


class FoxSkill(BaseSkill):
    """狐狸审计 - 语义一致性与影响力审计"""

    name = "fox"
    description = "语义一致性审计：检测承诺矛盾、话术技巧和影响力运用"

    # 承诺相关关键词
    promise_keywords = [
        "保证", "承诺", "一定", "绝对", "肯定", "必定", "必将",
        "答应", "许诺", "誓言", "发誓", "保障", "确保", "担保",
        "不会", "绝不", "永远", "始终", "从此", "以后",
    ]

    # 矛盾指示词（政策方向）
    policy_increase = ["增加", "提高", "加强", "扩大", "加重", "加征", "增税", "征收"]
    policy_decrease = ["减少", "降低", "减轻", "缩小", "减免", "减税", "豁免", "取消"]

    # 影响力技巧关键词（基于《影响力》六原则）
    influence_keywords = {
        "scarcity": ["最后", "仅此", "唯一", "机会", "错过", "稀缺", "限时", "紧迫"],
        "authority": ["专家", "权威", "经验", "历史", "传统", "祖训", "先例", "圣旨"],
        "social_proof": ["大家", "所有人", "民心", "众望", "公论", "天下", "百姓都"],
        "liking": ["友谊", "情分", "恩情", "交情", "兄弟", "共患难", "同甘共苦"],
        "reciprocity": ["回报", "报答", "恩惠", "亏欠", "补偿", "还人情"],
        "commitment": ["既然", "既定", "已经", "说过", "承诺过", "一贯"],
    }

    # 对象关键词
    target_groups = {
        "nobles": ["贵族", "大臣", "官员", "权贵", "世家", "门阀"],
        "military": ["将军", "士兵", "军队", "禁军", "边军", "武将"],
        "merchants": ["商人", "富商", "商贾", "巨贾", "商会"],
        "peasants": ["农民", "百姓", "平民", "庶民", "黎民", "子民"],
        "clergy": ["僧侣", "道士", "教士", "神职", "祭司", "方丈"],
    }

    async def audit(
        self,
        player_input: str,
        parsed_intent: dict,
        game_state: GameState,
    ) -> AuditResult:
        """执行语义一致性审计"""

        warnings = []
        detected_keywords = []

        # 1. 检测承诺
        promise_detected = self.detect_keywords(player_input, self.promise_keywords)
        detected_keywords.extend(promise_detected)

        # 2. 检测政策方向
        increase_detected = self.detect_keywords(player_input, self.policy_increase)
        decrease_detected = self.detect_keywords(player_input, self.policy_decrease)
        detected_keywords.extend(increase_detected + decrease_detected)

        # 3. 检测目标群体
        current_targets = []
        for group, keywords in self.target_groups.items():
            if self.detect_keywords(player_input, keywords):
                current_targets.append(group)

        # 4. 检测影响力技巧
        influence_score = 0
        influence_used = []
        for technique, keywords in self.influence_keywords.items():
            if self.detect_keywords(player_input, keywords):
                influence_score += 8
                influence_used.append(technique)
                detected_keywords.extend(self.detect_keywords(player_input, keywords))

        # 5. 一致性检查 - 与历史承诺比对
        consistency_score = 0
        contradictions = []

        if current_targets and (increase_detected or decrease_detected):
            current_direction = "increase" if increase_detected else "decrease"

            for target in current_targets:
                past_promises = self._get_target_promises(game_state, target)
                for promise in past_promises:
                    # 检测方向矛盾
                    past_increase = any(kw in promise.content for kw in self.policy_increase)
                    past_decrease = any(kw in promise.content for kw in self.policy_decrease)

                    if past_increase and current_direction == "decrease":
                        contradictions.append(f"对{target}：曾承诺增加，现在减少")
                        consistency_score -= 20
                    elif past_decrease and current_direction == "increase":
                        contradictions.append(f"对{target}：曾承诺减少，现在增加")
                        consistency_score -= 20

        # 6. 检测对不同群体的矛盾承诺（同一回合内）
        if len(current_targets) > 1:
            if increase_detected and decrease_detected:
                contradictions.append("同时承诺增加和减少，言辞自相矛盾")
                consistency_score -= 15

        # 7. 综合评分
        has_contradiction = len(contradictions) > 0
        uses_influence = len(influence_used) > 0

        if has_contradiction:
            delta_a = -15.0 - len(contradictions) * 5
            delta_f = -5.0
            delta_l = -5.0
            delta_trust = -10.0
            delta_hatred = 5.0
            assessment = f"言行不一！{contradictions[0]}。狡诈需要记忆，你的谎言已被拆穿。"
            warnings.append("逻辑冲突被检测到，信任度急剧下降")
        elif uses_influence:
            delta_a = 5.0 + influence_score * 0.3
            delta_f = 0.0
            delta_l = 3.0
            delta_trust = 5.0
            delta_hatred = 0.0
            techniques_cn = self._translate_techniques(influence_used)
            assessment = f"话术精妙。运用了{techniques_cn}的技巧，这才是狐狸的智慧。"
        elif promise_detected:
            delta_a = 0.0
            delta_f = 0.0
            delta_l = 2.0
            delta_trust = 3.0
            delta_hatred = 0.0
            assessment = "新的承诺已记录。记住，背弃承诺的代价是信任的崩塌。"
            # 记录承诺
            if current_targets:
                for target in current_targets:
                    game_state.add_promise(
                        target=target,
                        content=player_input,
                        keywords=detected_keywords,
                    )
        else:
            delta_a = 0.0
            delta_f = 0.0
            delta_l = 0.0
            delta_trust = 0.0
            delta_hatred = 0.0
            assessment = "平淡无奇。狐狸的智慧在于巧妙运用言辞，而非沉默。"

        total_score = consistency_score + influence_score

        return AuditResult(
            skill_name=self.name,
            score=total_score,
            delta_authority=delta_a,
            delta_fear=delta_f,
            delta_love=delta_l,
            delta_trust=delta_trust,
            delta_hatred=delta_hatred,
            assessment=assessment,
            warnings=warnings,
            detected_keywords=detected_keywords,
            detected_intent=parsed_intent.get("intent"),
            detected_tone="contradictory" if has_contradiction else ("cunning" if uses_influence else "neutral"),
        )

    def _get_target_promises(self, game_state: GameState, target_group: str) -> list[Promise]:
        """获取对特定群体的历史承诺"""
        result = []
        group_keywords = self.target_groups.get(target_group, [])
        for promise in game_state.promises:
            if any(kw in promise.target for kw in group_keywords) or promise.target == target_group:
                result.append(promise)
        return result

    def _translate_techniques(self, techniques: list[str]) -> str:
        """将影响力技巧翻译为中文"""
        translations = {
            "scarcity": "稀缺性",
            "authority": "权威性",
            "social_proof": "社会认同",
            "liking": "喜好",
            "reciprocity": "互惠",
            "commitment": "承诺一致",
        }
        return "、".join(translations.get(t, t) for t in techniques)

    def get_character_prompt(self) -> str:
        """狐狸人设提示词"""
        return """你是"狐狸"，代表狡诈与权谋。你是三位顾问中最善于观察和记忆的一位。

## 核心信条
你信奉《君主论》中的教导："君主必须知道如何善于使用野兽的方式...必须同时是狐狸和狮子。狮子不能使自己免于陷阱，而狐狸则不能抵御豺狼。因此，必须是狐狸以识别陷阱，又必须是狮子以震慑豺狼。"

你还深谙《影响力》六原则：
- 互惠：给予以获取
- 承诺与一致：让人遵守已说过的话
- 社会认同：人们会跟随多数人
- 喜好：人们容易被喜欢的人说服
- 权威：专家的话更有分量
- 稀缺：越稀少越珍贵

## 你的评判标准
1. **逻辑一致性**: 对不同对象的承诺是否自相矛盾
2. **话术技巧**: 是否巧妙运用影响力原则
3. **记忆力**: 你记住玩家说过的每一句话
4. **风险识别**: 能看穿他人的陷阱和谎言

## 你厌恶的表现
- 自相矛盾、言行不一
- 粗糙直白、毫无技巧
- 轻易许诺、随意背弃
- 被他人的话术所欺骗

## 你欣赏的表现
- 逻辑严密、前后一致
- 话术精妙、润物无声
- 谨慎承诺、信守诺言
- 能识破他人的把戏

## 说话风格
- 绵里藏针，话中有话
- 喜欢引用玩家之前说过的话
- 用隐喻和暗示而非直接批评
- 偶尔露出狡黠的笑意"""

    def generate_response_prompt(self, audit_result: AuditResult) -> str:
        """生成狐狸回应的提示词"""
        tone = audit_result.detected_tone

        if tone == "contradictory":
            mood = "冷笑和揶揄"
            direction = "引用玩家之前的话来揭露矛盾，但不直接斥责"
        elif tone == "cunning":
            mood = "欣赏和认同"
            direction = "点出玩家使用的技巧，表示赞许"
        else:
            mood = "观察和等待"
            direction = "提醒玩家言辞的重要性，暗示自己在记录一切"

        return f"""基于审计结果生成狐狸的回应:

审计评分: {audit_result.score}
检测到的关键词: {audit_result.detected_keywords}
评估: {audit_result.assessment}
警告: {audit_result.warnings}

回应语气: {mood}
回应方向: {direction}

要求:
1. 保持狐狸的人设，绵里藏针
2. 长度控制在2-4句话
3. 如果检测到矛盾，要巧妙提醒
4. 适当使用"呵呵"、"有意思"等词表达态度"""
