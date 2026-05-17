"""
Bot Renungan Harian Alkitab - Telegram (pakai Groq - GRATIS)
=============================================================
Install dulu:
    pip install groq python-telegram-bot apscheduler pytz python-dotenv

Isi file .env:
    TELEGRAM_BOT_TOKEN=...
    TELEGRAM_CHAT_ID=...
    GROQ_API_KEY=...

Jalankan:
    python main.py
"""

import asyncio
import logging
import os
from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from groq import Groq
from telegram import Bot
from telegram.constants import ParseMode

# ── Konfigurasi ──────────────────────────────────────────────────────────────

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")

TIMEZONE    = pytz.timezone("Asia/Jakarta")
JAM_KIRIM   = 5
MENIT_KIRIM = 0

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("renungan_bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ── Generate Renungan ─────────────────────────────────────────────────────────

def generate_renungan() -> str:
    client = Groq(api_key=GROQ_API_KEY)

    hari_ini = datetime.now(TIMEZONE).strftime("%A, %d %B %Y")

    prompt = f"""Hari ini adalah {hari_ini}.

Buatkan renungan harian Kristen yang inspiratif dalam Bahasa Indonesia dengan format berikut:

📖 *RENUNGAN HARIAN*
_{hari_ini}_

✨ *[Judul Renungan yang Menarik]*

📜 *Ayat Firman:*
[Satu ayat Alkitab lengkap dengan referensinya]

💭 *Renungan:*
[3-4 paragraf singkat: makna ayat, relevan kehidupan sehari-hari, hangat dan mudah dimengerti]

🙏 *Doa Hari Ini:*
[Doa singkat 2-3 kalimat sesuai tema]

💪 *Ayat Hafalan:*
[Ulang ayat utama atau ayat pendek yang mudah dihafal]

Selamat beraktivitas dan Tuhan memberkati! 🕊️

Gunakan format Markdown Telegram: *bold* dan _italic_. Renungan harus original dan menyentuh hati."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
    )

    return response.choices[0].message.content


# ── Kirim ke Telegram ─────────────────────────────────────────────────────────

async def kirim_renungan():
    log.info("Memulai pengiriman renungan harian...")
    try:
        log.info("Menghubungi Groq AI...")
        teks = generate_renungan()
        log.info("Renungan selesai dibuat (%d karakter)", len(teks))

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=teks,
            parse_mode=ParseMode.MARKDOWN,
        )
        log.info("✅ Renungan berhasil dikirim!")

    except Exception as e:
        log.error("❌ Gagal: %s", e, exc_info=True)


# ── Cek Konfigurasi ───────────────────────────────────────────────────────────

def cek_konfigurasi():
    missing = [k for k, v in {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID":   TELEGRAM_CHAT_ID,
        "GROQ_API_KEY":       GROQ_API_KEY,
    }.items() if not v]

    if missing:
        log.error("❌ Belum diisi di .env: %s", ", ".join(missing))
        raise SystemExit(1)

    log.info("✅ Konfigurasi OK")
    log.info("   Chat ID : %s", TELEGRAM_CHAT_ID)
    log.info("   Jadwal  : Setiap hari jam %02d:%02d WIB", JAM_KIRIM, MENIT_KIRIM)


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    cek_konfigurasi()

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        kirim_renungan,
        trigger="cron",
        hour=JAM_KIRIM,
        minute=MENIT_KIRIM,
        name="renungan_harian",
    )
    scheduler.start()

    log.info("🤖 Bot aktif! Renungan dikirim jam %02d:%02d WIB setiap hari.", JAM_KIRIM, MENIT_KIRIM)

    # Kirim langsung sekali sebagai tes
    log.info("📤 Mengirim renungan tes sekarang...")
    await kirim_renungan()

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot dihentikan.")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
