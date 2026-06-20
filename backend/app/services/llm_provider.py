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

        detected_names = [f["file_path"] for f in context_files]
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
        if any(x in query_lower for x in ["explain the full project", "what does this repository do", "what is this repository", "explain the project"]):
            if readme_chunk:
                readme_lines = [l.strip() for l in readme_chunk.split("\n") if l.strip()]
                # Extract first 15 clean lines (avoid large headers)
                desc_lines = []
                for line in readme_lines:
                    if line.startswith("# README") or line.startswith("Welcome to the repository") or "documentation is automatically generated" in line:
                        continue
                    desc_lines.append(line)
                    if len(desc_lines) >= 15:
                        break
                description = "\n".join(desc_lines)
                explanation = f"### Project Purpose & Overview\n{description}\n\n"
            else:
                explanation = (
                    f"### Project Purpose & Overview\n"
                    f"The `{repo_name}` repository is a software codebase comprising execution modules and configurations. "
                    f"Based on the files detected ({', '.join(detected_names[:3])}), the codebase is designed to manage "
                    f"core application logic, utilities, and integrations.\n\n"
                )
            
            # Technical Stack details
            explanation += "### Repository Technical Details\n"
            explanation += f"- **Repository Name**: `{repo_name}`\n"
            explanation += f"- **Total Files**: {total_files}\n"
            explanation += f"- **Lines of Code (LOC)**: {total_loc}\n"
            explanation += f"- **Languages Breakdown**: `{languages_str}`\n\n"

            # Code module details
            explanation += "### Main Code Modules\n"
            for f in detected_names[:5]:
                desc = "Contains setup, contributing guidelines, and onboarding documentation." if "readme" in f.lower() else "Implements core execution logic and functions."
                if "inference" in f.lower():
                    desc = "Loads machine learning/deep learning model weights (such as YOLO or CNN models) to perform detection, inference, and classification."
                elif "mapping" in f.lower():
                    desc = "Defines category and class mappings to convert model indices to human-readable labels."
                elif "utils" in f.lower():
                    desc = "Implements utility functions and data manipulation helpers."
                elif "core" in f.lower():
                    desc = "Defines core runtime objects, base classes, and execution parameters."
                elif "decorators" in f.lower():
                    desc = "Implements custom decorators for runtime behavior extension."
                explanation += f"- **`{f}`**: {desc}\n"
                
            answer_text = (
                f"**[Production LLM Simulation Mode - Provider: {selected_provider.upper()}, Model: {selected_model}]**\n\n"
                f"{explanation}"
            )
            
        elif "architecture" in query_lower:
            arch_summary = (
                f"### Repository Architecture Overview\n"
                f"The repository `{repo_name}` uses a modular design layout, dividing logic between core functions, "
                f"helper utilities, configuration blocks, and testing scripts. "
                f"The codebase contains {total_files} files with a total of {total_loc} lines of code. "
                f"The main building blocks are:\n\n"
            )
            for f in detected_names[:5]:
                arch_summary += f"- **`{f}`**: Module containing runtime scripts and components.\n"
            arch_summary += f"\nThis structure decouples data parsing and application execution, facilitating testing and expansion."
            
            answer_text = (
                f"**[Production LLM Simulation Mode - Provider: {selected_provider.upper()}, Model: {selected_model}]**\n\n"
                f"{arch_summary}"
            )
            
        elif any(x in query_lower for x in ["auth", "login", "jwt", "token", "user", "security"]):
            auth_files = [f for f in detected_names if any(x in f.lower() for x in ["auth", "login", "jwt", "token", "user", "security"])]
            if auth_files:
                auth_summary = (
                    "### Authentication & Security Handler Modules\n"
                    "The following files are responsible for managing authorization, logins, token encryption, and roles:\n\n"
                )
                for f in auth_files[:3]:
                    auth_summary += f"- **`{f}`**: Manages authentication sessions and validations.\n"
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
            
            if not matches_text and detected_names:
                matches_text = "I found the following files in the repository:\n"
                for f in detected_names[:5]:
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
