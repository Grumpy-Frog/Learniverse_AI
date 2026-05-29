from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


@dataclass(frozen=True)
class DeepSeekCompletion:
    content: str
    prompt_tokens: int | None
    completion_tokens: int | None
    finish_reason: str | None


class DeepSeekProvider:
    @staticmethod
    def _headers() -> dict[str, str]:
        if not settings.deepseek_api_key or settings.deepseek_api_key.startswith("PASTE_"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="DeepSeek API key is not configured",
            )

        return {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    async def ensure_credit_available() -> None:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{settings.deepseek_base_url.rstrip('/')}/user/balance",
                    headers=DeepSeekProvider._headers(),
                )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not verify DeepSeek balance",
            ) from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not verify DeepSeek balance",
            )

        data = response.json()

        if not data.get("is_available", False):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Token finished",
            )

        selected_currency = settings.deepseek_balance_currency.upper()

        balance_item = next(
            (
                item
                for item in data.get("balance_infos", [])
                if str(item.get("currency", "")).upper() == selected_currency
            ),
            None,
        )

        if balance_item is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"DeepSeek balance is not available in {selected_currency}",
            )

        try:
            balance = Decimal(str(balance_item["total_balance"]))
            minimum_balance = Decimal(str(settings.deepseek_min_balance))
        except (InvalidOperation, KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid balance response from DeepSeek",
            ) from exc

        if balance <= minimum_balance:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Token finished",
            )

    @staticmethod
    async def complete(
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> DeepSeekCompletion:
        payload = {
            "model": settings.deepseek_model,
            "messages": messages,
            "thinking": {"type": "disabled"},
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
                    headers=DeepSeekProvider._headers(),
                    json=payload,
                )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not connect to DeepSeek API",
            ) from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek generation request failed",
            )

        data = response.json()

        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
            usage = data.get("usage", {})
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from DeepSeek API",
            ) from exc

        if not content or not str(content).strip():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek returned an empty response",
            )

        return DeepSeekCompletion(
            content=str(content).strip(),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            finish_reason=finish_reason,
        )