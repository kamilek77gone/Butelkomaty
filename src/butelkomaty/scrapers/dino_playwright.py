import asyncio
import json
from playwright.async_api import async_playwright

URL = "https://marketdino.pl/wyszukiwarka/"

async def run():
    async with async_playwright() as p:
        # HEADLESS = FALSE → pełne okno przeglądarki
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-gpu"  # GPU w Surface i tak jest słabe, ale renderer działa
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/114.0 Safari/537.36"
        )

        page = await context.new_page()

        print("Ładowanie Dino...")
        await page.goto(URL, timeout=120000)

        print("Czekanie aż Nuxt się załaduje...")
        await page.wait_for_function("window.__NUXT__ !== undefined", timeout=120000)

        print("Uruchamianie wyszukiwarki Dino przez JS...")
        await page.evaluate("""
            window.__NUXT__.data[0].searchQuery = 'wroclaw';
            window.__NUXT__.data[0].searchResults =
                window.__NUXT__.data[0].search('wroclaw');
        """)

        print("Czekanie na wyniki...")
        await page.wait_for_timeout(5000)

        print("Wyciąganie danych...")
        nuxt = await page.evaluate("window.__NUXT__")

        with open("dino_data.json", "w", encoding="utf-8") as f:
            json.dump(nuxt, f, ensure_ascii=False, indent=2)

        print("Zapisano dane do dino_data.json")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
