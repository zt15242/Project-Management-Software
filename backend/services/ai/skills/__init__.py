"""
Skills for AI Superpowers
"""
from .base import AISkill, SkillResult
from .research import ResearchSkill
from .ppt_design import PPTStructureSkill

def get_all_skills():
    return [
        ResearchSkill(),
        PPTStructureSkill()
    ]
