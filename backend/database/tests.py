import asyncio
import json
import re
from os import getenv
from dotenv import load_dotenv
import aiohttp

load_dotenv()
DB_TOKEN = getenv("DB_TOKEN")


class User:
    def __init__(self, id: int, userID: int, userTG: str, keyID: int, key: str, keyLimit: int, PaymentSum: int):
        self.id = id
        self.userID = userID
        self.userTG = userTG if re.fullmatch(r'@[a-zA-Z0-9]{5,}', r''.join(userTG)) else Exception("UserTG Regular Error")
        self.keyID = keyID
        self.key = key if key.startswith("ss:/") else Exception("UserTG Regular Error")
        self.keyLimit = keyLimit
        self.PaymentSum = PaymentSum

    def change(self, field, new_value):
        if field == "userID":
            self.userID = new_value
        if field == "userTG":
            self.userTG = new_value
        if field == "keyID":
            self.keyID = new_value
        if field == "key":
            self.key = new_value
        if field == "keyLimit":
            self.keyLimit = new_value
        if field == "PaymentSum":
            self.PaymentSum = new_value

    def __str__(self):
        value = f"""
{self.userID=}
{self.userTG=}
{self.keyID=}
{self.key=}
{self.keyLimit=}
{self.PaymentSum=}
"""
        return value


async def get_user_by(ID: str = "", TG: str = "", KEY: str = "") -> str:
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
        return Exception("No data passed to get request!")
    async with aiohttp.ClientSession() as session:
        response = await session.get(
            f"https://api.baserow.io/api/database/rows/table/375433/?user_field_names=true&filters={json.dumps(filters)}",
            headers={
                "Authorization": f"Token {DB_TOKEN}"
            }
        )
        text = await response.text()
        if response.status == 200:
            return text
        else:
            return Exception(f"Get request ERROR!\n{text}")


async def create_user(userID: int, userTG: str, keyID: int, key: str, keyLimit: float, PaymentSum: int) -> str:
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            "https://api.baserow.io/api/database/rows/table/375433/?user_field_names=true",
            headers={
                "Authorization": f"Token {DB_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "userID": userID,
                "userTG": userTG,
                "keyID": keyID,
                "key": key,
                "keyLimit": keyLimit,
                "PaymentSum": PaymentSum
            }
        )
        text = await response.text()
        if response.status == 200:
            print(f"###UPDATED USER###\nCREATED: {text}\n#########")
            return text
        else:
            return Exception(f"Create request ERROR!\n{text}")


async def update_user(user: User, change: dict) -> User | Exception:
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
                f"Authorization": f"Token {DB_TOKEN}",
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
            return User(id=u["id"], userID=u["userID"], userTG=u["userTG"], keyID=u["keyID"], key=u["key"], keyLimit=u["keyLimit"], PaymentSum=u["PaymentSum"])
        else:
            return Exception(f"Update request ERROR!\n{text}")


async def delete_user(user: dict):
    async with aiohttp.ClientSession() as session:
        response = await session.delete(
            f"https://api.baserow.io/api/database/rows/table/375433/{user['id']}/",
            headers={
                f"Authorization": f"Token {DB_TOKEN}"
            }
        )
        text = response.status
        if response.status == 204:
            print(f"###DELETED USER###\nUSER: {user}\n#########")
            return text
        else:
            return Exception(f"Delete request ERROR!\n{text}")


# user = {"id": 15, "userID": 0, "userTG": "TestTG", "keyID": 30, "key": "ss://LOLtest", "keyLimit": 0.0, "PaymentSum": 100}

# GET: get_user_by(ID: str, KEY: str, TG: str) ID or TG or KEY

# CREATE: create_user(userID=1234567, userTG="TestTG", keyID=30, key="ss://LOLtest", keyLimit=0.0, PaymentSum=100)

# UPDATE: update_user(user=user, change={"keyID": 35})

# DELETE: delete_user(user)


async def main():
    user = User(id=16, userID=1234567, userTG='TestTG', keyID=30, key='ss://LOLtest', keyLimit=0, PaymentSum=100)
    res = await update_user(user=user, change={"keyID": 35})
    d = json.loads(res)
    print(d)


asyncio.run(main())
