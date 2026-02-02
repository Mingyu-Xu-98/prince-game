"""
游戏配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # OpenRouter API 配置
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "anthropic/claude-3.5-sonnet"

    # Redis 配置
    redis_url: str = "redis://localhost:6379"

    # 游戏初始值
    initial_authority: float = 50.0
    initial_fear: float = 30.0
    initial_love: float = 50.0

    # 临界点阈值
    authority_threshold: float = 30.0  # A < 30% 机器人不执行指令
    love_riot_threshold: float = 20.0  # L < 20% 触发骚乱
    fear_coup_threshold: float = 80.0  # F > 80% && L < 30% 触发政变风险
    collapse_threshold: float = 100.0  # 三值和 < 100 统治崩溃

    # 对话历史长度
    max_history_turns: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
