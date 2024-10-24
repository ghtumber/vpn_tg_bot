import asyncio
import logging

import sys
from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

from backend.outline.manager import OutlineManager




from aiogram import F


load_dotenv()
TOKEN = getenv("BOT_TOKEN")


dp = Dispatcher()







@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = [
        [
            KeyboardButton(text="User"),
            KeyboardButton(text="Admin")
        ],
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="выберите от чьего лица вы заходите в бота"
    )
    await message.answer("Вы админ или юзер?", reply_markup=keyboard)




@dp.message(F.text.lower() == "User")
async def with_puree(message: Message):
    await message.reply("Вы гой")

@dp.message(F.text.lower() == "Admin")
async def without_puree(message:Message):
    await message.reply("Прогревайте гоев")

'''
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    """
    `/start` handler
    """
    await message.answer(f"Hello, {message.from_user.full_name}!")

'''

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
