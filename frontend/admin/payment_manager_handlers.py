import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from frontend.replys import ADMIN_PAYMENTS_MANAGER_REPLY
from globals import ADMINS, XSERVERS, use_BASIC_VPN_COST, use_PREFERRED_PAYMENT_SETTINGS, MENU_KEYBOARD_MARKUP, edit_preferred_payment_settings

router = Router()

CANCEL_KB = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="❌ Отмена")]
], resize_keyboard=True)

# -----------------FSM-------------------
class ServerChangingState(StatesGroup):
    callback = State()
    server = State()
    confirmation = State()

class ProtocolChangingState(StatesGroup):
    callback = State()
    protocol = State()
    confirmation = State()

class CoastChangingState(StatesGroup):
    callback = State()
    coast = State()
    confirmation = State()



# PREFERRED_PAYMENT_SETTINGS = {"server_name": "XServer@94.159.100.60", "keyType": "VLESS"}

@router.callback_query((F.data == "admin_manage_payment_defaults") & (F.message.from_user.id in ADMINS))
async def handle_admin_manage_payment_defaults(callback: CallbackQuery):
    await callback.answer("")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Изменить сервер", callback_data="admin_change_payment_defaults_server")],
            [InlineKeyboardButton(text="⛓ Изменить протокол", callback_data="admin_change_payment_defaults_protocol")],
            [InlineKeyboardButton(text="🏧 Изменить цену", callback_data="admin_change_payment_defaults_coast")],
        ]
    )
    await callback.message.answer(ADMIN_PAYMENTS_MANAGER_REPLY(default_coast=use_BASIC_VPN_COST(), default_server=use_PREFERRED_PAYMENT_SETTINGS()["server_name"],
                                                               default_protocol=use_PREFERRED_PAYMENT_SETTINGS()["keyType"]), reply_markup=keyboard)


#-------------------------------------------Server editing---------------------------------------------------------
@router.callback_query((F.data == "admin_change_payment_defaults_server") & (F.message.from_user.id in ADMINS))
async def handle_admin_change_payment_defaults_server(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")

    answer = "🌐 Доступные сервера:"
    for server in XSERVERS:
        answer += f"\n🌍:{server.location} ɪᴘ: <code>{server.ip}</code>"
    answer += "\n\nВыбери IP нужного сервера."
    await callback.message.answer(answer, reply_markup=CANCEL_KB)
    await state.update_data(callback=callback)
    await state.set_state(ServerChangingState.server)


@router.message(ServerChangingState.server)
async def handle_admin_change_payment_defaults_server_ip(message: Message, state: FSMContext):
    try:
        if len(message.text.split(".")) == 4:
            server = [server for server in XSERVERS if server.ip == message.text.strip()][0]
        else:
            raise IndexError
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)

    await state.update_data(server=server)
    await state.set_state(ServerChangingState.confirmation)
    await message.answer(text=f"❔ Сохраняем изменения?\n {use_PREFERRED_PAYMENT_SETTINGS()['server_name']} -> {server.name}", reply_markup=kb, parse_mode="HTML")

@router.message(ServerChangingState.confirmation)
async def handle_admin_change_payment_defaults_server_confirmation(message: Message, state: FSMContext):
    global edit_preferred_payment_settings
    data = await state.get_data()
    new = dict(use_PREFERRED_PAYMENT_SETTINGS())
    new["server_name"] = data["server"].name
    edit_preferred_payment_settings(new=new)
    await state.clear()
    await message.answer(text="✅ Изменения сохранены", reply_markup=MENU_KEYBOARD_MARKUP)
    await asyncio.sleep(0.5)
    await handle_admin_manage_payment_defaults(callback=data["callback"])


#-------------------------------------------Protocol editing---------------------------------------------------------
@router.callback_query((F.data == "admin_change_payment_defaults_protocol") & (F.message.from_user.id in ADMINS))
async def handle_admin_change_payment_defaults_protocol(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🟣 VLESS"), KeyboardButton(text="⚫ ShadowSocks")]
    ])

    answer = "⛓ Доступные варианты:\n 1) VLESS\n 2) ShadowSocks"
    await callback.message.answer(answer, reply_markup=kb)
    await state.update_data(callback=callback)
    await state.set_state(ProtocolChangingState.protocol)


@router.message(ProtocolChangingState.protocol)
async def handle_admin_change_payment_defaults_protocol_vars(message: Message, state: FSMContext):
    if message.text.strip().endswith("VLESS"):
        protocol = "VLESS"
    elif message.text.strip().endswith("ShadowSocks"):
        protocol = "ShadowSocks"
    else:
        await message.answer("Ошибка ❗\nВероятно такого протокола нет 😑")
        return 0

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)

    await state.update_data(protocol=protocol)
    await state.set_state(ProtocolChangingState.confirmation)
    await message.answer(text=f"❔ Сохраняем изменения?\n {use_PREFERRED_PAYMENT_SETTINGS()['keyType']} -> {protocol}", reply_markup=kb, parse_mode="HTML")

@router.message(ServerChangingState.confirmation)
async def handle_admin_change_payment_defaults_protocol_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    new = dict(use_PREFERRED_PAYMENT_SETTINGS())
    new["keyType"] = data["protocol"]
    edit_preferred_payment_settings(new=new)
    await state.clear()
    await message.answer(text="✅ Изменения сохранены", reply_markup=MENU_KEYBOARD_MARKUP)
    await asyncio.sleep(0.5)
    await handle_admin_manage_payment_defaults(callback=data["callback"])



#-------------------------------------------Coast editing---------------------------------------------------------
@router.callback_query((F.data == "admin_change_payment_defaults_coast") & (F.message.from_user.id in ADMINS))
async def admin_change_payment_defaults_coast(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")

    answer = "💸 Какая новая цена? (ex. 150)"
    await callback.message.answer(answer, reply_markup=CANCEL_KB)
    await state.update_data(callback=callback)
    await state.set_state(CoastChangingState.coast)


@router.message(CoastChangingState.coast)
async def admin_change_payment_defaults_coast_value(message: Message, state: FSMContext):
    try:
        coast = float(message.text.strip())
    except ValueError:
        await message.answer("Ошибка ❗\nВероятно это не число, а какая-то залупа 😑")
        return 0

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)

    await state.update_data(coast=coast)
    await state.set_state(CoastChangingState.confirmation)
    await message.answer(text=f"❔ Сохраняем изменения?\n {use_BASIC_VPN_COST()} руб. -> {coast} руб.", reply_markup=kb, parse_mode="HTML")

@router.message(CoastChangingState.confirmation)
async def handle_admin_change_payment_defaults_protocol_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    new = dict(use_PREFERRED_PAYMENT_SETTINGS())
    new["coast"] = data["coast"]
    edit_preferred_payment_settings(new=new)
    await state.clear()
    await message.answer(text="✅ Изменения сохранены", reply_markup=MENU_KEYBOARD_MARKUP)
    await asyncio.sleep(0.5)
    await handle_admin_manage_payment_defaults(callback=data["callback"])