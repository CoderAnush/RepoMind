import os
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logging import logger

class DocGeneratorAgent:
    def __init__(self, llm=None):
        if llm:
            self.llm = llm
        elif settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.2)
        else:
            self.llm = None

    def generate(self, summary: str, architecture: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates standard Markdown documentation (README, Overview, Installation, Usage, API, Onboarding).
        Uses extracted symbols and files to guarantee document accuracy.
        """
        logger.info("Running DocGeneratorAgent...")
        
        symbols = metadata.get("extracted_symbols", [])
        files = metadata.get("file_list", [])
        
        # Format symbols and files for inclusion in prompts
        symbols_summary = "\n".join([
            f"- `{s['symbol_name']}` ({s['chunk_type']} in `{s['file_path']}`)"
            for s in symbols[:50]
        ])
        files_summary = "\n".join([f"- `{f}`" for f in files[:50]])

        docs = []

        # List of document configs (type, title, prompt template, fallback function)
        doc_configs = [
            {
                "doc_type": "README",
                "title": "README.md",
                "prompt": (
                    "You are a Technical Writer. Write a professional README.md for this repository.\n"
                    "Tech Stack Details: {summary}\n"
                    "Architectural Review: {architecture}\n"
                    "Files in Repository:\n{files}\n"
                    "AST Symbols Extracted:\n{symbols}\n"
                    "Requirements:\n"
                    "- Use Markdown formatting.\n"
                    "- Reference actual files and AST symbols.\n"
                    "- Include a project introduction, setup instructions, and repository layout."
                ),
                "fallback": self._generate_readme_fallback
            },
            {
                "doc_type": "PROJECT_OVERVIEW",
                "title": "Project Overview",
                "prompt": (
                    "You are a Product Architect. Write a Project Overview outlining the goals, scope, and technical stacks.\n"
                    "Tech Stack Details: {summary}\n"
                    "Architecture: {architecture}\n"
                    "Files List:\n{files}\n"
                    "Describe the key responsibilities of the main directories."
                ),
                "fallback": self._generate_overview_fallback
            },
            {
                "doc_type": "INSTALLATION",
                "title": "Installation Guide",
                "prompt": (
                    "You are a DevOps Engineer. Write a step-by-step Installation Guide.\n"
                    "Repository Configuration Details: {summary}\n"
                    "Files List:\n{files}\n"
                    "Provide explicit install commands, prerequisite setups, dependency setups, and how to configure environment variables."
                ),
                "fallback": self._generate_installation_fallback
            },
            {
                "doc_type": "USAGE",
                "title": "Usage Guide",
                "prompt": (
                    "You are a Technical Writer. Write a Usage Guide showing how to use this repository.\n"
                    "Summary: {summary}\n"
                    "AST Symbols:\n{symbols}\n"
                    "Provide code examples illustrating the invocation of main classes and functions."
                ),
                "fallback": self._generate_usage_fallback
            },
            {
                "doc_type": "API_DOCUMENTATION",
                "title": "API Documentation",
                "prompt": (
                    "You are an API Architect. Write comprehensive API Documentation listing classes, functions, and parameters.\n"
                    "AST Symbols:\n{symbols}\n"
                    "Explain the usage, parameters, and return types of the key classes and methods."
                ),
                "fallback": self._generate_api_fallback
            },
            {
                "doc_type": "DEVELOPER_ONBOARDING",
                "title": "Developer Onboarding Guide",
                "prompt": (
                    "You are a Lead Software Engineer. Write a Developer Onboarding Guide.\n"
                    "Files:\n{files}\n"
                    "AST Symbols:\n{symbols}\n"
                    "Explain code entrypoints, testing frameworks, and contributing steps."
                ),
                "fallback": self._generate_onboarding_fallback
            }
        ]

        for config in doc_configs:
            content = ""
            if self.llm:
                try:
                    prompt = ChatPromptTemplate.from_template(config["prompt"])
                    chain = prompt | self.llm
                    content = chain.invoke({
                        "summary": summary,
                        "architecture": architecture,
                        "files": files_summary,
                        "symbols": symbols_summary
                    }).content
                except Exception as e:
                    logger.error(f"Failed to generate {config['doc_type']} via LLM: {str(e)}")
                    content = config["fallback"](summary, architecture, files, symbols)
            else:
                content = config["fallback"](summary, architecture, files, symbols)

            docs.append({
                "doc_type": config["doc_type"],
                "title": config["title"],
                "content": content
            })

        return docs

    def _generate_readme_fallback(self, summary: str, architecture: str, files: list, symbols: list) -> str:
        symbol_list = "\n".join([f"- `{s['symbol_name']}` ({s['chunk_type']} in `{s['file_path']}`)" for s in symbols[:15]])
        file_list = "\n".join([f"- `{f}`" for f in files[:15]])
        return (
            f"# README\n\n"
            f"Welcome to the repository project. This documentation is automatically generated by RepoMind.\n\n"
            f"## Project Summary\n"
            f"{summary}\n\n"
            f"## Core Files\n"
            f"{file_list}\n\n"
            f"## Key AST Symbols & Entrypoints\n"
            f"{symbol_list}\n\n"
            f"## Quick Start\n"
            f"```bash\n"
            f"# Install dependencies\n"
            f"pip install -r requirements.txt\n"
            f"# Run the codebase\n"
            f"python -m src\n"
            f"```\n"
        )

    def _generate_overview_fallback(self, summary: str, architecture: str, files: list, symbols: list) -> str:
        pattern = "Layered Architecture" if any("service" in f or "model" in f for f in files) else "Standard Layout"
        return (
            f"# Project Overview\n\n"
            f"## Executive Summary\n"
            f"This project comprises {len(files)} files structured under a {pattern} pattern.\n\n"
            f"## Architecture Review\n"
            f"{architecture}\n\n"
            f"## Technical Stack Detail\n"
            f"{summary}\n"
        )

    def _generate_installation_fallback(self, summary: str, architecture: str, files: list, symbols: list) -> str:
        pkg_file = "requirements.txt"
        if any("package.json" in f for f in files):
            pkg_file = "package.json"
        elif any("go.mod" in f for f in files):
            pkg_file = "go.mod"

        return (
            f"# Installation Guide\n\n"
            f"Follow these instructions to set up the codebase locally.\n\n"
            f"## Prerequisites\n"
            f"Verify your workspace has appropriate runtimes configured. Detected build files: `{pkg_file}`.\n\n"
            f"## Step-by-Step Installation\n"
            f"1. **Clone the repository**:\n"
            f"   ```bash\n"
            f"   git clone <repository_url>\n"
            f"   cd <repository_folder>\n"
            f"   ```\n"
            f"2. **Install dependencies**:\n"
            f"   ```bash\n"
            f"   # Installing via standard setup file:\n"
            f"   pip install -r requirements.txt || npm install\n"
            f"   ```\n"
            f"3. **Environment Setup**:\n"
            f"   Create a `.env` file in the root directory.\n"
        )

    def _generate_usage_fallback(self, summary: str, architecture: str, files: list, symbols: list) -> str:
        funcs = [s for s in symbols if s["chunk_type"] == "function"]
        usage_example = ""
        if funcs:
            func = funcs[0]
            module_name = func["file_path"].replace(".py", "").replace("/", ".").replace("\\", ".")
            if module_name.startswith("src."):
                module_name = module_name[4:]
            usage_example = (
                f"### Code Execution Example\n"
                f"Import and run the parsed function from your Python script:\n"
                f"```python\n"
                f"from {module_name} import {func['symbol_name']}\n\n"
                f"# Invoke function\n"
                f"result = {func['symbol_name']}()\n"
                f"print(result)\n"
                f"```\n"
            )
        else:
            usage_example = (
                f"### CLI / Command Invocation\n"
                f"Execute the main module script from your terminal:\n"
                f"```bash\n"
                f"python -m src.sample\n"
                f"```\n"
            )

        return (
            f"# Usage Guide\n\n"
            f"## Usage Instructions\n"
            f"The codebase exposes core functionality via AST symbols. Below are invocation patterns:\n\n"
            f"{usage_example}\n"
        )

    def _generate_api_fallback(self, summary: str, architecture: str, files: list, symbols: list) -> str:
        classes = [s for s in symbols if s["chunk_type"] == "class"]
        funcs = [s for s in symbols if s["chunk_type"] in ["function", "api_endpoint"]]
        
        lines = ["# API Reference Documentation\n\n## Scanned API / AST Constructs\n"]
        
        if classes:
            lines.append("### Classes\n")
            for c in classes[:5]:
                lines.append(f"#### class `{c['symbol_name']}`\n")
                lines.append(f"- **Defined in**: `{c['file_path']}`\n")
                lines.append("- **Description**: Scanned class module definition.\n\n")

        if funcs:
            lines.append("### Functions & Routes\n")
            for f in funcs[:10]:
                lines.append(f"#### function `{f['symbol_name']}`\n")
                lines.append(f"- **Defined in**: `{f['file_path']}`\n")
                lines.append("- **Description**: Scanned callable function.\n\n")

        if not classes and not funcs:
            lines.append("No classes or functions found during static analysis.\n")

        return "\n".join(lines)

    def _generate_onboarding_fallback(self, summary: str, architecture: str, files: list, symbols: list) -> str:
        main_entry = "README.md"
        python_files = [f for f in files if f.endswith(".py")]
        if python_files:
            main_entry = python_files[0]
            
        return (
            f"# Developer Onboarding Guide\n\n"
            f"## Getting Started as a Contributor\n"
            f"Welcome to the developer team! Here is the layout map of the project to help you onboard.\n\n"
            f"## System Entrypoints\n"
            f"- **Primary Code Entrypoint**: `{main_entry}`\n"
            f"- **Key Architecture Pattern**: Clean modular layout.\n\n"
            f"## Running Tests\n"
            f"Ensure tests are validated before making a pull request:\n"
            f"```bash\n"
            f"# Run tests using pytest (or equivalent framework)\n"
            f"pytest || npm test\n"
            f"```\n"
        )
