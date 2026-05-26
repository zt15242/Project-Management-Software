"""
Research Skill - Enhanced search and analysis capabilities
"""

import logging
from typing import Dict, Any, Optional
from .base import AISkill, SkillResult
from core.ai_config import ai_config

logger = logging.getLogger(__name__)

class ResearchSkill(AISkill):
    """Skill for conducting deep research and web searches"""
    
    def __init__(self):
        super().__init__(
            name="research",
            description="Access real-time information from the internet and conduct deep multi-step analysis."
        )
        self._client = None
        self._init_client()

    def _init_client(self):
        """Lazy init Tavily client"""
        try:
            from tavily import TavilyClient
            api_key = ai_config.tavily_api_key
            if api_key:
                self._client = TavilyClient(api_key=api_key)
        except ImportError:
            logger.warning("tavily-python not installed. Research skill will be limited.")

    async def execute(self, params: Dict[str, Any], **kwargs) -> SkillResult:
        query = params.get("query")
        if not query:
            return SkillResult(content="", success=False, error="No query provided")

        if not self._client:
            return SkillResult(content="Search is currently unavailable (API key missing or library not installed).", success=False)

        try:
            # Perform search
            search_depth = params.get("depth", ai_config.tavily_search_depth)
            response = self._client.search(
                query=query,
                search_depth=search_depth,
                max_results=params.get("max_results", ai_config.tavily_max_results)
            )
            
            # Extract and format results
            results = response.get("results", [])
            formatted_content = "\n\n".join([
                f"Source: {r['url']}\nTitle: {r['title']}\nContent: {r['content']}"
                for r in results
            ])
            
            return SkillResult(
                content=formatted_content,
                metadata={"sources_count": len(results), "query": query}
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return SkillResult(content="", success=False, error=str(e))

    def get_system_prompt_extension(self) -> str:
        return """
[SKILL: research]
If you need current information from the web to answer the user's question or to gather data for a presentation, you can activate your RESEARCH skill.
Capabilities: 
- Search live web
- Compare multiple sources
- Analyze latest trends (2024-2025)
To use this: Just acknowledge you are searching and include research findings in your response.
"""
