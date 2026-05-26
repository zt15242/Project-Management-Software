"""
Central AI Service - Orchestrating Providers and Superpowers (Skills)
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

from api.models import ChatCompletionRequest, ChatMessage
from core.ai_config import ai_config
from services.ai import get_ai_provider, AIMessage, MessageRole
from services.ai.skills import get_all_skills

logger = logging.getLogger(__name__)

class AIService:
    """
    The orchestrator for AI operations.
    Handles provider selection and Skill (Superpower) injection.
    """

    def __init__(self, provider_name: Optional[str] = None):
        self.provider_name = provider_name
        self.skills = get_all_skills()

    async def get_active_provider(self):
        """Get the configured AI provider instance (asyncly from DB/Config)"""
        name = self.provider_name or ai_config.default_ai_provider
        return await get_ai_provider(name)

    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        # ... (keep existing implementation) ...
        base_prompt = """You are an advanced AI Project Assistant with specialized 'Superpowers'.
Your goal is to help users manage projects and create high-quality presentations (PPT).

Core Instructions:
- Professionalism: Maintain a helpful, analytical, and structured tone.
- Action-Oriented: Provide clear next steps and concrete outlines.
"""
        
        # Inject Skills description
        skills_prompt = "\n### YOUR SUPERPOWERS (SKILLS)\n"
        for skill in self.skills:
            skills_prompt += skill.get_system_prompt_extension()

        # Contextual Layer injection
        layer = context.get("layer", "general")
        layer_prompts = {
            "research": "\nCURRENT FOCUS: You are in Research Mode. Focus on gathering facts, trends, and data. Cite sources if available.",
            "outline": "\nCURRENT FOCUS: You are in Design Mode. Focus on logical structure, story hooks, and slide-by-slide breakdowns.",
            "polishing": "\nCURRENT FOCUS: You are in Editorial Mode. Focus on copywriting, tone adjustment, and visual placement suggestions."
        }
        
        return base_prompt + skills_prompt + layer_prompts.get(layer, "")

    async def chat(self, request: ChatCompletionRequest, context: Optional[Dict[str, Any]] = None) -> str:
        """Standard chat completion"""
        context = context or {}
        system_prompt = self._build_system_prompt(context)
        
        # Convert request messages to provider format
        messages = [AIMessage(role=MessageRole.SYSTEM, content=system_prompt)]
        for msg in request.messages:
            messages.append(AIMessage(role=MessageRole(msg.role), content=msg.content))
            
        provider = await self.get_active_provider()
        response = await provider.chat_completion(
            messages=messages,
            temperature=request.temperature or ai_config.temperature,
            max_tokens=request.max_tokens or ai_config.max_tokens
        )
        
        return response.content

    async def stream_chat(self, request: ChatCompletionRequest, context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Streaming chat completion"""
        context = context or {}
        system_prompt = self._build_system_prompt(context)
        
        messages = [AIMessage(role=MessageRole.SYSTEM, content=system_prompt)]
        for msg in request.messages:
            messages.append(AIMessage(role=MessageRole(msg.role), content=msg.content))
            
        provider = await self.get_active_provider()
        async for chunk in provider.stream_chat_completion(
            messages=messages,
            temperature=request.temperature or ai_config.temperature
        ):
            yield chunk

# Singleton instance
ai_service = AIService()
