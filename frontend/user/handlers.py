import asyncio
import re
import time
from datetime import date, datetime, timedelta

from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from frontend.user.balance_top_up import router as balance_top_up_router
from frontend.user.key_payment import router as key_payment_router
from frontend.user.free_period import router as free_period_router

from backend.database.clients import ClientsDatabase
from backend.models import User, XClient, Client
from backend.xapi.servers import XServer, Inbound
from frontend.replys import *
from backend.database.users import UsersDatabase
from globals import add_months, MENU_KEYBOARD_MARKUP, use_XSERVERS, \
    check_server_availability, trusted_search

router = Router()
router.include_router(balance_top_up_router)
router.include_router(key_payment_router)
router.include_router(free_period_router)

class RegistrationNoNickname(StatesGroup):
    nickname = State()


@router.callback_query(F.data == "regain_user_access")
async def handle_regain_user_access(callback: CallbackQuery):
    await asyncio.sleep(0.5)
    user: User = await UsersDatabase.get_user_by(tg_id=str(callback.from_user.id))
    if (user.PaymentDate - date.today()) <= timedelta(days=0):
        if user.moneyBalance < user.PaymentSum:
            await callback.message.answer(text="❌ Недостаточно <b>средств</b> на балансе.", reply_markup=MENU_KEYBOARD_MARKUP)
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup_user_balance")]
            ])
            await callback.message.answer(text="💰 <b>Пополните</b> баланс.", reply_markup=kb)
            return 0
        user.change("moneyBalance", user.moneyBalance - user.PaymentSum)
        new_date = add_months(user.PaymentDate, 1)
        epoch = datetime(year=1970, month=1, day=1, hour=0, minute=0, second=0) - timedelta(seconds=time.timezone)
        delta = timedelta(hours=14) if time.timezone == 0 else timedelta(hours=19)
        expiry_time = (datetime(new_date.year, new_date.month, new_date.day) - epoch + delta).total_seconds() * 1000
        for client_pk in user.clients:
            client: Client = await ClientsDatabase.get_client(client_row_id=client_pk)
            xclient: XClient = await client.server.get_xclient(client=client)
            xclient.enable = True
            inb: Inbound = trusted_search(xclient.protocol, use_XSERVERS(), lambda x: x.protocol)
            if inb:
                xclient.expiryTime = int(expiry_time)
                xclient.enable = True
                await inb.update_xclient(xclient)
                await inb.reset_client_traffic(xclient.for_api())
        user.change("PaymentDate", new_date)
        print(f"handle_regain_user_access() {user.userTG=} {use_XSERVERS()=}")
        await UsersDatabase.update_user(user)
        await callback.message.answer(text=PAYMENT_SUCCESS(user), reply_markup=MENU_KEYBOARD_MARKUP)
    await callback.answer("")
    return 0


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
async def handle_registration(callback: CallbackQuery, state: FSMContext):
    await asyncio.sleep(2)
    who_invited = callback.data.split("_")[2]
    if who_invited != "None":
        who_invited = int(who_invited)
    else:
        who_invited = None
    u = await UsersDatabase.get_user_by(tg_id=str(callback.from_user.id))
    if not u:
        if callback.from_user.username:
            user = User(userID=callback.from_user.id, userTG=f"@{callback.from_user.username}", PaymentSum=0, clients=[],
                        PaymentDate=None, who_invited=who_invited, referBonus=0, moneyBalance=0, tariff="None", paying=True)
            u = await UsersDatabase.create_user(user)
            await callback.message.answer(f"✅ Аккаунт создан!\n\n🔓 Доступ к меню открыт!", reply_markup=MENU_KEYBOARD_MARKUP)
        else:
            await callback.message.edit_text(f"✏ Для корректной работы бота нужен <b>username</b>!\n🤔Как к вам обращатся?\n(можно использовать только латинский алфавит)")
            await state.set_state(RegistrationNoNickname.nickname)
            await state.update_data(who_invited=who_invited)
    await callback.answer(text='')
    return None


@router.message(RegistrationNoNickname.nickname)
async def handle_registration_nickname(message: Message, state: FSMContext):
    if not re.fullmatch("[A-Za-z0-9_]+", message.text):
        await message.answer("❌ Nickname должен состоять только из <b>латиницы и символа '_'</b>.")
        return 0
    data = await state.get_data()
    user = User(userID=message.from_user.id, userTG=f"{message.text}", PaymentSum=0, PaymentDate=None,
                who_invited=data["who_invited"], referBonus=0, moneyBalance=0, tariff="None", paying=True)
    u = await UsersDatabase.create_user(user)
    await state.clear()
    await message.answer(f"✅ Аккаунт создан!\n\n🔓 Доступ к меню открыт!", reply_markup=MENU_KEYBOARD_MARKUP)
    return None


@router.callback_query(F.data == "view_user_clients")
async def handle_view_user_clients(callback: CallbackQuery):
    await asyncio.sleep(1)
    user = await UsersDatabase.get_user_by(tg_id=str(callback.from_user.id))
    clients = [await ClientsDatabase.get_client(client_row_id=cri) for cri in user.clients]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕Добавить соединение", callback_data="user_buy_key")],
        [InlineKeyboardButton(text="↩ Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text=CLIENTS_LIST_REPLY(username=user.userTG, clients=clients), reply_markup=keyboard)
    return 0


@router.message(Command(re.compile(r"client_[0-9]+")))
async def handle_client_info(message: Message, state: FSMContext):
    client_db_id = int(message.text.split("_")[1])
    client: Client = await ClientsDatabase.get_client(client_row_id=client_db_id)
    print(f"{client=}")
    if await check_server_availability(message=message, client=client):
        xclient: XClient = await client.server.get_xclient(client=client)
        print(f"{xclient=}")
        sub_key = xclient.get_link()
        epoch = datetime.utcfromtimestamp(0)
        expriryDate = epoch + timedelta(milliseconds=xclient.expiryTime)
    else:
        return None
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Использование", callback_data=f"xclient_vpn_usage_{client_db_id}")],
        [InlineKeyboardButton(text="↩ Назад", callback_data="view_user_clients")]
    ])
    await message.answer(text=CLIENT_INFO_REPLY(client_enable=xclient.enable, sub_key=sub_key, key=xclient.key,
                                           server_ip=xclient.get_server_ip(), ip_limit=xclient.limitIp,
                                           expiry_date=expriryDate.strftime('%A %d.%m.%Y')), reply_markup=keyboard)
    return 0


@router.callback_query(F.data.startswith("xclient_vpn_usage_"))
async def handle_xclient_vpn_usage(callback: CallbackQuery):
    """
    :param callback: needs to contain client db_id in data
    """
    client_db_id = int(callback.data.split("_")[3])
    client: Client = await ClientsDatabase.get_client(client_row_id=client_db_id)
    if type(client.server) is XServer:
        server: XServer = client.server
    else:
        await check_server_availability(callback=callback, client=client)
        return 0
    keyInfo = await server.get_client_traffics(uuid=client.uuid)
    traffic = keyInfo["up"] + keyInfo["down"]
    progress = round(traffic / keyInfo["total"], 2)
    traffic_info = {"keyInfo": keyInfo, "traffic": traffic, "progress": progress}
    answer = f"""
📈 <b>Использование VPN</b> за этот месяц:
<b>{round(traffic / 1024**3, 2)}GB</b>/<b>{keyInfo["total"] // 1024**3}GB</b>
[{"".join("☁" for i in range(int(progress * 10)))}{"".join("✦" for i in range(10 - int(progress * 10)))}]
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩ Назад", callback_data="view_user_clients")]
    ])
    await callback.answer(text='')
    await callback.message.edit_text(text=answer, reply_markup=keyboard)
    return 0


@router.callback_query(F.data == "update_clients_subId")
async def handle_update_client_subId(callback: CallbackQuery):
    subId = callback.from_user.username.replace("_", "")
    user: User = await UsersDatabase.get_user_by(tg_id=str(callback.from_user.id))
    clients = []
    for client_id in user.clients:
        client = await ClientsDatabase.get_client(client_row_id=client_id)
        if await check_server_availability(callback=callback, client=client):
            clients.append(await client.server.get_xclient(client=client))
        else:
            return 0
    if clients[0].subId == subId:
        await callback.answer("😐 Имя уже совпадает")
        return None
    else:
        for xclient in clients:
            inbound: Inbound = list(filter(lambda inb: inb.protocol.lower() == xclient.protocol.lower(), xclient.server.inbounds))[0]
            xclient.subId = subId
            await inbound.update_xclient(xclient=xclient)

        await callback.answer("✅ Обновлено успешно!")
    return None





