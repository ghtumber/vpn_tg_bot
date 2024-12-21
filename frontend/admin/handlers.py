from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from outline_vpn.outline_vpn import OutlineKey

from backend.models import User
from frontend.replys import *
from globals import ADMINS, MENU_KEYBOARD_MARKUP
from backend.outline.managers import SERVERS

router = Router()

CANCEL_KB = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="❌ Отмена")]
], resize_keyboard=True)


class KeyCreation(StatesGroup):
    server = State()
    name = State()
    data_limit = State()


class KeyRemoval(StatesGroup):
    server = State()
    id = State()
    confirmation = State()


@router.message(F.text == "❌ Отмена")
async def handle_cancel(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="menu"), InlineKeyboardButton(text="Нет", callback_data="cancel_of_cancel")]
        ]
    )
    await message.answer("Отмена?", reply_markup=kb)


@router.callback_query((F.data == "admin_create_key") & (F.message.from_user.uuid in ADMINS))
async def handle_create_key(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")

    def build_kb():
        builder = ReplyKeyboardBuilder()
        for ind in range(len(SERVERS)):
            builder.button(text=f"{str(ind + 1)}) {SERVERS[ind].name}")
        builder.button(text="❌ Отмена")
        if len(SERVERS) % 2 == 0:
            builder.adjust(*[2 for _ in range(len(SERVERS) // 2)], 1)
        else:
            builder.adjust(*[2 for _ in range(len(SERVERS) // 2 + 1)], 1)
        return builder.as_markup(resize_keyboard=True)

    await callback.message.answer("🌐 Доступные сервера:", reply_markup=build_kb())
    await callback.message.delete()
    await state.set_state(KeyCreation.server)


@router.message(KeyCreation.server)
async def handle_server_selection(message: Message, state: FSMContext):
    try:
        server = SERVERS[int(message.text.split(")")[0]) - 1]
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0
    await state.update_data(server=server)
    await state.set_state(KeyCreation.name)
    await message.answer(text="🔑 Дайте имя ключу:", reply_markup=CANCEL_KB)


@router.message(KeyCreation.name)
async def handle_key_naming(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(KeyCreation.data_limit)
    await message.answer(text="⏹ Ограничение ключа в ГБ(0 - нет):")


@router.message(KeyCreation.data_limit)
async def handle_key_data_limiting(message: Message, state: FSMContext):
    try:
        limit = float(message.text.strip())
    except ValueError:
        await message.answer(text="Ошибка ❗\nВероятно это не число 😑\np.s. или надо юзать точку ХД")
        return 0
    await state.update_data(data_limit=limit)
    data = await state.get_data()
    await state.clear()
    key: OutlineKey = data["server"].create_new_key(name=data["name"], data_limit_gb=data["data_limit"])
    link = str(key.access_url).split("?")[0] + "#Proxym1ty-VPN"
    answer = f"""
✅ <b>Ключ создан</b>
📛 <b>Название</b>: {key.name}
🆔 <b>ID</b>: {key.key_id}
🛰 <b>Сервер</b>: {data["server"].name}
⏹ <b>Ограничение</b>: {key.data_limit / 1024**3}GB
🔑 <b>Ключ</b>: <pre><code>{link}</code></pre>
"""
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)


@router.callback_query((F.data == "admin_delete_key") & (F.message.from_user.uuid in ADMINS)) # TODO: Add server selection
async def handle_create_key(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")

    def build_kb():
        builder = ReplyKeyboardBuilder()
        for ind in range(len(SERVERS)):
            builder.button(text=f"{str(ind + 1)}) {SERVERS[ind].name}")
        builder.button(text="❌ Отмена")
        if len(SERVERS) % 2 == 0:
            builder.adjust(*[2 for _ in range(len(SERVERS) // 2)], 1)
        else:
            builder.adjust(*[2 for _ in range(len(SERVERS) // 2 + 1)], 1)
        return builder.as_markup(resize_keyboard=True)

    await callback.message.answer("❔ На каком сервере ключ?\n\n🌐 Доступные сервера:", reply_markup=build_kb())
    await callback.message.delete()
    await state.set_state(KeyRemoval.server)


@router.message(KeyRemoval.server)
async def handle_key_removal_server_selection(message: Message, state: FSMContext):
    try:
        server = SERVERS[int(message.text.split(")")[0]) - 1]
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0
    await state.update_data(server=server)
    await state.set_state(KeyRemoval.id)
    await message.answer(text="🆔 Какой ID ключа?", reply_markup=CANCEL_KB)


@router.message(KeyRemoval.id)
async def handle_key_removal_identification(message: Message, state: FSMContext):
    try:
        id = int(message.text.strip())
        await state.update_data(id=id)
    except ValueError:
        await message.answer(text="Ошибка ❗\nВероятно это не целое число 😑")
        return 0
    await state.set_state(KeyRemoval.confirmation)
    data = await state.get_data()
    info = data["server"].get_key_info(str(id))
    if info is None:
        await message.answer(text="Ошибка ❗\nТакого ключа не существует 😑")
        return 0
    answer = f"""
❓ <b>Удаляем ключ?</b>
📛 <b>Название</b>: {info.name}
🆔 <b>ID</b>: {info.key_id}
🛰 <b>Сервер</b>: {data["server"].name}
⏹ <b>Ограничение</b>: {info.data_limit / 1024**3}GB
🔑 <b>Ключ</b>: <pre><code>{info.access_url}</code></pre>
"""
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Удаляем"), KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    await message.answer(text=answer, reply_markup=kb)


@router.message(KeyRemoval.confirmation)
async def handle_key_naming(message: Message, state: FSMContext):
    data = await state.get_data()
    info = data["server"].get_key_info(str(data["uuid"]))
    if info is None:
        await message.answer(text="Ошибка ❗\nТакого ключа не существует 😑")
        return 0
    data["server"].delete_key(str(data["uuid"]))
    answer = f"""
‼ <b>Ключ удалён</b>
📛 <b>Название</b>: {info.name}
🆔 <b>ID</b>: {info.key_id}
🛰 <b>Сервер</b>: {data["server"].name}
⏹ <b>Ограничение</b>: {info.data_limit / 1024**3}GB
🔑 <b>Ключ</b>: <pre><code>{info.access_url}</code></pre>
"""
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)



