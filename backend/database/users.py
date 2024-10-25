import json
from os import getenv
import aiohttp
from backend.models import User


class UsersDatabase:
    DB_TOKEN = getenv("DB_TOKEN")

    @classmethod
    async def get_user_by(cls, ID: str = "", TG: str = "", KEY: str = "") -> int | User:
        if ID:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'userID', 'type': 'equal', 'value': str(ID)}]}
        elif TG:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'userTG', 'type': 'equal', 'value': str(TG)}]}
        elif KEY:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'key', 'type': 'equal', 'value': str(KEY)}]}
        else:
            print(f"##########\nException: No data passed to get request!\n##########")
            return 0
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://api.baserow.io/api/database/rows/table/375433/?user_field_names=true&filters={json.dumps(filters)}",
                headers={
                    "Authorization": f"Token {cls.DB_TOKEN}"
                }
            )
            text = await response.text()
            u = json.loads(text)
            if response.status == 200 and len(u["results"]) > 0:
                u = u["results"][0]
                return User(id=int(u["id"]), userID=int(u["userID"]), userTG=u["userTG"], keyID=int(u["keyID"]), key=u["key"], keyLimit=float(u["keyLimit"]), PaymentSum=int(u["PaymentSum"]))
            else:
                print(f"##########\nException: Get request ERROR!\n{text}\n##########")
                return 0

    @classmethod
    async def create_user(cls, user: User) -> User | Exception:
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                "https://api.baserow.io/api/database/rows/table/375433/?user_field_names=true",
                headers={
                    "Authorization": f"Token {cls.DB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "userID": user.userID,
                    "userTG": user.userTG,
                    "keyID": user.keyID,
                    "key": user.key,
                    "keyLimit": user.keyLimit,
                    "PaymentSum": user.PaymentSum
                }
            )
            text = await response.text()
            if response.status == 200:
                print(f"###UPDATED USER###\nCREATED: {text}\n#########")
                u = json.loads(text)
                return User(id=u["id"], userID=u["userID"], userTG=u["userTG"], keyID=u["keyID"], key=u["key"], keyLimit=u["keyLimit"], PaymentSum=u["PaymentSum"])
            else:
                return Exception(f"Create request ERROR!\n{text}")

    @classmethod
    async def update_user(cls, user: User, change: dict) -> User | Exception:
        """
        change accepts dict formed like this: {"field_to_change": new_value}
        !!! new_value need to be in accepted datatype
        !!! field_to_change need to fully equal field you need to change
        """
        for field, value in change.items():
            user.change(field=field, new_value=value)
        async with aiohttp.ClientSession() as session:
            response = await session.patch(
                f"https://api.baserow.io/api/database/rows/table/375433/{user.id}/?user_field_names=true",
                headers={
                    f"Authorization": f"Token {cls.DB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "userID": str(user.userID),
                    "userTG": str(user.userTG),
                    "keyID": str(user.keyID),
                    "key": str(user.key),
                    "keyLimit": str(user.keyLimit),
                    "PaymentSum": str(user.PaymentSum)
                }
            )
            text = await response.text()
            if response.status == 200:
                print(f"###UPDATED USER###\nCHANGED: {change}\nUPDATED: {text}\n#########")
                u = json.loads(text)
                return User(id=u["id"], userID=u["userID"], userTG=u["userTG"], keyID=u["keyID"], key=u["key"], keyLimit=u["keyLimit"],
                            PaymentSum=u["PaymentSum"])
            else:
                return Exception(f"!!! Update request ERROR!\n{text}")

    @classmethod
    async def delete_user(cls, user: User):
        async with aiohttp.ClientSession() as session:
            response = await session.delete(
                f"https://api.baserow.io/api/database/rows/table/375433/{user.id}/",
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
