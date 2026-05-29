import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


@dataclass(frozen=True)
class DeepSeekCompletion:
    content: str
    prompt_tokens: int | None
    completion_tokens: int | None
    finish_reason: str | None


@dataclass(frozen=True)
class DeepSeekJsonCompletion:
    data: dict[str, Any]
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
        if not settings.deepseek_balance_check_enabled:
            return

        timeout = httpx.Timeout(
            settings.deepseek_request_timeout_seconds,
            connect=10.0,
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    f"{settings.deepseek_base_url.rstrip('/')}/user/balance",
                    headers=DeepSeekProvider._headers(),
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="DeepSeek balance check timed out",
            ) from exc
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

        requested_currency = settings.deepseek_balance_currency.upper()

        balance_info = next(
            (
                item
                for item in data.get("balance_infos", [])
                if str(item.get("currency", "")).upper() == requested_currency
            ),
            None,
        )

        if balance_info is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"DeepSeek balance is not available in {requested_currency}",
            )

        try:
            available_balance = Decimal(str(balance_info["total_balance"]))
            required_balance = Decimal(str(settings.deepseek_min_balance))
        except (InvalidOperation, KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid balance response from DeepSeek",
            ) from exc

        if available_balance <= required_balance:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Token finished",
            )

    @staticmethod
    async def _post_completion(payload: dict[str, Any]) -> dict[str, Any]:
        timeout = httpx.Timeout(
            settings.deepseek_request_timeout_seconds,
            connect=10.0,
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
                    headers=DeepSeekProvider._headers(),
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="DeepSeek response timed out",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not connect to DeepSeek API",
            ) from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"DeepSeek generation failed: {response.text}",
            )

        return response.json()

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

        data = await DeepSeekProvider._post_completion(payload)

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

    @staticmethod
    async def complete_json(
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float = 0.2,
    ) -> DeepSeekJsonCompletion:
        payload = {
            "model": settings.deepseek_model,
            "messages": messages,
            "thinking": {"type": "disabled"},
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "stream": False,
        }

        data = await DeepSeekProvider._post_completion(payload)

        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
            usage = data.get("usage", {})
        except (KeyError, IndexError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid JSON response from DeepSeek API",
            ) from exc

        if finish_reason == "length":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek JSON output was cut off. Increase diagnostic token limit.",
            )

        try:
            parsed_data = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek did not return valid JSON",
            ) from exc

        if not isinstance(parsed_data, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek JSON output must be an object",
            )

        return DeepSeekJsonCompletion(
            data=parsed_data,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            finish_reason=finish_reason,
        )