"""
NLP 解析器
使用 OpenRouter API 解析玩家输入的意图、对象、手段、目标和态度
"""
import json
from typing import Optional
from openai import AsyncOpenAI
from config import settings


class NLPParser:
    """NLP 意图解析器"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.default_model
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=settings.openrouter_base_url,
        )

    async def parse(self, player_input: str) -> dict:
        """
        解析玩家输入

        Returns:
            {
                "intent": str,          # 意图类型
                "target": str,          # 行动对象
                "method": str,          # 手段方式
                "goal": str,            # 预期目标
                "cost": str,            # 可能代价
                "tone": str,            # 态度语气
                "keywords": list[str],  # 关键词
                "raw_input": str,       # 原始输入
            }
        """
        system_prompt = """你是一个专门用于解析政治决策意图的分析器。
你需要从玩家的指令中提取以下信息，以JSON格式返回：

{
    "intent": "行动意图类型，如: 军事行动/经济政策/外交决策/内政改革/人事任免/应对危机",
    "target": "行动的直接对象，如: 农民/贵族/军队/敌国/特定人物",
    "method": "采用的手段方式，如: 武力镇压/怀柔安抚/税收调整/谈判协商",
    "goal": "预期达成的目标",
    "cost": "可能付出的代价或风险",
    "tone": "指令的态度语气，如: 果断/犹豫/愤怒/冷静/试探",
    "keywords": ["提取的关键动词和名词列表"]
}

注意：
1. 如果某项信息无法从输入中判断，填写"未明确"
2. keywords 应该提取所有重要的动词和名词
3. tone 要根据用词和句式判断
4. 只返回JSON，不要有其他内容"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"分析以下指令：\n\n{player_input}"},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            content = response.choices[0].message.content
            # 尝试提取JSON
            parsed = self._extract_json(content)
            parsed["raw_input"] = player_input
            return parsed

        except Exception as e:
            # 解析失败时返回基础结构
            return {
                "intent": "未知",
                "target": "未明确",
                "method": "未明确",
                "goal": "未明确",
                "cost": "未明确",
                "tone": "neutral",
                "keywords": self._extract_basic_keywords(player_input),
                "raw_input": player_input,
                "error": str(e),
            }

    def _extract_json(self, content: str) -> dict:
        """从响应中提取JSON"""
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试找到JSON块
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 返回默认结构
        return {
            "intent": "解析失败",
            "target": "未明确",
            "method": "未明确",
            "goal": "未明确",
            "cost": "未明确",
            "tone": "neutral",
            "keywords": [],
        }

    def _extract_basic_keywords(self, text: str) -> list[str]:
        """基础关键词提取（不依赖LLM）"""
        # 常见动词
        verbs = [
            "逮捕", "处决", "没收", "封锁", "镇压", "征税", "减税",
            "赈灾", "征兵", "出兵", "谈判", "结盟", "宣战", "投降",
            "任命", "罢免", "奖赏", "惩罚", "调查", "审判", "释放",
        ]
        # 常见名词
        nouns = [
            "农民", "贵族", "商人", "士兵", "将军", "大臣", "太监",
            "敌国", "藩王", "叛军", "百姓", "国库", "军队", "边境",
        ]

        keywords = []
        for word in verbs + nouns:
            if word in text:
                keywords.append(word)

        return keywords


class IntentClassifier:
    """意图分类器（本地轻量级分类）"""

    INTENT_PATTERNS = {
        "military": ["出兵", "征讨", "进攻", "防守", "围剿", "镇压", "征兵", "裁军"],
        "economic": ["增税", "减税", "征收", "免除", "通商", "闭关", "赈灾", "放粮"],
        "diplomatic": ["结盟", "断交", "谈判", "求和", "宣战", "朝贡", "和亲"],
        "internal": ["改革", "立法", "废除", "推行", "颁布", "取消"],
        "personnel": ["任命", "罢免", "提拔", "贬谪", "处决", "赦免", "流放"],
        "crisis": ["应对", "处理", "解决", "平息", "化解", "镇压"],
    }

    @classmethod
    def classify(cls, text: str) -> str:
        """快速分类意图"""
        scores = {}
        for intent, keywords in cls.INTENT_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[intent] = score

        if max(scores.values()) == 0:
            return "general"

        return max(scores, key=scores.get)
