import json
from typing import Tuple

import aiohttp

from backend.models import User
from datetime import date
from globals import DB_TOKEN, DEBUG, TEST_DB_TOKEN, TABLE_ID, TEST_TABLE_ID


class UsersDatabase:
    if DEBUG:
        DB_TOKEN = TEST_DB_TOKEN
        TABLE_ID = TEST_TABLE_ID
        print(f"[WARNING] Using TEST DB data!!!")
    else:
        DB_TOKEN = DB_TOKEN
        TABLE_ID = TABLE_ID

    @classmethod
    async def get_all_users(cls, size=100, page=1) -> None | Tuple[list[User], int]:
        """Don't use if you can!!! Returns  list[User], count_of_rows_in_DB"""
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/?user_field_names=true&size={size}&page={page}",
                headers={
                    "Authorization": f"Token {cls.DB_TOKEN}"
                }
            )
            text = await response.text()
            obj = json.loads(text)
            if response.status == 200 and len(obj["results"]) > 0:
                results = obj["results"]
                res = []
                for result in results:
                    if type(result["PaymentDate"]) is str:
                        PD = result["PaymentDate"].split("-")
                        PaymentDate = date(int(PD[0]), int(PD[1]), int(PD[2]))
                    else:
                        PaymentDate = None
                    res.append(User(userID=int(result["userID"]), userTG=result["userTG"], id=int(result["id"]),
                                    PaymentSum=int(result["PaymentSum"]), PaymentDate=PaymentDate, paying=bool(result["paying"]),
                                    who_invited=result["who_invited"], referBonus=result["referBonus"],
                                    moneyBalance=float(result["moneyBalance"]), tariff=result["tariff"],
                                    UserReliability=bool(result["UserReliability"]), clients=result["clients"]))
                return res, int(obj["count"])
            else:
                print(f"##########\nException: Get all users request ERROR!\n{text}\n##########")
                return None

    @classmethod
    async def get_user_by(cls, tg_id: str = "", tg: str = "", key: str = "", uuid: str = "") -> None | User:
        if tg_id:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'userID', 'type': 'equal', 'value': str(tg_id)}]}
        elif tg:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'userTG', 'type': 'equal', 'value': str(tg)}]}
        elif key:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'key', 'type': 'equal', 'value': str(key)}]}
        elif uuid:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'uuid', 'type': 'equal', 'value': str(uuid)}]}
        else:
            print(f"##########\nException: No data passed to get request!\n##########")
            return None
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/?user_field_names=true&filters={json.dumps(filters)}",
                headers={
                    "Authorization": f"Token {cls.DB_TOKEN}"
                }
            )
            text = await response.text()
            u = json.loads(text)
            if response.status == 200 and len(u["results"]) > 0:
                u = u["results"][0]
                if type(u["PaymentDate"]) is str:
                    PD = u["PaymentDate"].split("-")
                    PaymentDate = date(int(PD[0]), int(PD[1]), int(PD[2]))
                else:
                    PaymentDate = None
                clients = [c["id"] for c in u["clients"]]
                return User(userID=int(u["userID"]), userTG=u["userTG"], PaymentSum=int(u["PaymentSum"]),
                            PaymentDate=PaymentDate, who_invited=u["who_invited"], referBonus=u["referBonus"],
                            moneyBalance=float(u["moneyBalance"]), tariff=u["tariff"], clients=clients,
                            UserReliability=bool(u["UserReliability"]), id=int(u["id"]), paying=bool(u["paying"]))
            else:
                print(f"##########\nException: Get request ERROR! {tg_id=}\n{tg=}\n{uuid=}\n{key=}\n{text}\n##########")
                return None

    @classmethod
    async def get_all_referrals(cls, tg_id: int) -> None | list[dict]:
        """
        :param tg_id: Telegram ID of inviter
        :return: list of dicts typed: {"TG": str, "PaymentSum": int, "tariff": str}
        """
        if tg_id:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'who_invited', 'type': 'equal', 'value': int(tg_id)}]}
        else:
            print(f"########## get_all_referrals()\nException: No data passed to get request!\n##########")
            return None
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/?user_field_names=true&filters={json.dumps(filters)}",
                headers={
                    "Authorization": f"Token {cls.DB_TOKEN}"
                }
            )
            text = await response.text()
            u = json.loads(text)
            if response.status == 200 and len(u["results"]) > 0:
                results = u["results"]
                res = []
                for result in results:
                    res.append({"TG": result["userTG"], "tariff": result["tariff"], "PaymentSum": int(result["PaymentSum"])})
                return res
            else:
                print(f"########## get_all_referrals()\nException: Get request ERROR! {tg_id=}\n{text}\n##########")
                return None

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
                    "tariff": user.tariff,
                    "PaymentSum": int(user.PaymentSum),
                    "PaymentDate": None,
                    "moneyBalance": 0,
                    "who_invited": user.who_invited,
                    "referBonus": user.referBonus,
                    "UserReliability": user.reliability,
                    "paying": user.paying,
                    "clients": user.clients
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
                return User(userID=int(u["userID"]), userTG=u["userTG"], PaymentSum=int(u["PaymentSum"]),id=user.id,
                            PaymentDate=PaymentDate, who_invited=u["who_invited"], referBonus=u["referBonus"],
                            moneyBalance=0, tariff=u["tariff"], UserReliability=user.reliability, clients=u["clients"],
                            paying=bool(u["paying"]))
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
        PaymentDate = None
        if user.PaymentDate:
            PaymentDate = str(user.PaymentDate.strftime("%Y-%m-%d"))
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
                    "tariff": user.tariff,
                    "PaymentSum": int(user.PaymentSum),
                    "PaymentDate": PaymentDate,
                    "moneyBalance": user.moneyBalance,
                    "who_invited": user.who_invited,
                    "referBonus": user.referBonus,
                    "UserReliability": user.reliability,
                    "paying": user.paying,
                    "clients": user.clients,
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
                return User(userID=int(u["userID"]), userTG=u["userTG"], PaymentSum=int(u["PaymentSum"]),
                            PaymentDate=PaymentDate, who_invited=user.who_invited, referBonus=u["referBonus"],
                            moneyBalance=u["moneyBalance"], tariff=u["tariff"], UserReliability=user.reliability,
                            id=user.id, clients=u["clients"], paying=bool(u["paying"]))
            else:
                raise Exception(f"!!! Update user request ERROR!\n{text}")

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
                return Exception(f"Delete user request ERROR!\n{text}")
