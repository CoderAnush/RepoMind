from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logging import logger

class ArchitectureAgent:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.1)
        else:
            self.llm = None

    def analyze(self, summary: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes dependencies, structures, and files to outline the architectural design pattern.
        """
        logger.info("Running ArchitectureAgent...")
        
        file_tree = metadata.get("file_list", [])
        
        if self.llm:
            try:
                prompt = ChatPromptTemplate.from_template(
                    "You are a Principal Software Architect.\n"
                    "Analyze the architecture pattern of the repository based on the following details:\n"
                    "Tech Stack Summary: {summary}\n"
                    "File Tree: {file_tree}\n\n"
                    "Write a comprehensive Architectural design review detailing:\n"
                    "1. Architecture Pattern (MVC, Clean Architecture, Hexagonal, Monolithic, Microservices, or Serverless)\n"
                    "2. System Entrypoints and Boundaries\n"
                    "3. Data Flow between layers\n"
                    "4. Relationship between core folders/packages."
                )
                chain = prompt | self.llm
                response = chain.invoke({
                    "summary": summary,
                    "file_tree": str(file_tree[:200])  # Cap tree to avoid LLM context overflow
                })
                arch_review = response.content
            except Exception as e:
                logger.error(f"LLM call failed in ArchitectureAgent: {str(e)}")
                arch_review = self._fallback_review(file_tree)
        else:
            arch_review = self._fallback_review(file_tree)

        return {
            "architecture_review": arch_review,
            "detected_pattern": self._heuristic_pattern_detect(file_tree)
        }

    def _heuristic_pattern_detect(self, file_tree: List[str]) -> str:
        patterns = []
        for path in file_tree:
            if "controller" in path or "view" in path or "model" in path:
                return "MVC (Model-View-Controller)"
            if "domain" in path or "usecase" in path or "infrastructure" in path:
                return "Clean Architecture / DDD"
            if "handler" in path or "service" in path or "repository" in path:
                patterns.append("layered")
        return "Layered Architecture" if patterns else "Standard Directory Layout"

    def _fallback_review(self, file_tree: List[str]) -> str:
        pattern = self._heuristic_pattern_detect(file_tree)
        review = (
            f"### Architectural Design Review\n"
            f"- **Architectural Pattern Detected**: {pattern}\n"
            f"- **Core Entrypoints**: Detected in root layout paths.\n\n"
            f"#### Folder Layout Hierarchy:\n"
            f"The codebase utilizes namespaces for components. Core components reside in folders like `/app` or `/src`.\n"
            f"Modules import dependencies hierarchically. Direct interactions seem to be localized per directory module."
        )
        return review
