import asyncio
import logging
import sys

from aiogram import Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from frontend.replys import *
from backend.database.users import UsersDatabase
from backend.models import User
from frontend.user.handlers import router as user_router
from frontend.admin.handlers import router as admin_router
from frontend.notifications.handlers import router as notifications_router
from backend.outline.managers import SERVERS
from globals import *

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(REPLY_REGISTRATION, reply_markup=MENU_KEYBOARD_MARKUP)


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.answer(text="")
    if callback.from_user.id in ADMINS:
        await admin_menu(callback.message)
    else:
        await menu(callback.message, callback=callback)
    await callback.message.delete()


@dp.callback_query(F.data == "menu")
async def to_menu(callback: CallbackQuery, state: FSMContext):
    if state:
        await state.clear()
    await callback.answer(text="")
    await callback.message.edit_reply_markup()
    if callback.from_user.id in ADMINS:
        await admin_menu(callback.message)
    else:
        await menu(callback.message)
    await callback.message.delete()


@dp.callback_query(F.data == "cancel_of_cancel")
async def cancel_of_cancel(callback: CallbackQuery):
    await callback.answer(text="")
    await callback.message.delete()


async def admin_menu(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать ключ", callback_data="admin_create_key"),
             InlineKeyboardButton(text="Удалить ключ", callback_data="admin_delete_key")],
            [InlineKeyboardButton(text="Информация по юзеру", callback_data="admin_view_user")],
            [InlineKeyboardButton(text="Оповещения", callback_data="admin_notifications_menu")],
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
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Использование VPN", callback_data="vpn_usage")],
                [InlineKeyboardButton(text="🔑 Мой ключ", callback_data="view_user_key")],
                [InlineKeyboardButton(text="📘 Инструкции", callback_data="get_instructions")]
            ])
            server = [s for s in SERVERS if s.name == user.serverName][0]
            await message.answer(text=USER_GREETING_REPLY(username=user.userTG, paymentSum=user.PaymentSum, paymentDate=user.PaymentDate, serverName=user.serverName, serverLocation=server.location), reply_markup=keyboard)
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Регистрация", callback_data="user_registration")]
                ]
            )
            await message.answer(PREREGISTRATION_MENU_REPLY, reply_markup=keyboard)

@dp.message(F.text == "User")
async def with_puree(message: Message):
    await message.reply("Вы гой")


@dp.message(F.text == "Admin")
async def without_puree(message: Message):
    await message.reply("Прогревайте гоев")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(notifications_router)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
