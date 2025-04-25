import time
from datetime import date, datetime, timedelta
import re
from enum import Enum

from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from backend.database.users import UsersDatabase
from backend.models import User, XClient
from backend.xapi.servers import Inbound
from frontend.replys import *
from frontend.admin.payment_manager_handlers import router as payment_manager_router
from globals import ADMINS, MENU_KEYBOARD_MARKUP, use_XSERVERS, use_LAST_ALL_XSERVERS_UPDATE, get_servers, use_PREFERRED_PAYMENT_SETTINGS
from backend.outline.managers import SERVERS

router = Router()
router.include_router(payment_manager_router)

CANCEL_KB = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="❌ Отмена")]
], resize_keyboard=True)

# ----------------CallbackData---------------- not used for now ~~~
class ClientAction(str, Enum):
    disable = "💡Выключить"
    delete = "⛔Удалить"

class AdminClientAction(CallbackData, prefix="a"):
    action: ClientAction
    server_name: str
    inbound_id: int
    client_uuid: str

# -----------------FSM-------------------
class OutlineKeyCreation(StatesGroup):
    server = State()
    name = State()
    data_limit = State()

class OutlineKeyRemoval(StatesGroup):
    server = State()
    id = State()
    confirmation = State()

class XserverClientCreation(StatesGroup):
    server = State()
    inbound = State()
    email = State()
    expiryDate = State()
    data_limit = State()

class XserverClientListing(StatesGroup):
    server = State()
    UUID = State()

class XserverClientDisabling(StatesGroup):
    client = State()
    inbound = State()
    confirmation = State()

class XserverClientEnabling(StatesGroup):
    client = State()
    inbound = State()
    confirmation = State()

class XserverClientDeleting(StatesGroup):
    UUID = State()
    inbound = State()
    confirmation = State()

class XserverClientExpriryDateUpdating(StatesGroup):
    UUID = State()
    inbound = State()
    days = State()
    confirmation = State()

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


#@router.message(F.text == "❌ Отмена")
async def handle_cancel(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="menu"), InlineKeyboardButton(text="Нет", callback_data="cancel_of_cancel")],
        ]
    )
    fake_callback = CallbackQuery(
        id="12345",  # Любой ID, не важно
        from_user=message.from_user,
        message=message,
        data="menu",
        chat_instance=""
    )
    await router.callback_query.handlers.notify(fake_callback)
    # await message.answer("Отмена?", reply_markup=kb)



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
🆔 <b>UUID</b>: {user.uuid}
📡 <b>Протокол</b>: {user.Protocol}
🛰 <b>Сервер</b>: {user.serverType} -> {user.serverName}
🕓 <b>Оплата</b>: {user.PaymentDate.strftime(r"%d.%m.%Y") if user.PaymentDate else "None"}
<span class="tg-spoiler">|api|{user.userID}|api|</span>
"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💸 Изменить баланс", callback_data=f"admin_change_user_balance"),],
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
        if cl["id"] == data["user"].uuid:
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
💰 <b>Balance</b>: {user.moneyBalance}руб.
"""
    await state.clear()
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)


#----------------------------------------------SERVER DATA UPDATER---------------------------------

@router.callback_query((F.data == "admin_update_all_xserver_shiit") & (F.message.from_user.id in ADMINS))
async def handle_update_all_xserver_shiit(callback: CallbackQuery):
    if (datetime.now() - use_LAST_ALL_XSERVERS_UPDATE()) >= timedelta(minutes=5):
        await callback.answer(text="( ◡̀_◡́)ᕤ Now updating...", show_alert=True)
        await get_servers()
        await callback.message.answer(text=f"😎 Yap! All data updated!!!")
    else:
        await callback.answer("Not so frequent")

#-----------------------------------------------Managers-------------------------------------------
@router.callback_query((F.data == "admin_manage_xservers") & (F.message.from_user.id in ADMINS))
async def handle_create_xserver_client(callback: CallbackQuery):
    await callback.answer("")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать клиента", callback_data="admin_create_xserver_client"),
             InlineKeyboardButton(text="🚹 Информация по клиенту", callback_data="admin_get_xserver_client_info")],
            [InlineKeyboardButton(text="🔃 Обновить все данные", callback_data="admin_update_all_xserver_shiit")]
        ]
    )
    await callback.message.answer(f"Доступно {len(use_XSERVERS())} XServers.", reply_markup=MENU_KEYBOARD_MARKUP)
    await callback.message.answer("⚡ Вот что можно сделать сейчас.", reply_markup=keyboard)


@router.callback_query((F.data == "admin_manage_outlines") & (F.message.from_user.id in ADMINS))
async def handle_create_xserver_client(callback: CallbackQuery):
    await callback.answer("")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать ключ", callback_data="admin_create_outline_key"),
             InlineKeyboardButton(text="🚹 Удалить ключ", callback_data="admin_delete_outline_key")],
        ]
    )
    await callback.message.answer(f"Доступно {len(SERVERS)} Outline серверов.", reply_markup=MENU_KEYBOARD_MARKUP)
    await callback.message.answer("⚡ Вот что можно сделать сейчас.", reply_markup=keyboard)


# ------------------------------------------XServers-------------------------------------------------
@router.callback_query((F.data == "admin_create_xserver_client") & (F.message.from_user.id in ADMINS))
async def handle_create_xserver_client(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")

    def build_kb():
        builder = ReplyKeyboardBuilder()
        for ind in range(len(use_XSERVERS())):
            builder.button(text=f"{str(ind + 1)}) {use_XSERVERS()[ind].name}")
        builder.button(text="❌ Отмена")
        if len(use_XSERVERS()) % 2 == 0:
            builder.adjust(*[2 for _ in range(len(use_XSERVERS()) // 2)], 1)
        else:
            builder.adjust(*[2 for _ in range(len(use_XSERVERS()) // 2 + 1)], 1)
        return builder.as_markup(resize_keyboard=True)

    await callback.message.answer("🌐 Доступные сервера:", reply_markup=build_kb())
    await callback.message.delete()
    await state.set_state(XserverClientCreation.server)


@router.message(XserverClientCreation.server)
async def handle_xserver_new_client_server_selection(message: Message, state: FSMContext):
    try:
        server = use_XSERVERS()[int(message.text.split(")")[0]) - 1]
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0

    inbounds = server.inbounds
    def build_kb():
        builder = ReplyKeyboardBuilder()
        for ind in range(len(inbounds)):
            builder.button(text=f"{int(message.text.split(')')[0]) - 1}.{str(ind + 1)}) {inbounds[ind].protocol}")

        builder.button(text="❌ Отмена")
        if len(inbounds) % 2 == 0:
            builder.adjust(*[2 for _ in range(len(inbounds) // 2)], 1)
        else:
            builder.adjust(*[2 for _ in range(len(inbounds) // 2 + 1)], 1)
        return builder.as_markup(resize_keyboard=True)

    await state.update_data(server=server)
    await state.set_state(XserverClientCreation.inbound)
    await message.answer(text="🔱 Какой протокол?", reply_markup=build_kb())

@router.message(XserverClientCreation.inbound)
async def handle_xserver_new_client_inbound(message: Message, state: FSMContext):
    try:
        inbound = use_XSERVERS()[int(message.text.split(")")[0].split(".")[0])].inbounds[int(message.text.split(")")[0].split(".")[1]) - 1]
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0

    await state.update_data(inbound=inbound)
    await state.set_state(XserverClientCreation.email)
    await message.answer(text="🔑 Название клиента:", reply_markup=CANCEL_KB)

@router.message(XserverClientCreation.email)
async def handle_key_naming(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await state.set_state(XserverClientCreation.expiryDate)
    await message.answer("Теперь <b>ограничение ключа по дате</b>.\n\n‼В сообщении укажите дату в формате <b>ДД.ММ.ГГГГ</b>.\nИли просто <b>0</b>, если нет ограничения.")

@router.message(XserverClientCreation.expiryDate)
async def handle_xserver_new_client_expriry_date(message: Message, state: FSMContext):
    if message.text.strip() != "0":
        if not re.fullmatch(r'[0-9][0-9].[0-9][0-9].[2-9][0-9][2-9][4-9]', r''.join(message.text.strip())):
            await message.answer(text="❌ Неверный <b>формат</b> даты.\n\n‼ В сообщении укажите дату в формате <b>ДД.ММ.ГГГГ</b>.")
            return 0
        ED_mes = message.text.strip().split(".")
        expiryDate = date(int(ED_mes[2]), int(ED_mes[1]), int(ED_mes[0]))
    else:
        expiryDate = 0
    await state.update_data(expiryDate=expiryDate)
    await state.set_state(XserverClientCreation.data_limit)
    await message.answer(text="⏹ Ограничение ключа в ГБ(0 - нет):")


@router.message(XserverClientCreation.data_limit)
async def handle_xserver_new_client_data_limiting(message: Message, state: FSMContext):
    try:
        limit = float(message.text.strip())
    except ValueError:
        await message.answer(text="Ошибка ❗\nВероятно это не число 😑\np.s. или надо юзать точку ХД")
        return 0
    await state.update_data(data_limit=limit)
    data = await state.get_data()
    await state.clear()
    expiryTime = 0
    if data["expiryDate"]:
        print(f"{time.timezone=}")
        epoch = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0) - timedelta(seconds=time.timezone)
        delta = timedelta(hours=15) if time.timezone == 0 else timedelta(hours=20)
        expiryTime = (datetime(data["expiryDate"].year, data["expiryDate"].month, data["expiryDate"].day, hour=0, minute=0) - epoch + delta).total_seconds() * 1000
    xclient: XClient = await data["inbound"].add_client(email=data["email"], totalBytes=data["data_limit"]*1024**3, expiryTime=expiryTime)
    answer = f"""
✅ <b>Ключ создан</b>
📛 <b>Название</b>: {xclient.email}
🆔 <b>UUID</b>: {xclient.uuid}
📡 <b>Протокол</b>: {data["inbound"].protocol}
🛰 <b>Сервер</b>: {data["server"].name}
⏹ <b>Ограничение</b>: {xclient.totalGB / 1024**3}GB
🔑 <b>Ключ</b>: <pre><code>{xclient.key}</code></pre>
"""
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)


@router.callback_query((F.data == "admin_get_xserver_client_info") & (F.message.from_user.id in ADMINS))
async def handle_get_xserver_client_info(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")

    def build_kb():
        builder = ReplyKeyboardBuilder()
        for ind in range(len(use_XSERVERS())):
            builder.button(text=f"{str(ind + 1)}) {use_XSERVERS()[ind].name}")
        builder.button(text="❌ Отмена")
        if len(use_XSERVERS()) % 2 == 0:
            builder.adjust(*[2 for _ in range(len(use_XSERVERS()) // 2)], 1)
        else:
            builder.adjust(*[2 for _ in range(len(use_XSERVERS()) // 2 + 1)], 1)
        return builder.as_markup(resize_keyboard=True)

    await callback.message.answer("🌐 Доступные сервера:", reply_markup=build_kb())
    await callback.message.delete()
    await state.set_state(XserverClientListing.server)


@router.message(XserverClientListing.server)
async def handle_xserver_xclient_person_selection(message: Message, state: FSMContext):
    try:
        server = use_XSERVERS()[int(message.text.split(")")[0]) - 1]
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0

    clients = await server.get_all_clients()
    text = ""
    for client in clients:
        text += f"\n🏷Email: {client.email}\n🆔UUID: <code>{client.uuid if not client.password else client.email}</code>"

    await state.update_data(server=server)
    await state.set_state(XserverClientListing.UUID)
    await message.answer(text=f"Все клиенты сервера: {text}\n▶Выбери UUID", reply_markup=CANCEL_KB, parse_mode="HTML")


@router.message(XserverClientListing.UUID)
async def handle_xserver_new_client_data_listing(message: Message, state: FSMContext):
    await state.update_data(UUID=message.text.strip())
    data = await state.get_data()
    await state.clear()
    xclient: XClient = await data["server"].get_client_info(identifier=data["UUID"])
    if xclient.password:
        client_traffics = await data["server"].get_client_traffics(email=data["UUID"])
    else:
        client_traffics = await data["server"].get_client_traffics(uuid=data["UUID"])
    inbound = None
    for inb in data["server"].inbounds:
        if xclient.flow:
            if inb.protocol == "vless":
                inbound = inb
                break
        else:
            if inb.protocol == "shadowsocks":
                inbound = inb
                break
    epoch = datetime.utcfromtimestamp(0)
    expriryDate = epoch + timedelta(milliseconds=xclient.expiryTime)
    exprDate = f"{expriryDate.strftime('%A %d.%m.%Y')}"
    expriryDateAcc = True if (expriryDate - datetime.now()) >= timedelta(days=-1) else False
    # print(f"{client_traffics=}\n{xclient=}")
    answer = f"""
✅ <b>Ключ</b>
{'🌚 <b>Отключен</b>' if not (xclient.enable and expriryDateAcc) else '🌝 <b>Включён</b>'}
📛 <b>Название</b>: {xclient.email}
🆔 <b>UUID</b>: {xclient.uuid}
📡 <b>Протокол</b>: {"ShadowSocks" if not xclient.flow else "VLESS"}
🛰 <b>Сервер</b>: {data["server"].name}
⏹ <b>Трафик</b>: {round((client_traffics["up"] + client_traffics["down"]) / 1024**3, 2)}/{xclient.totalGB / 1024**3}GB
🕓 <b>Истекает</b>: {exprDate if xclient.expiryTime else "♾ Вечный"}
🔑 <b>Ключ</b>: <pre><code>{await xclient.get_key(use_XSERVERS())}</code></pre>
<span class="tg-spoiler">|api|{data["server"].name}:{inbound.id}:{xclient.uuid if xclient.uuid else xclient.email}|api|</span>
"""
    if xclient.enable:
        turn_text = "📴 Выключить"
        turn_call = "admin_offClient"
    else:
        turn_text = "💡 Включить"
        turn_call = "admin_onClient"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=turn_text, callback_data=turn_call),
             InlineKeyboardButton(text="⛔ Удалить", callback_data=f"admin_delClient")],
            [InlineKeyboardButton(text="🗓 Продлить подписку", callback_data="admin_updateExpriryDate")]
        ]
    )
    await message.answer(text=answer, reply_markup=kb)

@router.callback_query(F.data == "admin_offClient")
async def handle_admin_disable_xclient(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    prev_text = callback.message.text
    packed = prev_text.split("|api|")[1].split(":")
    inbound = None
    client = None
    for srv in use_XSERVERS():
        if srv.name == packed[0]:
            for inb in srv.inbounds:
                if inb.id == int(packed[1]):
                    inbound = inb
    for cl in inbound.settings["clients"]:
        if cl["id"] == packed[2]:
            client = XClient.create_from_dict(cl)
    await state.update_data(inbound=inbound, client=client)
    await state.set_state(XserverClientDisabling.confirmation)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Отключаем"), KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    await callback.message.answer(text="❓ Отключаем клиента?", reply_markup=kb)

@router.message(XserverClientDisabling.confirmation)
async def handle_xserver_client_disabling(message: Message, state: FSMContext):
    data = await state.get_data()
    inbound = data["inbound"]
    success = await inbound.update_client(client=data["client"], changes={'enable': False})
    await state.clear()
    await message.delete()
    if success:
        answer = f"""
    ‼ <b>Клиент отключён</b>
    📛 <b>Название</b>: {data["client"].email}
    🆔 <b>ID</b>: {data["client"].uuid}
    🛰 <b>Сервер</b>: {inbound.server.name}
    📡 <b>Протокол</b>: {"ShadowSocks" if inbound.protocol == "shadowsocks" else "VLESS"}
    """
        await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)
        return
    await message.answer(text="‼ Ошибка!\nState очищен.", reply_markup=MENU_KEYBOARD_MARKUP)

@router.callback_query(F.data == "admin_onClient")
async def handle_admin_enable_xclient(callback: CallbackQuery, state: FSMContext):
    prev_text = callback.message.text
    packed = prev_text.split("|api|")[1].split(":")
    inbound = None
    client = None
    for srv in use_XSERVERS():
        if srv.name == packed[0]:
            for inb in srv.inbounds:
                if inb.id == int(packed[1]):
                    inbound = inb
    for cl in inbound.settings["clients"]:
        if cl["id"] == packed[2]:
            client = XClient.create_from_dict(cl)
    await state.update_data(inbound=inbound, client=client)
    await state.set_state(XserverClientEnabling.confirmation)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Включаем"), KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    await callback.message.answer(text="❓ Включаем клиента?", reply_markup=kb)

@router.message(XserverClientEnabling.confirmation)
async def handle_xserver_client_enabling(message: Message, state: FSMContext):
    data = await state.get_data()
    inbound = data["inbound"]
    success = await inbound.update_client(client=data["client"], changes={'enable': True})
    await state.clear()
    await message.delete()
    if success:
        answer = f"""
    ‼ <b>Клиент включён</b>
    📛 <b>Название</b>: {data["client"].email}
    🆔 <b>ID</b>: {data["client"].uuid}
    🛰 <b>Сервер</b>: {inbound.server.name}
    📡 <b>Протокол</b>: {"ShadowSocks" if inbound.protocol == "shadowsocks" else "VLESS"}
    """
        await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)
        return
    await message.answer(text="‼ Ошибка!\nState очищен.", reply_markup=MENU_KEYBOARD_MARKUP)

@router.callback_query(F.data == "admin_delClient")
async def handle_admin_delete_xclient(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    await state.set_state(XserverClientDeleting.inbound)
    prev_text = callback.message.text
    packed = prev_text.split("|api|")[1].split(":")
    inbound = None
    for srv in use_XSERVERS():
        if srv.name == packed[0]:
            for inb in srv.inbounds:
                if inb.id == int(packed[1]):
                    inbound = inb
    await state.update_data(inbound=inbound, UUID=packed[2])
    await state.set_state(XserverClientDeleting.confirmation)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Удаляем"), KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    await callback.message.answer(text=f"❓ Удаляем клиента?", reply_markup=kb)

@router.message(XserverClientDeleting.confirmation)
async def handle_xserver_client_deletion(message: Message, state: FSMContext):
    data = await state.get_data()
    client = None
    inbound = data["inbound"]
    for cl in inbound.settings["clients"]:
        if cl["id"] == data["UUID"]:
            client = cl
    success = await inbound.delete_client(client_id=data["UUID"])
    await state.clear()
    await message.delete()
    if success:
        answer = f"""
    ‼ <b>Клиент удалён</b>
    📛 <b>Название</b>: {client["email"]}
    🆔 <b>ID</b>: {data["UUID"]}
    🛰 <b>Сервер</b>: {inbound.server.name}
    📡 <b>Протокол</b>: {"ShadowSocks" if inbound.protocol == "shadowsocks" else "VLESS"}
    """
        await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)
        return
    await message.answer(text="‼ Ошибка!\nState очищен.", reply_markup=MENU_KEYBOARD_MARKUP)


@router.callback_query(F.data == "admin_updateExpriryDate")
async def handle_admin_updateExpriryDate(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    await state.set_state(XserverClientExpriryDateUpdating.inbound)
    prev_text = callback.message.text
    packed = prev_text.split("|api|")[1].split(":")
    inbound = None
    for srv in use_XSERVERS():
        if srv.name == packed[0]:
            for inb in srv.inbounds:
                if inb.id == int(packed[1]):
                    inbound = inb
                    break
            break
    epoch = datetime.utcfromtimestamp(0)
    xclient: XClient = await srv.get_client_info(identifier=packed[2])
    expriryDate = epoch + timedelta(milliseconds=xclient.expiryTime)

    await state.update_data(inbound=inbound, UUID=packed[2], expriryDate=expriryDate)
    await state.set_state(XserverClientExpriryDateUpdating.days)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    await callback.message.answer(text=f"❓ Как изменяем? (+30/-30)", reply_markup=kb)

@router.message(XserverClientExpriryDateUpdating.days)
async def handle_admin_updateExpriryDate_new_value(message: Message, state: FSMContext):
    text = message.text
    if text[0] != "+" and text[0] != "-":
        await message.answer(text="❌ Неверный <b>формат</b> изменения.\n\n‼ Просто укажите +30 или -10.")
        return 0
    try:
        text = int(text)
    except ValueError:
        await message.answer(text="❌ Неверный <b>формат</b> изменения.\n\n‼ Просто укажите +30 или -10.")
        return 0
    data = await state.get_data()
    new_date: datetime = data["expriryDate"] + timedelta(days=text)
    new_date_str = f"{new_date.strftime('%A %d.%m.%Y')}"
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Применяем")],
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    answer = f"""
✅ Следующие изменения:
⌚ <b>Окончание</b>: {data["expriryDate"].strftime('%A %d.%m.%Y')} -> {new_date_str}
❔ Применяем изменения
"""
    await state.update_data(inbound=data["inbound"], UUID=data["UUID"], expriryDate=data["expriryDate"], new_value=new_date)
    await state.set_state(XserverClientExpriryDateUpdating.confirmation)
    await message.answer(text=answer, reply_markup=kb)

@router.message(XserverClientExpriryDateUpdating.confirmation)
async def handle_xserver_updateExpriryDate_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    client = None
    new_date = data["new_value"]
    inbound: Inbound = data["inbound"]
    for cl in inbound.settings["clients"]:
        if inbound.protocol == "vless":
            if cl["id"] == data["UUID"]:
                client = XClient.create_from_dict(cl)
        elif inbound.protocol == "shadowsocks":
            if cl["email"] == data["UUID"]:
                client = XClient.create_from_dict(cl)
    epoch = datetime.utcfromtimestamp(0)
    delta = timedelta(hours=14) if time.timezone == 0 else timedelta(hours=19)
    success = await inbound.update_client(client, {
        "expiryTime": (datetime(new_date.year, new_date.month, new_date.day) - epoch + delta).total_seconds() * 1000})
    await state.clear()
    await message.delete()
    if success:
        answer = f"""
    ‼ <b>Клиент изменён</b>
    📛 <b>Название</b>: {client.email}
    🆔 <b>ID</b>: {data["UUID"]}
    🛰 <b>Сервер</b>: {inbound.server.name}
    🕓 <b>Истекает</b>: {new_date.strftime('%A %d.%m.%Y')}
    📡 <b>Протокол</b>: {"ShadowSocks" if inbound.protocol == "shadowsocks" else "VLESS"}
    """
        await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)
        return
    await message.answer(text="‼ Ошибка!\nState очищен.", reply_markup=MENU_KEYBOARD_MARKUP)



# -------------------------------------------Outline-------------------------------------------------
@router.callback_query((F.data == "admin_create_outline_key") & (F.message.from_user.id in ADMINS))
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
    await state.set_state(OutlineKeyCreation.server)


@router.message(OutlineKeyCreation.server)
async def handle_server_selection(message: Message, state: FSMContext):
    try:
        server = SERVERS[int(message.text.split(")")[0]) - 1]
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0
    await state.update_data(server=server)
    await state.set_state(OutlineKeyCreation.name)
    await message.answer(text="🔑 Дайте имя ключу:", reply_markup=CANCEL_KB)


@router.message(OutlineKeyCreation.name)
async def handle_key_naming(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(OutlineKeyCreation.data_limit)
    await message.answer(text="⏹ Ограничение ключа в ГБ(0 - нет):")


@router.message(OutlineKeyCreation.data_limit)
async def handle_key_data_limiting(message: Message, state: FSMContext):
    try:
        limit = float(message.text.strip())
    except ValueError:
        await message.answer(text="Ошибка ❗\nВероятно это не число 😑\np.s. или надо юзать точку ХД")
        return 0
    await state.update_data(data_limit=limit)
    data = await state.get_data()
    await state.clear()
    key = data["server"].create_new_key(name=data["name"], data_limit_gb=data["data_limit"])
    link = str(key.access_url).split("?")[0] + "#Proxym1ty-VPN"
    #raise Exception(f"{key=}")
    # print(f"{key=}")
    answer = f"""
✅ <b>Ключ создан</b>
📛 <b>Название</b>: {key.name}
🆔 <b>ID</b>: {key.key_id}
🛰 <b>Сервер</b>: {data["server"].name}
⏹ <b>Ограничение</b>: {key.data_limit / 1024**3 if key.data_limit else "~INF~"}GB
🔑 <b>Ключ</b>: <pre><code>{link}</code></pre>
"""
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)


@router.callback_query((F.data == "admin_delete_outline_key") & (F.message.from_user.id in ADMINS))
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
    await state.set_state(OutlineKeyRemoval.server)


@router.message(OutlineKeyRemoval.server)
async def handle_key_removal_server_selection(message: Message, state: FSMContext):
    try:
        m = message.text.split(")")
        server = SERVERS[int(m[0]) - 1]
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0
    await state.update_data(server=server)
    await state.set_state(OutlineKeyRemoval.id)
    await message.answer(text="🆔 Какой ID ключа?", reply_markup=CANCEL_KB)


@router.message(OutlineKeyRemoval.id)
async def handle_key_removal_identification(message: Message, state: FSMContext):
    try:
        id = int(message.text.strip())
        await state.update_data(id=id)
    except ValueError:
        await message.answer(text="Ошибка ❗\nВероятно это не целое число 😑")
        return 0
    await state.set_state(OutlineKeyRemoval.confirmation)
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
🔑 <b>Ключ</b>: <code>{info.access_url}</code>
"""
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Удаляем"), KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    await message.answer(text=answer, reply_markup=kb, parse_mode="HTML")


@router.message(OutlineKeyRemoval.confirmation)
async def handle_key_naming(message: Message, state: FSMContext):
    data = await state.get_data()
    info = data["server"].get_key_info(str(data["id"]))
    if info is None:
        await message.answer(text="Ошибка ❗\nТакого ключа не существует 😑")
        return 0
    data["server"].delete_key(str(data["id"]))
    answer = f"""
‼ <b>Ключ удалён</b>
📛 <b>Название</b>: {info.name}
🆔 <b>ID</b>: {info.key_id}
🛰 <b>Сервер</b>: {data["server"].name}
⏹ <b>Ограничение</b>: {info.data_limit / 1024**3}GB
🔑 <b>Ключ</b>: <pre><code>{info.access_url}</code></pre>
"""
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)



