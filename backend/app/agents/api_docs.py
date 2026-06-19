import os
import re
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logging import logger

class APIDocsAgent:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.1)
        else:
            self.llm = None

    def generate(self, clone_path: str, file_list: List[str]) -> Dict[str, Any]:
        """
        Scans code files for route definitions and generates clean API Reference documentation.
        """
        logger.info("Running APIDocsAgent...")
        
        # 1. Search for potential API route patterns (FastAPI, Express, Spring, Flask)
        endpoints = self._detect_endpoints_heuristically(clone_path, file_list)
        
        if self.llm and endpoints:
            try:
                prompt = ChatPromptTemplate.from_template(
                    "You are a Technical Writer and API Architect.\n"
                    "Create a professional API Reference Guide based on these endpoints detected: {endpoints}\n"
                    "Provide request structures, payload fields, authentication, HTTP verbs, and example response payloads."
                )
                chain = prompt | self.llm
                api_content = chain.invoke({
                    "endpoints": str(endpoints)
                }).content
            except Exception as e:
                logger.error(f"API documentation generation failed: {str(e)}")
                api_content = self._fallback_api_reference(endpoints)
        else:
            api_content = self._fallback_api_reference(endpoints)

        return {
            "doc_type": "API_REFERENCE",
            "title": "API Reference Guide",
            "content": api_content,
            "endpoints_found": endpoints
        }

    def _detect_endpoints_heuristically(self, clone_path: str, file_list: List[str]) -> List[Dict[str, str]]:
        endpoints = []
        route_patterns = [
            # FastAPI / Flask: @app.get('/path'), @router.post("/path")
            re.compile(r'@(?:app|router|blueprint)\.(get|post|put|delete|patch|route)\s*\(\s*["\']([^"\']+)["\']'),
            # Express: app.get('/path', ...), router.post('/path', ...)
            re.compile(r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']')
        ]

        # Scan Python and JS/TS files in file_list
        for rel_path in file_list:
            if not any(rel_path.endswith(ext) for ext in [".py", ".js", ".ts", ".jsx", ".tsx"]):
                continue
            
            abs_path = os.path.join(clone_path, rel_path)
            if not os.path.exists(abs_path):
                continue
                
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                for pattern in route_patterns:
                    for match in pattern.finditer(content):
                        verb = match.group(1).upper()
                        route = match.group(2)
                        endpoints.append({
                            "file": rel_path,
                            "method": verb,
                            "route": route
                        })
            except Exception:
                pass
                
        return endpoints[:50]  # Cap list to prevent giant outputs

    def _fallback_api_reference(self, endpoints: List[Dict[str, str]]) -> str:
        if not endpoints:
            return (
                f"# API Reference Guide\n\n"
                f"No explicit API endpoints or routes were automatically detected in this repository. "
                f"This may be a CLI tool, library, UI frontend, or background worker."
            )
            
        lines = ["# API Reference Guide\n\nDetected REST API routes in this codebase:\n"]
        for ep in endpoints:
            lines.append(f"### `{ep['method']}` {ep['route']}\n")
            lines.append(f"- **Source File**: `{ep['file']}`\n")
            lines.append(f"- **Description**: Automatically scanned endpoint router handler.\n")
            lines.append("- **Authentication**: JWT Token / Cognito (default standard config)\n")
            lines.append("- **Response Status**: `200 OK` on success.\n")
            
        return "\n".join(lines)
