import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from frontend.replys import *
from frontend.user.handlers import router as user_router
from globals import *


dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤Menu"),
            ],
        ],
        resize_keyboard=True
    )
    await message.answer(REPLY_REGISTRATION, reply_markup=keyboard)


@dp.callback_query(F.data == "menu")
async def to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer(text="")
    await menu(callback.message)


@dp.message(F.text.contains("Menu"))
async def menu(message: Message):
    if message.from_user.id in ADMINS:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Создать ключ", callback_data="admin_create_key"),
                 InlineKeyboardButton(text="Удалить ключ", callback_data="admin_delete_key")],
                [InlineKeyboardButton(text="Информация по юзеру", callback_data="admin_view_user")],
                [InlineKeyboardButton(text="Транзакции", callback_data="admin_view_transactions")],
            ]
        )
        await message.answer(f"Привет!\n‼Сейчас идёт регистрация!\n\nВот что можно сделать сейчас.", reply_markup=keyboard)
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
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.include_router(user_router)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
