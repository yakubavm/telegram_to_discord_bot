import asyncio
import logging
from config import TELEGRAM_BOT_TOKEN, DISCORD_BOT_TOKEN, HASHTAG_TO_CHANNEL

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

import discord
from discord.ext import commands

# Логування
logging.basicConfig(level=logging.INFO)

# Discord бот
intents = discord.Intents.default()
intents.message_content = True
discord_bot = commands.Bot(command_prefix="!", intents=intents)

# Telegram частина
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()


async def forward_to_discord(text, files):
    hashtags = [word for word in text.split() if word.startswith("#")]
    sent = False

    for hashtag in hashtags:
        if hashtag in HASHTAG_TO_CHANNEL:
            channel_id = HASHTAG_TO_CHANNEL[hashtag]
            channel = discord_bot.get_channel(channel_id)
            if not channel:
                logging.warning(f"Канал з ID {channel_id} не знайдено.")
                continue

            if files:
                await channel.send(content=text or " ", files=files)
            else:
                await channel.send(content=text)
            sent = True

    if not sent:
        logging.info("Хештеги не знайдено або не відповідають жодному каналу.")


@telegram_app.message_handler(filters.ALL)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return

    msg = update.effective_message
    text = msg.caption if msg.caption else msg.text if msg.text else ""

    files = []
    if msg.photo:
        file = await msg.photo[-1].get_file()
        file_bytes = await file.download_as_bytearray()
        files.append(discord.File(fp=bytes(file_bytes), filename="image.jpg"))

    elif msg.document:
        file = await msg.document.get_file()
        file_bytes = await file.download_as_bytearray()
        files.append(discord.File(fp=bytes(file_bytes), filename=msg.document.file_name))

    elif msg.video:
        file = await msg.video.get_file()
        file_bytes = await file.download_as_bytearray()
        files.append(discord.File(fp=bytes(file_bytes), filename="video.mp4"))

    await forward_to_discord(text, files)


async def main():
    await discord_bot.login(DISCORD_BOT_TOKEN)
    await discord_bot.connect()


# Запуск Telegram та Discord одночасно
async def start_bots():
    telegram_task = telegram_app.run_polling(allowed_updates=telegram_app.allowed_updates, close_loop=False)
    discord_task = main()
    await asyncio.gather(telegram_task, discord_task)


if __name__ == "__main__":
    asyncio.run(start_bots())
