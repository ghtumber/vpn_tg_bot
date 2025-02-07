import asyncio
import datetime
from sys import exit
from calendar import monthrange
from datetime import date
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from os import getenv
from backend.xapi.servers import GET_XSERVERS

load_dotenv()

"""DEBUG MODE MUST BE DISABLED ON PROD"""
DEBUG = True
"""###################################"""

def get_servers():
    XSERVERS.extend(asyncio.run(GET_XSERVERS()))

def get_donat_pay_token() -> str:
    DONATPAY_API_KEY = getenv('DONATPAY_API_KEY')
    if DONATPAY_API_KEY:
        return DONATPAY_API_KEY
    asyncio.get_event_loop().stop()
    raise Exception(f"[GLOBAL EXCEPTION] NO DonatPAY TOKEN {DONATPAY_API_KEY=}")

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, monthrange(year, month)[1])
    return date(year, month, day)

TOKEN = getenv("BOT_TOKEN") if not DEBUG else getenv("DEBUG_BOT_TOKEN")
ADMINS = [902448626, 1124386913] # 1124386913

BASIC_VPN_COST = 150
DONATPAY_API_KEY = get_donat_pay_token()

OUTLINE_API_URL_1 = getenv('API_URL_1')
OUTLINE_CERT_SHA256_1 = getenv('CERT_SHA_1')
OUTLINE_API_URL_2 = getenv('API_URL_2')
OUTLINE_CERT_SHA256_2 = getenv('CERT_SHA_2')
XSERVERS = []
get_servers()

# Database tokens & tables (one token has access to one table)
DB_TOKEN = getenv("DB_TOKEN")
TEST_DB_TOKEN = getenv("TEST_DB_TOKEN")

TABLE_ID = "375433"
DB_SERVER_TYPES = {"None": 2412169, "Outline": 2354398, "XSERVER": 2354397}
DB_PROTOCOL_TYPES = {"ShadowSocks": 2365214, "VLESS": 2365215, "None": 2412170}
TEST_TABLE_ID = "428486"
DB_TEST_SERVER_TYPES = {"None": 2447416, "Outline": 2447415, "XSERVER": 2447414}
DB_TEST_PROTOCOL_TYPES = {"ShadowSocks": 2447417, "VLESS": 2447418, "None": 2447419}


bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
NEXT_WS_UPDATE = datetime.datetime.now()
SHUTDOWN = False

PREFERRED_PAYMENT_SETTINGS = {"server_name": "XServer@94.159.100.60", "keyType": "VLESS"}

MENU_KEYBOARD_MARKUP = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤Menu"),
            ],
            [
                KeyboardButton(text="🚨Тех. поддержка"),
            ],
        ],
        resize_keyboard=True
    )


if __name__ == "globals":
    if DEBUG:
        print(f"##################################################################\n\n###DEBUG MODE MUST BE DISABLED ON PROD {__name__}.py {DEBUG=}\n\n##################################################################")

