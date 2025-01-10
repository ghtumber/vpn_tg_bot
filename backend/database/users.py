import json
from os import getenv
import aiohttp
from backend.models import User, OutlineClient, XClient
from datetime import date
from globals import DB_TOKEN, XSERVERS


class UsersDatabase:
    DB_TOKEN = DB_TOKEN
    SERVER_TYPES = {"None": 2412169, "Outline": 2354398, "XSERVER": 2354397}
    PROTOCOL_TYPES = {"ShadowSocks": 2365214, "VLESS": 2365215, "None": 2412170}
    @classmethod
    async def get_all_users(cls, size=100, page=1) -> None | list[User]:
        """Don't use if you can!!!"""
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://api.baserow.io/api/database/rows/table/375433/?user_field_names=true&size={size}&page={page}",
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
                    if type(result["LastPaymentDate"]) is str:
                        LPD = result["LastPaymentDate"].split("-")
                        lastPaymentDate = date(int(LPD[0]), int(LPD[1]), int(LPD[2]))
                    else:
                        lastPaymentDate = None
                    xClient = None
                    outlineClient = None
                    if result["serverType"]["value"] == "Outline":
                        outlineClient = OutlineClient(keyID=int(result["keyID"]), key=result["key"], keyLimit=float(result["keyLimit"]))
                    elif result["serverType"]["value"] == "XSERVER":
                        for server in XSERVERS:
                            if server.name == result["serverName"]:
                                break
                            server = None
                        xClient = server.get_client_info(result["uuid"])
                    res.append(User(id=int(result["id"]), userID=int(result["userID"]), userTG=result["userTG"], outline_client=outlineClient,
                            xclient=xClient, PaymentSum=int(result["PaymentSum"]), PaymentDate=PaymentDate,
                            serverName=result["serverName"], uuid=result["uuid"], serverType=result["serverType"]["value"],
                            lastPaymentDate=lastPaymentDate, Protocol=result["Protocol"]["value"], moneyBalance=result["moneyBalance"]))
                return res
            else:
                print(f"##########\nException: Get all users request ERROR!\n{text}\n##########")
                return None

    @classmethod
    async def get_user_by(cls, ID: str = "", TG: str = "", KEY: str = "", UUID: str = "") -> None | User:
        if ID:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'userID', 'type': 'equal', 'value': str(ID)}]}
        elif TG:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'userTG', 'type': 'equal', 'value': str(TG)}]}
        elif KEY:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'key', 'type': 'equal', 'value': str(KEY)}]}
        elif UUID:
            filters = {'filter_type': 'AND',
                       'filters': [{'field': 'uuid', 'type': 'equal', 'value': str(UUID)}]}
        else:
            print(f"##########\nException: No data passed to get request!\n##########")
            return None
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
                if type(u["PaymentDate"]) is str:
                    PD = u["PaymentDate"].split("-")
                    PaymentDate = date(int(PD[0]), int(PD[1]), int(PD[2]))
                else:
                    PaymentDate = None
                if type(u["LastPaymentDate"]) is str:
                    LPD = u["LastPaymentDate"].split("-")
                    lastPaymentDate = date(int(LPD[0]), int(LPD[1]), int(LPD[2]))
                else:
                    lastPaymentDate = None
                UUID = u["uuid"] if u["uuid"] else 0
                serverType = u["serverType"]
                outlineClient = None
                xClient = None
                if serverType["value"] == "Outline":
                    outlineClient = OutlineClient(keyID=int(u["keyID"]), key=u["key"], keyLimit=float(u["keyLimit"]))
                elif serverType["value"] == "XSERVER":
                    for server in XSERVERS:
                        if server.name == u["serverName"]:
                            break
                        server = None
                    if u["Protocol"]["value"] == "ShadowSocks":
                        xClient: XClient = await server.get_client_info(u["userTG"][1:])
                    elif u["Protocol"]["value"] == "VLESS":
                        xClient: XClient = await server.get_client_info(UUID)
                return User(id=int(u["id"]), userID=int(u["userID"]), userTG=u["userTG"], outline_client=outlineClient, xclient=xClient, PaymentSum=int(u["PaymentSum"]),
                            PaymentDate=PaymentDate, serverName=u["serverName"], uuid=UUID, lastPaymentDate=lastPaymentDate, serverType=serverType["value"],
                            Protocol=u["Protocol"]["value"], moneyBalance=float(u["moneyBalance"]))
            else:
                print(f"##########\nException: Get request ERROR! {ID=} {TG=}\n{UUID=}\n{KEY=}\n{text}\n##########")
                return None

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
                    "keyID": None,
                    "key": "",
                    "keyLimit": None,
                    "PaymentSum": int(user.PaymentSum),
                    "PaymentDate": None,
                    "LastPaymentDate": None,
                    "serverName": str(user.serverName),
                    "Protocol": 2412170,
                    "serverType": 2412169,
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
    async def update_user(cls, user: User, change: dict) -> User | Exception:
        """
        change accepts dict formed like this: {"field_to_change": new_value}
        !!! new_value need to be in accepted datatype
        !!! field_to_change need to fully equal field you need to change
        """
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
                f"https://api.baserow.io/api/database/rows/table/375433/{user.id}/?user_field_names=true",
                headers={
                    f"Authorization": f"Token {cls.DB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "userID": user.userID,
                    "userTG": user.userTG,
                    "keyID": user.outline_client.keyID if user.outline_client else "",
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
                return Exception(f"!!! Update request ERROR!\n{text}")

    @classmethod
    async def delete_user(cls, user: User) -> User | Exception:
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
