import asyncio
import logging
import sys
from datetime import datetime
import time

import aiohttp.client_exceptions
from aiogram import Dispatcher, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from frontend.replys import *
from backend.database.users import UsersDatabase
from backend.models import User
from frontend.user.handlers import router as user_router
from frontend.admin.handlers import router as admin_router
from backend.Payments.stars import router as stars_router
from frontend.notifications.handlers import router as notifications_router
from backend.outline.managers import SERVERS
from globals import *
from frontend.notifications.handlers import period_checker_scheduler, check_period

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    user_resp = await UsersDatabase.get_user_by(TG="@" + message.from_user.username)
    if user_resp:
        await message.answer(REPLY_REGISTRATION(who_invited=False), reply_markup=MENU_KEYBOARD_MARKUP)
    else:
        if command.args:
            try:
                who_invited = int(command.args)
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Регистрация", callback_data=f"user_registration_{who_invited}")]
                    ]
                )
            except TypeError:
                print(f"""##### {message.text}\nBad refer.\n#####""")
                await cmd_start(message, command=CommandObject())
                return 0
            who_invited_user = await UsersDatabase.get_user_by(ID=str(who_invited))
            await message.answer(text=REPLY_REGISTRATION(who_invited=who_invited_user.userTG), reply_markup=keyboard)
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Регистрация", callback_data="user_registration_None")]
                ]
            )
            await message.answer(text=REPLY_REGISTRATION(who_invited=False), reply_markup=keyboard)


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.answer(text="")
    if callback.from_user.id in ADMINS:
        await admin_menu(callback.message)
    else:
        await menu(callback.message, callback=callback)
    await callback.message.delete()

@dp.callback_query(F.data == "to_menu")
async def call_to_menu(callback: CallbackQuery, state: FSMContext):
    if state:
        await state.clear()
    await callback.answer(text="")
    if callback.from_user.id in ADMINS:
        await admin_menu(callback.message)
    else:
        await callback.message.answer("🔃 Загрузка~", reply_markup=MENU_KEYBOARD_MARKUP)
        await menu(callback.message, callback=callback)

@dp.message(F.text == "❌ Отмена")
async def open_menu(message: Message, state: FSMContext):
    await state.clear()
    if message.from_user.id in ADMINS:
        await admin_menu(message)
    else:
        load_message = await message.answer("🔃 Загрузка~", reply_markup=MENU_KEYBOARD_MARKUP)
        await menu(message)

@dp.callback_query(F.data == "menu")
async def to_menu(callback: CallbackQuery, state: FSMContext):
    if state:
        await state.clear()
    await callback.answer(text="")
    if callback.from_user.id in ADMINS:
        await admin_menu(callback.message)
    else:
        await callback.message.answer("🔃 Загрузка~", reply_markup=MENU_KEYBOARD_MARKUP)
        await menu(callback.message, callback=callback)
    await callback.message.delete()


@dp.message(F.text.contains("Тех. поддержка"))
async def TA(message: Message, *args, **kwargs):
    user: User = await UsersDatabase.get_user_by(ID=str(message.from_user.id))
    await message.answer(text=TECH_ASSISTANCE_RESPONSE(user=user), reply_markup=MENU_KEYBOARD_MARKUP)

@dp.callback_query(F.data == "user_get_TA_help")
async def get_TA(callback: CallbackQuery, *args, **kwargs):
    await TA(callback.message)
    await callback.answer("")

@dp.callback_query(F.data == "cancel_of_cancel")
async def cancel_of_cancel(callback: CallbackQuery):
    await callback.answer(text="")
    await callback.message.delete()


async def admin_menu(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Управление XServers", callback_data="admin_manage_xservers"),
             InlineKeyboardButton(text="Payment manager", callback_data="admin_manage_payment_defaults")],
            [InlineKeyboardButton(text="Оповещения", callback_data="admin_notifications_menu")],
            [InlineKeyboardButton(text="Просмотр UsersDB", callback_data="admin_get_user_info")],
        ]
    )

    online_users_count = 0
    # print(f"{''.join([' ' + r.ip for r in use_XSERVERS()])}")
    for server in use_XSERVERS():
        try:
            online_users = await server.get_online_users()
        except aiohttp.client_exceptions.ConnectionTimeoutError:
            online_users = 0
        online_users_count += len(online_users)

    await message.answer(ADMIN_GREETING_REPLY(username=f"@{message.from_user.username}", online_users_count=online_users_count,
                                              servers_count=len(use_XSERVERS())), reply_markup=MENU_KEYBOARD_MARKUP)
    await message.answer("⚡ Вот что можно сделать сейчас.", reply_markup=keyboard)


@dp.message(F.text.contains("Menu"))
async def menu(message: Message, *args, **kwargs):
    if "callback" in kwargs.keys():
        user_id = kwargs["callback"].from_user.id
    else:
        user_id = message.from_user.id
    if user_id in ADMINS:
        await admin_menu(message)
        return
    else:
        user: User = await UsersDatabase.get_user_by(ID=str(user_id))
        if user:
            if user.xclient:
                if user.xclient != "None":
                    if user.xclient.enable:
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📊 Использование", callback_data="xclient_vpn_usage"), InlineKeyboardButton(text="🔑 Ключ", callback_data="view_user_key")],
                            [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="topup_user_balance")],
                            [InlineKeyboardButton(text="📘 Инструкции", callback_data=f"get_instructions")]
                        ])
                        server = [s for s in use_XSERVERS() if s.name == user.serverName][0]
                    else:
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="topup_user_balance")],
                            [InlineKeyboardButton(text="👉 Оплатить VPN", callback_data="regain_user_access")]
                        ])
                        await message.answer(text=EXHAUSTED_USER_GREETING_REPLY(user=user), reply_markup=keyboard)
                        return
                elif user.xclient == "None":
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🚨Тех. поддержка", callback_data="user_get_TA_help")]
                        ]
                    )
                    await message.answer(SERVER_ERROR_USER_GREETING_REPLY(user), reply_markup=keyboard)
                    for admin in ADMINS:
                        await bot.send_message(chat_id=admin, text=f"У {user.userTG} потерян доступ к серверу. Вероятно <b>сервер недоступен</b>.")
                    return
            elif user.outline_client:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔑 Мой ключ", callback_data="view_user_key")],
                    [InlineKeyboardButton(text="📘 Инструкции", callback_data="get_outline_instructions")]
                ])
                server = [s for s in SERVERS if s.name == user.serverName][0]
            else:
                if Available_Tariffs:
                    kb_l = [
                        [InlineKeyboardButton(text="🔓 Купить ключ", callback_data="buy_key")],
                        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="topup_user_balance")]
                    ]
                else:
                    kb_l = [
                        [InlineKeyboardButton(text="😕 Сейчас покупка недоступна", callback_data="user_get_TA_help")],
                        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="topup_user_balance")]
                    ]
                keyboard = InlineKeyboardMarkup(inline_keyboard=kb_l)
                await message.answer(text=CLEAN_USER_GREETING_REPLY(user_balance=user.moneyBalance, username=user.userTG), reply_markup=keyboard)
                return
            await message.answer(text=USER_GREETING_REPLY(username=user.userTG, paymentSum=user.PaymentSum, paymentDate=user.PaymentDate, tariff=user.tariff, serverLocation=server.location, user_balance=user.moneyBalance), reply_markup=keyboard)
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Регистрация", callback_data="user_registration_None")]
                ]
            )
            await message.answer(REPLY_REGISTRATION(who_invited=False), reply_markup=keyboard)

@dp.message(F.text == "User")
async def with_puree(message: Message):
    await message.reply("Вы гой")

@dp.message(F.text == "Admin")
async def without_puree(message: Message):
    await message.reply("Прогревайте гоев")

def get_utc_time(time_to_convert: datetime) -> datetime:
    tz = time.timezone
    return time_to_convert + datetime.timedelta(seconds=tz)

async def main():
    await get_servers()
    # period_checker_scheduler.start()
    server_checker_scheduler.start()
    await dp.start_polling(bot, polling_timeout=60)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(notifications_router)
    dp.include_router(stars_router)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        SHUTDOWN = True
        print("Shutting down...")
        # sys.exit()