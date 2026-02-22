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

from backend.models import User, XClient
from backend.xapi.servers import Inbound
from frontend.replys import *
from frontend.admin.payment_manager_handlers import router as payment_manager_router
from frontend.admin.user_db_management import router as user_db_management_router
from globals import ADMINS, MENU_KEYBOARD_MARKUP, use_XSERVERS, use_LAST_ALL_XSERVERS_UPDATE, get_servers

router = Router()
router.include_router(payment_manager_router)
router.include_router(user_db_management_router)

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



#----------------------------------------------SERVER DATA UPDATER---------------------------------

@router.callback_query((F.data == "admin_update_all_xserver_shiit") & (F.message.from_user.pk_id in ADMINS))
async def handle_update_all_xserver_shiit(callback: CallbackQuery):
    if (datetime.now() - use_LAST_ALL_XSERVERS_UPDATE()) >= timedelta(minutes=5):
        await callback.answer(text="( ◡̀_◡́)ᕤ Now updating...", show_alert=True)
        await get_servers()
        await callback.message.answer(text=f"😎 Yap! All data updated!!!")
    else:
        await callback.answer("Not so frequent")

#-----------------------------------------------Managers-------------------------------------------
@router.callback_query((F.data == "admin_manage_xservers") & (F.message.from_user.pk_id in ADMINS))
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
    xclient: XClient = await data["inbound"].add_xclient(email=data["email"], totalBytes=data["data_limit"] * 1024 ** 3, expiryTime=expiryTime)
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

    clients = await server.get_all_xclients()
    text = ""
    for client in clients:
        text += f"\n🏷Email: {client['email']}\n🆔UUID: <code>{client['uuid']}</code>"

    await state.update_data(server=server)
    await state.set_state(XserverClientListing.UUID)
    await message.answer(text=f"Все клиенты сервера: {text}\n▶Выбери UUID", reply_markup=CANCEL_KB, parse_mode="HTML")


@router.message(XserverClientListing.UUID)
async def handle_xserver_new_client_data_listing(message: Message, state: FSMContext):
    await state.update_data(UUID=message.text.strip())
    data = await state.get_data()
    await state.clear()
    xclient: XClient = await data["server"].get_xclient(identifier=data["UUID"])
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
🔑 <b>Sub-Ключ</b>: <pre><code>{xclient.sub_key}</code></pre>
🔑 <b>Ключ</b>: <pre><code>{xclient.key}</code></pre>
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
                if inb.pk_id == int(packed[1]):
                    inbound = inb
    for cl in inbound.settings["clients"]:
        if cl["pk_id"] == packed[2]:
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
    data["client"].enable = False
    success = await inbound.update_xclient(client=data["client"])
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
                if inb.pk_id == int(packed[1]):
                    inbound = inb
    for cl in inbound.settings["clients"]:
        if cl["pk_id"] == packed[2]:
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
    data["client"].enable = True
    success = await inbound.update_xclient(client=data["client"])
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
                if inb.pk_id == int(packed[1]):
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
        if cl["pk_id"] == data["UUID"]:
            client = cl
    success = await inbound.delete_xclient(client_uuid=data["UUID"])
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
                if inb.pk_id == int(packed[1]):
                    inbound = inb
                    break
            break
    epoch = datetime.utcfromtimestamp(0)
    xclient: XClient = await srv.get_xclient(identifier=packed[2])
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
            if cl["pk_id"] == data["UUID"]:
                client = XClient.create_from_dict(cl)
        elif inbound.protocol == "shadowsocks":
            if cl["email"] == data["UUID"]:
                client = XClient.create_from_dict(cl)
    epoch = datetime.utcfromtimestamp(0)
    delta = timedelta(hours=14) if time.timezone == 0 else timedelta(hours=19)
    client.expiryTime = int((datetime(new_date.year, new_date.month, new_date.day) - epoch + delta).total_seconds() * 1000)
    success = await inbound.update_xclient(client)
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