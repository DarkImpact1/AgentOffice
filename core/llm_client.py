import hashlib
import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict, Union
from anthropic import Anthropic, APIError
from .config import settings
from .database import Database


class LLMClient:
    _instance: "Optional[LLMClient]" = None

    def __new__(cls, db: Optional[Database] = None) -> "LLMClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db: Optional[Database] = None) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.db = db
        self.default_model = settings.default_model
        self.complex_model = settings.complex_model
        self.cache_ttl = settings.cache_ttl_seconds

    def set_db(self, db: Database) -> None:
        self.db = db

    def _cache_key(self, model: str, system: str, messages: List[Dict], **kwargs: Any) -> str:
        content = json.dumps({"model": model, "system": system, "messages": messages, **kwargs}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    async def _get_cached(self, key: str) -> Optional[str]:
        if not self.db:
            return None
        return await self.db.get_cache(key)

    async def _set_cached(self, key: str, value: str) -> None:
        if not self.db:
            return
        expires = (datetime.now() + timedelta(seconds=self.cache_ttl)).isoformat()
        await self.db.set_cache(key, value, expires)

    async def _log_usage(self, agent: str, model: str, input_tokens: int, output_tokens: int, cached: bool) -> None:
        if self.db:
            await self.db.log_token_usage(agent, model, input_tokens, output_tokens, cached)

    async def complete(
        self,
        prompt: str,
        agent_name: str = "system",
        system: str = "You are a helpful assistant. Be concise.",
        use_complex_model: bool = False,
        use_cache: bool = True,
        json_mode: bool = False,
        max_tokens: int = 1024,
    ) -> str:
        model = self.complex_model if use_complex_model else self.default_model
        messages = [{"role": "user", "content": prompt}]

        if use_cache:
            cache_key = self._cache_key(model, system, messages, json_mode=json_mode)
            cached = await self._get_cached(cache_key)
            if cached:
                await self._log_usage(agent_name, model, 0, 0, cached=True)
                return cached

        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages,
                )
                result = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

                await self._log_usage(agent_name, model, input_tokens, output_tokens, cached=False)

                if use_cache:
                    await self._set_cached(cache_key, result)

                return result

            except APIError as e:
                if attempt == 2:
                    raise
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)

        return ""

    async def complete_json(
        self,
        prompt: str,
        agent_name: str = "system",
        system: str = "You are a helpful assistant. Respond only with valid JSON.",
        use_complex_model: bool = False,
        use_cache: bool = True,
        max_tokens: int = 1024,
    ) -> Union[Dict, List]:
        result = await self.complete(
            prompt=prompt,
            agent_name=agent_name,
            system=system,
            use_complex_model=use_complex_model,
            use_cache=use_cache,
            json_mode=True,
            max_tokens=max_tokens,
        )
        try:
            text = result.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": result}

    async def get_stats(self, agent: Optional[str] = None) -> Dict:
        if not self.db:
            return {"input_tokens": 0, "output_tokens": 0}
        return await self.db.get_token_stats(agent)


llm_client = LLMClient()
