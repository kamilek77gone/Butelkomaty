import requests
import re


URL = "https://www.biedronka.pl/pl/sklepy/lista"

headers = {
    "User-Agent": "Mozilla/5.0"
}


html = requests.get(
    URL,
    headers=headers
).text


print("Szukam plików JS...\n")


skrypty = re.findall(
    r'<script[^>]+src="([^"]+)"',
    html
)


for s in skrypty:
    print(s)