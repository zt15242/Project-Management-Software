"""
PPT Design Skill - Expertise in presentation structure and storytelling
"""

import logging
from typing import Dict, Any
from .base import AISkill, SkillResult

logger = logging.getLogger(__name__)

class PPTStructureSkill(AISkill):
    """Skill for designing professional presentation outlines and content"""
    
    def __init__(self):
        super().__init__(
            name="ppt_design",
            description="Create logical, persuasive, and visually balanced presentation structures."
        )

    async def execute(self, params: Dict[str, Any], **kwargs) -> SkillResult:
        topic = params.get("topic")
        # This is a prompt-based skill, so execution mostly happens via the main AI call
        # with the system prompt extension we provide.
        return SkillResult(content=f"Ready to design PPT for: {topic}")

    def get_system_prompt_extension(self) -> str:
        return """
[SKILL: ppt_design]
You are a world-class presentation consultant. When helping with a PPT:
1. **HOOK**: Start with a compelling narrative or problem statement.
2. **BALANCE**: Ensure content is not too dense. Aim for 3-5 bullet points per slide.
3. **VISUALS**: Suggest high-impact visual concepts instead of just text.
4. **SCENARIO**: Adaptive logic for Corporate, Educational, Creative, or Technical scenarios.
When asked for an outline, always follow a hierarchical structure and specify what should be on each slide clearly.
"""
