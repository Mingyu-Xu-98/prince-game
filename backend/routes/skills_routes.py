# 《君主论》技能包 API 路由

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.prince_skills_service import get_skills_service

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillResponse(BaseModel):
    """技能包响应"""
    name: str
    description: str
    category: str
    use_when: str
    content: Optional[str] = None


class SkillListResponse(BaseModel):
    """技能包列表响应"""
    skills: List[SkillResponse]
    total: int


class ScenarioRequest(BaseModel):
    """场景请求"""
    text: str


class ScenarioResponse(BaseModel):
    """场景检测响应"""
    scenario: str
    skills: List[SkillResponse]


@router.get("/", response_model=SkillListResponse)
async def list_skills():
    """获取所有技能包列表"""
    service = get_skills_service()
    skills = service.get_all_skills()

    return SkillListResponse(
        skills=[
            SkillResponse(
                name=s.name,
                description=s.description,
                category=s.category,
                use_when=s.use_when
            )
            for s in skills.values()
        ],
        total=len(skills)
    )


@router.get("/{skill_name}", response_model=SkillResponse)
async def get_skill(skill_name: str):
    """获取指定技能包详情"""
    service = get_skills_service()
    skill = service.get_skill(skill_name)

    if not skill:
        raise HTTPException(status_code=404, detail=f"技能包不存在: {skill_name}")

    return SkillResponse(
        name=skill.name,
        description=skill.description,
        category=skill.category,
        use_when=skill.use_when,
        content=skill.content
    )


@router.get("/category/{category}", response_model=SkillListResponse)
async def get_skills_by_category(category: str):
    """按分类获取技能包"""
    service = get_skills_service()
    skills = service.get_skills_by_category(category)

    return SkillListResponse(
        skills=[
            SkillResponse(
                name=s.name,
                description=s.description,
                category=s.category,
                use_when=s.use_when
            )
            for s in skills
        ],
        total=len(skills)
    )


@router.post("/detect-scenario", response_model=ScenarioResponse)
async def detect_scenario(request: ScenarioRequest):
    """根据文本检测场景并返回相关技能包"""
    service = get_skills_service()

    # 检测场景
    scenario = service.detect_scenario(request.text)

    # 获取相关技能包
    skills = service.get_skills_for_scenario(scenario)

    return ScenarioResponse(
        scenario=scenario,
        skills=[
            SkillResponse(
                name=s.name,
                description=s.description,
                category=s.category,
                use_when=s.use_when
            )
            for s in skills
        ]
    )


@router.get("/scenario/{scenario}", response_model=SkillListResponse)
async def get_skills_for_scenario(scenario: str):
    """获取指定场景的相关技能包"""
    service = get_skills_service()
    skills = service.get_skills_for_scenario(scenario)

    return SkillListResponse(
        skills=[
            SkillResponse(
                name=s.name,
                description=s.description,
                category=s.category,
                use_when=s.use_when,
                content=s.content
            )
            for s in skills
        ],
        total=len(skills)
    )


@router.post("/search")
async def search_skills(keywords: List[str]):
    """根据关键词搜索技能包"""
    service = get_skills_service()
    skills = service.search_skills(keywords)

    return SkillListResponse(
        skills=[
            SkillResponse(
                name=s.name,
                description=s.description,
                category=s.category,
                use_when=s.use_when
            )
            for s in skills
        ],
        total=len(skills)
    )
