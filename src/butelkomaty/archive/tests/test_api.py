import requests

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "pl-PL,pl;q=0.9",
    "Referer": "https://www.biedronka.pl/pl/sklepy/",
    "X-Requested-With": "XMLHttpRequest"
}

print("Otwieram stronę główną...")

r = session.get(
    "https://www.biedronka.pl/pl/sklepy/",
    headers=headers
)

print("Strona:", r.status_code)
print("Cookies:")
print(session.cookies)


print("\nPytam API...")

url = "https://www.biedronka.pl/api/shop/getbycity"

params = {
    "city": "32",
    "special": ""
}

api = session.get(
    url,
    params=params,
    headers=headers
)

print("API status:", api.status_code)

print(api.text[:1000])