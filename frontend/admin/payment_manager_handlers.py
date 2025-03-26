import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from frontend.replys import ADMIN_PAYMENTS_MANAGER_REPLY
from globals import ADMINS, use_BASIC_VPN_COST, use_PREFERRED_PAYMENT_SETTINGS, MENU_KEYBOARD_MARKUP, \
    edit_preferred_payment_settings, DONATION_WIDGET_URL, use_XSERVERS, use_Available_Tariffs, All_Tariffs

router = Router()

CANCEL_KB = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="❌ Отмена")]
], resize_keyboard=True)

# -----------------FSM-------------------
class ServerChangingState(StatesGroup):
    tariff = State()
    callback = State()
    server = State()
    confirmation = State()

class ProtocolChangingState(StatesGroup):
    tariff = State()
    callback = State()
    protocol = State()
    confirmation = State()

class CoastChangingState(StatesGroup):
    tariff = State()
    callback = State()
    coast = State()
    confirmation = State()

class TariffManagingState(StatesGroup):
    callback = State()
    func = State()
    to_edit = State()
    confirmation = State()



# PREFERRED_PAYMENT_SETTINGS = {"server_name": "XServer@94.159.100.60", "keyType": "VLESS"}

@router.callback_query((F.data == "admin_manage_payment_defaults") & (F.message.from_user.id in ADMINS))
async def handle_admin_manage_payment_defaults(callback: CallbackQuery):
    await callback.answer("")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👀 Виджет с донатами", url=DONATION_WIDGET_URL)],
            [InlineKeyboardButton(text="🌐 Изменить сервер", callback_data="admin_change_payment_defaults_server")],
            [InlineKeyboardButton(text="⛓ Изменить протокол", callback_data="admin_change_payment_defaults_protocol")],
            [InlineKeyboardButton(text="🏧 Изменить цену", callback_data="admin_change_payment_defaults_coast")],
            [InlineKeyboardButton(text="➰ Tariffs Manager", callback_data="admin_change_payment_defaults_tariffs")],
        ]
    )
    tars = use_PREFERRED_PAYMENT_SETTINGS()["Tariffs"]
    servers = ", ".join([tars[t_k]["server_name"] for t_k in tars.keys()])
    protocols = ", ".join([tars[t_k]["keyType"] for t_k in tars.keys()])
    coasts = ", ".join([str(tars[t_k]["coast"]) for t_k in tars.keys()])
    await callback.message.answer(ADMIN_PAYMENTS_MANAGER_REPLY(default_coast=coasts, default_server=servers, Available_Tariffs=use_Available_Tariffs(),
                                                               default_protocol=protocols), reply_markup=keyboard)



#-------------------------------------------Tariffs editing---------------------------------------------------------
@router.callback_query((F.data == "admin_change_payment_defaults_tariffs") & (F.message.from_user.id in ADMINS))
async def handle_admin_change_payment_defaults_tariffs(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    answer = "➡ Выбери действие:"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Включить", callback_data="admin_change_payment_defaults_tariffs_func_activate")],
            [InlineKeyboardButton(text="🟡 Отключить", callback_data="admin_change_payment_defaults_tariffs_func_deactivate")],
        ]
    )
    await callback.message.edit_text(answer, reply_markup=keyboard)
    await state.update_data(callback=callback)
    await state.set_state(TariffManagingState.func)


@router.callback_query(F.data.startswith("admin_change_payment_defaults_tariffs_func_"))
async def handle_admin_change_payment_defaults_tariffs_func(callback: CallbackQuery, state: FSMContext):
    type = callback.data.split("_")[6]
    kb_l = []
    if type == "activate":
        deact = [t for t in All_Tariffs if t not in use_Available_Tariffs()]
        answer = f"Сейчас отключено {len(All_Tariffs) - len(use_Available_Tariffs())}:"
        for e in deact:
            kb_l.append([InlineKeyboardButton(text=e, callback_data=f"admin_change_payment_defaults_tariffs_do_{type}_{e}")])
    elif type == "deactivate":
        answer = f"Сейчас активны {len(use_Available_Tariffs())}:"
        for e in use_Available_Tariffs():
            kb_l.append([InlineKeyboardButton(text=e, callback_data=f"admin_change_payment_defaults_tariffs_do_{type}_{e}")])
    kb_l.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_l, resize_keyboard=True)
    await state.update_data(func=type)
    await state.set_state(TariffManagingState.to_edit)
    await callback.message.edit_text(text=answer, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("admin_change_payment_defaults_tariffs_do_"))
async def handle_admin_change_payment_defaults_tariffs_do(callback: CallbackQuery, state: FSMContext):
    type, tariff = callback.data.split("_")[6], callback.data.split("_")[7]
    if type == "activate":
        answer = f"⚠ Тариф {tariff} будут активирован!"
    elif type == "deactivate":
        answer = f"⚠ Тариф {tariff} будет отключен!"

    kb_l = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="admin_change_payment_defaults_tariffs_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=kb_l, resize_keyboard=True)

    await state.update_data(to_edit=tariff)
    await state.set_state(TariffManagingState.confirmation)
    await callback.message.edit_text(text=answer, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "admin_change_payment_defaults_tariffs_confirm")
async def handle_admin_change_payment_defaults_tariffs_confirmation(callback: CallbackQuery, state: FSMContext):
    global edit_preferred_payment_settings
    data = await state.get_data()
    if data["func"] == "deactivate":
        new = use_PREFERRED_PAYMENT_SETTINGS()
        t = use_Available_Tariffs()
        t.remove(data['to_edit'])
        new["Available_Tariffs"] = t
        edit_preferred_payment_settings(new)
        answer = f"✅ Тариф {data['to_edit']} отключен!"
    elif data["func"] == "activate":
        new = use_PREFERRED_PAYMENT_SETTINGS()
        t = use_Available_Tariffs()
        t.append(data['to_edit'])
        new["Available_Tariffs"] = t
        edit_preferred_payment_settings(new)
        answer = f"✅ Тариф {data['to_edit']} активирован!"
    await state.clear()
    await callback.message.edit_text(text=answer)
    await asyncio.sleep(0.5)
    await handle_admin_manage_payment_defaults(callback=data["callback"])


#-------------------------------------------Server editing---------------------------------------------------------
@router.callback_query((F.data == "admin_change_payment_defaults_server") & (F.message.from_user.id in ADMINS))
async def handle_admin_change_payment_defaults_server(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    kb_l = []
    answer = f"Сейчас активны {len(use_Available_Tariffs())} тарифа(оф):"
    for e in use_Available_Tariffs():
        kb_l.append([InlineKeyboardButton(text=e, callback_data=f"admin_change_payment_defaults_server_{e}")])
    kb_l.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_l)
    await callback.message.answer(answer, reply_markup=kb)
    await state.update_data(callback=callback)
    await state.set_state(ServerChangingState.tariff)


@router.callback_query(F.data.startswith("admin_change_payment_defaults_server_"))
async def handle_admin_change_payment_defaults_server(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    tariff = callback.data.split("_")[5]
    answer = "🌐 Доступные сервера:"
    fs = filter(lambda x: x.tariff == tariff, use_XSERVERS())
    for server in fs:
        answer += f"\n🌍:{server.location} ɪᴘ: <code>{server.ip}</code>"
    answer += "\n\nВыбери IP нужного сервера."
    await callback.message.answer(answer, reply_markup=CANCEL_KB)
    await state.update_data(tariff=tariff)
    await state.set_state(ServerChangingState.server)


@router.message(ServerChangingState.server)
async def handle_admin_change_payment_defaults_server_ip(message: Message, state: FSMContext):
    try:
        if len(message.text.split(".")) == 4:
            server = [server for server in use_XSERVERS() if server.ip == message.text.strip()][0]
        else:
            raise IndexError
    except IndexError:
        await message.answer("Ошибка ❗\nВероятно такого сервера нет 😑")
        return 0

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)

    data = await state.get_data()
    tariff = data["tariff"]
    await state.set_state(ServerChangingState.confirmation)
    await message.answer(text=f"❔ Сохраняем изменения?\n {use_PREFERRED_PAYMENT_SETTINGS()['Tariffs'][tariff]['server_name']} -> {server.name}", reply_markup=kb, parse_mode="HTML")
    await state.update_data(server=server, tariff=tariff, callback=data["callback"])

@router.message(ServerChangingState.confirmation)
async def handle_admin_change_payment_defaults_server_confirmation(message: Message, state: FSMContext):
    global edit_preferred_payment_settings
    data = await state.get_data()
    new = dict(use_PREFERRED_PAYMENT_SETTINGS())
    tariff = data["tariff"]
    new["Tariffs"][tariff]["server_name"] = data["server"].name
    edit_preferred_payment_settings(new=new)
    await state.clear()
    await message.answer(text="✅ Изменения сохранены", reply_markup=MENU_KEYBOARD_MARKUP)
    await asyncio.sleep(0.5)
    await handle_admin_manage_payment_defaults(callback=data["callback"])


#-------------------------------------------Protocol editing---------------------------------------------------------
@router.callback_query((F.data == "admin_change_payment_defaults_protocol") & (F.message.from_user.id in ADMINS))
async def handle_admin_change_payment_defaults_server(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    kb_l = []
    answer = f"Сейчас активны {len(use_Available_Tariffs())} тарифа(оф):"
    for e in use_Available_Tariffs():
        kb_l.append([InlineKeyboardButton(text=e, callback_data=f"admin_change_payment_defaults_protocol_{e}")])
    kb_l.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_l)
    await callback.message.answer(answer, reply_markup=kb)
    await state.update_data(callback=callback)
    await state.set_state(ProtocolChangingState.tariff)

@router.callback_query(F.data.startswith("admin_change_payment_defaults_protocol_"))
async def handle_admin_change_payment_defaults_protocol(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    tariff = callback.data.split("_")[5]

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🟣 VLESS"), KeyboardButton(text="⚫ ShadowSocks")],
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)

    answer = "⛓ Доступные варианты:\n 1) VLESS\n 2) ShadowSocks"
    await callback.message.answer(answer, reply_markup=kb)
    await state.update_data(tariff=tariff)
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

    data = await state.get_data()
    tariff = data["tariff"]
    await state.set_state(ProtocolChangingState.confirmation)
    await message.answer(text=f"❔ Сохраняем изменения?\n {use_PREFERRED_PAYMENT_SETTINGS()['Tariffs'][tariff]['keyType']} -> {protocol}", reply_markup=kb, parse_mode="HTML")
    await state.update_data(protocol=protocol, tariff=tariff, callback=data["callback"])

@router.message(ProtocolChangingState.confirmation)
async def handle_admin_change_payment_defaults_protocol_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    new = dict(use_PREFERRED_PAYMENT_SETTINGS())
    tariff = data["tariff"]
    new["Tariffs"][tariff]["keyType"] = data["protocol"]
    edit_preferred_payment_settings(new=new)
    await state.clear()
    await message.answer(text="✅ Изменения сохранены", reply_markup=MENU_KEYBOARD_MARKUP)
    await asyncio.sleep(0.5)
    await handle_admin_manage_payment_defaults(callback=data["callback"])



#-------------------------------------------Coast editing---------------------------------------------------------
@router.callback_query((F.data == "admin_change_payment_defaults_coast") & (F.message.from_user.id in ADMINS))
async def handle_admin_change_payment_defaults_server(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    kb_l = []
    answer = f"Сейчас активны {len(use_Available_Tariffs())} тарифа(оф):"
    for e in use_Available_Tariffs():
        kb_l.append([InlineKeyboardButton(text=e, callback_data=f"admin_change_payment_defaults_coast_{e}")])
    kb_l.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_l)
    await callback.message.answer(answer, reply_markup=kb)
    await state.update_data(callback=callback)
    await state.set_state(ProtocolChangingState.tariff)

@router.callback_query(F.data.startswith("admin_change_payment_defaults_coast_"))
async def admin_change_payment_defaults_coast(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    tariff = callback.data.split("_")[5]

    answer = "💸 Какая новая цена? (ex. 150)"
    await callback.message.answer(answer, reply_markup=CANCEL_KB)
    await state.update_data(tariff=tariff)
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

    data = await state.get_data()
    tariff = data["tariff"]
    await state.set_state(CoastChangingState.confirmation)
    await message.answer(text=f"❔ Сохраняем изменения?\n {use_PREFERRED_PAYMENT_SETTINGS()['Tariffs'][tariff]['coast']} руб. -> {coast} руб.", reply_markup=kb, parse_mode="HTML")
    await state.update_data(coast=coast, tariff=tariff, callback=data["callback"])

@router.message(CoastChangingState.confirmation)
async def handle_admin_change_payment_defaults_protocol_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    new = dict(use_PREFERRED_PAYMENT_SETTINGS())
    tariff = data["tariff"]
    new["Tariffs"][tariff]["coast"] = data["coast"]
    edit_preferred_payment_settings(new=new)
    await state.clear()
    await message.answer(text="✅ Изменения сохранены", reply_markup=MENU_KEYBOARD_MARKUP)
    await asyncio.sleep(0.5)
    await handle_admin_manage_payment_defaults(callback=data["callback"])