from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from backend.Payments.stars import XTRPayments
from backend.database.users import UsersDatabase
from backend.models import User
from frontend.replys import BALANCE_TOPUP_BY_RELIABLE_USER
from globals import use_Available_Tariffs, use_PREFERRED_PAYMENT_SETTINGS, NAME_PAYMENT_DATA, SPB_PAYMENT_DATA, \
    CARD_PAYMENT_DATA, ADMINS, MENU_KEYBOARD_MARKUP

router = Router()


class CustomTopUp(StatesGroup):
    summ = State()
    callback = State()

class ReliableTopUp(StatesGroup):
    comment = State()


@router.callback_query(F.data == "topup_user_balance")
async def handle_topup_user_balance(callback: CallbackQuery):
    await callback.answer("")
    user = await UsersDatabase.get_user_by(tg_id=str(callback.from_user.id))
    kb = []
    for i in use_Available_Tariffs():
        summ = int(use_PREFERRED_PAYMENT_SETTINGS()['Tariffs'][i]['coast'])
        kb.append([InlineKeyboardButton(text=f"🌟 Пополнить на {summ}", callback_data=f"get_topup_invoice_{summ}")])
    kb.append([InlineKeyboardButton(text=f"🌟 Пополнить на другое количество", callback_data=f"topup_for_custom_sum")])
    if user.reliability:
        kb.append([InlineKeyboardButton(text=f"🤙 Пополнить переводом", callback_data=f"topup_reliable_user")])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=kb
    )
    addition = "\n🤝 Вы доверенный пользователь\n😎 Доступно пополнение переводом" if user.reliability else ""
    await callback.message.answer(
        "💰 Пополнение баланса\n➖➖➖➖➖➖➖➖\n🌟 Пополнить баланс можно звёздами телеграм!\n💳 Оплата картой будет доступна в будущем..." + addition,
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("topup_reliable_user"))
async def handle_topup_reliable_user(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    user: User = await UsersDatabase.get_user_by(tg_id=str(callback.from_user.id))
    summ_to_pay = round((user.PaymentSum * use_PREFERRED_PAYMENT_SETTINGS()["XTR_exchange_rate"])/100, 2) * 100
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Перевёл", callback_data="reliable_user_transferred_topup")]
    ])
    await callback.message.edit_text(f"👤 На имя: {NAME_PAYMENT_DATA}\n📱 По СПБ: {SPB_PAYMENT_DATA}\n💳 По номеру карты: {CARD_PAYMENT_DATA}\n💵 Сумма: {summ_to_pay}руб",
                                     reply_markup=kb)


@router.callback_query(F.data.startswith("reliable_user_transferred_topup"))
async def handle_reliable_user_transferred_topup(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")]
        ]
    )
    await callback.message.edit_text(f"🧾 Укажи имя(от кого придут деньги) и сумму\n❤ Спасибо", reply_markup=keyboard)
    await state.set_state(ReliableTopUp.comment)

@router.message(ReliableTopUp.comment)
async def handle_topup_for_custom_sum_checkout(message: Message, state: FSMContext):
    comment = message.text.strip()
    user: User = await UsersDatabase.get_user_by(tg_id=str(message.from_user.id))
    for adm in ADMINS:
        await message.bot.send_message(chat_id=adm, text=BALANCE_TOPUP_BY_RELIABLE_USER(userTG=f"@{message.from_user.username}", userID=message.from_user.id, comment=comment, user=user))
    await message.answer("✅ Заявка составлена!\n⌚ Ожидайте пополнение.", reply_markup=MENU_KEYBOARD_MARKUP)

@router.callback_query(F.data.startswith("topup_for_custom_sum"))
async def handle_topup_for_custom_sum(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu")]
        ]
    )
    await callback.message.edit_text(f"🌟 Введите количество (числом)", reply_markup=keyboard)
    await state.set_state(CustomTopUp.summ)
    await state.update_data(callback=callback)

@router.message(CustomTopUp.summ)
async def handle_topup_for_custom_sum_checkout(message: Message, state: FSMContext):
    try:
        summ = int(message.text.strip())
    except TypeError:
        await message.answer(text="❌ Неверный <b>тип</b> данных.\n\n🌟 Введите количество <b>числом</b>!")
        return 0
    data = await state.get_data()
    await data["callback"].answer("✍(◔◡◔)")
    await state.clear()
    await message.answer("✅ Счёт готов!\n👉 Баланс пополнится сразу после оплаты!")
    await XTRPayments.send_invoice(message=message, title=f"Пополнение баланса на {summ} XTR",
                                   description="Пополнение баланса с помощью 🌟XTR", payload="stars_topup", price=summ)
    return 0


@router.callback_query(F.data.startswith("get_topup_invoice_"))
async def handle_topup_user_balance(callback: CallbackQuery):
    await callback.answer("")
    summ = int(callback.data.split("_")[3])
    await XTRPayments.send_invoice(message=callback.message, title=f"Пополнение баланса на {summ} XTR",
                                   description="Пополнение баланса с помощью ⭐XTR", payload="stars_topup", price=summ)
