import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler


from frontend.admin.handlers import CANCEL_KB, handle_cancel
from backend.models import User, XClient
from frontend.notifications.models import GlobalNotification
from datetime import date, timedelta
from frontend.replys import *
from backend.database.users import UsersDatabase
from globals import DEBUG, bot, XSERVERS

router = Router()
period_checker_scheduler = AsyncIOScheduler()


class GlobalNotificationState(StatesGroup):
    text = State()
    confirmation = State()

async def check_period():
    all_users = await UsersDatabase.get_all_users(size=3000)
    if DEBUG:
        print(f"check_period() execution in DEBUG mode")
        dat = date(day=1, month=1, year=2025)
        xclient = XClient(uuid="9d439b90-8e77-4e49-b845-f1afe8dd67a7", email="OK_now", enable=True, expiryTime=1734256800744, reset=0, tgId=5475897905, totalGB=644245094400)
        all_users = [User(id=1, userID=5475897905, userTG="@M1rtex", PaymentSum=200, PaymentDate=dat, serverName="XServer@94.159.100.60", xclient=xclient, serverType="XSERVER", Protocol="VLESS", lastPaymentDate=dat)]
    now = datetime.datetime.now()
    for user in all_users:
        for svr in XSERVERS:
            if svr.name == user.serverName:
                user.xclient = svr.get_client_info(uuid=user.uuid)
                user_traffic = await svr.get_client_traffics(uuid=user.xclient.uuid)
                user_traffic = user_traffic["up"] + user_traffic["down"]
                break
        if user.xclient:
            if timedelta(days=3) > (now - datetime.datetime.fromtimestamp(user.xclient.expiryTime // 1000)) >= timedelta(days=0):
                await bot.send_message(chat_id=user.userID, text=PAYD_PERIOD_ENDING(user))
                continue
            if (user.xclient.totalGB - user_traffic) < 5*1024**3:
                await bot.send_message(chat_id=user.userID, text=TRAFFICS_ENDING(user, user.xclient.totalGB - user_traffic))
                continue


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
        all_users = await UsersDatabase.get_all_users(size=3000)
        if DEBUG:
            all_users = [User(userID=902448626, userTG="@M1rtexFAde", id=0, keyID=0, key="ss://123", PaymentSum=120, PaymentDate=date(2024, 12, 31), keyLimit=999, serverName="LOL"),
                      User(userID=863746464, userTG="@Anxious666Japan", id=0, keyID=0, key="ss://123", PaymentSum=120, PaymentDate=date(2024, 12, 31), keyLimit=999, serverName="LOL")]
        notif = GlobalNotification(text=data["text"], users_to=all_users, callback_to=message.from_user.id)
        success = await notif.send()
        await state.clear()


# period_checker_scheduler.add_job(func=check_period, day_of_week='mon-sun', trigger="cron", hour=14, minute=30) #TODO: change to normal