import os
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logging import logger

class RepoAnalysisAgent:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.1)
        else:
            self.llm = None

    def analyze(self, clone_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes repository structure, file setup, and configuration files to determine the tech stack.
        """
        logger.info("Running RepoAnalysisAgent...")
        
        # 1. Look for configuration files to parse tech stack
        config_files = self._detect_config_files(clone_path)
        
        # 2. Extract content of config files to get dependencies
        config_summaries = {}
        for rel_path, abs_path in config_files.items():
            try:
                with open(abs_path, "r", errors="ignore") as f:
                    # Capture first 100 lines
                    lines = f.readlines()
                    config_summaries[rel_path] = "".join(lines[:100])
            except Exception:
                pass

        # Detect README content for rich summarization
        readme_content = ""
        readme_candidates = ["README.md", "readme.md", "README", "readme", "README.TXT", "readme.txt"]
        for cand in readme_candidates:
            full = os.path.join(clone_path, cand)
            if os.path.exists(full):
                try:
                    with open(full, "r", encoding="utf-8", errors="ignore") as f:
                        readme_content = "".join(f.readlines()[:150])
                except Exception:
                    pass
                break

        # 3. Call LLM to summarize tech stack if key is present
        if self.llm:
            try:
                prompt = ChatPromptTemplate.from_template(
                    "You are a Senior Project Architect analyzing a new code repository.\n"
                    "Here is the directory file tree: {file_tree}\n"
                    "Here is the configuration details: {config_details}\n"
                    "Here is the first part of the repository README:\n{readme_text}\n\n"
                    "Provide a detailed structured overview summarizing:\n"
                    "1. Primary Languages and Frameworks\n"
                    "2. Database & Storage layers\n"
                    "3. Cloud Infrastructure & DevOps setups\n"
                    "4. Summary of the system's purpose."
                )
                chain = prompt | self.llm
                response = chain.invoke({
                    "file_tree": str(metadata.get("file_list", [])),
                    "config_details": str(config_summaries),
                    "readme_text": readme_content
                })
                summary = response.content
            except Exception as e:
                logger.error(f"LLM call failed in RepoAnalysisAgent: {str(e)}")
                summary = self._fallback_summary(metadata, config_files, clone_path)
        else:
            summary = self._fallback_summary(metadata, config_files, clone_path)

        return {
            "summary": summary,
            "detected_configs": list(config_files.keys()),
            "frameworks": self._heuristic_framework_detect(config_files)
        }

    def _detect_config_files(self, clone_path: str) -> Dict[str, str]:
        configs = {}
        target_files = {
            "package.json", "requirements.txt", "pyproject.toml", 
            "go.mod", "Cargo.toml", "pom.xml", "build.gradle", 
            "docker-compose.yml", "Dockerfile", "serverless.yml"
        }
        for root, _, files in os.walk(clone_path):
            for file in files:
                if file in target_files:
                    rel_path = os.path.relpath(os.path.join(root, file), clone_path)
                    configs[rel_path] = os.path.join(root, file)
        return configs

    def _heuristic_framework_detect(self, config_files: Dict[str, str]) -> List[str]:
        frameworks = []
        for rel_path in config_files.keys():
            if "package.json" in rel_path:
                frameworks.append("NodeJS")
            elif "requirements.txt" in rel_path or "pyproject.toml" in rel_path:
                frameworks.append("Python Pip")
            elif "go.mod" in rel_path:
                frameworks.append("Go Modules")
            elif "Cargo.toml" in rel_path:
                frameworks.append("Rust Cargo")
        return frameworks

    def _fallback_summary(self, metadata: Dict[str, Any], config_files: Dict[str, str], clone_path: str = "") -> str:
        project_desc = ""
        if clone_path:
            # Look for README file
            readme_candidates = ["README.md", "readme.md", "README", "readme", "README.TXT", "readme.txt"]
            readme_path = None
            for cand in readme_candidates:
                full = os.path.join(clone_path, cand)
                if os.path.exists(full):
                    readme_path = full
                    break
            
            if readme_path:
                try:
                    with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    
                    # Extract the first few sections/paragraphs that describe the project
                    desc_lines = []
                    heading_count = 0
                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            if desc_lines and desc_lines[-1] != "\n":
                                desc_lines.append("\n")
                            continue
                        
                        # Stop if we hit too many sections or a setup/license section
                        if stripped.startswith("#"):
                            lower_strip = stripped.lower()
                            if any(x in lower_strip for x in ["license", "contributing", "installation", "setup", "usage"]):
                                break
                            
                            # Limit to first 3 headers
                            heading_count += 1
                            if heading_count > 3:
                                break
                        
                        desc_lines.append(line)
                    
                    if desc_lines:
                        project_desc = "".join(desc_lines).strip()
                except Exception as e:
                    logger.warning(f"Error reading README in fallback summary: {e}")
        
        if not project_desc:
            # Fallback if no README
            project_desc = (
                "This repository is a software codebase comprising execution modules and configurations. "
                "The system provides services designed to process codebase structures and automate core logic workflows."
            )

        langs = ", ".join([f"{k} ({v}%)" for k, v in metadata.get("languages_loc_percentage", {}).items()])
        summary = (
            f"### Project Description\n"
            f"{project_desc}\n\n"
            f"### Technical Stack Summary\n"
            f"- **Languages Detected**: {langs if langs else 'Unknown'}\n"
            f"- **Total Files**: {metadata.get('total_files', 0)}\n"
            f"- **Lines of Code**: {metadata.get('total_loc', 0)}\n"
            f"- **Configuration Files Found**: {', '.join(config_files.keys()) if config_files else 'None'}"
        )
        return summary
