import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from frontend.replys import *
from frontend.user.handlers import router as user_router
from frontend.admin.handlers import router as admin_router
from globals import *


dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(REPLY_REGISTRATION, reply_markup=MENU_KEYBOARD_MARKUP)


@dp.callback_query(F.data == "menu")
async def to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer(text="")
    await callback.message.edit_reply_markup()
    await callback.message.delete()
    if callback.from_user.id in ADMINS:
        await admin_menu(callback.message)
    else:
        await menu(callback.message)


@dp.callback_query(F.data == "cancel_of_cancel")
async def to_menu(callback: CallbackQuery):
    await callback.answer(text="")
    await callback.message.delete()


async def admin_menu(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать ключ", callback_data="admin_create_key"),
             InlineKeyboardButton(text="Удалить ключ", callback_data="admin_delete_key")],
            [InlineKeyboardButton(text="Информация по юзеру", callback_data="admin_view_user")],
            [InlineKeyboardButton(text="Транзакции", callback_data="admin_view_transactions")],
        ]
    )
    await message.answer(f"Привет!\n‼Сейчас идёт регистрация!", reply_markup=MENU_KEYBOARD_MARKUP)
    await message.answer("⚡ Вот что можно сделать сейчас.", reply_markup=keyboard)


@dp.message(F.text.contains("Menu"))
async def menu(message: Message):
    if message.from_user.id in ADMINS:
        await admin_menu(message)
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
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
