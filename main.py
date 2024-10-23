import asyncio
import logging

import sys
from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

from decouple import config
from outline_vpn.outline_vpn import OutlineVPN

from aiogram import F


load_dotenv()
TOKEN = getenv("BOT_TOKEN")


dp = Dispatcher()



api_url = config('API_URL')
cert_sha256 = config('CERT_SHA')

client = OutlineVPN(api_url=api_url, cert_sha256=cert_sha256)

def get_key_info(key_id: str):
    return client.get_key(key_id)

def create_new_key(key_id: str = None, name: str = None, data_limit_bytes: float = None):
    return client.create_key(key_id=key_id, name=name, data_limit=data_limit_bytes)

def delete_key(key_id: str):
    return client.delete_key(key_id)

def upd_limit(key_id: str, data_limit_bytes: float):
    return client.add_data_limit(key_id, data_limit_bytes)




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
