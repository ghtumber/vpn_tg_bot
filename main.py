import asyncio
import logging
import sys
from aiogram import Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import threading
from threading import Thread
from backend.DonatPAY.centrifugo_websocket import listen_to_centrifugo
from frontend.replys import *
from backend.database.users import UsersDatabase
from backend.models import User
from frontend.user.handlers import router as user_router
from frontend.admin.handlers import router as admin_router
from frontend.notifications.handlers import router as notifications_router
from backend.outline.managers import SERVERS
from globals import *
from frontend.notifications.handlers import period_checker_scheduler, check_period

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_resp = await UsersDatabase.get_user_by(TG="@" + message.from_user.username)
    if user_resp:
        await message.answer(REPLY_REGISTRATION, reply_markup=MENU_KEYBOARD_MARKUP)
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Регистрация", callback_data="user_registration")]
            ]
        )
        await message.answer(REPLY_REGISTRATION, reply_markup=keyboard)


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.answer(text="")
    if callback.from_user.id in ADMINS:
        await admin_menu(callback.message)
    else:
        await menu(callback.message, callback=callback)
    await callback.message.delete()

@dp.callback_query(F.data == "to_menu")
async def open_menu(callback: CallbackQuery):
    await callback.answer("")
    if callback.from_user.id in ADMINS:
        await admin_menu(callback.message)
    else:
        await menu(callback.message, callback=callback)

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


@dp.callback_query(F.data == "cancel_of_cancel")
async def cancel_of_cancel(callback: CallbackQuery):
    await callback.answer(text="")
    await callback.message.delete()


async def admin_menu(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Управление XServers", callback_data="admin_manage_xservers"),
             InlineKeyboardButton(text="Управление Outline", callback_data="admin_manage_outlines")],
            [InlineKeyboardButton(text="Оповещения", callback_data="admin_notifications_menu")],
            [InlineKeyboardButton(text="Просмотр UsersDB", callback_data="admin_get_user_info")],
        ]
    )
    await message.answer(f"Привет!\n‼ Сейчас идёт регистрация!\n\n😌 Не забывайте прогревать ГОЕВ❗❗❗", reply_markup=MENU_KEYBOARD_MARKUP)
    await message.answer("⚡ Вот что можно сделать сейчас.", reply_markup=keyboard)


@dp.message(F.text.contains("Menu"))
async def menu(message: Message, *args, **kwargs):
    if "callback" in kwargs.keys():
        user_id = kwargs["callback"].from_user.id
    else:
        user_id = message.from_user.id
    if user_id in ADMINS:
        await admin_menu(message)
    else:
        user: User = await UsersDatabase.get_user_by(ID=str(user_id))
        if user:
            if user.xclient:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📊 Использование VPN", callback_data="xclient_vpn_usage")],
                    [InlineKeyboardButton(text="🔑 Мой ключ", callback_data="view_user_key")],
                    [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="topup_user_balance")],
                    [InlineKeyboardButton(text="📘 Инструкции", callback_data=f"get_{user.Protocol}_instructions")]
                ])
                server = [s for s in XSERVERS if s.name == user.serverName][0]
            elif user.outline_client:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔑 Мой ключ", callback_data="view_user_key")],
                    [InlineKeyboardButton(text="📘 Инструкции", callback_data="get_outline_instructions")]
                ])
                server = [s for s in SERVERS if s.name == user.serverName][0]
            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔓 Купить ключ", callback_data="buy_key")],
                    [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="topup_user_balance")]
                ])
                await message.answer(text=CLEAN_USER_GREETING_REPLY(user_balance=user.moneyBalance, username=user.userTG), reply_markup=keyboard)
                return
            await message.answer(text=USER_GREETING_REPLY(username=user.userTG, paymentSum=user.PaymentSum, paymentDate=user.PaymentDate, serverName=user.serverName, serverLocation=server.location, user_balance=user.moneyBalance), reply_markup=keyboard)
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Регистрация", callback_data="user_registration")]
                ]
            )
            await message.answer(REPLY_REGISTRATION, reply_markup=keyboard)

@dp.message(F.text == "User")
async def with_puree(message: Message):
    await message.reply("Вы гой")


@dp.message(F.text == "Admin")
async def without_puree(message: Message):
    await message.reply("Прогревайте гоев")

def between_callback():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen_to_centrifugo())
    loop.close()

async def main():
    period_checker_scheduler.start()
    #asyncio.get_event_loop().create_task(listen_to_centrifugo(), name="Centrifugo listener")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(notifications_router)
    t = Thread(target=between_callback, args=[], name="Centrifugo listener")
    try:
        t.start()
        asyncio.run(main())
    except KeyboardInterrupt:
        SHUTDOWN[0] = True
        print("Shutting down...")
        t.join()
        # sys.exit()