import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from os import getenv

from backend.xapi.tests import GET_XSERVERS

import ssl
load_dotenv()

"""DEBUG MODE MUST BE DISABLED ON PROD"""
DEBUG = True
"""###################################"""

def get_servers():
    XSERVERS.extend(asyncio.run(GET_XSERVERS()))

TOKEN = getenv("BOT_TOKEN") if not DEBUG else getenv("DEBUG_BOT_TOKEN")
ADMINS = [902448626, 1124386913]
OUTLINE_API_URL_1 = getenv('API_URL_1')
OUTLINE_CERT_SHA256_1 = getenv('CERT_SHA_1')
OUTLINE_API_URL_2 = getenv('API_URL_2')
OUTLINE_CERT_SHA256_2 = getenv('CERT_SHA_2')
XSERVERS = []
get_servers()
DB_TOKEN = getenv("DB_TOKEN")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

MENU_KEYBOARD_MARKUP = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤Menu"),
            ],
        ],
        resize_keyboard=True
    )


if __name__ == "globals":
    if DEBUG:
        print(f"###DEBUG MODE MUST BE DISABLED ON PROD {__name__}.py###\n{DEBUG=}\n#########################################")

