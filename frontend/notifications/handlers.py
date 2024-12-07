from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


from frontend.admin.handlers import CANCEL_KB, handle_cancel
from backend.models import User
from frontend.notifications.models import GlobalNotification
from datetime import date
from frontend.replys import *
from backend.database.users import UsersDatabase
from globals import DEBUG


router = Router()

class GlobalNotificationState(StatesGroup):
    text = State()
    confirmation = State()

@router.callback_query(F.data == "admin_notifications_menu")
async def handle_admin_notifications_menu(callback: CallbackQuery):
    await callback.answer(text='')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛑 Глобальное оповещение", callback_data="admin_send_global_notification")]
    ])
    await callback.message.answer("📩 Доступные действия:", reply_markup=keyboard)
    await callback.message.delete()


@router.callback_query(F.data == "admin_send_global_notification")
async def handle_admin_send_global_notification_state_1(callback: CallbackQuery, state: FSMContext):
    await callback.answer(text='')
    await callback.message.answer("❔ Какой текст оповещения?", reply_markup=CANCEL_KB)
    await callback.message.delete()
    await state.set_state(GlobalNotificationState.text)


@router.message(GlobalNotificationState.text)
async def handle_admin_send_global_notification_state_2(message: Message, state: FSMContext):
    await state.update_data(text=message.text.strip())
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Отмена"),],
        ],
        resize_keyboard=True
    )
    await message.answer("💯 Отправляем?", reply_markup=keyboard)
    await state.set_state(GlobalNotificationState.confirmation)

@router.message(GlobalNotificationState.confirmation)
async def handle_admin_send_global_notification_state_2(message: Message, state: FSMContext):
    if message.text.strip() == "✅ Да":
        await state.update_data(confirmation=True)
        data = await state.get_data()
        all_users = await UsersDatabase.get_all_users()
        if DEBUG:
            all_users = [User(userID=902448626, userTG="@M1rtexFAde", id=0, keyID=0, key="ss://123", PaymentSum=120, PaymentDate=date(2024, 12, 20), keyLimit=999, serverName="LOL"),
                      User(userID=863746464, userTG="@Anxious666Japan", id=0, keyID=0, key="ss://123", PaymentSum=120, PaymentDate=date(2024, 12, 20), keyLimit=999, serverName="LOL")]
        notif = GlobalNotification(text=data["text"], users_to=all_users, callback_to=message.from_user.id)
        success = await notif.send()
        await state.clear()
