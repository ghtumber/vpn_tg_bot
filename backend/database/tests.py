import json
from os import getenv
from dotenv import load_dotenv
import aiohttp

load_dotenv()
DB_TOKEN = getenv("DB_TOKEN")


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


async def update_user(user: dict, change: dict) -> str:
    """
    change accepts dict formed like this: {"field_to_change": new_value}
    !!! new_value need to be in accepted datatype
    !!! field_to_change need to fully equal field you need to change
    """
    for field, value in change.items():
        user[field] = value
    async with aiohttp.ClientSession() as session:
        response = await session.patch(
            f"https://api.baserow.io/api/database/rows/table/375433/{user['id']}/?user_field_names=true",
            headers={
                f"Authorization": f"Token {DB_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "userID": user["userID"],
                "userTG": user["userTG"],
                "keyID": user["keyID"],
                "key": user["key"],
                "keyLimit": user["keyLimit"],
                "PaymentSum": user["PaymentSum"]
            }
        )
        text = await response.text()
        if response.status == 200:
            print(f"###UPDATED USER###\nCHANGED: {change}\nUPDATED: {text}\n#########")
            return text
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

