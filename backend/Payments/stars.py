import asyncio

from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F

from backend.models import User
from backend.database.users import UsersDatabase
from frontend.replys import NEW_PRE_PAYMENT_ADMIN_REPLY, BALANCE_TOPUP_USER_REPLY
from globals import ADMINS

router = Router()

@router.pre_checkout_query()
async def process_pre_checkout(event: PreCheckoutQuery):
    await event.answer(True)
    for adm in ADMINS:
        print(f"[INFO] TRYING TO SEND !!!PreCheckout!!! MESSAGE TO ADMIN {adm}")
        await event.bot.send_message(chat_id=adm, text=NEW_PRE_PAYMENT_ADMIN_REPLY(name=event.from_user.username, currency=event.currency, sum=event.total_amount))

@router.message(F.successful_payment)
async def handle_xtr_payment(message: Message):
    payment = message.successful_payment
    user: User = await UsersDatabase.get_user_by(ID=str(message.from_user.id))
    if user:
        summ = payment.total_amount
        user = await UsersDatabase.update_user(user, change={"moneyBalance": user.moneyBalance + float(summ)})
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👤 Меню", callback_data="to_menu")]])
        await message.answer(text=BALANCE_TOPUP_USER_REPLY(user, summ), kb=kb)
    await asyncio.sleep(2)

    # await message.bot.refund_star_payment(message.from_user.id, payment.telegram_payment_charge_id)

class XTRPayments:
    @staticmethod
    async def send_invoice(message: Message, title: str, description: str, price: int, payload: str):
        await message.answer_invoice(
            title=title,
            description=description,
            payload=payload,
            currency="XTR",
            prices = [
                LabeledPrice(label="💳 Пополнить баланс", amount=price)
            ]
        )

