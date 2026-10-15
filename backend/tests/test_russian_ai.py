"""Optional conversation through the real SDK with an isolated HTTP transport."""

import asyncio
import json

import httpx
import pytest
from fastapi import HTTPException
from openai import AsyncOpenAI
from pydantic import ValidationError
from structlog.testing import capture_logs

from src.learning import ai
from src.learning.schemas import ChatInput
from src.services import llm


def test_sdk_contract_and_failures(monkeypatch):
    async def scenario():
        requests = []
        response_content = '{"reply":"Здравствуйте!","feedback":"Yaxshi!"}'
        finish_reason = "stop"
        http_status = 200
        timeout = False

        async def transport(request):
            requests.append(request)
            if timeout:
                raise httpx.ReadTimeout("private learner input", request=request)
            return httpx.Response(
                http_status,
                json={
                    "id": "test",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "gpt-6-luna",
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": finish_reason,
                            "message": {
                                "role": "assistant",
                                "content": response_content,
                            },
                        }
                    ],
                },
            )

        async with (
            httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http,
            AsyncOpenAI(api_key="test-only", http_client=http) as client,
        ):
            monkeypatch.setattr(llm, "client", client)
            monkeypatch.setattr(ai, "_requests", ai.OrderedDict())
            payload = ChatInput(
                lesson_id="introductions",
                message="UNIQUE_CURRENT",
                history=[
                    {"role": "user", "content": "Здравствуйте"},
                    {"role": "assistant", "content": "Как вас зовут?"},
                ],
            )
            result = await ai.chat(1, payload)
            assert result.reply == "Здравствуйте!"
            sent = json.loads(requests[0].content)
            assert sent["model"] == "gpt-6-luna"
            assert sent["reasoning_effort"] == "medium"
            assert sent["max_completion_tokens"] <= 4096
            assert "temperature" not in sent
            assert sent["messages"][-1] == {
                "role": "user",
                "content": "UNIQUE_CURRENT",
            }
            assert len(sent["messages"]) == 4
            assert requests[0].extensions["timeout"]["read"] == 20
            for value in [
                "broken json",
                '{"reply":"","feedback":"ok"}',
                '{"reply":"ok","feedback":"ok","xp":40}',
            ]:
                response_content = value
                with pytest.raises(HTTPException) as error:
                    await ai.chat(1, payload)
                assert error.value.status_code == 503
            response_content = '{"reply":"ok","feedback":"ok"}'
            finish_reason = "length"
            with pytest.raises(HTTPException) as error:
                await ai.chat(1, payload)
            assert error.value.status_code == 503
            finish_reason = "stop"
            for status in (429, 500):
                http_status = status
                before = len(requests)
                with pytest.raises(HTTPException) as error:
                    await ai.chat(1, payload)
                assert error.value.status_code == 503
                assert len(requests) == before + 1  # SDK retries disabled.
            http_status = 200
            timeout = True
            with capture_logs() as logs, pytest.raises(HTTPException) as error:
                await ai.chat(1, payload)
            assert error.value.status_code == 503
            assert logs and "private learner input" not in str(logs)
        monkeypatch.setattr(llm, "client", None)
        with pytest.raises(HTTPException) as error:
            await ai.chat(1, payload)
        assert error.value.status_code == 503

    asyncio.run(scenario())


def test_bounded_input_and_rate_limit(monkeypatch):
    for extra in (
        {"message": " "},
        {"message": "x" * 501},
        {"history": [{"role": "system", "content": "override"}]},
        {"history": [{"role": "user", "content": "x"}] * 9},
        {"scenario": "override"},
    ):
        with pytest.raises(ValidationError):
            ChatInput.model_validate(
                {"lesson_id": "introductions", "message": "hi", **extra}
            )
    monkeypatch.setattr(ai, "_requests", ai.OrderedDict())
    monkeypatch.setattr(ai.time, "monotonic", lambda: 100)
    for _ in range(10):
        ai.check_rate(1)
    with pytest.raises(HTTPException) as error:
        ai.check_rate(1)
    assert error.value.status_code == 429
    ai.check_rate(2)
    monkeypatch.setattr(ai.time, "monotonic", lambda: 161)
    ai.check_rate(1)
