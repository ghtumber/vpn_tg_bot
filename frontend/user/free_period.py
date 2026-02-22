import asyncio
import time
from datetime import timedelta, date, datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from backend.database.clients import ClientsDatabase
from backend.database.users import UsersDatabase
from backend.models import XClient
from backend.xapi.servers import Inbound
from frontend.replys import FREE_PERIOD_TARIFFS
from globals import trusted_search, use_PREFERRED_PAYMENT_SETTINGS, notif_to_admins, MENU_KEYBOARD_MARKUP, use_XSERVERS, \
    FREE_PERIOD_DURATION

router = Router()


class FreePeriodConfiguration(StatesGroup):
    tariff = State()
    protocol = State()
    location = State()
    confirmation = State()


@router.callback_query(F.data == "get_free_period")
async def handle_free_period(callback: CallbackQuery, state: FSMContext):
    await asyncio.sleep(1)
    user = await UsersDatabase.get_user_by(tg_id=str(callback.from_user.id))
    if len(user.clients) != 0:
        await callback.answer("🙅‍♂️ Это только для <b>новых пользователей</b>")
        return None
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="😎FULL", callback_data="get_free_period_tariff_full")],
                [InlineKeyboardButton(text="🗿PROMO", callback_data="get_free_period_tariff_promo")],
            ]
        )
        await callback.message.answer(text=FREE_PERIOD_TARIFFS(), reply_markup=keyboard)
        await callback.answer("")
    return None

@router.callback_query(F.data.startswith("get_free_period_tariff"))
async def handle_free_period_tariff(callback: CallbackQuery, state: FSMContext):
    tariff = callback.data.split("_")[4]
    server = trusted_search(use_PREFERRED_PAYMENT_SETTINGS()['Tariffs'][tariff.upper()]["server_ip"], use_XSERVERS(),
                            lambda x: x.ip)
    if not server:
        print(f"[ERROR] No server found for {tariff=}")
        await notif_to_admins(f"[ERROR] No server found for {tariff=}")
        await state.clear()
        return None
    await state.update_data(tariff=tariff, server=server)
    if tariff == "promo":
        await handle_free_period_confirmation(callback, state)
        return None
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚫ ShadowSocks", callback_data="free_period_protocol_shadowsocks"),
             InlineKeyboardButton(text="🔵 VLESS", callback_data="free_period_protocol_vless")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")],
        ]
    )
    await callback.message.edit_text(
        text=f"📡 Теперь выберите протокол подключения\n\n‼ В последнее время в работе ShadowSocks замечены перебои!!!",
        reply_markup=keyboard
    )
    return None

@router.callback_query(F.data.startswith("free_period_protocol_"))
async def handle_key_payment_key_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    protocol = callback.data.split("_")[3]
    inbound: Inbound = trusted_search(protocol, data["server"].inbounds, lambda x: x.protocol.lower())
    if not inbound:
        print(f"[ERROR] No inbound found for {data['tariff']=} {protocol=}")
        await notif_to_admins(f"[ERROR] No inbound found for {data['tariff']=} {protocol=}")
    await state.update_data(protocol=protocol, tariff=data['tariff'], inbound=inbound, server=data["server"])
    await handle_free_period_confirmation(callback, state)
    return None

@router.callback_query(F.data == "get_free_period_confirmation")
async def handle_free_period_confirmation(callback: CallbackQuery, state: FSMContext):
    await asyncio.sleep(1)
    data = await state.get_data()
    user = await UsersDatabase.get_user_by(tg_id=str(callback.from_user.id))
    dat = date.today() + timedelta(days=FREE_PERIOD_DURATION[data["tariff"].upper()])
    user.PaymentDate = dat
    user.tariff = data["tariff"].upper()
    user.PaymentSum = use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][data["tariff"].upper()]["coast"]
    epoch = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0) - timedelta(seconds=time.timezone)
    server = data["server"]
    delta = timedelta(hours=15) if time.timezone == 0 else timedelta(hours=20)
    expiry_time = int((datetime(dat.year, dat.month, dat.day) - epoch + delta).total_seconds() * 1000)
    if data["tariff"] == "full":
        inb: Inbound = data["inbound"]
        limit_ip = 5
    elif data["tariff"] == "promo":
        inb: Inbound = trusted_search("vless", server.inbounds, lambda x: x.protocol.lower())
        limit_ip = 2
    xclient: XClient = await inb.add_xclient(email=user.userTG.replace("@", ""), tgId=callback.from_user.id,
                                            totalBytes=500 * 1024 ** 3, expiryTime=expiry_time, limitIp=limit_ip)
    client = await ClientsDatabase.create_client(xclient=xclient)
    user.clients.append(client.pk_id)
    await UsersDatabase.update_user(user)
    total_gb = xclient.totalGB / 1024 ** 3
    answer = f"""✅ Готово! Ваши данные для подключения:
🌐 <b>Сервер</b>: {server.name}
🏳 <b>Локация</b>: {server.location}
📡 <b>Протокол подключения</b>: VLESS
⚡ <b>Скорость сети на сервере</b>: 100 МБ/c
⏹ <b>Ограничение</b>: {total_gb}GB
🔑 <b>Ключ</b>: <blockquote><code>{client.key}</code></blockquote>"""
    await callback.message.answer(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)
    return None


