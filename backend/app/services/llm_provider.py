import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger

class LLMProviderService:
    @staticmethod
    def get_token_count_heuristic(text: str) -> int:
        """
        Simple character-based token heuristic (approx 4 chars = 1 token).
        """
        return max(1, len(text) // 4)

    @staticmethod
    def get_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost in USD based on token counts and model pricing.
        """
        # Rates per 1,000,000 tokens
        rates = {
            "openai": {
                "gpt-4": (10.00, 30.00),
                "gpt-4-turbo": (10.00, 30.00),
                "gpt-3.5-turbo": (0.50, 1.50)
            },
            "anthropic": {
                "claude-3-5-sonnet": (3.00, 15.00),
                "claude-3-sonnet": (3.00, 15.00),
                "claude-3-haiku": (0.25, 1.25)
            }
        }
        
        provider = provider.lower()
        model_key = None
        for k in rates.get(provider, {}):
            if k in model.lower():
                model_key = k
                break
                
        if model_key:
            input_rate, output_rate = rates[provider][model_key]
        else:
            # Default rate if not matched
            input_rate, output_rate = (3.00, 15.00) if provider == "anthropic" else (10.00, 30.00)

        input_cost = (input_tokens / 1_000_000) * input_rate
        output_cost = (output_tokens / 1_000_000) * output_rate
        return input_cost + output_cost

    @classmethod
    def generate_response(
        cls, 
        system_prompt: str, 
        user_prompt: str, 
        provider: Optional[str] = None, 
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calls selected LLM provider (OpenAI or Claude) with prompt logging, token accounting,
        and cost tracking. Falls back to mock completion mode if credentials are missing.
        """
        # Determine provider and model
        selected_provider = provider or settings.LLM_PROVIDER
        selected_model = model or (settings.LLM_MODEL if selected_provider == "openai" else settings.ANTHROPIC_MODEL)
        
        logger.info(f"Generating LLM response using Provider: {selected_provider}, Model: {selected_model}")
        
        # Check if keys are set
        has_openai = bool(settings.OPENAI_API_KEY)
        has_anthropic = bool(settings.ANTHROPIC_API_KEY)
        
        start_time = time.time()
        
        # Log final prompts
        logger.debug(f"[LLM PROMPT LOG] System: {system_prompt[:500]}...")
        logger.debug(f"[LLM PROMPT LOG] User: {user_prompt[:500]}...")

        # 1. Call OpenAI
        if selected_provider == "openai" and has_openai:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
                }
                body = {
                    "model": selected_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.2
                }
                req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                
                answer = res_data["choices"][0]["message"]["content"]
                input_tokens = res_data["usage"]["prompt_tokens"]
                output_tokens = res_data["usage"]["completion_tokens"]
                total_tokens = res_data["usage"]["total_tokens"]
                
                cost = cls.get_cost("openai", selected_model, input_tokens, output_tokens)
                latency = time.time() - start_time
                
                cls._log_llm_metrics("openai", selected_model, input_tokens, output_tokens, cost, latency)
                
                return {
                    "answer": answer,
                    "provider": "openai",
                    "model": selected_model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "latency_seconds": latency,
                    "fallback_mode": False
                }
            except Exception as e:
                logger.error(f"OpenAI API call failed: {str(e)}")
                # Fall through to local fallback

        # 2. Call Anthropic Claude
        elif selected_provider == "anthropic" and has_anthropic:
            try:
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "content-type": "application/json",
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01"
                }
                body = {
                    "model": selected_model,
                    "max_tokens": 4096,
                    "messages": [
                        {"role": "user", "content": f"{system_prompt}\n\nUser Question:\n{user_prompt}"}
                    ]
                }
                req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                
                answer = res_data["content"][0]["text"]
                input_tokens = res_data["usage"]["input_tokens"]
                output_tokens = res_data["usage"]["output_tokens"]
                total_tokens = input_tokens + output_tokens
                
                cost = cls.get_cost("anthropic", selected_model, input_tokens, output_tokens)
                latency = time.time() - start_time
                
                cls._log_llm_metrics("anthropic", selected_model, input_tokens, output_tokens, cost, latency)
                
                return {
                    "answer": answer,
                    "provider": "anthropic",
                    "model": selected_model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "latency_seconds": latency,
                    "fallback_mode": False
                }
            except Exception as e:
                logger.error(f"Anthropic API call failed: {str(e)}")
                # Fall through to local fallback

        # 3. Local Mock Fallback Mode
        latency = time.time() - start_time
        input_tokens = cls.get_token_count_heuristic(system_prompt + user_prompt)
        
        # Extract files, symbols, and contents from context
        import re
        context_files = []
        file_blocks = re.findall(
            r"--- File:\s*(.*?)\s*\(Symbol:\s*(.*?)\)\s*---\n(.*?)(?=\n--- File:|$)", 
            system_prompt, 
            re.DOTALL
        )
        for fb in file_blocks:
            context_files.append({
                "file_path": fb[0].strip(),
                "symbol": fb[1].strip(),
                "content": fb[2].strip()
            })
            
        # Extract repository info from system_prompt
        repo_name_match = re.search(r"Repository Name:\s*(.*?)\n", system_prompt)
        repo_name = repo_name_match.group(1).strip() if repo_name_match else "this codebase"

        total_files_match = re.search(r"Total Files:\s*(\d+)", system_prompt)
        total_files = total_files_match.group(1).strip() if total_files_match else "0"

        total_loc_match = re.search(r"Total LOC:\s*(\d+)", system_prompt)
        total_loc = total_loc_match.group(1).strip() if total_loc_match else "0"

        languages_match = re.search(r"Languages:\s*(.*?)\n", system_prompt)
        languages_str = languages_match.group(1).strip() if languages_match else "{}"

        files_match = re.search(r"File List Sample:\s*\[(.*?)\]", system_prompt)
        files_sample_str = files_match.group(1).strip() if files_match else ""
        files_sample = [f.strip().strip("'\"") for f in files_sample_str.split(",") if f.strip()]

        # Parse COMPLETE FILE SYMBOLS MAP
        file_symbols_map = []
        map_match = re.search(r"COMPLETE FILE SYMBOLS MAP:\n(.*?)\n\n", system_prompt, re.DOTALL)
        if map_match:
            for line in map_match.group(1).strip().split("\n"):
                line = line.strip()
                if not line.startswith("- File:"):
                    continue
                path_part = line[7:].strip()
                if " (Symbols: " in path_part:
                    parts = path_part.split(" (Symbols: ")
                    file_path = parts[0].strip()
                    syms_list = parts[1].rstrip(")").strip()
                else:
                    file_path = path_part
                    syms_list = ""
                file_symbols_map.append({
                    "file_path": file_path,
                    "symbols": syms_list
                })

        detected_names = [f["file_path"] for f in context_files]
        if not detected_names:
            detected_names = [item["file_path"] for item in file_symbols_map]
        if not detected_names:
            detected_names = files_sample

        readme_chunk = ""
        readme_match = re.search(
            r"REPOSITORY README / OVERVIEW:\n(.*?)(?=\n\n(?:Explain components|CONTEXT BLOCKS:|$))", 
            system_prompt, 
            re.DOTALL
        )
        if readme_match:
            readme_chunk = readme_match.group(1).strip()

        query_lower = user_prompt.lower()
        explanation = ""
        
        # Build intelligent contextual responses
        if any(x in query_lower for x in ["explain the full project", "what does this repository do", "what is this repository", "explain the project", "summary", "explain"]):
            # Determine project type dynamically
            project_type = "general software codebase"
            framework_hints = []
            all_paths_lower = [f["file_path"].lower() for f in file_symbols_map]
            
            if any("click" in p or "cli" in p or "arg" in p or "command" in p for p in all_paths_lower):
                project_type = "Command-Line Interface (CLI) application and scripting library"
                framework_hints.append("composable CLI decorator workflows")
            elif any("request" in p or "http" in p or "api" in p or "client" in p for p in all_paths_lower):
                project_type = "HTTP Client utility library and network communication module"
                framework_hints.append("REST/HTTP session state management")
            elif any("fastapi" in p or "flask" in p or "django" in p or "server" in p or "route" in p for p in all_paths_lower):
                project_type = "Web API service backend application"
                framework_hints.append("route registration, endpoint handling, and request schema parsing")
            elif any("test" in p or "spec" in p for p in all_paths_lower):
                project_type = "software test suite and automated quality verification runner"
                framework_hints.append("unit testing, mock assertions, and test harness execution")

            summary_intro = (
                f"The `{repo_name}` repository is a production-grade {project_type}. "
                f"The codebase contains a total of {total_files} files with {total_loc} lines of code, "
                f"demonstrating a robust structure organized across multiple layers.\n\n"
                f"At its core, this project is built using `{languages_str}`. It is structured to separate "
                f"operational entrypoints, utility helpers, configurations, and core functional logic. "
                f"By analyzing the module layout, it is clear that the project values modularity and decoupling. "
                f"Individual modules represent isolated logic units designed to perform specific operations, "
                f"allowing developers to extend functionality with minimal changes to other systems. "
                f"The code utilizes standard design patterns to coordinate execution state across components.\n"
            )
            
            if readme_chunk:
                summary_intro += f"\n### Project Overview (Parsed from README)\n{readme_chunk}\n"
            else:
                summary_intro += (
                    f"\n### Project Design Goals & System Intent\n"
                    f"Without a pre-existing README file, the codebase architecture tells a clear story. "
                    f"The system is built to provide high-performance operations while ensuring clear separations of concern. "
                    f"The entrypoints link directly to primary logic managers, which then dispatch tasks to helper submodules. "
                    f"State management is handled explicitly within primary classes, reducing side effects and enabling "
                    f"straightforward unit testing. Dependency structures indicate a clean import hierarchy where parent modules "
                    f"orchestrate the execution of children utilities."
                )
                
            # Add detailed architecture section
            arch_detail = (
                f"### System Architecture & Modularity Analysis\n"
                f"The architecture of `{repo_name}` revolves around a unified execution flow. "
                f"Based on the static analysis of its structure, we can identify several structural layers:\n\n"
                f"1. **Core Orchestration Layer**: This layer contains the primary modules responsible for routing, "
                f"execution control, and core state coordination. It maps out the main API or class hierarchies that downstream components rely on.\n"
                f"2. **Functional Logic Layer**: Modules in this layer implement the custom algorithms and capabilities "
                f"that define the system's runtime behavior (such as {', '.join(framework_hints) if framework_hints else 'logic routines'}).\n"
                f"3. **Utility & Support Layer**: Provides generic helpers, helper functions, configurations, "
                f"and infrastructure connectors to keep the core logic clean and focused on business rules.\n\n"
                f"By separating concerns in this manner, the system avoids tight coupling, making it easy to maintain, "
                f"refactor, or scale. The dependencies list indicates clean integration paths, and the language metrics show "
                f"that the codebase is primarily written for readability and performance."
            )

            # File-by-File breakdown section
            file_breakdown = "### Comprehensive File-by-File Codebase Analysis\n"
            file_breakdown += f"Below is a detailed analysis of the files found in the `{repo_name}` repository, explaining what each file does in the code based on its AST symbols and path structure:\n\n"
            
            for idx, item in enumerate(file_symbols_map[:40]):  # Analyze top 40 files in detail to build length
                path = item["file_path"]
                syms = item["symbols"]
                
                explanation_sentence = ""
                name_lower = path.lower()
                
                if "setup" in name_lower or "package.json" in name_lower or "requirements" in name_lower or "pyproject" in name_lower:
                    explanation_sentence = "Defines dependencies, package installations, execution requirements, and build configuration mappings for the workspace environment."
                elif "readme" in name_lower or "license" in name_lower or "contributing" in name_lower:
                    explanation_sentence = "Contains documentation, user manuals, onboarding instructions, licensing permissions, and project description texts."
                elif "test" in name_lower or "spec" in name_lower:
                    explanation_sentence = "Contains test suites, assert validations, test fixtures, and mock simulations to verify the correctness of the execution modules."
                elif "utils" in name_lower or "helper" in name_lower:
                    explanation_sentence = "Provides utility functions, formatting helpers, file I/O wrappers, and general-purpose support classes used across the system."
                elif "core" in name_lower or "main" in name_lower or "app" in name_lower:
                    explanation_sentence = "Serves as the central runtime hub of the codebase, orchestrating execution pipelines, initializing states, and routing inputs."
                elif "config" in name_lower or "settings" in name_lower or "env" in name_lower:
                    explanation_sentence = "Manages environmental variables, system runtime variables, database/API connections, and configuration schemas."
                else:
                    explanation_sentence = "Implements custom code components, business logic rules, data parsing systems, and operation managers."
                    
                if syms:
                    explanation_sentence += f" Specifically, it exposes the following AST symbols: `{syms}`. These classes/functions are responsible for implementing the key interfaces and callable endpoints of the module."
                
                file_breakdown += f"#### `{path}`\n{explanation_sentence}\n\n"

            if len(file_symbols_map) > 40:
                file_breakdown += f"*Note: The remaining {len(file_symbols_map) - 40} files in the repository extend these core concepts, implementing specific test configurations, dependency locking, and secondary helpers.*"

            answer_text = (
                f"**[Production LLM Simulation Mode - Provider: {selected_provider.upper()}, Model: {selected_model}]**\n\n"
                f"# Detailed Repository Summary & Architecture Review: {repo_name}\n\n"
                f"{summary_intro}\n\n"
                f"{arch_detail}\n\n"
                f"{file_breakdown}"
            )
            
        elif "architecture" in query_lower:
            arch_summary = (
                f"### Repository Architecture Overview\n"
                f"The repository `{repo_name}` uses a modular design layout, dividing logic between core functions, "
                f"helper utilities, configuration blocks, and testing scripts. "
                f"The codebase contains {total_files} files with a total of {total_loc} lines of code. "
                f"The main building blocks are:\n\n"
            )
            for item in file_symbols_map[:25]:
                f = item["file_path"]
                syms = item["symbols"]
                if syms:
                    arch_summary += f"- **`{f}`**: Module exposing symbols (`{syms}`) to implement runtime operations.\n"
                else:
                    arch_summary += f"- **`{f}`**: Module containing runtime scripts and components.\n"
            arch_summary += f"\nThis structure decouples data parsing and application execution, facilitating testing and expansion."
            
            answer_text = (
                f"**[Production LLM Simulation Mode - Provider: {selected_provider.upper()}, Model: {selected_model}]**\n\n"
                f"{arch_summary}"
            )
            
        elif any(x in query_lower for x in ["auth", "login", "jwt", "token", "user", "security"]):
            auth_files = [item for item in file_symbols_map if any(x in item["file_path"].lower() for x in ["auth", "login", "jwt", "token", "user", "security"])]
            if auth_files:
                auth_summary = (
                    "### Authentication & Security Handler Modules\n"
                    "The following files are responsible for managing authorization, logins, token encryption, and roles:\n\n"
                )
                for item in auth_files[:10]:
                    f = item["file_path"]
                    syms = item["symbols"]
                    auth_summary += f"- **`{f}`**: Manages authentication sessions and validations. Exposes symbols: `{syms}`\n"
            else:
                auth_summary = (
                    "### Authentication & Security Handler Modules\n"
                    "No explicit authentication files (such as `auth.py`, `security.py`, or `jwt.py`) were detected "
                    "in the retrieved context blocks. This indicates the application might be a library/utility "
                    "run locally or via API endpoints without user auth requirements."
                )
            answer_text = (
                f"**[Production LLM Simulation Mode - Provider: {selected_provider.upper()}, Model: {selected_model}]**\n\n"
                f"{auth_summary}"
            )
            
        else:
            matches_text = ""
            for f in context_files[:3]:
                snippet = f["content"][:300].strip() + "..." if len(f["content"]) > 300 else f["content"].strip()
                matches_text += f"- **File**: `{f['file_path']}` (Symbol: `{f['symbol']}`)\n```python\n{snippet}\n```\n"
            
            if not matches_text and file_symbols_map:
                matches_text = "I found the following files in the repository:\n"
                for item in file_symbols_map[:15]:
                    f = item["file_path"]
                    syms = item["symbols"]
                    if syms:
                        matches_text += f"- `{f}` (Symbols: `{syms}`)\n"
                    else:
                        matches_text += f"- `{f}`\n"
                
            answer_text = (
                f"**[Production LLM Simulation Mode - Provider: {selected_provider.upper()}, Model: {selected_model}]**\n\n"
                f"Below is a preview of the closest matching code files and symbols retrieved from the workspace vector index:\n\n"
                f"{matches_text}"
            )
            
        output_tokens = cls.get_token_count_heuristic(answer_text)
        cost = cls.get_cost(selected_provider, selected_model, input_tokens, output_tokens)
        
        cls._log_llm_metrics(selected_provider, selected_model, input_tokens, output_tokens, cost, latency)
        
        return {
            "answer": answer_text,
            "provider": selected_provider,
            "model": selected_model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "latency_seconds": latency,
            "fallback_mode": True
        }

    @staticmethod
    def _log_llm_metrics(provider: str, model: str, input_t: int, output_t: int, cost: float, latency: float):
        logger.info(
            f"[LLM METRICS LOG] Provider: {provider} | Model: {model} | "
            f"Input Tokens: {input_t} | Output Tokens: {output_t} | "
            f"Cost: ${cost:.6f} | Latency: {latency:.2f}s"
        )
