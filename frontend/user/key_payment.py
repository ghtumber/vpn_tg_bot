import time
from datetime import timedelta, datetime, date

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from backend.database.clients import ClientsDatabase
from backend.database.users import UsersDatabase
from backend.models import User, XClient, Client
from globals import Available_Tariffs, use_Available_Tariffs, use_XSERVERS, use_PREFERRED_PAYMENT_SETTINGS, \
    MENU_KEYBOARD_MARKUP, add_months, Tariffs, trusted_search, notif_to_admins, MENU_INLINE_KEYBOARD_MARKUP

router = Router()


class KeyPayment(StatesGroup):
    tariff = State()
    configuration_type = State()
    server = State()
    keyType = State()
    confirmation = State()


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
👉 <b>🗿PROMO</b> подходит для тех, кто редко использует VPN (к примеру для просмотра Youtube)
- <b>1</b> ключ в комплекте
- <b>100 МБ/с</b> канал на сервере (ограничены вашим соединением)
- подключение <b>до 2 устройств одновременно</b>
- обычная тех. поддержка
- возможны подвисания
👉 <b>😎FULL</b> подходит для активных пользователей
- <b>2</b> ключа в комплекте
- <b>10 Gbit/s</b> канал на сервере (ограничены вашим соединением)
- подключение <b>до 5 устройств одновременно</b>
- приоритетная тех. поддержка
- стабильный uptime 99%
"""
    await callback.message.answer(answer, reply_markup=keyboard)
    await state.set_state(KeyPayment.tariff)

@router.callback_query(F.data.startswith("buy_key_tariff_"))
async def handle_buy_key(callback: CallbackQuery, state: FSMContext):
    tariff = callback.data.split("_")[3]
    if tariff.lower() == Tariffs.FULL.lower():
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚡ Авто подбор", callback_data="key_configuration_type_auto"), InlineKeyboardButton(text="⚙ Ручная настройка", callback_data="key_configuration_type_manual")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")],
            ], resize_keyboard=True
        )
        await state.update_data(tariff=tariff)
        await callback.message.edit_text(f"🔑 Выбор конфигурации VPN-ключа\nВыбери способ настройки:", reply_markup=keyboard)
        await state.set_state(KeyPayment.configuration_type)
    elif tariff == Tariffs.PROMO:
        svr = trusted_search(use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][tariff]["server_ip"], use_XSERVERS(), lambda x: x.ip)
        if not svr:
            await callback.message.answer(
                text="😓 Ошибка сервера. Не найден сервер.\n🙏 Если вы видите это сообщение, пожалуйста, напишите в поддержку.",
                reply_markup=MENU_KEYBOARD_MARKUP
            )
            await state.clear()
            return None
        await state.update_data(server=svr, keyType=use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][tariff]["keyType"],
                                tariff=tariff, configuration_type="Auto")
        await state.set_state(KeyPayment.keyType)
        await handle_key_payment_key_type(callback=callback, state=state)
    await callback.answer("")
    return None

@router.callback_query(F.data.startswith("key_configuration_type_"))
async def handle_key_payment_server_type(callback: CallbackQuery, state: FSMContext):
    configuration_type = callback.data.split("_")[3]
    data = await state.get_data()
    tariff = data["tariff"]
    if configuration_type == "auto":
        svr = None
        for server in use_XSERVERS():
            if server.name == use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][tariff]["server_name"]:
                svr = server
                break
        if not svr:
            await callback.message.edit_text(text="😓 Ошибка сервера. Не найден сервер.\n🙏 Если вы видите это сообщение, пожалуйста, напишите в поддержку.",
                                             reply_markup=InlineKeyboardMarkup(
                                                    inline_keyboard=[[InlineKeyboardButton(text="👤 Меню", callback_data="menu")]]))
            return 0
        await state.update_data(server=svr, keyType=use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][tariff]["keyType"],
                                tariff=tariff, configuration_type=configuration_type)
        await state.set_state(KeyPayment.keyType)
        await handle_key_payment_key_type(callback=callback, state=state)
    elif configuration_type == "manual":
        svr = trusted_search(use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][tariff]["server_ip"], use_XSERVERS(), lambda x: x.ip)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚫ ShadowSocks", callback_data="key_type_shadowsocks"), InlineKeyboardButton(text="🔵 VLESS", callback_data="key_type_vless")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")],
            ]
        )
        await state.set_state(KeyPayment.keyType)
        await state.update_data(tariff=tariff, server=svr, configuration_type=configuration_type)
        await callback.message.edit_text(text=f"📡 Теперь выберите протокол подключения\n\n‼ В последнее время в работе ShadowSocks замечены перебои!!!", reply_markup=keyboard)
    return None


@router.callback_query(F.data.startswith("key_type_"))
async def handle_key_payment_key_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    protocol = ""
    if data["configuration_type"] == "Manual":
        protocol = callback.data.split("_")[2]
    else:
        protocol = data["keyType"]
    answer = f"""✅ Отлично. Выбрано:
⚡ <b>Тариф</b>: {data["tariff"]}
🏳 <b>Локация</b>: {data['server'].location}
📡 <b>Протокол подключения</b>: {protocol} 
⚡ <b>Скорость сети на сервере</b>: {'10 Gbit/s' if data["tariff"] == Tariffs.FULL else '100 МБ/c'}
💸 <b>Стоимость</b>: {use_PREFERRED_PAYMENT_SETTINGS()['Tariffs'][data['tariff']]['coast']}🌟XTR/мес
🧾 Для продолжения <b>подтвердите</b> оплату
"""
    await state.set_state(KeyPayment.confirmation)
    await state.update_data(configuration_type=data["configuration_type"], server=data["server"], keyType=protocol, tariff=data["tariff"])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✔ Подтвердить", callback_data="key_confirmation")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")],
        ], resize_keyboard=True
    )
    await callback.message.edit_text(text=answer, reply_markup=keyboard)
    return 0

@router.callback_query(F.data == "key_confirmation")
async def handle_key_payment_confirmation(callback: CallbackQuery, state: FSMContext):
    user: User = await UsersDatabase.get_user_by(tg_id=str(callback.from_user.id))
    data = await state.get_data()
    coast = use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"][data["tariff"]]["coast"]
    if user.moneyBalance < coast:
        await callback.message.edit_text(text="❌ Недостаточно <b>средств</b> на балансе.")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup_user_balance")],
            [InlineKeyboardButton(text="👤 Menu", callback_data="menu")],
        ])
        await callback.message.edit_text(text="💰 <b>Пополните</b> баланс.", reply_markup=kb)
        await state.clear()
        return None
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
    inb = trusted_search(data["keyType"].lower(), data["server"].inbounds, lambda x: x.protocol)
    if inb:
        limit_ip = 2 if data["tariff"] == Tariffs.PROMO else 5
        delta = timedelta(hours=15) if time.timezone == 0 else timedelta(hours=20)
        expiry_time = (datetime(dat.year, dat.month, dat.day) - epoch + delta).total_seconds() * 1000
        xclient: XClient = await inb.add_xclient(email=callback.from_user.username, tgId=callback.from_user.id,
                                                totalBytes=500 * 1024 ** 3, expiryTime=expiry_time, limitIp=limit_ip)
        user.Protocol = data["keyType"]
        user.serverType = "XSERVER"
        user.uuid = xclient.uuid
        total_gb = xclient.totalGB / 1024 ** 3
        key = xclient.get_link()
        client: Client = await ClientsDatabase.create_client(xclient)
        user.clients.append(client.pk_id)
    else:
        await callback.message.edit_text("🛑 Возникла критическая ошибка!\n🙏 Пожалуйста, напишите об этом в поддержку.\n😢 Заранее просим прощения(((",
                             reply_markup=MENU_INLINE_KEYBOARD_MARKUP)
        print(f"[ERROR] INBOUND not found in handle_key_payment_confirmation() {data['server'].name=}")
        await notif_to_admins(f"[ERROR] INBOUND not found in handle_key_payment_confirmation() {data['server'].name=}")
        await state.clear()
        await callback.answer("")
        return None
    user: User = await UsersDatabase.update_user(user=user, change={})
    answer = f"""✅ Готово! Ваши данные для подключения:
⚡ <b>Тариф</b>: {data["tariff"]}
🌐 <b>Сервер</b>: {data["server"].name}
🏳 <b>Локация</b>: {data["server"].location}
📡 <b>Протокол подключения</b>: {data["keyType"]}
⚡ <b>Скорость сети на сервере</b>: {'10 Gbit/s' if data["tariff"] == "MAX" else '100 МБ/c'}
⏹ <b>Ограничение</b>: {total_gb}GB
🔑 <b>Ключ</b>: <blockquote><code>{key}</code></blockquote>
    """
    await state.clear()
    await callback.message.edit_text(text=answer, reply_markup=MENU_KEYBOARD_MARKUP)
    await callback.answer("")
    return None