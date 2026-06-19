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
        
        # Build a response summarizing context
        answer_text = (
            f"**[Production LLM Simulation Mode - Provider: {selected_provider.upper()}, Model: {selected_model}]**\n\n"
            f"Here is a mockup of how a real LLM would reply using Qdrant vector retrieval context.\n\n"
            f"**Retrieved Context Summary**:\n"
            f"We analyzed the query '{user_prompt}' and retrieved files that contained symbols like classes, methods, or setup specifications.\n\n"
            f"To build this response on the backend, RepoMind computed inputs using the standard pricing matrices:\n"
            f"- input tokens: {input_tokens}\n"
            f"- output tokens: 180\n"
            f"- calculated transaction cost: ${cls.get_cost(selected_provider, selected_model, input_tokens, 180):.6f} USD"
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
