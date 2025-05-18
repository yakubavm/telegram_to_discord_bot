import os
import logging
import discord
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN or not DISCORD_BOT_TOKEN:
    raise RuntimeError("Токени не задані у змінних оточення!")

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

HASHTAG_TO_CHANNEL = {
    '#3dprint': 1373507331924693094,  # заміни на свої ID
    '#logo': 1373507348735463434,
    '#wallpaper': 1373507362886909952,
}

@discord_client.event
async def on_ready():
    logger.info(f'Discord бот увійшов як {discord_client.user}')

async def send_to_discord_channels(message_text, files, hashtags):
    for tag in hashtags:
        channel_id = HASHTAG_TO_CHANNEL.get(tag.lower())
        if channel_id:
            channel = discord_client.get_channel(channel_id)
            if channel:
                if files:
                    discord_files = [discord.File(fp=f) for f in files]
                    await channel.send(content=message_text or None, files=discord_files)
                else:
                    await channel.send(content=message_text or "Нове повідомлення з Telegram")
            else:
                logger.warning(f"Канал з ID {channel_id} не знайдено")
        else:
            logger.info(f"Хештег {tag} не призначений для каналів")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text = msg.text or msg.caption or ""
    hashtags = [part for part in text.split() if part.startswith('#')]

    files = []
    if msg.photo:
        photo_file = await msg.photo[-1].get_file()
        photo_path = f"/tmp/{photo_file.file_id}.jpg"
        await photo_file.download_to_drive(photo_path)
        files.append(photo_path)
    if msg.document:
        doc_file = await msg.document.get_file()
        doc_path = f"/tmp/{doc_file.file_id}_{msg.document.file_name}"
        await doc_file.download_to_drive(doc_path)
        files.append(doc_path)
    if msg.video:
        video_file = await msg.video.get_file()
        video_path = f"/tmp/{video_file.file_id}.mp4"
        await video_file.download_to_drive(video_path)
        files.append(video_path)

    await send_to_discord_channels(text, files, hashtags)

    for f in files:
        try:
            os.remove(f)
        except Exception as e:
            logger.error(f"Не вдалося видалити файл {f}: {e}")

telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
telegram_app.add_handler(MessageHandler(filters.ALL, handle_message))

import asyncio

async def main():
    # Запускаємо одночасно Discord і Telegram боти
    discord_task = asyncio.create_task(discord_client.start(DISCORD_BOT_TOKEN))
    telegram_task = asyncio.create_task(telegram_app.start())
    await telegram_app.updater.start_polling()  # починаємо приймати оновлення

    await asyncio.gather(discord_task, telegram_task)

if __name__ == '__main__':
    asyncio.run(main())
