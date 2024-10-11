import asyncio
import logging
import sys
from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

load_dotenv()
TOKEN = getenv("BOT_TOKEN")


dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    """
    `/start` handler
    """
    await message.answer(f"Hello, {message.from_user.full_name}!")


@dp.message()
async def echo_handler(message: Message):
    """
    Just echo
    """
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        """
        Не всё можно скопировать )
        """
        await message.answer("Nice try!")


async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
