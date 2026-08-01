"""Provider adapter — the R1 axis-C ruling made concrete (gate-log 2026-07-23).

Environment-split providers: local/producer runs on the Anthropic API key,
the company runtime on Azure OpenAI. Both bind through this one adapter
(litellm underneath), model ids and endpoints come ONLY from env/config —
never code (the KGoT hardcoded-tool-model trap) — and ``extract_usage``
normalizes both providers' token metadata into one shape from day one
(llm-graph-builder's ``get_total_tokens`` is the template).

litellm imports lazily so the pipeline stays unit-testable in envs without
it (the poetry env); tests inject a fake provider instead.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

PROVIDERS = ("anthropic", "azure")


@dataclass
class LlmUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class LlmReply:
    text: str
    usage: LlmUsage
    model: str
    ms: int


def extract_usage(usage_obj) -> LlmUsage:
    """Normalize provider token metadata (anthropic / azure-openai / litellm / gemini)."""
    if usage_obj is None:
        return LlmUsage()

    def _get(name: str) -> int | None:
        if isinstance(usage_obj, dict):
            value = usage_obj.get(name)
        else:
            value = getattr(usage_obj, name, None)
        return int(value) if isinstance(value, int | float) else None

    prompt = _get("prompt_tokens")  # openai / azure / litellm
    completion = _get("completion_tokens")
    if prompt is None:
        prompt = _get("input_tokens")  # anthropic raw
        completion = completion if completion is not None else _get("output_tokens")
    if prompt is None:
        prompt = _get("prompt_token_count")  # gemini usage_metadata
        completion = completion if completion is not None else _get("candidates_token_count")
    return LlmUsage(prompt_tokens=prompt or 0, completion_tokens=completion or 0)


class ProviderConfigError(RuntimeError):
    """Missing/invalid provider configuration — fail with a fixable message, never a stack dive."""


class LiteLlmProvider:
    """One ``complete()`` seam over litellm for both ruled providers."""

    def __init__(self, provider: str, model: str) -> None:
        if provider not in PROVIDERS:
            raise ProviderConfigError(
                f"GRAPHQA_PROVIDER={provider!r} — must be one of {PROVIDERS} (R1 ruling: "
                "local/producer=anthropic, company=azure)"
            )
        self.provider = provider
        self.model = model
        # litellm routing prefix; the model NAME still comes from env, never here.
        self._litellm_model = f"{provider}/{model}"

    def complete(self, system: str, user: str, max_tokens: int = 1200) -> LlmReply:
        import litellm  # lazy: agents-venv dependency only

        started = time.perf_counter()
        response = litellm.completion(
            model=self._litellm_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
            max_tokens=max_tokens,
        )
        text = (response.choices[0].message.content or "").strip()
        return LlmReply(
            text=text,
            usage=extract_usage(getattr(response, "usage", None)),
            model=getattr(response, "model", self.model),
            ms=int((time.perf_counter() - started) * 1000),
        )


def provider_from_env() -> LiteLlmProvider:
    provider = os.getenv("GRAPHQA_PROVIDER", "anthropic").strip().lower()
    model = os.getenv("GRAPHQA_MODEL", "").strip()
    if not model:
        raise ProviderConfigError(
            "GRAPHQA_MODEL is not set (agents/.env) — model ids live in config, never code"
        )
    if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        raise ProviderConfigError("ANTHROPIC_API_KEY is not set (agents/.env)")
    if provider == "azure" and not (
        os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE")
    ):
        raise ProviderConfigError(
            "AZURE_API_KEY / AZURE_API_BASE are not set (agents/.env; company runtime)"
        )
    return LiteLlmProvider(provider=provider, model=model)
