import json
from dataclasses import dataclass
import aiohttp
from aiogram.types import Message
from backend.models import User, OutlineClient, XClient
from datetime import date, timedelta, datetime
from globals import DONATPAY_API_KEY
from frontend.replys import AWAIT_DONAT_FETCH

@dataclass
class Donation:
    name: str
    comment: str
    sum: float

class DonatPAYHandler:
    API_KEY = DONATPAY_API_KEY
    LAST_REQUEST_TIME = datetime(day=1, month=1, year=2000, hour=0, minute=0, second=1)

    @classmethod
    async def check_availability(cls, message: Message):
        now = datetime.now()
        if (now - cls.LAST_REQUEST_TIME) < timedelta(minutes=1):
            await message.answer(text=AWAIT_DONAT_FETCH(user=message.from_user.username))
            return False
        cls.LAST_REQUEST_TIME = now
        return True

    @classmethod
    async def get_notifications(cls, message: Message) -> list[Donation]:
        if cls.check_availability(message=message):
            async with aiohttp.ClientSession() as session:
                response = await session.get(
                    f"https://donatepay.ru/api/v1/notifications/?access_token={cls.API_KEY}&limit=100&type=donation&view=0",
                )
                text = await response.text()
                obj = json.loads(text)
                if obj['status'] == 'success':
                    res = []
                    for notif in obj['data']:
                        res.append(Donation(name=notif["vars"]["name"], comment=notif["vars"]["comment"], sum=float(notif["vars"]["sum"])))
                    return res
                else:
                    raise Exception(f"##########\nException: Get donat notifications request ERROR!\n{text}\n##########")


    @classmethod
    async def get_transactions(cls, message: Message) -> list[Donation]:
        if cls.check_availability(message=message):
            async with aiohttp.ClientSession() as session:
                response = await session.get(
                    f"https://donatepay.ru/api/v1/transactions/?access_token={cls.API_KEY}&limit=100&type=donation&status=success",
                )
                text = await response.text()
                obj = json.loads(text)
                if obj['status'] == 'success':
                    res = []
                    for notif in obj['data']:
                        res.append(
                            Donation(name=notif["what"], comment=notif["comment"], sum=float(notif["sum"])))
                    return res
                else:
                    raise Exception(f"##########\nException: Get donat notifications request ERROR!\n{text}\n##########")

    @staticmethod
    def form_link(user: User) -> str:
        if user.userID and user.userTG:
            to_pay = 1
            if user.PaymentSum:
                to_pay = user.PaymentSum
            return f"https://new.donatepay.ru/@proxym1ty?message={user.userID}&name={user.userTG[1:]}&amount={to_pay}"
        else:
            raise Exception(f"[EXCEPTION] Not valid user in link forming\n{user=}")