# 《君主论》技能包服务
# 加载和管理 prince-skills 文件夹中的技能包

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Skill:
    """技能包数据结构"""
    name: str
    description: str
    content: str
    use_when: str
    category: str


class PrinceSkillsService:
    """《君主论》技能包服务"""

    # 技能分类映射
    SKILL_CATEGORIES = {
        # 核心政治哲学与领导力
        "machiavellian-political-principles": "政治哲学",
        "machiavellian-political-strategy": "政治哲学",
        "machiavellian-leadership-principles": "领导力",
        "adapting-to-fortune-and-circumstances": "领导力",
        "machiavelli-political-analysis": "政治哲学",
        "machiavelli-political-philosophy-analysis": "政治哲学",

        # 军事战略
        "military-reform-and-liberation": "军事战略",
        "security-and-military-strategy": "军事战略",
        "army-classification-french-characteristics": "军事战略",
        "military-organization-training": "军事战略",
        "military-force-analysis": "军事战略",
        "military-force-selection-and-composition": "军事战略",
        "defense-and-military-preparedness": "军事战略",
        "military-strategy-and-defense": "军事战略",

        # 国家治理与权力巩固
        "internal-stability-management": "权力巩固",
        "domestic-power-base-management": "权力巩固",
        "territorial-governance-strategies": "领土治理",
        "territory-acquisition-and-retention": "领土治理",
        "power-acquisition-consolidation": "权力巩固",
        "power-acquisition-methods": "权力巩固",
        "power-consolidation-tactics": "权力巩固",
        "governance-and-minister-management": "治理策略",
        "reputation-and-external-relations": "外交策略",
        "strategic-use-of-negative-attributes": "策略运用",
        "hereditary-principality-maintenance": "权力维持",
        "new-ruler-power-consolidation": "权力巩固",
        "territorial-conquest-and-integration": "领土治理",
        "internal-politics-and-nobility-management": "内政管理",

        # 风险管理与危机应对
        "succession-appointment-risk-management": "风险管理",
        "monarch-succession-and-appointment-risk-management": "风险管理",
        "crowd-psychology-diplomatic-posturing-revenge": "危机应对",
        "crowd-psychology-diplomatic-strategy": "危机应对",
        "political-crisis-management": "危机应对",
    }

    # 游戏场景与技能的映射
    SCENARIO_SKILL_MAPPING = {
        # 财政危机
        "finance": [
            "strategic-use-of-negative-attributes",
            "governance-and-minister-management",
            "reputation-and-external-relations",
        ],
        # 瘟疫/民众
        "plague": [
            "crowd-psychology-diplomatic-strategy",
            "internal-stability-management",
            "political-crisis-management",
        ],
        # 外交/战争
        "diplomacy": [
            "reputation-and-external-relations",
            "military-strategy-and-defense",
            "adapting-to-fortune-and-circumstances",
        ],
        # 内部叛乱
        "rebellion": [
            "internal-stability-management",
            "power-consolidation-tactics",
            "crowd-psychology-diplomatic-strategy",
        ],
        # 继承/权力交接
        "succession": [
            "succession-appointment-risk-management",
            "hereditary-principality-maintenance",
            "governance-and-minister-management",
        ],
        # 军事行动
        "military": [
            "military-strategy-and-defense",
            "security-and-military-strategy",
            "military-force-selection-and-composition",
        ],
        # 贵族管理
        "nobility": [
            "internal-politics-and-nobility-management",
            "domestic-power-base-management",
            "governance-and-minister-management",
        ],
        # 默认/通用
        "default": [
            "machiavellian-leadership-principles",
            "machiavellian-political-principles",
            "adapting-to-fortune-and-circumstances",
        ],
    }

    def __init__(self, skills_dir: str = None):
        """初始化技能包服务"""
        if skills_dir is None:
            # 默认路径：项目根目录下的 prince-skills
            base_dir = Path(__file__).parent.parent.parent
            skills_dir = base_dir / "prince-skills"

        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Skill] = {}
        self._load_skills()

    def _load_skills(self):
        """加载所有技能包"""
        if not self.skills_dir.exists():
            print(f"警告: 技能包目录不存在: {self.skills_dir}")
            return

        for skill_folder in self.skills_dir.iterdir():
            if skill_folder.is_dir() and not skill_folder.name.startswith('.'):
                skill_file = skill_folder / "SKILL.md"
                if skill_file.exists():
                    self._load_skill(skill_folder.name, skill_file)

    def _load_skill(self, skill_name: str, skill_file: Path):
        """加载单个技能包"""
        try:
            content = skill_file.read_text(encoding='utf-8')

            # 解析 YAML frontmatter
            name = skill_name
            description = ""

            # 提取 frontmatter
            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                # 提取 name
                name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
                if name_match:
                    name = name_match.group(1).strip()
                # 提取 description
                desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
                if desc_match:
                    description = desc_match.group(1).strip()

                # 移除 frontmatter
                content = content[frontmatter_match.end():]

            # 提取使用场景
            use_when = ""
            use_when_match = re.search(r'##\s*使用场景\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
            if use_when_match:
                use_when = use_when_match.group(1).strip()

            # 获取分类
            category = self.SKILL_CATEGORIES.get(skill_name, "其他")

            self.skills[skill_name] = Skill(
                name=name,
                description=description,
                content=content,
                use_when=use_when,
                category=category
            )
        except Exception as e:
            print(f"加载技能包失败 {skill_name}: {e}")

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """获取指定技能包"""
        return self.skills.get(skill_name)

    def get_all_skills(self) -> Dict[str, Skill]:
        """获取所有技能包"""
        return self.skills

    def get_skills_by_category(self, category: str) -> List[Skill]:
        """按分类获取技能包"""
        return [s for s in self.skills.values() if s.category == category]

    def get_skills_for_scenario(self, scenario: str) -> List[Skill]:
        """根据场景获取相关技能包"""
        skill_names = self.SCENARIO_SKILL_MAPPING.get(
            scenario,
            self.SCENARIO_SKILL_MAPPING["default"]
        )
        return [self.skills[name] for name in skill_names if name in self.skills]

    def search_skills(self, keywords: List[str]) -> List[Skill]:
        """根据关键词搜索技能包"""
        results = []
        for skill in self.skills.values():
            score = 0
            text = f"{skill.name} {skill.description} {skill.use_when}".lower()
            for keyword in keywords:
                if keyword.lower() in text:
                    score += 1
            if score > 0:
                results.append((score, skill))

        # 按匹配度排序
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results]

    def get_skill_summary(self, skill_name: str) -> Optional[str]:
        """获取技能包摘要（用于AI提示）"""
        skill = self.get_skill(skill_name)
        if not skill:
            return None

        return f"""【{skill.name}】
分类：{skill.category}
描述：{skill.description}
使用场景：{skill.use_when}
"""

    def get_relevant_skills_prompt(self, scenario: str, max_skills: int = 3) -> str:
        """获取与场景相关的技能包内容，用于AI提示"""
        skills = self.get_skills_for_scenario(scenario)[:max_skills]

        if not skills:
            skills = self.get_skills_for_scenario("default")[:max_skills]

        prompt_parts = ["以下是《君主论》中与当前情境相关的策略原则：\n"]

        for skill in skills:
            prompt_parts.append(f"""
---
【{skill.name}】- {skill.category}
{skill.description}

{skill.content[:1500]}...
---
""")

        return "\n".join(prompt_parts)

    def detect_scenario(self, text: str) -> str:
        """根据文本内容检测场景类型"""
        text_lower = text.lower()

        # 关键词映射
        scenario_keywords = {
            "finance": ["财政", "税收", "国库", "银两", "空饷", "贪腐", "赈灾", "钱粮"],
            "plague": ["瘟疫", "疾病", "流言", "民心", "恐慌", "骚乱", "流民"],
            "diplomacy": ["外交", "和亲", "战争", "邻国", "条约", "使节", "进贡"],
            "rebellion": ["叛乱", "谋反", "政变", "刺杀", "逆贼", "起义"],
            "succession": ["继承", "储君", "太子", "皇位", "禅让", "遗诏"],
            "military": ["军队", "将军", "兵力", "战役", "征讨", "边疆", "防御"],
            "nobility": ["贵族", "世家", "门阀", "大臣", "权臣", "朝臣"],
        }

        scores = {scenario: 0 for scenario in scenario_keywords}

        for scenario, keywords in scenario_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[scenario] += 1

        # 找出得分最高的场景
        max_score = max(scores.values())
        if max_score > 0:
            for scenario, score in scores.items():
                if score == max_score:
                    return scenario

        return "default"


# 单例实例
_skills_service: Optional[PrinceSkillsService] = None


def get_skills_service() -> PrinceSkillsService:
    """获取技能包服务单例"""
    global _skills_service
    if _skills_service is None:
        _skills_service = PrinceSkillsService()
    return _skills_service
