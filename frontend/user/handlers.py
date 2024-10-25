from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from backend.models import User
from frontend.replys import *
from backend.outline.manager import OutlineManager
from backend.database.users import UsersDatabase

router = Router()


class Registration(StatesGroup):
    key = State()
    payment_sum = State()


@router.callback_query(F.data == "user_registration")
async def handel_reg(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='')
    user_resp = await UsersDatabase.get_user_by(TG="@"+callback.from_user.username)
    if user_resp != 0:
        await callback.message.answer(text="Вы уже зарегистрированы 😎\n\nСкоро бот заработает на полную 🔥")
    else:
        await callback.message.answer(REGISTRATION_FSM_REPLY)
        await state.set_state(Registration.key)


@router.message(Registration.key)
async def handle_reg_key(message: Message, state: FSMContext):
    await state.update_data(key=message.text)
    await state.set_state(Registration.payment_sum)
    await message.answer("Отлично! Теперь отправьте сумму вашей месячной оплаты в ответ на это сообщение.\n‼В сообщении укажите только число.")


@router.message(Registration.payment_sum)
async def complete_reg(message: Message, state: FSMContext):
    await state.update_data(payment_sum=message.text)
    data = await state.get_data()
    await state.clear()
    key = data["key"]
    key = key.split("?")[0]
    print(key)
    k = OutlineManager.get_key_info_by_key(key=key)
    if not k:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ В меню", callback_data="menu")]
            ]
        )
        await message.answer(f"Неверный ключ!", reply_markup=keyboard)
        return Exception("No key found")
    keyID = k.key_id
    keyLimit = k.data_limit
    userID = message.from_user.id
    userTG = "@" + message.from_user.username
    PaymentSum = data["payment_sum"]
    user = User(userID=userID, userTG=userTG, keyID=keyID, keyLimit=keyLimit, key=key, PaymentSum=PaymentSum)
    u = await UsersDatabase.create_user(user)
    # await message.answer(f"Юзер записан в БД: {u.id=} {u}")
    await message.answer(f"✅ Аккаунт активирован!\n\nСкоро бот заработает на полную 🔥")

