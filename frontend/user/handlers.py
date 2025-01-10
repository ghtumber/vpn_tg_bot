import re
from datetime import date, datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from backend.models import User, OutlineClient
from backend.xapi.servers import Inbound, XServer
from frontend.replys import *
from backend.outline.managers import SERVERS, OutlineManager
from backend.database.users import UsersDatabase
from globals import add_months, XSERVERS, MENU_KEYBOARD_MARKUP, BASIC_VPN_COST

router = Router()

@router.message(F.text == "❌ Отмена")
async def handle_user_cancel(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="menu"), InlineKeyboardButton(text="Нет", callback_data="cancel_of_cancel")],
        ]
    )
    await message.answer("Отмена?", reply_markup=kb)


class OldRegistration(StatesGroup):
    key = State()
    payment_date = State()
    payment_sum = State()

class KeyPayment(StatesGroup):
    serverType = State()
    server = State()
    outline_server = State()
    keyType = State()
    confirmation = State()

#----------------------------------------Key Payment----------------------------------------------
@router.callback_query(F.data == "buy_key")
async def handle_registration(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='')
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟢 Outline"), KeyboardButton(text="🟣 Proxym1ty")],
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    await callback.message.answer(f"🌐 Выберите тип сервера", reply_markup=keyboard)
    await state.set_state(KeyPayment.serverType)

@router.message(KeyPayment.serverType)
async def handle_key_payment_server_type(message: Message, state: FSMContext):
    if not ("Outline" in message.text.strip() or "Proxym1ty" in message.text.strip()):
        await message.answer(text="❌ Неверный <b>тип</b> сервера.\n\n‼ Выберите тип из <b>предложенных в списке</b>.")
        return 0
    server_type = message.text.strip().split(" ")[1]
    await state.update_data(serverType=server_type)
    if server_type == "Outline":
        def build_kb():
            builder = ReplyKeyboardBuilder()
            for ind in range(len(SERVERS)):
                location_imoji = ''
                if 'Germany' in SERVERS[ind].location:
                    location_imoji = '🇩🇪'
                elif 'Finland' in SERVERS[ind].location:
                    location_imoji = '🇫🇮'
                builder.button(text=f"{str(ind + 1)}) {SERVERS[ind].name}{location_imoji}")
            builder.button(text="❌ Отмена")
            if len(SERVERS) % 2 == 0:
                builder.adjust(*[2 for _ in range(len(SERVERS) // 2)], 1)
            else:
                builder.adjust(*[2 for _ in range(len(SERVERS) // 2 + 1)], 1)
            return builder.as_markup(resize_keyboard=True)
        await state.set_state(KeyPayment.keyType)
    elif server_type == "Proxym1ty":
        def build_kb():
            builder = ReplyKeyboardBuilder()
            for ind in range(len(XSERVERS)):
                location_imoji = ''
                if 'Germany' in XSERVERS[ind].location:
                    location_imoji = '🇩🇪'
                elif 'Finland' in XSERVERS[ind].location:
                    location_imoji = '🇫🇮'
                builder.button(text=f"{str(ind + 1)}) {location_imoji}{XSERVERS[ind].name}")
            builder.button(text="❌ Отмена")
            if len(XSERVERS) % 2 == 0:
                builder.adjust(*[2 for _ in range(len(XSERVERS) // 2)], 1)
            else:
                builder.adjust(*[2 for _ in range(len(XSERVERS) // 2 + 1)], 1)
            return builder.as_markup(resize_keyboard=True)
        await state.set_state(KeyPayment.server)
    await message.answer(text=f"✅ Отлично! 🏳 Теперь выберите сервер", reply_markup=build_kb())

@router.message(KeyPayment.server)
async def handle_key_payment_server(message: Message, state: FSMContext):
    try:
        server = XSERVERS[int(message.text.split(")")[0]) - 1]
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0
    await state.update_data(server=server)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚫ ShadowSocks"), KeyboardButton(text="🔵 VLESS")],
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    await message.answer(text=f"📡 Теперь выберите протокол подключения", reply_markup=keyboard)
    await state.set_state(KeyPayment.keyType)

@router.message(KeyPayment.keyType)
async def handle_key_payment_protocol(message: Message, state: FSMContext):
    data = await state.get_data()
    if data["serverType"] == "VLESS":
        if not ("ShadowSocks" in message.text.strip() or "VLESS" in message.text.strip()):
            await message.answer(text="❌ Неверный <b>протокол</b> подключения.\n\n‼ Выберите тип из <b>предложенных в списке</b>.")
            return 0
        protocol = message.text.strip().split(" ")[1]
    elif data["serverType"] == "Outline":
        try:
            server = SERVERS[int(message.text.split(")")[0]) - 1]
            data["server"] = server
        except IndexError:
            await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
            return 0
        await state.update_data(server=server)
        protocol = "ShadowSocks"

    answer = f"""✅ Отлично. Твой заказ:
🌐 <b>Сервер</b> {data["serverType"]}: {data["server"].name}
🏳 <b>Локация</b>: {data["server"].location}
📡 <b>Протокол подключения</b>: {protocol} 
💸 <b>Стоимость</b>: {BASIC_VPN_COST}р
🧾 Для продолжения <b>подтвердите</b> оплату
"""
    await state.set_state(KeyPayment.confirmation)
    await state.update_data(serverType=data["serverType"], server=data["server"], keyType=protocol)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✔ Подтвердить")],
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    await message.answer(text=answer, reply_markup=keyboard)

@router.message(KeyPayment.confirmation)
async def handle_key_payment_confirmation(message: Message, state: FSMContext):
    user: User = await UsersDatabase.get_user_by(ID=str(message.from_user.id))
    if user.moneyBalance < BASIC_VPN_COST:
        await message.answer(text="❌ Недостаточно <b>средств</b> на балансе.\n\n‼ <b>Пополните</b> баланс.", reply_markup=MENU_KEYBOARD_MARKUP)
        await state.clear()
        await message.delete()
        return 0
    data = await state.get_data()
    epoch = datetime.utcfromtimestamp(0)
    user.moneyBalance -= BASIC_VPN_COST
    dat = add_months(date.today(), 1)
    user.PaymentDate = dat
    user.lastPaymentDate = date.today()
    user.PaymentSum = BASIC_VPN_COST
    user.serverName = data["server"].name
    if data["serverType"] == "Proxym1ty":
        for inb in data["server"].inbounds:
            if inb.protocol == data["keyType"].lower():
                expiryTime = (datetime(dat.year, dat.month, dat.day) - epoch).total_seconds() * 1000
                client = await inb.add_client(email=message.from_user.username, tgId=message.from_user.id, totalBytes=500*1024**3, expiryTime=expiryTime)
                user.xclient = client
                user.Protocol = data["keyType"]
                user.serverType = "XSERVER"
                user.uuid = client.uuid
                key = client.key
    elif data["serverType"] == "Outline":
        server: OutlineManager = data["server"]
        key = server.create_new_key(name=f"@{message.from_user.username}", data_limit_gb=500)
        if not key.key_id:
            key.key_id = "9999"
        user.outline_client = OutlineClient(key=key.access_url, keyID=int(key.key_id), keyLimit=key.data_limit)
        user.Protocol = "ShadowSocks"
        user.serverType = "Outline"
        key = key.access_url.split("#")[0] + "#PROXYM1TY"
    user: User = await UsersDatabase.update_user(user=user, change={})
    totalGB = user.xclient.totalGB / 1024**3 if user.xclient else user.outline_client.keyLimit / 1000**3
    answer = f"""✅ Готово! Ваши данные для подключения:
🌐 <b>Сервер</b> {data["serverType"]}: {data["server"].name}
🏳 <b>Локация</b>: {data["server"].location}
📡 <b>Протокол подключения</b>: {data["keyType"]}
⏹ <b>Ограничение</b>: {totalGB}GB
🔑 <b>Ключ</b>: <pre><code>{user.xclient.key if data["serverType"] == "Proxym1ty" else user.outline_client.key}</code></pre>
    """
    await state.clear()
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)


@router.callback_query(F.data == "user_registration")
async def handle_registration(callback: CallbackQuery):
    await callback.answer(text='')
    user = User(userID=callback.from_user.id, userTG=f"@{callback.from_user.username}", PaymentSum=0, PaymentDate=None,
                serverName="", serverType="", moneyBalance=0, Protocol="", lastPaymentDate=None)
    u = await UsersDatabase.create_user(user)
    await callback.message.answer(f"✅ Аккаунт создан!\n\n🔓 Доступ к меню открыт!", reply_markup=MENU_KEYBOARD_MARKUP)



@router.callback_query(F.data == "user_registration")
async def handle_reg(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='')
    user_resp = await UsersDatabase.get_user_by(TG="@"+callback.from_user.username)
    if user_resp:
        await callback.message.answer(text="Вы уже зарегистрированы 😎\n\nСкоро бот заработает на полную 🔥")
    else:
        await callback.message.answer(REGISTRATION_FSM_REPLY)
        await state.set_state(OldRegistration.key)


@router.message(OldRegistration.key)
async def handle_reg_payment_date(message: Message, state: FSMContext):
    await state.update_data(key=message.text)
    await state.set_state(OldRegistration.payment_date)
    await message.answer("Также отправьте <b>последнюю дату вашей оплаты</b> в ответ на это сообщение.\n\n‼В сообщении укажите дату в формате <b>ДД.ММ.ГГГГ</b>.")


@router.message(OldRegistration.payment_date)
async def handle_reg_payment_sum(message: Message, state: FSMContext):
    if not re.fullmatch(r'[0-9][0-9].[0-9][0-9].[2-9][0-9][2-9][4-9]', r''.join(message.text.strip())):
        await message.answer(text="❌ Неверный <b>формат</b> даты.\n\n‼ В сообщении укажите дату в формате <b>ДД.ММ.ГГГГ</b>.")
        return 0
    PD_mes = message.text.strip().split(".")
    payment_date = date(int(PD_mes[2]), int(PD_mes[1]), int(PD_mes[0]))
    await state.update_data(payment_date=payment_date)
    await state.set_state(OldRegistration.payment_sum)
    await message.answer("Отлично! Теперь отправьте сумму вашей месячной оплаты в ответ на это сообщение.\n\n‼ В сообщении укажите только число.\np.s. Все данные проверяются админами 😉")


@router.message(OldRegistration.payment_sum)
async def complete_reg(message: Message, state: FSMContext):
    try:
        payment_sum = float(message.text.strip())
    except ValueError:
        await message.answer(text="❌ Неверный <b>формат</b> суммы.\n\n‼ В сообщении укажите <b>только число</b>.")
        return 0
    await state.update_data(payment_sum=payment_sum)
    data = await state.get_data()
    await state.clear()
    key = data["key"]
    key = key.split("?")[0]
    server = None
    info = None
    for server in SERVERS:
        info = server.get_key_info_by_key(key)
        if info:
            break
    if not info:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ В меню", callback_data="menu")]
            ]
        )
        await message.answer(f"Неверный ключ!", reply_markup=keyboard)
        return Exception("No key found")
    keyID = info.key_id
    keyLimit = info.data_limit
    userID = message.from_user.id
    userTG = "@" + message.from_user.username
    PaymentSum = data["payment_sum"]
    PaymentDate: date = data["payment_date"]
    PaymentDate = add_months(PaymentDate, 1)
    user = User(userID=userID, userTG=userTG, keyID=keyID, keyLimit=keyLimit, key=key, PaymentSum=PaymentSum, PaymentDate=PaymentDate, serverName=server.name)
    u = await UsersDatabase.create_user(user)
    await message.answer(f"✅ Аккаунт активирован!\n\n🔓 Доступ к меню открыт!")



@router.callback_query(F.data == "xclient_vpn_usage")
async def handle_xclient_vpn_usage(callback: CallbackQuery):
    await callback.answer(text='')
    user = await UsersDatabase.get_user_by(ID=str(callback.from_user.id))
    d = await user.xclient.get_server_and_inbound(servers=XSERVERS)
    server: XServer = d["server"]
    if user.Protocol == "VLESS":
        keyInfo = await server.get_client_traffics(uuid=user.uuid)
    else:
        keyInfo = await server.get_client_traffics(email=user.xclient.email)
    traffic = keyInfo["up"] + keyInfo["down"]
    progress = round(traffic / keyInfo["total"], 2)
    answer = f"""
📈 <b>Использование VPN</b> за этот месяц:
<b>{round(traffic / 1024**3, 2)}GB</b>/<b>{keyInfo["total"] // 1024**3}GB</b>
[{"".join("☁" for i in range(int(progress * 10)))}{"".join("✦" for i in range(10 - int(progress * 10)))}]
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩ Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text=answer, reply_markup=keyboard)

@router.callback_query(F.data == "view_user_key")
async def handle_vpn_key(callback: CallbackQuery):
    await callback.answer(text='')
    user = await UsersDatabase.get_user_by(ID=str(callback.from_user.id))
    if user.xclient:
        key = await user.xclient.get_key(servers=XSERVERS)
    else:
        key = user.outline_client.key
    answer = f"""
🔑 <b>Твой ключ</b>:
<pre><code>{key}</code></pre>
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩ Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text=answer, reply_markup=keyboard)



