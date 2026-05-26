"""
Base class for AI Skills (Superpowers)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from pydantic import BaseModel

class SkillResult(BaseModel):
    """Result from a skill execution"""
    content: str
    metadata: Dict[str, Any] = {}
    success: bool = True
    error: Optional[str] = None

class AISkill(ABC):
    """Abstract base class for all AI Skills"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, params: Dict[str, Any], **kwargs) -> SkillResult:
        """Execute the skill with given parameters"""
        pass

    @abstractmethod
    def get_system_prompt_extension(self) -> str:
        """Get the prompt extension to tell the AI how to use this skill"""
        pass
