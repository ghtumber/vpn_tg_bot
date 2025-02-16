import datetime
import time

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.DonatPAY.donations import DonatPAYHandler
from backend.xapi.servers import XServer, Inbound
from frontend.admin.handlers import CANCEL_KB, handle_cancel
from backend.models import User, XClient
from frontend.notifications.models import GlobalNotification
from datetime import date, timedelta
from frontend.replys import *
from backend.database.users import UsersDatabase
from globals import DEBUG, bot, XSERVERS, add_months

router = Router()
period_checker_scheduler = AsyncIOScheduler()


class GlobalNotificationState(StatesGroup):
    text = State()
    confirmation = State()


async def payment_system():
    now = datetime.datetime.now()
    all_users, count = await UsersDatabase.get_all_users(page=1, size=1)
    if (count // 100) < 1:
        rng = 1
    elif (count % 100) == 0:
        rng = (count // 100)
    else:
        rng = (count // 100) + 1
    for page in range(1, rng + 1):
        all_users, _ = await UsersDatabase.get_all_users(page=page, size=100)
        for user in all_users:
            server: XServer = None
            for svr in XSERVERS:
                if svr.name == user.serverName:
                    server = svr
                    user.xclient = await svr.get_client_info(identifier=user.uuid)
                    break
            if user.xclient:
                # print(f"[INFO] {user.xclient=} {datetime.datetime.fromtimestamp(user.xclient.expiryTime // 1000)}")
                # Payment system
                if timedelta(hours=24) > (datetime.datetime.fromtimestamp(user.xclient.expiryTime // 1000) - now) >= timedelta(minutes=0):
                    data = await user.xclient.get_server_and_inbound(XSERVERS)
                    inbound: Inbound = data["inbound"]
                    if user.moneyBalance >= user.PaymentSum:
                        print(f"[PAYMENT PROCEED] {user.userTG} ({user.moneyBalance}) - {user.PaymentSum}")
                        user.change("moneyBalance", user.moneyBalance - user.PaymentSum)
                        new_date = add_months(user.PaymentDate, 1)
                        epoch = datetime.datetime.utcfromtimestamp(0)
                        await inbound.update_client(user.xclient, {
                            "expiryTime": (datetime.datetime(new_date.year, new_date.month, new_date.day) - epoch).total_seconds() * 1000})
                        await inbound.reset_client_traffic(user.xclient.for_api())
                        user.change("PaymentDate", new_date)
                        await user.xclient.get_key(XSERVERS)
                        await UsersDatabase.update_user(user)
                        await bot.send_message(chat_id=user.userID, text=PAYMENT_SUCCESS(user))
                        continue
                    else:
                        user.xclient.enable = False
                        await user.xclient.get_key(XSERVERS)
                        await inbound.update_client(user.xclient, {"enable": False})
                        await UsersDatabase.update_user(user)
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💰 Пополнить баланс", url=DonatPAYHandler.form_link(user=user))]
                        ])
                        await bot.send_message(chat_id=user.userID, text=NO_MONEY_LEFT(user), reply_markup=kb)
                        continue

async def check_period():
    # if DEBUG:
    #     print(f"check_period() execution in DEBUG mode")
    #     dat = date(day=1, month=1, year=2025)
    #     xclient = XClient(uuid="9d439b90-8e77-4e49-b845-f1afe8dd67a7", email="OK_now", enable=True, expiryTime=1734256800744, reset=0, tgId=5475897905, totalGB=644245094400)
    #     all_users = [User(id=1, userID=5475897905, userTG="@M1rtex", PaymentSum=200, PaymentDate=dat, serverName="XServer@94.159.100.60", xclient=xclient, serverType="XSERVER", Protocol="VLESS", lastPaymentDate=dat, moneyBalance=0)]
    now = datetime.datetime.now()
    all_users, count = await UsersDatabase.get_all_users(page=1, size=1)
    if (count // 100) < 1:
        rng = 1
    elif (count % 100) == 0:
        rng = (count // 100)
    else:
        rng = (count // 100) + 1
    for page in range(1, rng + 1):
        all_users, _ = await UsersDatabase.get_all_users(page=page, size=100)
        for user in all_users:
            server: XServer = None
            for svr in XSERVERS:
                if svr.name == user.serverName:
                    server = svr
                    user.xclient = await svr.get_client_info(identifier=user.uuid)
                    user_traffic = await svr.get_client_traffics(uuid=user.xclient.uuid)
                    user_traffic = user_traffic["up"] + user_traffic["down"]
                    break
            if user.xclient:
                if timedelta(days=3) > (datetime.datetime.fromtimestamp(user.xclient.expiryTime // 1000) - now) >= timedelta(days=-2):
                    if user.xclient.enable:
                        if user.moneyBalance < user.PaymentSum:
                            await bot.send_message(chat_id=user.userID, text=MONEY_ENDING(user))
                            continue
                    else:
                        if user.moneyBalance < user.PaymentSum:
                            kb = InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text="💳 Пополнить баланс", url=DonatPAYHandler.form_link(user=user))]
                            ])
                            await bot.send_message(chat_id=user.userID, text=PERIOD_ENDED(user), reply_markup=kb)
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
        all_users = []
        _, count = await UsersDatabase.get_all_users(page=1)
        if (count // 100) < 1:
            rng = 1
        elif (count % 100) == 0:
            rng = (count // 100)
        else:
            rng = (count // 100) + 1
        for page in range(1, rng + 1):
            alls, _ = await UsersDatabase.get_all_users(page=page, size=100)
            all_users.extend(alls)
        # if DEBUG:
        #     all_users = [User(userID=902448626, userTG="@M1rtexFAde", id=0, keyID=0, key="ss://123", PaymentSum=120, PaymentDate=date(2024, 12, 31), keyLimit=999, serverName="LOL"),
        #               User(userID=863746464, userTG="@Anxious666Japan", id=0, keyID=0, key="ss://123", PaymentSum=120, PaymentDate=date(2024, 12, 31), keyLimit=999, serverName="LOL")]
        notif = GlobalNotification(text=data["text"], users_to=all_users, callback_to=message.from_user.id)
        success = await notif.send()
        await state.clear()

tz = timedelta(seconds=time.timezone).total_seconds() // 3600
delta = -5 if time.timezone == 0 else 0
period_checker_scheduler.add_job(func=check_period, day_of_week='mon-sun', trigger="cron", hour=int(17+tz+delta), minute=30)
print(f"check_period will be in {int(17+tz+delta)}")
period_checker_scheduler.add_job(func=payment_system, day_of_week='mon-sun', trigger="cron", hour=int(23+tz+delta), minute=15)
print(f"payment_system will be in {int(23+tz+delta)}")
#period_checker_scheduler.add_job(func=payment_system, trigger="interval", minutes=1)
