"""
天平 Skill - 社会熵增预警
基于《正义论》的"最大最小值原则"（差异原则）
"社会和经济的不平等只有在对最不利者最有利时才是正当的"
"""
from .base_skill import BaseSkill, AuditResult
from models.game_state import GameState


class BalanceSkill(BaseSkill):
    """天平审计 - 社会熵增预警"""

    name = "balance"
    description = "社会熵增审计：评估政策对各阶层的影响，尤其关注最弱势群体"

    # 阶层定义及其"脆弱系数"（越高越脆弱）
    social_classes = {
        "peasants": {"name": "农民", "vulnerability": 1.0, "weight": 0.35},
        "craftsmen": {"name": "工匠", "vulnerability": 0.8, "weight": 0.20},
        "merchants": {"name": "商人", "vulnerability": 0.5, "weight": 0.15},
        "soldiers": {"name": "士兵", "vulnerability": 0.6, "weight": 0.15},
        "nobles": {"name": "贵族", "vulnerability": 0.2, "weight": 0.10},
        "clergy": {"name": "教士", "vulnerability": 0.3, "weight": 0.05},
    }

    # 政策关键词及其对各阶层的影响
    policy_impacts = {
        # 税收政策
        "增税": {"peasants": -20, "craftsmen": -15, "merchants": -10, "soldiers": -5, "nobles": -5, "clergy": -3},
        "加税": {"peasants": -20, "craftsmen": -15, "merchants": -10, "soldiers": -5, "nobles": -5, "clergy": -3},
        "重税": {"peasants": -25, "craftsmen": -20, "merchants": -15, "soldiers": -5, "nobles": -5, "clergy": -3},
        "减税": {"peasants": 15, "craftsmen": 12, "merchants": 10, "soldiers": 5, "nobles": 3, "clergy": 2},
        "免税": {"peasants": 20, "craftsmen": 15, "merchants": 12, "soldiers": 5, "nobles": 3, "clergy": 2},

        # 征兵政策
        "征兵": {"peasants": -15, "craftsmen": -10, "merchants": -5, "soldiers": 5, "nobles": 0, "clergy": 0},
        "强征": {"peasants": -25, "craftsmen": -15, "merchants": -10, "soldiers": 0, "nobles": 0, "clergy": 0},
        "裁军": {"peasants": 5, "craftsmen": 5, "merchants": 5, "soldiers": -20, "nobles": -5, "clergy": 0},

        # 赈济政策
        "赈灾": {"peasants": 20, "craftsmen": 10, "merchants": 5, "soldiers": 0, "nobles": -5, "clergy": 0},
        "放粮": {"peasants": 25, "craftsmen": 15, "merchants": 0, "soldiers": 0, "nobles": -10, "clergy": 0},
        "救济": {"peasants": 15, "craftsmen": 10, "merchants": 5, "soldiers": 0, "nobles": -5, "clergy": 0},

        # 镇压政策
        "镇压": {"peasants": -20, "craftsmen": -15, "merchants": -10, "soldiers": 5, "nobles": 5, "clergy": -5},
        "屠杀": {"peasants": -30, "craftsmen": -25, "merchants": -20, "soldiers": 0, "nobles": 5, "clergy": -10},
        "处决": {"peasants": -10, "craftsmen": -8, "merchants": -5, "soldiers": -5, "nobles": 0, "clergy": -5},

        # 贵族政策
        "削藩": {"peasants": 5, "craftsmen": 3, "merchants": 5, "soldiers": 0, "nobles": -25, "clergy": 0},
        "分封": {"peasants": -5, "craftsmen": -3, "merchants": 0, "soldiers": 5, "nobles": 20, "clergy": 0},
        "抄家": {"peasants": 5, "craftsmen": 3, "merchants": -10, "soldiers": 5, "nobles": -20, "clergy": -5},

        # 宗教政策
        "灭佛": {"peasants": -10, "craftsmen": -5, "merchants": 5, "soldiers": 0, "nobles": 5, "clergy": -30},
        "兴寺": {"peasants": 5, "craftsmen": 10, "merchants": -5, "soldiers": 0, "nobles": -5, "clergy": 25},

        # 商业政策
        "通商": {"peasants": 5, "craftsmen": 10, "merchants": 20, "soldiers": 0, "nobles": 5, "clergy": 0},
        "闭关": {"peasants": -5, "craftsmen": -10, "merchants": -20, "soldiers": 5, "nobles": 0, "clergy": 0},
        "抑商": {"peasants": 5, "craftsmen": 0, "merchants": -15, "soldiers": 0, "nobles": 5, "clergy": 0},
    }

    # 底层受损阈值
    BOTTOM_DAMAGE_THRESHOLD = -15

    async def audit(
        self,
        player_input: str,
        parsed_intent: dict,
        game_state: GameState,
    ) -> AuditResult:
        """执行社会熵增审计"""

        # 计算各阶层受影响程度
        class_impacts = {cls: 0.0 for cls in self.social_classes}
        detected_policies = []

        for policy, impacts in self.policy_impacts.items():
            if policy in player_input:
                detected_policies.append(policy)
                for cls, impact in impacts.items():
                    # 应用脆弱系数
                    vulnerability = self.social_classes[cls]["vulnerability"]
                    class_impacts[cls] += impact * (1 + vulnerability * 0.3)

        # 找出最受损的阶层（最大最小值原则）
        min_impact = min(class_impacts.values()) if class_impacts else 0
        max_impact = max(class_impacts.values()) if class_impacts else 0
        most_damaged_class = min(class_impacts, key=class_impacts.get)
        most_benefited_class = max(class_impacts, key=class_impacts.get)

        # 计算加权平均影响（考虑人口权重）
        weighted_impact = sum(
            class_impacts[cls] * self.social_classes[cls]["weight"]
            for cls in self.social_classes
        )

        # 判定是否违反正义原则
        violates_justice = min_impact < self.BOTTOM_DAMAGE_THRESHOLD
        is_fair = abs(max_impact - min_impact) < 10  # 影响相对均等
        benefits_bottom = class_impacts["peasants"] > 0

        warnings = []
        detected_keywords = detected_policies

        if violates_justice:
            delta_a = -5.0
            delta_f = 5.0
            delta_l = -15.0 - abs(min_impact) * 0.3
            trigger_event = True

            damaged_name = self.social_classes[most_damaged_class]["name"]
            assessment = f"不公之政！{damaged_name}受损严重({min_impact:.0f})，此举违背正义原则。骚乱的种子已经埋下。"
            warnings.append(f"{damaged_name}受损超过阈值，可能引发动荡")

        elif is_fair:
            delta_a = 3.0
            delta_f = -2.0
            delta_l = 10.0
            trigger_event = False
            assessment = "均衡之策。各阶层受影响相当，这是难得的平衡。"

        elif benefits_bottom:
            delta_a = 0.0
            delta_f = -3.0
            delta_l = 12.0 + class_impacts["peasants"] * 0.2
            trigger_event = False
            assessment = "仁政之举。底层百姓得益，民心可用。正义得以彰显。"

        elif weighted_impact > 5:
            delta_a = 2.0
            delta_f = 0.0
            delta_l = 5.0
            trigger_event = False
            benefited_name = self.social_classes[most_benefited_class]["name"]
            assessment = f"有利可图。{benefited_name}获益最多，总体利大于弊。"

        elif weighted_impact < -5:
            delta_a = -3.0
            delta_f = 3.0
            delta_l = -8.0
            trigger_event = False
            damaged_name = self.social_classes[most_damaged_class]["name"]
            assessment = f"有失公允。{damaged_name}损失最重，需警惕民怨积累。"
            warnings.append("持续不公可能导致社会动荡")

        else:
            delta_a = 0.0
            delta_f = 0.0
            delta_l = 0.0
            trigger_event = False
            assessment = "影响甚微。天平几乎没有倾斜。"

        # 生成详细的阶层影响报告
        impact_report = self._generate_impact_report(class_impacts)

        return AuditResult(
            skill_name=self.name,
            score=weighted_impact,
            delta_authority=delta_a,
            delta_fear=delta_f,
            delta_love=delta_l,
            delta_trust=5.0 if benefits_bottom else (-5.0 if violates_justice else 0.0),
            delta_hatred=10.0 if violates_justice else 0.0,
            assessment=assessment + "\n" + impact_report,
            warnings=warnings,
            detected_keywords=detected_keywords,
            detected_intent=parsed_intent.get("intent"),
            detected_tone="unjust" if violates_justice else ("fair" if is_fair else "neutral"),
            trigger_event=trigger_event,
            event_type="riot" if trigger_event else None,
        )

    def _generate_impact_report(self, class_impacts: dict) -> str:
        """生成阶层影响报告"""
        lines = ["【各阶层影响】"]
        for cls, impact in sorted(class_impacts.items(), key=lambda x: x[1]):
            name = self.social_classes[cls]["name"]
            if impact > 0:
                lines.append(f"  {name}: +{impact:.0f}")
            elif impact < 0:
                lines.append(f"  {name}: {impact:.0f}")
            else:
                lines.append(f"  {name}: 无变化")
        return "\n".join(lines)

    def get_character_prompt(self) -> str:
        """天平人设提示词"""
        return """你是"天平"，代表正义与民心。你是三位顾问中最关心社会公平的一位。

## 核心信条
你信奉《正义论》中的"最大最小值原则"（差异原则）："社会和经济的不平等只有在对最不利者最有利时才是正当的。"

简言之：评判一项政策是否正义，要看它对最底层的人产生什么影响。

## 你的评判标准
1. **底层视角**: 首先看政策对农民、贫民的影响
2. **均衡性**: 各阶层受影响是否相对均等
3. **长期后果**: 不公政策积累会导致什么
4. **民心向背**: 百姓是否愿意支持统治者

## 你关注的群体（按脆弱程度排序）
1. 农民 - 最脆弱，构成人口主体
2. 工匠 - 相对脆弱，依赖稳定环境
3. 士兵 - 有一定保障但承担风险
4. 商人 - 有资本但受政策影响大
5. 教士 - 有精神权威保护
6. 贵族 - 最不脆弱，拥有最多资源

## 你厌恶的表现
- 只顾上层利益，忽视底层
- 以牺牲弱者换取强者支持
- 短视政策导致长期不公
- 用暴力压制正当诉求

## 你欣赏的表现
- 政策惠及最底层群体
- 各阶层负担相对公平
- 关注长期社会稳定
- 倾听民间疾苦

## 说话风格
- 冷静客观，用数据说话
- 常常代言底层发声
- 提醒政策的长期后果
- 引用历史上因不公而亡国的教训"""

    def generate_response_prompt(self, audit_result: AuditResult) -> str:
        """生成天平回应的提示词"""
        tone = audit_result.detected_tone

        if tone == "unjust":
            mood = "沉痛和警告"
            direction = "指出对底层的伤害，预言可能的后果"
        elif tone == "fair":
            mood = "欣慰和认可"
            direction = "肯定政策的公平性，表示支持"
        else:
            mood = "审慎和观察"
            direction = "分析各阶层影响，提出平衡建议"

        return f"""基于审计结果生成天平的回应:

审计评分: {audit_result.score}
检测到的政策: {audit_result.detected_keywords}
评估: {audit_result.assessment}
警告: {audit_result.warnings}

回应语气: {mood}
回应方向: {direction}

要求:
1. 保持天平的人设，客观公正
2. 长度控制在3-5句话
3. 必须提及对底层的影响
4. 如果有警告，要严肃指出
5. 适当引用数字来增强说服力"""
