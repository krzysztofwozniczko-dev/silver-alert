import os
import requests
import anthropic
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]

FRANKFURTER_URL = "https://api.frankfurter.app/latest"

def get_silver_usd() -> float:
    url = "https://query1.finance.yahoo.com/v8/finance/chart/SI%3DF"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    return float(price)

def get_fx_rates() -> dict:
    r = requests.get(FRANKFURTER_URL, params={"from": "EUR", "to": "PLN"}, timeout=10)
    r.raise_for_status()
    eur_pln = r.json()["rates"]["PLN"]

    r2 = requests.get(FRANKFURTER_URL, params={"from": "USD", "to": "PLN"}, timeout=10)
    r2.raise_for_status()
    usd_pln = r2.json()["rates"]["PLN"]

    return {"EUR_PLN": round(eur_pln, 4), "USD_PLN": round(usd_pln, 4)}

def silver_pln(silver_usd: float, usd_pln: float) -> float:
    return round(silver_usd * usd_pln / 31.1035, 2)

def get_ai_comment(silver_usd: float, eur_pln: float, usd_pln: float) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = (
        f"Cena srebra: {silver_usd:.2f} USD/oz | "
        f"EUR/PLN: {eur_pln} | USD/PLN: {usd_pln}\n\n"
        "Napisz po polsku 2-3 zdania (max 300 znaków) – krótki, rzeczowy komentarz "
        "o głównych czynnikach wpływających DZIŚ na cenę srebra oraz kursy EUR/PLN i USD/PLN. "
        "Bez wstępów, bez formatowania, tylko sam komentarz."
    )
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()

def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    print("✅ Wiadomość wysłana na Telegram.")

def main():
    today = datetime.now().strftime("%d.%m.%Y
