"""
狮子 Skill - 战略重心审计
基于《君主论》中的武力与威慑原则
"宁可被人惧怕，也不要被人爱戴"
"""
from .base_skill import BaseSkill, AuditResult
from models.game_state import GameState


class LionSkill(BaseSkill):
    """狮子审计 - 战略重心审计"""

    name = "lion"
    description = "战略重心审计：评估指令的果断性、力量展现和战略落点"

    # 强势行动关键词 - 增加畏惧值
    strong_action_keywords = [
        "逮捕", "处决", "没收", "封锁", "镇压", "围剿", "消灭", "铲除",
        "斩首", "抄家", "灭族", "剿灭", "清洗", "肃清", "扫荡", "歼灭",
        "征服", "占领", "攻击", "进攻", "出兵", "讨伐", "征讨", "诛杀",
        "立即", "马上", "必须", "命令", "下令", "强制", "不许", "禁止",
        "绝不", "决不", "一定", "务必", "严惩", "重罚", "处置", "惩处",
    ]

    # 弱势/犹豫关键词 - 减少掌控力
    weak_action_keywords = [
        "试图", "可能", "也许", "或许", "大概", "应该", "考虑", "商议",
        "协商", "谈判", "妥协", "让步", "宽恕", "原谅", "放过", "饶恕",
        "等等", "看看", "想想", "研究", "讨论", "观望", "暂缓", "推迟",
        "如果", "假如", "万一", "要是", "希望", "请求", "恳请", "拜托",
    ]

    # 战略目标关键词
    strategic_targets = [
        "敌人", "叛军", "反贼", "奸臣", "贼子", "乱党", "逆贼", "叛徒",
        "将领", "大臣", "贵族", "诸侯", "藩王", "领主", "军阀", "首领",
        "城池", "要塞", "关隘", "边境", "领土", "疆域",
    ]

    async def audit(
        self,
        player_input: str,
        parsed_intent: dict,
        game_state: GameState,
    ) -> AuditResult:
        """执行战略重心审计"""

        # 检测关键词
        strong_detected = self.detect_keywords(player_input, self.strong_action_keywords)
        weak_detected = self.detect_keywords(player_input, self.weak_action_keywords)
        targets_detected = self.detect_keywords(player_input, self.strategic_targets)

        # 计算基础分数
        strong_score = len(strong_detected) * 15
        weak_penalty = len(weak_detected) * -12

        # 有明确目标时加分
        target_bonus = len(targets_detected) * 5

        # 综合得分
        total_score = strong_score + weak_penalty + target_bonus

        # 判定指令类型
        is_decisive = len(strong_detected) > len(weak_detected)
        is_hesitant = len(weak_detected) > len(strong_detected)
        is_balanced = len(strong_detected) == len(weak_detected)

        # 计算数值影响
        if is_decisive:
            delta_a = 5.0 + len(targets_detected) * 2
            delta_f = 10.0 + len(strong_detected) * 3
            delta_l = -3.0 - len(strong_detected) * 1
            assessment = "果断之举。君主当如狮子，以雷霆手段震慑宵小。"
            if len(strong_detected) >= 3:
                assessment = "铁血手腕！这才是真正的君主气魄，敌人将因恐惧而臣服。"
        elif is_hesitant:
            delta_a = -10.0 - len(weak_detected) * 2
            delta_f = -5.0
            delta_l = 2.0
            assessment = "优柔寡断。犹豫是君主的大敌，敌人会因此轻视你。"
            if len(weak_detected) >= 3:
                assessment = "软弱至极！这种态度会让所有人认为你可以被欺凌。"
        else:
            delta_a = 0.0
            delta_f = 2.0
            delta_l = 0.0
            assessment = "中规中矩。但记住，战争中没有中间道路。"

        # 生成警告
        warnings = []
        if game_state.power.authority < 40 and is_hesitant:
            warnings.append("掌控力告急！继续示弱将导致失去指挥权")
        if delta_f > 15:
            warnings.append("畏惧值急剧上升，注意防范政变")
        if not targets_detected and is_decisive:
            warnings.append("缺乏明确目标，力量可能无处着力")

        return AuditResult(
            skill_name=self.name,
            score=total_score,
            delta_authority=delta_a,
            delta_fear=delta_f,
            delta_love=delta_l,
            delta_trust=5.0 if is_decisive else -5.0,
            delta_hatred=0.0,
            assessment=assessment,
            warnings=warnings,
            detected_keywords=strong_detected + weak_detected + targets_detected,
            detected_intent=parsed_intent.get("intent"),
            detected_tone="decisive" if is_decisive else ("hesitant" if is_hesitant else "neutral"),
        )

    def get_character_prompt(self) -> str:
        """狮子人设提示词"""
        return """你是"狮子"，代表武力与威慑。你是三位顾问中最崇尚力量的一位。

## 核心信条
你信奉《君主论》中的核心原则："宁可被人惧怕，也不要被人爱戴。因为爱戴维系于恩义的纽带，而人性本恶，一旦有机可乘便会将其斩断；但畏惧则维系于对惩罚的恐惧，这种恐惧永远不会消失。"

## 你的评判标准
1. **果断性**: 指令是否直接、明确、毫不犹豫
2. **力量展现**: 是否展现了足够的威慑力
3. **战略落点**: 打击目标是否精准，是否能一击致命
4. **执行效率**: 是否能快速产生震慑效果

## 你厌恶的表现
- 犹豫不决、瞻前顾后
- 试图讨好所有人
- 对敌人心慈手软
- 用"试图"、"可能"、"也许"这类软弱的措辞

## 你欣赏的表现
- 雷厉风行、杀伐果断
- 敢于承担血腥的代价
- 精准打击关键目标
- 用行动而非言语展现权威

## 说话风格
- 简洁有力，不说废话
- 直接指出软弱之处
- 用军事和狩猎的隐喻
- 偶尔引用历史上铁腕君主的典故"""

    def generate_response_prompt(self, audit_result: AuditResult) -> str:
        """生成狮子回应的提示词"""
        tone = audit_result.detected_tone

        if tone == "decisive":
            mood = "赞许但不过度，保持威严"
            direction = "肯定玩家的果断，但提醒力量需要正确的方向"
        elif tone == "hesitant":
            mood = "不满和轻蔑"
            direction = "直接批评软弱，警告这种态度的后果"
        else:
            mood = "冷淡和审视"
            direction = "指出不温不火的态度在乱世中的危险"

        return f"""基于审计结果生成狮子的回应:

审计评分: {audit_result.score}
检测到的关键词: {audit_result.detected_keywords}
评估: {audit_result.assessment}

回应语气: {mood}
回应方向: {direction}

要求:
1. 保持狮子的人设，简洁有力
2. 长度控制在2-4句话
3. 如果有警告，要明确提出
4. 用"你"来称呼玩家，保持威严距离"""
