import requests


pliki = [
    "https://static.biedronka.pl/js/biedronka.js?v=1106119",
    "https://static.biedronka.pl/js/shop.js?v=1106119"
]


headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.biedronka.pl/"
}


for url in pliki:

    print("\n==============================")
    print(url)
    print("==============================")

    r = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    print("Status:", r.status_code)
    print("Długość:", len(r.text))

    print("\nPierwsze 500 znaków:")
    print(r.text[:500])

    print("\nSzukam:")
    
    for slowo in [
        "ajax",
        "url",
        "shop",
        "json",
        "latitude",
        "longitude",
        "location",
        "map"
    ]:
        if slowo.lower() in r.text.lower():
            print("  +", slowo)
        else:
            print("  -", slowo)