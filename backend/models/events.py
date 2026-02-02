"""
事件系统模型
定义游戏中的突发事件和困境
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import random


class EventType(str, Enum):
    """事件类型"""

    RIOT = "riot"  # 骚乱
    COUP = "coup"  # 政变
    REBELLION = "rebellion"  # 叛乱
    FAMINE = "famine"  # 饥荒
    WAR = "war"  # 战争威胁
    PLAGUE = "plague"  # 瘟疫
    CONSPIRACY = "conspiracy"  # 阴谋
    BETRAYAL = "betrayal"  # 背叛
    CRISIS = "crisis"  # 经济危机
    INVASION = "invasion"  # 外敌入侵


class Event(BaseModel):
    """事件定义"""

    id: str
    type: EventType
    title: str
    description: str
    trigger_condition: str  # 触发条件描述
    choices: list[dict] = Field(default_factory=list)  # 可选应对方案
    default_impact: dict = Field(
        default_factory=lambda: {"authority": 0, "fear": 0, "love": 0}
    )

    def get_choice_impacts(self, choice_id: str) -> dict:
        """获取选择的影响"""
        for choice in self.choices:
            if choice.get("id") == choice_id:
                return choice.get("impact", self.default_impact)
        return self.default_impact


class EventLibrary:
    """事件库"""

    @staticmethod
    def get_all_events() -> dict[str, Event]:
        """获取所有事件定义"""
        return {
            # 骚乱事件 (L < 20% 触发)
            "riot_peasant": Event(
                id="riot_peasant",
                type=EventType.RIOT,
                title="农民起义",
                description="城外农民因重税揭竿而起，聚众数千，已逼近城门。你必须立即做出决断。",
                trigger_condition="love < 20",
                choices=[
                    {
                        "id": "suppress",
                        "text": "派兵镇压，杀一儆百",
                        "impact": {"authority": 5, "fear": 15, "love": -10},
                    },
                    {
                        "id": "negotiate",
                        "text": "派使者谈判，许诺减税",
                        "impact": {"authority": -5, "fear": -5, "love": 10},
                    },
                    {
                        "id": "bribe_leaders",
                        "text": "收买起义领袖，分化瓦解",
                        "impact": {"authority": 0, "fear": 0, "love": 5},
                    },
                ],
                default_impact={"authority": -10, "fear": -5, "love": -5},
            ),
            "riot_urban": Event(
                id="riot_urban",
                type=EventType.RIOT,
                title="城市暴动",
                description="市民因物价飞涨而暴动，已有商铺被焚。",
                trigger_condition="love < 20",
                choices=[
                    {
                        "id": "curfew",
                        "text": "实施宵禁，严惩闹事者",
                        "impact": {"authority": 5, "fear": 10, "love": -8},
                    },
                    {
                        "id": "relief",
                        "text": "开仓放粮，平抑物价",
                        "impact": {"authority": 0, "fear": -5, "love": 12},
                    },
                ],
                default_impact={"authority": -8, "fear": -3, "love": -10},
            ),
            # 政变事件 (F > 80 && L < 30 触发)
            "coup_military": Event(
                id="coup_military",
                type=EventType.COUP,
                title="禁军哗变",
                description="禁军将领密谋政变，今夜将举事。你的眼线刚刚送来密报。",
                trigger_condition="fear > 80 and love < 30",
                choices=[
                    {
                        "id": "preemptive",
                        "text": "先发制人，逮捕主谋",
                        "impact": {"authority": 10, "fear": 5, "love": -5},
                    },
                    {
                        "id": "flee",
                        "text": "秘密出逃，保全性命",
                        "impact": {"authority": -30, "fear": -20, "love": 0},
                    },
                    {
                        "id": "negotiate_power",
                        "text": "与将领谈判，分享权力",
                        "impact": {"authority": -15, "fear": -10, "love": 5},
                    },
                ],
                default_impact={"authority": -25, "fear": -15, "love": 0},
            ),
            "coup_noble": Event(
                id="coup_noble",
                type=EventType.COUP,
                title="贵族阴谋",
                description="数位大贵族联名弹劾你，要求你退位。宫廷中暗流涌动。",
                trigger_condition="fear > 80 and love < 30",
                choices=[
                    {
                        "id": "purge",
                        "text": "血洗宫廷，杀尽叛党",
                        "impact": {"authority": 15, "fear": 20, "love": -15},
                    },
                    {
                        "id": "divide",
                        "text": "分化瓦解，各个击破",
                        "impact": {"authority": 5, "fear": 5, "love": 0},
                    },
                    {
                        "id": "abdicate",
                        "text": "体面退位，保全家族",
                        "impact": {"authority": -50, "fear": -30, "love": 10},
                    },
                ],
                default_impact={"authority": -20, "fear": -10, "love": -5},
            ),
            # 外患事件
            "invasion_neighbor": Event(
                id="invasion_neighbor",
                type=EventType.INVASION,
                title="邻国入侵",
                description="邻国大军压境，已攻破边境要塞。战火即将烧至腹地。",
                trigger_condition="random",
                choices=[
                    {
                        "id": "fight",
                        "text": "御驾亲征，誓死抵抗",
                        "impact": {"authority": 10, "fear": 10, "love": 5},
                    },
                    {
                        "id": "diplomacy",
                        "text": "求和谈判，割地赔款",
                        "impact": {"authority": -10, "fear": -10, "love": -10},
                    },
                    {
                        "id": "alliance",
                        "text": "联络他国，结盟抗敌",
                        "impact": {"authority": 5, "fear": 0, "love": 5},
                    },
                ],
                default_impact={"authority": -15, "fear": 5, "love": -10},
            ),
            # 内部危机
            "conspiracy_assassination": Event(
                id="conspiracy_assassination",
                type=EventType.CONSPIRACY,
                title="刺客现身",
                description="深夜，一名刺客潜入寝宫，被侍卫格杀。审讯后发现背后有大人物。",
                trigger_condition="random",
                choices=[
                    {
                        "id": "investigate",
                        "text": "彻查到底，揪出幕后黑手",
                        "impact": {"authority": 5, "fear": 10, "love": -3},
                    },
                    {
                        "id": "ignore",
                        "text": "秘而不宣，暗中戒备",
                        "impact": {"authority": 0, "fear": 5, "love": 0},
                    },
                    {
                        "id": "blame_enemy",
                        "text": "嫁祸外敌，凝聚人心",
                        "impact": {"authority": 5, "fear": 5, "love": 8},
                    },
                ],
                default_impact={"authority": -5, "fear": 5, "love": -5},
            ),
            "crisis_economic": Event(
                id="crisis_economic",
                type=EventType.CRISIS,
                title="国库空虚",
                description="财政大臣禀报：国库仅余三月开支，若不增收，军饷将无法发放。",
                trigger_condition="random",
                choices=[
                    {
                        "id": "tax_heavy",
                        "text": "加征重税，充实国库",
                        "impact": {"authority": 5, "fear": 5, "love": -15},
                    },
                    {
                        "id": "tax_rich",
                        "text": "向富商巨贾摊派",
                        "impact": {"authority": 0, "fear": 5, "love": 5},
                    },
                    {
                        "id": "cut_spending",
                        "text": "削减开支，裁撤冗员",
                        "impact": {"authority": -5, "fear": -5, "love": 5},
                    },
                ],
                default_impact={"authority": -10, "fear": -5, "love": -5},
            ),
            "famine_drought": Event(
                id="famine_drought",
                type=EventType.FAMINE,
                title="旱灾饥荒",
                description="连月大旱，颗粒无收。饥民遍野，已开始易子而食。",
                trigger_condition="random",
                choices=[
                    {
                        "id": "relief_full",
                        "text": "倾尽国库，全力赈灾",
                        "impact": {"authority": 0, "fear": -5, "love": 15},
                    },
                    {
                        "id": "relief_partial",
                        "text": "适度赈济，优先军需",
                        "impact": {"authority": 5, "fear": 5, "love": -5},
                    },
                    {
                        "id": "relocate",
                        "text": "迁移灾民，分散压力",
                        "impact": {"authority": 0, "fear": 0, "love": 5},
                    },
                ],
                default_impact={"authority": -5, "fear": 0, "love": -15},
            ),
            "betrayal_advisor": Event(
                id="betrayal_advisor",
                type=EventType.BETRAYAL,
                title="心腹叛逃",
                description="你最信任的谋士携带机密文件投奔敌国。宫中人心惶惶。",
                trigger_condition="random",
                choices=[
                    {
                        "id": "execute_family",
                        "text": "灭其满门，以儆效尤",
                        "impact": {"authority": 5, "fear": 15, "love": -10},
                    },
                    {
                        "id": "pardon_family",
                        "text": "赦免家属，展现宽仁",
                        "impact": {"authority": -5, "fear": -5, "love": 10},
                    },
                    {
                        "id": "send_assassin",
                        "text": "派刺客追杀，以绝后患",
                        "impact": {"authority": 5, "fear": 10, "love": -5},
                    },
                ],
                default_impact={"authority": -10, "fear": -5, "love": -5},
            ),
        }

    @staticmethod
    def get_riot_event() -> Event:
        """获取骚乱事件"""
        events = EventLibrary.get_all_events()
        riot_events = [e for e in events.values() if e.type == EventType.RIOT]
        return random.choice(riot_events)

    @staticmethod
    def get_coup_event() -> Event:
        """获取政变事件"""
        events = EventLibrary.get_all_events()
        coup_events = [e for e in events.values() if e.type == EventType.COUP]
        return random.choice(coup_events)

    @staticmethod
    def get_random_event() -> Event:
        """获取随机事件"""
        events = EventLibrary.get_all_events()
        random_events = [
            e
            for e in events.values()
            if e.trigger_condition == "random"
        ]
        return random.choice(random_events)

    @staticmethod
    def check_triggered_events(power) -> Optional[Event]:
        """检查是否触发条件事件"""
        if power.is_riot_risk():
            return EventLibrary.get_riot_event()
        if power.is_coup_risk():
            return EventLibrary.get_coup_event()
        # 10% 概率触发随机事件
        if random.random() < 0.1:
            return EventLibrary.get_random_event()
        return None
