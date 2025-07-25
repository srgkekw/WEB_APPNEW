import asyncio
import logging
import sys
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, BotCommand

from faststream.rabbit import RabbitBroker

LOG_FILE = "message_log.json"

async def log_message(chat_id: int, message_id: int):
    log_entry = {"chat_id": chat_id, "message_id": message_id}
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)
    except FileNotFoundError:
        messages = []

    messages.append(log_entry)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

# --- Конфигурация ---
TOKEN = "8025883202:AAGS2AVDdp6C1skDFo-RHCJUXxyQkwpHWNE"
RABBIT_URL = "amqp://guest:guest@rabbitmq:5672/"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
broker = RabbitBroker(RABBIT_URL)

subscribers: set[int] = set()

# --- Команды бота ---
COMMANDS = [
    BotCommand(command="start", description="Начать работу с ботом"),
    BotCommand(command="subscribe", description="Подписаться на уведомления"),
    BotCommand(command="unsubscribe", description="Отписаться от уведомлений"),
    BotCommand(command="clear", description="Удалить все отправленные сообщения"),
]

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет!\n"
        "Я отправляю уведомления из RabbitMQ.\n\n"
        "📬 /subscribe — подписаться\n"
        "🚫 /unsubscribe — отписаться\n"
        "🧹 /clear — удалить все отправленные сообщения"
    )

@dp.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    subscribers.add(message.chat.id)
    await message.answer("✅ Вы подписались на уведомления.")

@dp.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    subscribers.discard(message.chat.id)
    await message.answer("❌ Вы отписались от уведомлений.")

@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    if not os.path.exists(LOG_FILE):
        await message.answer("❌ Нет сообщений для удаления.")
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)

        deleted = 0
        for msg in messages:
            try:
                await bot.delete_message(chat_id=msg["chat_id"], message_id=msg["message_id"])
                deleted += 1
            except Exception as e:
                print(f"Ошибка удаления сообщения {msg['message_id']}: {e}")

        os.remove(LOG_FILE)
        await message.answer(f"✅ Удалено сообщений: {deleted}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при удалении: {e}")

# --- RabbitMQ — Обработка заказов ---
@broker.subscriber("orders")
async def handle_orders_and_send_message(data: str):
    if not subscribers:
        logging.info("Нет подписанных пользователей.")
        return

    for chat_id in subscribers:
        try:
            sent_msg = await bot.send_message(chat_id, f"📦 <b>Заказ создан:</b> {data}")
            await log_message(chat_id, sent_msg.message_id)
        except Exception as e:
            logging.error(f"Ошибка отправки в чат {chat_id}: {e}")

# --- Запуск ---
async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await bot.set_my_commands(COMMANDS)

    async with broker:
        await asyncio.gather(
            dp.start_polling(bot),
            broker.start(),
        )

if __name__ == "__main__":
    asyncio.run(main())
