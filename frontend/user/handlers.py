import asyncio
import re
import time
from datetime import date, datetime, timedelta
from typing import Protocol

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from backend.DonatPAY.donations import DonatPAYHandler
from backend.models import User, OutlineClient, XClient
from backend.xapi.servers import XServer
from frontend.replys import *
from backend.outline.managers import SERVERS, OutlineManager
from backend.database.users import UsersDatabase
from globals import add_months, MENU_KEYBOARD_MARKUP, use_BASIC_VPN_COST, DEBUG, use_PREFERRED_PAYMENT_SETTINGS, bot, use_XSERVERS, \
    Available_Tariffs, use_Available_Tariffs, REFERRAL_PERCENTAGE_QUEUE

router = Router()

#@router.message(F.text == "❌ Отмена")
async def handle_user_cancel(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="menu"), InlineKeyboardButton(text="Нет", callback_data="cancel_of_cancel")],
        ]
    )
    print("Nihuya HERE")
    await message.answer("Отмена?", reply_markup=kb)


class OldRegistration(StatesGroup):
    key = State()
    payment_date = State()
    payment_sum = State()

class KeyPayment(StatesGroup):
    tariff = State()
    configuration_type = State()
    server = State()
    outline_server = State()
    keyType = State()
    confirmation = State()

#----------------------------------------Balance top-up----------------------------------------------
@router.callback_query(F.data == "topup_user_balance")
async def handle_topup_user_balance(callback: CallbackQuery):
    await callback.answer("")
    user = await UsersDatabase.get_user_by(ID=str(callback.from_user.id))
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплата", url=DonatPAYHandler.form_link(user=user))]
        ]
    )
    await callback.message.answer(f"💰 Пополнение баланса\n➖➖➖➖➖➖➖➖\n❓ Нажми на кнопку ниже и измени сумму пожертвования\n❗ Не меняй комментарий и имя\n✨ Бот пополнит твой баланс в течении 5-10 минут", reply_markup=keyboard)


#----------------------------------------Key Payment----------------------------------------------
@router.callback_query(F.data == "buy_key")
async def handle_buy_key(callback: CallbackQuery, state: FSMContext):
    if not Available_Tariffs:
        await callback.answer(text="😕 Сейчас покупка недоступна")
        return
    await callback.answer(text='')
    kb_l = []
    for e in use_Available_Tariffs():
        kb_l.append([InlineKeyboardButton(text=f"♦ {e}", callback_data=f"buy_key_tariff_{e}")])
    kb_l.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_l)
    answer = f"""
🌟 Выбор <b>тарифа</b>.
Выбери подходящий вам тариф:
👉 <b>PROMO</b> подходит для тех, кто редко использует VPN (к примеру для просмотра Youtube)
- 100 МБ/с канал на сервере (ограничены вашим соединением)
- подключение до 2 устройств одновременно
- обычная тех. поддержка
- возможны подвисания
👉 <b>MAX</b> подходит для активных пользователей
- 10 Gbit/s канал на сервере (ограничены вашим соединением)
- подключение до 5 устройств одновременно
- приоритетная тех. поддержка
- стабильный uptime 99%
"""
    await callback.message.answer(answer, reply_markup=keyboard)
    await state.set_state(KeyPayment.tariff)

@router.callback_query(F.data.startswith("buy_key_tariff_"))
async def handle_buy_key(callback: CallbackQuery, state: FSMContext):
    tariff = callback.data.split("_")[3]
    await callback.answer("")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚡ Авто подбор"), KeyboardButton(text="⚙ Ручная настройка")],
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    await state.update_data(tariff=tariff)
    await callback.message.answer(f"🔑 Выбор конфигурации VPN-ключа\nВыбери способ настройки:", reply_markup=keyboard)
    await callback.message.delete()
    await state.set_state(KeyPayment.configuration_type)

@router.message(KeyPayment.configuration_type)
async def handle_key_payment_server_type(message: Message, state: FSMContext):
    if not ("Авто подбор" in message.text.strip() or "Ручная настройка" in message.text.strip()):
        await message.answer(text="❌ Неверный <b>тип</b> сервера.\n\n‼ Выберите тип из <b>предложенных в списке</b>.")
        return 0
    configuration_type = "Auto" if "Авто подбор" in message.text.strip() else "Manual"
    data = await state.get_data()
    tariff = data["tariff"]
    if configuration_type == "Auto":
        svr = None
        for server in use_XSERVERS():
            if server.name == use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][tariff]["server_name"]:
                svr = server
                break
        if not svr:
            await message.answer(text="😓 Ошибка сервера. Не найден сервер.\n🙏 Если вы видите это сообщение, пожалуйста, напишите в поддержку.")
            return 0
        await state.update_data(server=svr, keyType=use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][tariff]["keyType"], auto=True, tariff=tariff, configuration_type=configuration_type)
        await state.set_state(KeyPayment.keyType)
        await handle_key_payment_key_type(message=message, state=state)
    elif configuration_type == "Manual":
        svr = None
        for server in use_XSERVERS():
            if server.name == use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][tariff]["server_name"]:
                svr = server
                break
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⚫ ShadowSocks"), KeyboardButton(text="🔵 VLESS")],
                [KeyboardButton(text="❌ Отмена")]
            ], resize_keyboard=True
        )
        await state.set_state(KeyPayment.keyType)
        await state.update_data(tariff=tariff, server=svr, configuration_type=configuration_type)
        await message.answer(text=f"📡 Теперь выберите протокол подключения\n\n‼ В последнее время в работе ShadowSocks замечены перебои!!!", reply_markup=keyboard)

@router.message(KeyPayment.server)
async def handle_key_payment_server(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        servers = data["server_variants"]
        server = servers[int(message.text.split(")")[0]) - 1]
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0
    await state.update_data(server=server, tariff=data["tariff"])
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚫ ShadowSocks"), KeyboardButton(text="🔵 VLESS")],
            [KeyboardButton(text="❌ Отмена")]
        ], resize_keyboard=True
    )
    await message.answer(text=f"📡 Теперь выберите протокол подключения\n\n‼ В последнее время в работе ShadowSocks замечены перебои!!!", reply_markup=keyboard)
    await state.set_state(KeyPayment.keyType)

@router.message(KeyPayment.keyType)
async def handle_key_payment_key_type(message: Message, state: FSMContext):
    data = await state.get_data()
    protocol = ""
    if data["configuration_type"] == "Manual":
        if not ("ShadowSocks" in message.text.strip() or "VLESS" in message.text.strip()):
            await message.answer(text="❌ Неверный <b>протокол</b> подключения.\n\n‼ Выберите тип из <b>предложенных в списке</b>.")
            return 0
        protocol = message.text.strip().split(" ")[1]
    else:
        protocol = data["keyType"]

    answer = f"""✅ Отлично. Выбрано:
⚡ <b>Тариф</b>: {data["tariff"]}
🌐 <b>Сервер</b> {data['server'].name}
🏳 <b>Локация</b>: {data['server'].location}
📡 <b>Протокол подключения</b>: {protocol} 
⚡ <b>Скорость сети на сервере</b>: {'10 Gbit/s' if data["tariff"] == "MAX" else '100 МБ/c'}
💸 <b>Стоимость</b>: {use_PREFERRED_PAYMENT_SETTINGS()['Tariffs'][data['tariff']]['coast']}р/мес
🧾 Для продолжения <b>подтвердите</b> оплату
"""
    await state.set_state(KeyPayment.confirmation)
    await state.update_data(configuration_type=data["configuration_type"], server=data["server"], keyType=protocol, tariff=data["tariff"])
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
    data = await state.get_data()
    coast = use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][data["tariff"]]["coast"]
    if user.moneyBalance < coast:
        await message.answer(text="❌ Недостаточно <b>средств</b> на балансе.", reply_markup=MENU_KEYBOARD_MARKUP)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пополнить баланс", url=DonatPAYHandler.form_link(user=user))]
        ])
        await message.answer(text="💰 <b>Пополните</b> баланс.", reply_markup=kb)
        await state.clear()
        await message.delete()
        return 0
    epoch = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0) - timedelta(seconds=time.timezone)

    # Referral system
    # if user.who_invited:
    #     inviter = await UsersDatabase.get_user_by(ID=user.who_invited)
    #     all_refs = await UsersDatabase.get_all_referrals(ID=inviter.userID)
    #     if REFERRAL_PERCENTAGE_QUEUE[len(all_refs)] > int(inviter.referBonus):
    #         i = REFERRAL_PERCENTAGE_QUEUE.index(int(inviter.referBonus))
    #         print(f"{inviter.userTG} has {inviter.who_invited} now. and position is {i}")
    #         inviter.referBonus = REFERRAL_PERCENTAGE_QUEUE[i + 1]
    #         await UsersDatabase.update_user(inviter, {})
    #         await bot.send_message(chat_id=inviter.userID, text=f"🤝 У вас новый реферал {user.userTG}." + "\n" + f"📈 Новый коэффициент {inviter.referBonus}%!", reply_markup=MENU_KEYBOARD_MARKUP)

    user.change("moneyBalance", user.moneyBalance - coast)
    dat = add_months(date.today(), 1)
    user.PaymentDate = dat
    user.tariff = data["tariff"]
    user.PaymentSum = coast
    user.serverName = data["server"].name
    for inb in data["server"].inbounds:
        if inb.protocol == data["keyType"].lower():
            limitIp = 2 if data["tariff"] == "PROMO" else 5
            delta = timedelta(hours=15) if time.timezone == 0 else timedelta(hours=20)
            expiryTime = (datetime(dat.year, dat.month, dat.day) - epoch + delta).total_seconds() * 1000
            client: XClient = await inb.add_client(email=message.from_user.username, tgId=message.from_user.id, totalBytes=500*1024**3, expiryTime=expiryTime, limitIp=limitIp)
            user.xclient = client
            user.Protocol = data["keyType"]
            user.serverType = "XSERVER"
            user.uuid = client.uuid
            key = client.key
    # elif data["configuration_type"] == "Outline":
    #     server: OutlineManager = data["server"]
    #     key = server.create_new_key(name=f"@{message.from_user.username}", data_limit_gb=500)
    #     if not key.key_id:
    #         key.key_id = "9999"
    #     user.outline_client = OutlineClient(key=key.access_url, keyID=int(key.key_id), keyLimit=key.data_limit)
    #     user.Protocol = "ShadowSocks"
    #     user.serverType = "Outline"
    #     key = key.access_url.split("#")[0] + "#PROXYM1TY"
    user: User = await UsersDatabase.update_user(user=user, change={})
    totalGB = user.xclient.totalGB / 1024**3 if user.xclient else user.outline_client.keyLimit / 1000**3
    answer = f"""✅ Готово! Ваши данные для подключения:
⚡ <b>Тариф</b>: {data["tariff"]}
🌐 <b>Сервер</b>: {data["server"].name}
🏳 <b>Локация</b>: {data["server"].location}
📡 <b>Протокол подключения</b>: {data["keyType"]}
⚡ <b>Скорость сети на сервере</b>: {'10 Gbit/s' if data["tariff"] == "MAX" else '100 МБ/c'}
⏹ <b>Ограничение</b>: {totalGB}GB
🔑 <b>Ключ</b>: <pre><code>{user.xclient.key}</code></pre>
    """
    await state.clear()
    await message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)


@router.callback_query(F.data == "regain_user_access")
async def handle_regain_user_access(callback: CallbackQuery):
    await asyncio.sleep(0.5)
    user: User = await UsersDatabase.get_user_by(ID=str(callback.from_user.id))
    if (datetime.fromtimestamp(user.xclient.expiryTime // 1000).date() - date.today()) <= timedelta(days=0):
        if user.moneyBalance < use_BASIC_VPN_COST():
            await callback.message.answer(text="❌ Недостаточно <b>средств</b> на балансе.", reply_markup=MENU_KEYBOARD_MARKUP)
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Пополнить баланс", url=DonatPAYHandler.form_link(user=user))]
            ])
            await callback.message.answer(text="💰 <b>Пополните</b> баланс.", reply_markup=kb)
            return 0
        data = await user.xclient.get_server_and_inbound(use_XSERVERS())
        user.change("moneyBalance", user.moneyBalance - user.PaymentSum)
        new_date = add_months(user.PaymentDate, 1)
        epoch = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0) - timedelta(seconds=time.timezone)
        user.xclient.enable = True
        await data["inbound"].update_client(user.xclient, {"expiryTime": (datetime(new_date.year, new_date.month, new_date.day) - epoch + timedelta(hours=19)).total_seconds() * 1000, "enable": True})
        await data["inbound"].reset_client_traffic(user.xclient.for_api())
        user.change("PaymentDate", new_date)
        await user.xclient.get_key(use_XSERVERS())
        await UsersDatabase.update_user(user)
        await callback.message.answer(text=PAYMENT_SUCCESS(user), reply_markup=MENU_KEYBOARD_MARKUP)
    await callback.answer("")

@router.callback_query(F.data == "get_instructions")
async def handle_get_instructions(callback: CallbackQuery):
    await callback.answer("")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱Android", url="https://telegra.ph/Nastrojka-Proxym1ty-na-android-03-16"), InlineKeyboardButton(text="🍏IOS", url="https://telegra.ph/Nastrojka-Proxym1ty-na-iPhone-03-16")],
            [InlineKeyboardButton(text="💻Win(easy)", url="https://telegra.ph/Nastrojka-Proxym1ty-na-pk-dlya-debilov-ne-gejmerov-03-16"), InlineKeyboardButton(text="🖥️Win(pro)", url="https://telegra.ph/Nastrojka-Proxym1ty-VPN-na-pk-i-noutbuki-01-29")],
            [InlineKeyboardButton(text="↩ Назад", callback_data="back_to_menu")]
        ]
    )
    await callback.message.edit_text(text=INSTRUCTIONS_TEXT, reply_markup=kb)

@router.callback_query(F.data.startswith("user_registration_"))
async def handle_registration(callback: CallbackQuery):
    await asyncio.sleep(2)
    who_invited = callback.data.split("_")[2]
    if who_invited != "None":
        who_invited = int(who_invited)
    else:
        who_invited = None
    u = await UsersDatabase.get_user_by(ID=str(callback.from_user.id))
    await callback.answer(text='')
    if not u:
        if callback.from_user.username:
            user = User(userID=callback.from_user.id, userTG=f"@{callback.from_user.username}", PaymentSum=0, PaymentDate=None,
                        serverName="", serverType="None", moneyBalance=0, Protocol="None", tariff="None", who_invited=who_invited, referBonus=0)
            u = await UsersDatabase.create_user(user)
            await callback.message.answer(f"✅ Аккаунт создан!\n\n🔓 Доступ к меню открыт!", reply_markup=MENU_KEYBOARD_MARKUP)
        else:
            await callback.message.answer(f"✏ Для корректной работы бота нужен <b>username</b> в телеграмм!")


@router.callback_query(F.data == "xclient_vpn_usage")
async def handle_xclient_vpn_usage(callback: CallbackQuery):
    await callback.answer(text='')
    user = await UsersDatabase.get_user_by(ID=str(callback.from_user.id))
    d = await user.xclient.get_server_and_inbound(servers=use_XSERVERS())
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
        key = await user.xclient.get_key(servers=use_XSERVERS())
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



