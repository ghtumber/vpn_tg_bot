import asyncio
import json
import re
from os import getenv
from types import NoneType

from aiogram.client.session import aiohttp


DB_TEST_SERVER_TYPES = {"None": 2447416, "Outline": 2447415, "XSERVER": 2447414}
DB_TEST_PROTOCOL_TYPES = {"ShadowSocks": 2447417, "VLESS": 2447418, "None": 2447419}
DEBUG = True
from random import randint
from uuid import uuid4
from datetime import timedelta, date



class User:
    def __init__(self, userID: int, userTG: str, PaymentSum: int, PaymentDate: date, lastPaymentDate: date, serverName: str, serverType: str,
                 Protocol: str, moneyBalance: float, xclient = None, outline_client = None, id: int = None, uuid: str = ""):
        self.id = id
        self.uuid = uuid
        self.moneyBalance = moneyBalance
        if type(lastPaymentDate) is date or type(lastPaymentDate) is NoneType:
            self.lastPaymentDate = lastPaymentDate
        else:
            raise Exception(f"lastPaymentDate is not a [datetime.date or None] {type(lastPaymentDate)}")
        self.Protocol = Protocol
        self.serverType = serverType
        self.userID = userID
        if re.fullmatch(r'@[a-zA-Z0-9_]+', r''.join(userTG)):
            self.userTG = userTG
        else:
            raise Exception("UserTG Regular Error")
        self.outline_client = outline_client
        self.xclient = xclient
        self.PaymentSum = PaymentSum
        if type(PaymentDate) is date or type(PaymentDate) is NoneType:
            self.PaymentDate = PaymentDate
        else:
            raise Exception(f"PaymentDate is not a [datetime.date or None] {type(PaymentDate)}")
        self.serverName = serverName

    def change(self, field, new_value):
        match field:
            case "lastPaymentDate":
                self.lastPaymentDate = new_value
                return
            case "moneyBalance":
                print(f"[WARNING] {self.userTG} moneyBalance changed from {self.moneyBalance} to {new_value}")
                self.moneyBalance = new_value
                return
            case "Protocol":
                self.Protocol = new_value
                return
            case "configuration_type":
                self.serverType = new_value
                return
            case "PaymentSum":
                self.PaymentSum = new_value
                return
            case "PaymentDate":
                self.PaymentDate = new_value
                return
            case "serverName":
                self.serverName = new_value
                return
            case "keyId":
                self.outline_client.keyID = new_value
                return
            case "key":
                if self.outline_client:
                    self.outline_client.key = new_value
                else:
                    self.xclient.key = new_value
                return
        raise Exception(f"Non changeable field {field} or etc...")


    def __str__(self):
        value = f"""
{self.userID=}
{self.userTG=}
{self.uuid=}
{self.serverName=}
{self.serverType=}
"""
        return value



class UsersDatabase:
    if DEBUG:
        DB_TOKEN = ""
        TABLE_ID = ""
        SERVER_TYPES = DB_TEST_SERVER_TYPES
        PROTOCOL_TYPES = DB_TEST_PROTOCOL_TYPES
        print(f"[WARNING] Using TEST DB data!!!")


    @classmethod
    async def create_user(cls, user: User) -> User | Exception:
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/?user_field_names=true",
                headers={
                    "Authorization": f"Token {cls.DB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "userID": user.userID,
                    "userTG": user.userTG,
                    "Enabled": user.xclient.enable if user.xclient else True,
                    "key": "",
                    "keyLimit": None,
                    "PaymentSum": int(user.PaymentSum),
                    "PaymentDate": None,
                    "LastPaymentDate": None,
                    "serverName": str(user.serverName),
                    "Protocol": user.Protocol,
                    "serverType": user.serverType,
                    "uuid": user.uuid,
                    "moneyBalance": 0
                }
            )
            text = await response.text()
            if response.status == 200:
                print(f"###CREATED USER###\nCREATED: {text}\n#########")
                u = json.loads(text)
                PaymentDate = None
                if u["PaymentDate"]:
                    PD = u["PaymentDate"].split("-")
                    PaymentDate = date(int(PD[0]), int(PD[1]), int(PD[2]))
                lastPaymentDate = None
                if u["LastPaymentDate"]:
                    LPD = u["LastPaymentDate"].split("-")
                    lastPaymentDate = date(int(LPD[0]), int(LPD[1]), int(LPD[2]))
                return User(id=user.id, userID=int(u["userID"]), userTG=u["userTG"], PaymentSum=int(u["PaymentSum"]), PaymentDate=PaymentDate, serverName=u["serverName"],
                            lastPaymentDate=lastPaymentDate, serverType=user.serverType, Protocol=u["Protocol"], moneyBalance=0)
            else:
                raise Exception(f"Create request ERROR!\n{text}")

    @classmethod
    async def update_user(cls, user: User, change: dict = None) -> User | Exception:
        """
        change accepts dict formed like this: {"field_to_change": new_value}
        !!! new_value need to be in accepted datatype
        !!! field_to_change need to fully equal field you need to change
        """
        if change:
            for field, value in change.items():
                user.change(field=field, new_value=value)
        if user.outline_client:
            key = user.outline_client.key
            keyLimit = user.outline_client.keyLimit
        elif user.xclient:
            key = user.xclient.key
            keyLimit = user.xclient.totalGB
        else:
            key = ""
            keyLimit = None
        PaymentDate = None
        LastPaymentDate = None
        if user.PaymentDate:
            PaymentDate = str(user.PaymentDate.strftime("%Y-%m-%d"))
        if user.lastPaymentDate:
            LastPaymentDate = str(user.lastPaymentDate.strftime("%Y-%m-%d"))
        async with aiohttp.ClientSession() as session:
            response = await session.patch(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/{user.id}/?user_field_names=true",
                headers={
                    f"Authorization": f"Token {cls.DB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "userID": user.userID,
                    "userTG": user.userTG,
                    "Enabled": user.xclient.enable,
                    "key": key,
                    "keyLimit": keyLimit,
                    "PaymentSum": int(user.PaymentSum),
                    "PaymentDate": PaymentDate,
                    "LastPaymentDate": LastPaymentDate,
                    "serverName": str(user.serverName),
                    "Protocol": cls.PROTOCOL_TYPES[user.Protocol],
                    "serverType": cls.SERVER_TYPES[user.serverType],
                    "uuid": user.uuid,
                    "moneyBalance": user.moneyBalance
                }
            )
            text = await response.text()
            if response.status == 200:
                print(f"###UPDATED USER###\nCHANGED: {change}\nUPDATED: {text}\n#########")
                u = json.loads(text)
                PaymentDate = None
                if u["PaymentDate"]:
                    PD = u["PaymentDate"].split("-")
                    PaymentDate = date(int(PD[0]), int(PD[1]), int(PD[2]))
                lastPaymentDate = None
                if u["LastPaymentDate"]:
                    LPD = u["LastPaymentDate"].split("-")
                    lastPaymentDate = date(int(LPD[0]), int(LPD[1]), int(LPD[2]))
                return User(id=user.id, userID=int(u["userID"]), userTG=u["userTG"], outline_client=user.outline_client,
                            xclient=user.xclient, PaymentSum=int(u["PaymentSum"]), moneyBalance=u["moneyBalance"],
                            PaymentDate=PaymentDate, serverName=u["serverName"], uuid=user.uuid,
                            lastPaymentDate=lastPaymentDate, serverType=user.serverType, Protocol=u["Protocol"])
            else:
                raise Exception(f"!!! Update request ERROR!\n{text}")

    @classmethod
    async def delete_user(cls, user: User) -> User | Exception:
        async with aiohttp.ClientSession() as session:
            response = await session.delete(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/{user.id}/",
                headers={
                    f"Authorization": f"Token {cls.DB_TOKEN}"
                }
            )
            text = response.status
            if response.status == 204:
                print(f"###DELETED USER###\nUSER: {user}\n#########")
                return user
            else:
                return Exception(f"Delete request ERROR!\n{text}")




async def fill_db(n=100):
    for _ in range(n):
        await asyncio.sleep(2)
        i = randint(1000000000, 9999999999)
        u = User(userID=i, userTG=f"@M1rtex_test_{i}", moneyBalance=randint(0, 100), Protocol=DB_TEST_PROTOCOL_TYPES["VLESS"], serverType=DB_TEST_SERVER_TYPES["XSERVER"],
                 serverName="TESTING@94.159.100.60", PaymentSum=randint(1, 100), lastPaymentDate=date(year=1970, month=1, day=1), xclient=None,
                 uuid=str(uuid4()), PaymentDate=(date.today() + timedelta(days=30)))
        user = await UsersDatabase.create_user(user=u)
        if user:
            print(f"User: {user.userTG} created!")
            continue
        else:
            print(f"Error on {user.userTG}")
            break


if __name__ == "__main__":
    # asyncio.run(fill_db())
    ...