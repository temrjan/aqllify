"""Browser regression against local real API + migrated disposable PostgreSQL.

Install Playwright separately. Start API with BOT_TOKEN=local-browser-test and
OPENAI_API_KEY='' on 8019 and Vite with VITE_API_URL=http://127.0.0.1:8019 on 5179.
This script signs synthetic identities in the test harness, never in product code.
"""

import asyncio
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4

from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
COURSE = json.loads((ROOT / "courses/russian/course.json").read_text())


async def main():
    fields = {
        "auth_date": str(int(time.time())),
        "user": json.dumps({"id": uuid4().int % 10**12, "first_name": "Browser test"}),
    }
    secret = hmac.new(b"WebAppData", b"local-browser-test", hashlib.sha256).digest()
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    signed = urlencode(fields)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        context = await browser.new_context(viewport={"width": 375, "height": 812})
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        async def authenticate(route):
            await route.continue_(
                headers={**route.request.headers, "X-Telegram-InitData": signed}
            )

        await page.route("http://127.0.0.1:8019/api/**", authenticate)

        async def fail_fetch(route):
            await route.fulfill(status=502, json={"detail": "test unavailable"})

        await page.route("**/learning/progress", fail_fetch, times=2)
        # `/` hosts the direction selector; a stored direction redirects to the course.
        await context.add_init_script("localStorage.setItem('direction', 'ru')")
        await page.goto("http://127.0.0.1:5179/")
        await expect(page.get_by_role("alert")).to_be_visible()
        await page.unroute("**/learning/progress", fail_fetch)
        await page.get_by_role("button", name="Qayta urinish", exact=True).click()
        await expect(
            page.get_by_role("heading", name=COURSE["title"], exact=True)
        ).to_be_visible()
        await page.get_by_role("button", name="Darajamni tekshirish").click()
        await expect(
            page.get_by_role("button", name="Tavsiyani ko‘rish")
        ).to_be_disabled()
        for question in COURSE["placement"]:
            await (
                page.locator(f'input[name="{question["id"]}"]')
                .nth(question["options"].index(question["accepted"][0]))
                .check()
            )
        await page.get_by_role(
            "button", name="Matnni yordam sifatida ko‘rish"
        ).first.click()
        await page.get_by_role("button", name="Tavsiyani ko‘rish").click()
        await expect(page.get_by_text("6/6 · Matn yordami bilan")).to_be_visible()
        await page.get_by_role("button", name="Shu darajani ko‘rish").click()
        await expect(
            page.get_by_text("To‘liq darslar tayyorlanmoqda.", exact=False)
        ).to_be_visible()
        await page.get_by_role("button", name="Boshlang‘ich mashqlarga qaytish").click()
        await page.locator('a[href="/ru/lesson/introductions"]').click()
        audio = page.locator("audio").first

        async def fail_audio(route):
            await route.fulfill(status=404, body="test media unavailable")

        await page.route("**/learning/audio/*", fail_audio, times=1)
        await audio.evaluate("el => el.load()")
        await expect(page.get_by_text("Audio yuklanmadi.", exact=False)).to_be_visible()
        await page.get_by_role("button", name="Qayta yuklash", exact=True).click()
        await audio.evaluate("el => { el.load(); return el.play(); }")
        await expect(audio).to_have_js_property("paused", False)
        assert await audio.evaluate("el => el.duration > 0")
        await page.get_by_role("checkbox", name="Sekinroq").first.check()
        await expect(audio).to_have_js_property("playbackRate", 0.8)
        await audio.evaluate("el => el.pause()")
        await page.get_by_role(
            "button", name="Mashqlarni boshlash / davom ettirish"
        ).click()
        lesson = COURSE["lessons"][0]
        answer_posts = []
        page.on(
            "request",
            lambda request: (
                answer_posts.append(request.url)
                if request.method == "POST" and request.url.endswith("/answers")
                else None
            ),
        )
        for index, exercise in enumerate(lesson["exercises"]):
            await expect(
                page.get_by_role("heading", name=exercise["prompt"], exact=True)
            ).to_be_visible()
            if exercise["kind"] == "choice":
                await page.get_by_role(
                    "radio", name=exercise["accepted"][0], exact=True
                ).check()
            else:
                await page.get_by_label("Ruscha javob", exact=True).fill(
                    exercise["accepted"][0]
                )
            if index == 0:
                # Server commits the first answer, but its response is lost.
                async def lose_answer(route):
                    response = await route.fetch(
                        headers={**route.request.headers, "X-Telegram-InitData": signed}
                    )
                    assert response.status == 200
                    await route.fulfill(
                        status=502, json={"detail": "test response loss"}
                    )

                await page.route("**/attempts/*/answers", lose_answer, times=1)
                await page.get_by_role("button", name="Tekshirish", exact=True).click()
                await expect(page.get_by_role("alert")).to_be_visible()
                await expect(
                    page.get_by_role("button", name="Keyingi", exact=True)
                ).to_have_count(0)
            before = len(answer_posts)
            await page.get_by_role("button", name="Tekshirish", exact=True).evaluate(
                "el => { el.click(); el.click(); }"
            )
            await expect(
                page.get_by_role("button", name="Keyingi", exact=True)
            ).to_be_visible()
            assert len(answer_posts) == before + 1
            await page.get_by_role("button", name="Keyingi", exact=True).evaluate(
                "el => { el.click(); el.click(); }"
            )
            if index + 1 < len(lesson["exercises"]):
                await expect(
                    page.get_by_role(
                        "heading",
                        name=lesson["exercises"][index + 1]["prompt"],
                        exact=True,
                    )
                ).to_be_visible()
            if index == 0:
                await page.reload()
                await page.get_by_role(
                    "button", name="Mashqlarni boshlash / davom ettirish"
                ).click()

        async def lose_completion(route):
            response = await route.fetch(
                headers={**route.request.headers, "X-Telegram-InitData": signed}
            )
            assert response.status == 200
            await route.fulfill(status=502, json={"detail": "test response loss"})

        await page.route("**/attempts/*/complete", lose_completion, times=1)
        await page.get_by_role("button", name="Natijani saqlash", exact=True).click()
        await expect(page.get_by_role("alert")).to_be_visible()
        await expect(page.get_by_text("NATIJA SAQLANDI", exact=True)).to_have_count(0)
        await page.get_by_role("button", name="Natijani saqlash", exact=True).click()
        await expect(page.get_by_text("100%", exact=False)).to_be_visible()
        await expect(page.get_by_text("40 XP", exact=False)).to_be_visible()
        await page.get_by_role("textbox", name="Javobingiz", exact=True).fill(
            "Здравствуйте"
        )
        await page.get_by_role("button", name="Yuborish", exact=True).click()
        await expect(page.get_by_role("alert")).to_contain_text(
            "Suhbat hozir ishlamayapti"
        )
        await expect(
            page.get_by_role("textbox", name="Javobingiz", exact=True)
        ).to_have_value("Здравствуйте")
        await page.get_by_role("link", name="Iboralarni takrorlash →").click()
        await page.get_by_role("button", name="Ruschasini ko‘rish").click()
        await page.get_by_role("button", name="Esladim", exact=True).click()
        await expect(page.get_by_text("3 TA IBORA", exact=True)).to_be_visible()
        await page.get_by_role("button", name="Natijalar", exact=True).click()
        await expect(page.get_by_text("40", exact=True)).to_be_visible()
        assert await page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        await page.goto("http://127.0.0.1:5179/uzbek")
        await expect(page).to_have_url("http://127.0.0.1:5179/uz")
        await page.get_by_role(
            "button", name="1 Salomlashish (Приветствия)", exact=True
        ).click()
        await expect(page).to_have_url(
            "http://127.0.0.1:5179/uz/lesson/block-1/01-salomlashish"
        )
        await page.goto("http://127.0.0.1:5179/")
        await expect(
            page.get_by_role("heading", name=COURSE["title"], exact=True)
        ).to_be_visible()
        assert not errors, errors
        if destination := os.environ.get("BROWSER_SCREENSHOT"):
            await page.screenshot(path=destination, full_page=True)
        await browser.close()
    print(
        "PASS: placement/manual levels, real audio/slow mode, response-loss retry, resume, double click, completion, no-key AI, review, progress, legacy route, mobile width, no JS exceptions"
    )


if __name__ == "__main__":
    asyncio.run(main())
