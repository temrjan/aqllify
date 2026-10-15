"""Bot entry contract; all outbound calls are captured, never sent."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import urlsplit

from src.bot import handlers


def test_new_course_buttons_and_honest_copy():
    async def scenario():
        message = SimpleNamespace(
            from_user=SimpleNamespace(id=123, first_name="<Test>"), answer=AsyncMock()
        )
        await handlers.cmd_start(message)
        call = message.answer.call_args
        assert "rus tilini" in call.args[0]
        assert "Hozir boshlang‘ich darslar mavjud" in call.args[0]
        assert "&lt;Test&gt;" in call.args[0]
        buttons = call.kwargs["reply_markup"].inline_keyboard
        assert [urlsplit(row[0].web_app.url).path for row in buttons] == ["", "/uzbek"]
        for command, path in (
            (handlers.cmd_lesson, ""),
            (handlers.cmd_review, "/learn/review"),
        ):
            await command(message)
            button = message.answer.call_args.kwargs["reply_markup"].inline_keyboard[0][
                0
            ]
            assert urlsplit(button.web_app.url).path == path

    asyncio.run(scenario())
