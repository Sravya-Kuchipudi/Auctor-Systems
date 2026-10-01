"""
Auctor Systems — LLM Service Abstraction
Provides unified access to Google Gemini with resilient local/deterministic fallback.
Never exposes keys, never crashes if credentials are missing.
"""

import os
import logging
from typing import Optional, Dict, Any

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE

logger = logging.getLogger("auctor.llm")


class LLMService:
    """
    Manages LLM completions for Auctor agents.
    If GEMINI_API_KEY is configured and mode is 'real', queries Google Gemini.
    Otherwise gracefully falls back to deterministic persona generation.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
        # Strip provider prefix if present (e.g. gemini/gemini-2.5-flash -> gemini-2.5-flash)
        raw_model = os.getenv("GEMINI_MODEL", GEMINI_MODEL) or "gemini-2.5-flash"
        self.model_name = raw_model.replace("gemini/", "") if "gemini/" in raw_model else raw_model
        self.temperature = float(os.getenv("GEMINI_TEMPERATURE", str(GEMINI_TEMPERATURE)))
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Google GenAI client with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI client: {e}")
                self._client = None
        else:
            logger.info("No GEMINI_API_KEY detected. Local deterministic mode active.")
            self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None and bool(self.api_key)

    async def generate_text(
        self,
        system_instruction: str,
        user_prompt: str,
        fallback_generator=None,
        mode: str = "real",
    ) -> str:
        """
        Generate text response from Gemini, or fallback if unavailable or error occurs.
        In demo mode, immediately returns deterministic persona generation via fallback_generator.
        """
        if mode == "demo":
            if fallback_generator:
                return fallback_generator()
            return ""

        if self._client and self.api_key:
            try:
                # Synchronous SDK call wrapped in executor or direct call
                import asyncio
                loop = asyncio.get_running_loop()

                def _call():
                    from google.genai import types
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=self.temperature,
                    )
                    response = self._client.models.generate_content(
                        model=self.model_name,
                        contents=user_prompt,
                        config=config,
                    )
                    return response.text

                text = await loop.run_in_executor(None, _call)
                if text and text.strip():
                    return text.strip()
            except Exception as err:
                logger.warning(
                    f"Gemini API call encountered an issue ({err}). Falling back to local intelligence."
                )

        if fallback_generator:
            return fallback_generator()
        return ""


# Singleton instance
llm_service = LLMService()
