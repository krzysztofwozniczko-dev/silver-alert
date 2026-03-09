import os
import requests
import anthropic
from datetime import datetime

# ── Konfiguracja ──────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]

# Darmowe API – nie wymaga klucza
FRANKFURTER_URL = "https://api.frankfurter.app/latest"

# ── Pobieranie danych ─────────────────────────────────────────────────────────
def get_silver_usd() -> float:
    """Cena srebra w USD za uncję trojańską (Yahoo Finance)."""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/SI%3DF"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    return float(price)


def get_fx_rates() -> dict:
    """Kursy EUR/PLN i USD/PLN."""
    r = requests.get(FRANKFURTER_URL, params={"from": "EUR", "to": "PLN,USD"}, timeout=10)
    r.raise_for_status()
    data = r.json()
    eur_pln = data["rates"]["PLN"]

    r2 = requests.get(FRANKFURTER_URL, params={"from": "USD", "to": "PLN"}, timeout=10)
    r2.raise_for_status()
    usd_pln = r2.json()["rates"]["PLN"]

    return {"EUR_PLN": round(eur_pln, 4), "USD_PLN": round(usd_pln, 4)}


def silver_pln(silver_usd: float, usd_pln: float) -> float:
    """Przelicz cenę srebra na PLN za gram (1 uncja = 31,1035 g)."""
    return round(silver_usd * usd_pln / 31.1035, 2)


# ── Komentarz AI ─────────────────────────────────────────────────────────────
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


# ── Telegram ──────────────────────────────────────────────────────────────────
def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    print("✅ Wiadomość wysłana na Telegram.")


# ── Główna logika ─────────────────────────────────────────────────────────────
def main():
    today = datetime.now().strftime("%d.%m.%Y")

    print("📡 Pobieram dane...")
    silver_usd_val = get_silver_usd()
    fx              = get_fx_rates()
    eur_pln_val     = fx["EUR_PLN"]
    usd_pln_val     = fx["USD_PLN"]
    silver_pln_val  = silver_pln(silver_usd_val, usd_pln_val)

    print("🤖 Generuję komentarz AI...")
    comment = get_ai_comment(silver_usd_val, eur_pln_val, usd_pln_val)

    message = (
        f"📊 <b>Raport dzienny – {today}</b>\n\n"
        f"🥈 <b>Srebro:</b>  {silver_usd_val:.2f} USD/oz  |  {silver_pln_val:.2f} PLN/g\n"
        f"💶 <b>EUR/PLN:</b> {eur_pln_val}\n"
        f"💵 <b>USD/PLN:</b> {usd_pln_val}\n\n"
        f"💬 <i>{comment}</i>"
    )

    print(message)
    send_telegram(message)


if __name__ == "__main__":
    main()
