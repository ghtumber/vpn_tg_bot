import re
from datetime import date
from calendar import monthrange
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from backend.models import User
from frontend.replys import *
from backend.outline.managers import SERVERS
from backend.database.users import UsersDatabase

router = Router()


class Registration(StatesGroup):
    key = State()
    payment_date = State()
    payment_sum = State()


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, monthrange(year, month)[1])
    return date(year, month, day)


@router.callback_query(F.data == "user_registration")
async def handle_reg(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='')
    user_resp = await UsersDatabase.get_user_by(TG="@"+callback.from_user.username)
    if user_resp:
        await callback.message.answer(text="Вы уже зарегистрированы 😎\n\nСкоро бот заработает на полную 🔥")
    else:
        await callback.message.answer(REGISTRATION_FSM_REPLY)
        await state.set_state(Registration.key)


@router.message(Registration.key)
async def handle_reg_payment_date(message: Message, state: FSMContext):
    await state.update_data(key=message.text)
    await state.set_state(Registration.payment_date)
    await message.answer("Также отправьте <b>последнюю дату вашей оплаты</b> в ответ на это сообщение.\n\n‼В сообщении укажите дату в формате <b>ДД.ММ.ГГГГ</b>.")


@router.message(Registration.payment_date)
async def handle_reg_payment_sum(message: Message, state: FSMContext):
    if not re.fullmatch(r'[0-9][0-9].[0-9][0-9].[2-9][0-9][2-9][4-9]', r''.join(message.text.strip())):
        await message.answer(text="❌ Неверный <b>формат</b> даты.\n\n‼ В сообщении укажите дату в формате <b>ДД.ММ.ГГГГ</b>.")
        return 0
    PD_mes = message.text.strip().split(".")
    payment_date = date(int(PD_mes[2]), int(PD_mes[1]), int(PD_mes[0]))
    await state.update_data(payment_date=payment_date)
    await state.set_state(Registration.payment_sum)
    await message.answer("Отлично! Теперь отправьте сумму вашей месячной оплаты в ответ на это сообщение.\n\n‼ В сообщении укажите только число.\np.s. Все данные проверяются админами 😉")


@router.message(Registration.payment_sum)
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


@router.callback_query(F.data == "vpn_usage")
async def handle_vpn_usage(callback: CallbackQuery):
    await callback.answer(text='')
    user = await UsersDatabase.get_user_by(ID=str(callback.from_user.id))
    server = [s for s in SERVERS if s.name == user.serverName][0]
    keyInfo = server.get_key_info(key_id=str(user.keyID))
    progress = round(keyInfo.used_bytes / keyInfo.data_limit, 2)
    answer = f"""
📈 <b>Использование VPN</b> за этот месяц:
<b>{round(keyInfo.used_bytes / 1000**3, 2)}GB</b>/<b>{keyInfo.data_limit // 1000**3}GB</b>
[{"".join("☁" for i in range(int(progress * 10)))}{"".join("✦" for i in range(10 - int(progress * 10)))}]
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩ Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text=answer, reply_markup=keyboard)


@router.callback_query(F.data == "view_user_key")
async def handle_vpn_usage(callback: CallbackQuery):
    await callback.answer(text='')
    user = await UsersDatabase.get_user_by(ID=str(callback.from_user.id))
    answer = f"""
🔑 <b>Твой ключ</b>:
<pre><code>{user.key}</code></pre>
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩ Назад", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text=answer, reply_markup=keyboard)



