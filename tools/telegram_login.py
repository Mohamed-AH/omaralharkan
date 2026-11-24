"""Make the TG_SESSION login string the daily job uses to copy the channel's audio to R2 (tools/audio_sync.py).

Run it once on your own computer, with a Telegram account that can see the channel (a separate account for the
site is better than a personal one):
  pip install telethon
  python3 tools/telegram_login.py
It asks for the API id and hash (https://my.telegram.org → API development tools), the phone number and the code
Telegram sends, then prints a long string. Save that string as the GitHub secret TG_SESSION. Keep it private: it
is a login to that account. Ending the session in Telegram (Settings → Devices) cancels it.
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input('API id: ').strip())
api_hash = input('API hash: ').strip()
with TelegramClient(StringSession(), api_id, api_hash) as client:
    print('\nTG_SESSION (save as a GitHub secret):\n')
    print(client.session.save())
