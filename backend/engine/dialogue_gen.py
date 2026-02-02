"""
对话生成器
基于审计结果和角色人设生成机器人对话
"""
from typing import Optional
from openai import AsyncOpenAI
from config import settings
from skills import LionSkill, FoxSkill, BalanceSkill, AuditResult


class DialogueGenerator:
    """对话生成器"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.default_model
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=settings.openrouter_base_url,
        )

        # 初始化 Skill 实例以获取人设
        self.skills = {
            "lion": LionSkill(),
            "fox": FoxSkill(),
            "balance": BalanceSkill(),
        }

    async def generate_response(
        self,
        robot_name: str,
        audit_result: AuditResult,
        player_input: str,
        context: Optional[list[dict]] = None,
    ) -> str:
        """
        生成机器人回应

        Args:
            robot_name: 机器人名称 (lion/fox/balance)
            audit_result: 该机器人的审计结果
            player_input: 玩家原始输入
            context: 历史对话上下文

        Returns:
            机器人的回应文本
        """
        skill = self.skills.get(robot_name)
        if not skill:
            return "（沉默）"

        # 获取人设提示词
        character_prompt = skill.get_character_prompt()

        # 获取响应提示词
        response_prompt = skill.generate_response_prompt(audit_result)

        # 构建消息
        messages = [
            {"role": "system", "content": character_prompt},
        ]

        # 添加历史上下文（最近几轮）
        if context:
            for entry in context[-6:]:  # 最近3轮对话
                role = "user" if entry.get("speaker") == "player" else "assistant"
                messages.append({"role": role, "content": entry.get("content", "")})

        # 添加当前请求
        messages.append({
            "role": "user",
            "content": f"""玩家说："{player_input}"

{response_prompt}

请以你的身份回应：""",
        })

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=300,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            # 生成失败时返回基于评估的简短回应
            return self._fallback_response(robot_name, audit_result)

    async def generate_all_responses(
        self,
        audit_results: dict[str, AuditResult],
        player_input: str,
        context: Optional[list[dict]] = None,
    ) -> dict[str, str]:
        """
        并发生成所有机器人的回应

        Returns:
            {
                "lion": str,
                "fox": str,
                "balance": str,
            }
        """
        import asyncio

        tasks = []
        for robot_name, audit_result in audit_results.items():
            task = self.generate_response(robot_name, audit_result, player_input, context)
            tasks.append((robot_name, task))

        responses = {}
        for robot_name, task in tasks:
            try:
                responses[robot_name] = await task
            except Exception:
                responses[robot_name] = self._fallback_response(robot_name, audit_results[robot_name])

        return responses

    def _fallback_response(self, robot_name: str, audit_result: AuditResult) -> str:
        """生成失败时的备用回应"""
        tone = audit_result.detected_tone

        fallbacks = {
            "lion": {
                "decisive": "不错，这才是君主该有的魄力。",
                "hesitant": "犹豫不决是弱者的表现。",
                "neutral": "力量需要方向。",
            },
            "fox": {
                "contradictory": "呵呵，你之前可不是这么说的。",
                "cunning": "有意思，你在学狐狸的方式。",
                "neutral": "我在听，也在记。",
            },
            "balance": {
                "unjust": "底层的百姓正在受苦，你看不到吗？",
                "fair": "这是一个公正的决定。",
                "neutral": "天平在衡量一切。",
            },
        }

        robot_fallbacks = fallbacks.get(robot_name, {})
        return robot_fallbacks.get(tone, "......")

    async def generate_event_narration(self, event) -> str:
        """
        生成事件叙述

        Args:
            event: 事件对象

        Returns:
            戏剧性的事件描述
        """
        prompt = f"""你是一个古典风格的叙事者，正在描述一个紧急的政治事件。

事件类型：{event.type.value}
事件标题：{event.title}
事件描述：{event.description}

请用简短但戏剧性的语言描述这个事件的发生，营造紧张气氛。
要求：
1. 2-3句话
2. 使用古典文言白话混合风格
3. 突出紧迫感
4. 不要提及具体的选项"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=150,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return event.description

    async def generate_game_over_narration(self, reason: str, power_state: dict) -> str:
        """
        生成游戏结束叙述

        Args:
            reason: 结束原因
            power_state: 最终权力状态

        Returns:
            游戏结束的叙述
        """
        prompt = f"""你是一个历史叙事者，正在描述一个统治者的结局。

结束原因：{reason}
最终状态：
- 掌控力: {power_state.get('authority', {}).get('value', 0)}
- 畏惧值: {power_state.get('fear', {}).get('value', 0)}
- 爱戴值: {power_state.get('love', {}).get('value', 0)}

请用简短但深刻的语言描述这个统治者的结局，像是在写一段历史记载。
要求：
1. 3-4句话
2. 有历史感和宿命感
3. 总结统治者的得失
4. 可以引用《君主论》的相关观点"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return f"统治落幕。{reason}"
