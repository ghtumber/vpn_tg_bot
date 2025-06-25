import time
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from backend.database.users import UsersDatabase
from backend.models import User, XClient
from backend.xapi.servers import Inbound
from globals import MENU_KEYBOARD_MARKUP, use_XSERVERS, use_PREFERRED_PAYMENT_SETTINGS, ADMINS, bot
from frontend.replys import KEY_UPDATE_USER_REPLY

router = Router()

CANCEL_KB = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="❌ Отмена")]
], resize_keyboard=True)

# -----------------FSM-------------------
class UserExpriryDateUpdating(StatesGroup):
    user = State()
    inbound = State()
    days = State()
    confirmation = State()

class UsersListing(StatesGroup):
    userID = State()

class UserBalanceUpdating(StatesGroup):
    user = State()
    new_value = State()
    confirmation = State()

class UserKeyUpdating(StatesGroup):
    user = State()
    new_value = State()
    new_uuid = State()
    new_server = State()
    confirmation = State()

#-----------------------------------------------UserDB-------------------------------------------
@router.callback_query((F.data == "admin_get_user_info") & (F.message.from_user.id in ADMINS))
async def handle_get_user_info(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    page = 1
    users, _ = await UsersDatabase.get_all_users(page=page, size=25)
    text = ""
    for user in users:
        text += f"\n🏷UserTG: {user.userTG}  🆔: <code>{user.userID}</code>"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="+1 стр", callback_data=f"users_pagination_plus_{page}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")]
        ]
    )

    await callback.message.answer(text=f"Листинг пользователей страница {page}\n{text}\n❔ Выберите userID", reply_markup=kb, parse_mode="HTML")
    await callback.message.delete()
    await state.set_state(UsersListing.userID)

@router.callback_query(F.data.startswith("users_pagination_plus"))
async def users_paginate_plus(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[3])
    page += 1
    resp = await UsersDatabase.get_all_users(page=page, size=25)
    if resp is None:
        await callback.answer(text="❌ Это <b>последняя</b> страница")
        return 0
    users, _ = resp
    text = ""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="-1 стр", callback_data=f"users_pagination_minus_{page}"),
             InlineKeyboardButton(text="+1 стр", callback_data=f"users_pagination_plus_{page}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")]
        ]
    )
    for user in users:
        text += f"\n🏷UserTG: {user.userTG}  🆔: <code>{user.userID}</code>"
    await callback.message.edit_text(text=f"Листинг пользователей страница {page}\n{text}\n❔ Выберите userID", parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("users_pagination_minus"))
async def users_paginate_minus(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[3])
    resp = None
    if page - 1 > 0:
        page -= 1
        resp = await UsersDatabase.get_all_users(page=page, size=25)
    if resp is None:
        await callback.answer(text="❌ Это <b>первая</b> страница")
        return 0
    users, _ = resp
    text = ""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="-1 стр", callback_data=f"users_pagination_minus_{page}"),
             InlineKeyboardButton(text="+1 стр", callback_data=f"users_pagination_plus_{page}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")]
        ]
    )
    for user in users:
        text += f"\n🏷UserTG: {user.userTG}  🆔: <code>{user.userID}</code>"
    await callback.message.edit_text(text=f"Листинг пользователей страница {page}\n{text}\n❔ Выберите userID", parse_mode="HTML", reply_markup=kb)

@router.message(UsersListing.userID)
async def handle_xserver_new_client_data_listing(message: Message, state: FSMContext):
    await state.update_data(userID=message.text.strip())
    data = await state.get_data()
    await state.clear()
    user = await UsersDatabase.get_user_by(ID=data["userID"])
    answer = f"""
🔗 <b>TG</b>: {user.userTG}
💰 <b>Balance</b>: {user.moneyBalance}🌟XTR
💸 <b>Подписка</b>: {user.PaymentSum}🌟XTR (~ {user.PaymentSum*float(use_PREFERRED_PAYMENT_SETTINGS()["XTR_exchange_rate"])}руб)
🆔 <b>UUID</b>: {user.uuid}
📡 <b>Протокол</b>: {user.Protocol}
🛰 <b>Сервер</b>: {user.serverType} -> {user.serverName}
🕓 <b>Оплата</b>: {user.PaymentDate.strftime(r"%d.%m.%Y") if user.PaymentDate else "None"}
<span class="tg-spoiler">|api|{user.userID}|api|</span>
"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💸 Изменить баланс", callback_data=f"admin_change_user_balance"),],
            [InlineKeyboardButton(text="🔑 Изменить ключ", callback_data="admin_change_user_key")],
            [InlineKeyboardButton(text="🗓 Продлить подписку", callback_data="admin_updateUserExpriryDate")]
        ]
    )
    await message.answer(text=answer, reply_markup=kb)


@router.callback_query((F.data == "admin_updateUserExpriryDate") & (F.message.from_user.id in ADMINS))
async def handle_admin_updateUserExpriryDate(callback: CallbackQuery, state: FSMContext):
    prev_text = callback.message.text
    userID = prev_text.split("|api|")[1]
    await callback.answer(f"UserID: {userID}")
    user = await UsersDatabase.get_user_by(ID=userID)
    inbound = None
    for srv in use_XSERVERS():
        if srv.name == user.serverName:
            for inb in srv.inbounds:
                if inb.protocol.lower() == user.Protocol.lower():
                    inbound = inb
                    break
            break
    await state.update_data(user=user, inbound=inbound)
    await state.set_state(UserExpriryDateUpdating.days)
    answer = f"""
✅ Следующие изменения:
⌚ <b>Payment Date</b>: {user.PaymentDate.strftime('%A %d.%m.%Y')}
❔ На сколько изменяем? (ex. +30)
"""
    await callback.message.answer(text=answer, reply_markup=CANCEL_KB)

@router.message(UserExpriryDateUpdating.days)
async def handle_admin_updateUserExpriryDate_new_value(message: Message, state: FSMContext):
    text = message.text
    if text[0] != "+" and text[0] != "-":
        await message.answer(text="❌ Неверный <b>формат</b> изменения.\n\n‼ Просто укажите +100 или -100.")
        return 0
    try:
        text = int(text)
    except ValueError:
        await message.answer(text="❌ Неверный <b>формат</b> изменения.\n\n‼ Просто укажите +100 или -100.")
        return 0
    data = await state.get_data()
    new_date = data["user"].PaymentDate + timedelta(days=text)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Применяем")],
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    answer = f"""
✅ Следующие изменения:
🔗 <b>TG</b>: {data["user"].userTG}
⌚ <b>Оплата</b>: {data["user"].PaymentDate.strftime('%A %d.%m.%Y')} -> {new_date.strftime('%A %d.%m.%Y')}
❔ Применяем изменения
"""
    await state.update_data(user=data["user"], new_value=new_date, inbound=data["inbound"])
    await state.set_state(UserExpriryDateUpdating.confirmation)
    await message.answer(text=answer, reply_markup=kb)


@router.message(UserExpriryDateUpdating.confirmation)
async def handle_xserver_updateUserExpriryDate_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    client = None
    new_date = data["new_value"]
    inbound: Inbound = data["inbound"]
    for cl in inbound.settings["clients"]:
        if "id" in cl.keys() and cl["id"] == data["user"].uuid:
            client = XClient.create_from_dict(cl)
        elif "id" not in cl.keys() and cl["email"] == data["user"].uuid:
            client = XClient.create_from_dict(cl)
    if client:
        epoch = datetime.utcfromtimestamp(0)
        delta = timedelta(hours=14) if time.timezone == 0 else timedelta(hours=19)
        success = await inbound.update_client(client, {
            "expiryTime": (datetime(new_date.year, new_date.month, new_date.day) - epoch + delta).total_seconds() * 1000})
        data["user"].PaymentDate = datetime(new_date.year, new_date.month, new_date.day)
        user: User = await UsersDatabase.update_user(user=data["user"], change={})
        await state.clear()
        await message.delete()
        if success:
            answer = f"""
✅ <b>Клиент изменён</b>
👤 <b>Имя</b>: {client.email}
🆔 <b>UUID</b>: {user.uuid}
🛰 <b>Сервер</b>: {inbound.server.name}
🕓 <b>Истекает</b>: {user.PaymentDate.strftime('%A %d.%m.%Y')}
📡 <b>Протокол</b>: {"ShadowSocks" if inbound.protocol == "shadowsocks" else "VLESS"}
"""
            await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)
            return
    await message.answer(text="‼ Ошибка!\nState очищен.\n" + f"{client=}", reply_markup=MENU_KEYBOARD_MARKUP)


@router.callback_query((F.data == "admin_change_user_balance") & (F.message.from_user.id in ADMINS))
async def handle_admin_change_user_balance(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    prev_text = callback.message.text
    userID = prev_text.split("|api|")[1]
    user = await UsersDatabase.get_user_by(ID=userID)
    await state.update_data(user=user)
    await state.set_state(UserBalanceUpdating.new_value)
    answer = f"""
🔗 <b>TG</b>: {user.userTG}
💰 <b>Balance</b>: {user.moneyBalance}🌟XTR
📈 <b>Курс 🌟XTR</b>: {use_PREFERRED_PAYMENT_SETTINGS()["XTR_exchange_rate"]}
❔ На сколько изменяем баланс? (ex. +100)
"""
    await callback.message.answer(text=answer, reply_markup=CANCEL_KB)


@router.message(UserBalanceUpdating.new_value)
async def handle_admin_change_user_balance_new_value(message: Message, state: FSMContext):
    text = message.text
    if text[0] != "+" and text[0] != "-":
        await message.answer(text="❌ Неверный <b>формат</b> изменения.\n\n‼ Просто укажите +100 или -100.")
        return 0
    try:
        text = int(text)
    except ValueError:
        await message.answer(text="❌ Неверный <b>формат</b> изменения.\n\n‼ Просто укажите +100 или -100.")
        return 0
    data = await state.get_data()
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Применяем")],
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    answer = f"""
✅ Следующие изменения:
🔗 <b>TG</b>: {data["user"].userTG}
💰 <b>Balance</b>: {data["user"].moneyBalance}🌟XTR -> {data["user"].moneyBalance + text}🌟XTR
❔ Применяем изменения
"""
    await state.update_data(user=data["user"], new_value=text)
    await state.set_state(UserBalanceUpdating.confirmation)
    await message.answer(text=answer, reply_markup=kb)

@router.message(UserBalanceUpdating.confirmation)
async def handle_admin_change_user_balance_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    user: User = data["user"]
    user.moneyBalance += data["new_value"]
    user: User = await UsersDatabase.update_user(user=user, change={})
    answer = f"""
✅ Данные изменены!
🔗 <b>TG</b>: {user.userTG}
💰 <b>Balance</b>: {user.moneyBalance}🌟XTR
"""
    await state.clear()
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)


@router.callback_query((F.data == "admin_change_user_key") & (F.message.from_user.id in ADMINS))
async def handle_admin_change_user_key(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    prev_text = callback.message.text
    userID = prev_text.split("|api|")[1]
    user = await UsersDatabase.get_user_by(ID=userID)
    await state.update_data(user=user)
    await state.set_state(UserKeyUpdating.new_value)
    answer = f"""
🔗 <b>TG</b>: {user.userTG}
💰 <b>Balance</b>: {user.moneyBalance}🌟XTR
🔑 <b>Key</b>: {await user.get_key(use_XSERVERS())}
❔ Введите новый ключ.
"""
    await callback.message.answer(text=answer, reply_markup=CANCEL_KB)

@router.message(UserKeyUpdating.new_value)
async def handle_admin_change_user_balance_new_value(message: Message, state: FSMContext):
    text = message.text
    if not (text.startswith("vless://") or text.startswith("ss://")):
        await message.answer(text="❌ Неверный <b>формат</b> изменения.")
        return 0
    data = await state.get_data()
    try:
        if data["user"].Protocol == "VLESS":
            uid = text.split("vless://")[1].split("@")[0]
        else:
            uid = data["user"].uuid
        srv = text.split("@")[1].split(":")[0]
    except:
        await message.answer(text="❌ Неверный <b>формат</b> изменения.")
        return 0
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Применяем")],
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    answer = f"""
✅ Следующие изменения:
🔗 <b>TG</b>: {data["user"].userTG}
🆔 <b>New uuid</b>: {uid}
🛰 <b>New server</b>: {srv}
🔑 <b>New Key</b>: {await data["user"].get_key(use_XSERVERS())}
❔ Применяем изменения
"""
    await state.update_data(user=data["user"], new_value=text, new_uuid=uid, new_server=srv)
    await state.set_state(UserKeyUpdating.confirmation)
    await message.answer(text=answer, reply_markup=kb)


@router.message(UserKeyUpdating.confirmation)
async def handle_admin_change_user_balance_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    user: User = data["user"]
    user.xclient.key = data["new_value"]
    user.uuid = data["new_uuid"]
    user.serverName = "XServer@" + data["new_server"]
    d = await user.get_server_and_inbound(use_XSERVERS())
    user.xclient = await d["server"].get_client_info(user.uuid)
    user.subId = user.xclient.subId
    user: User = await UsersDatabase.update_user(user=user, change={})
    answer = f"""
✅ Данные изменены!
🔗 <b>TG</b>: {user.userTG}
🆔 <b>New uuid</b>: {user.uuid}
🆔 <b>New sub-id</b>: {user.subId}
🛰 <b>New server</b>: {user.serverName}
🔑 <b>New Key</b>: {await user.get_key(use_XSERVERS())}
"""
    await bot.send_message(chat_id=user.userID, text=KEY_UPDATE_USER_REPLY(user=user, sub_key=await user.get_sub_key(use_XSERVERS()), key=await user.get_key(use_XSERVERS())), parse_mode="html")
    await state.clear()
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)

