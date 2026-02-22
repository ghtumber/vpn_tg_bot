import json

import aiohttp
from typing import Tuple

from backend.models import XClient, Client
from globals import DB_TOKEN, DEBUG, CLIENTS_TABLE_ID, DB_PROTOCOL_TYPES, use_XSERVERS, notif_to_admins


class ClientsDatabase:
    if DEBUG:
        # DB_TOKEN = TEST_DB_TOKEN
        # TABLE_ID = TEST_TABLE_ID
        # SERVER_TYPES = DB_TEST_SERVER_TYPES
        # PROTOCOL_TYPES = DB_TEST_PROTOCOL_TYPES
        # print(f"[WARNING] Using TEST DB data!!!")
        ...
    PROTOCOL_TYPES = DB_PROTOCOL_TYPES
    DB_TOKEN = DB_TOKEN
    TABLE_ID = CLIENTS_TABLE_ID

    @classmethod
    async def get_all_clients(cls, size=100, page=1) -> None | Tuple[list[Client], int]:
        """Don't use if you can!!! Returns list[Client], count_of_rows"""
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
                    for server in use_XSERVERS():
                        if server.ip == result["server"]["value"]:
                            break
                        server = result["server"]["value"]
                    if type(server) == str:
                        print(f"[WARNING] server for client {result['subId']} not found!!! IP: {server}")
                    res.append(Client(pk_id=int(result["pk_id"]), subId=result["subId"], uuid=result["uuid"],
                                      protocol=result["protocol"]["value"], key=result["key"],
                                      server=server))
                return res, int(obj["count"])
            else:
                print(f"##########\nException: Get all clients request ERROR!\n{text}\n##########")
                return None

    @classmethod
    async def get_client(cls, client_row_id: int = None, uuid: str = None) -> None | Client:
        async with aiohttp.ClientSession() as session:
            filter_st = ""
            client_row_id_st = ""
            if uuid:
                filters = {'filter_type': 'AND',
                           'filters': [{'field': 'who_invited', 'type': 'equal', 'value': str(uuid)}]}
                filter_st = f"&filters={json.dumps(filters)}"
            if client_row_id:
                client_row_id_st = f"{client_row_id}/"
            if  not (client_row_id_st or filter_st):
                raise Exception(f"No client row pk_id or filters provided: {client_row_id_st=} {filter_st=}")
            response = await session.get(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/{client_row_id_st}?user_field_names=true{filter_st}",
                headers={
                    "Authorization": f"Token {cls.DB_TOKEN}"
                }
            )
            text = await response.text()
            c = json.loads(text)
            if response.status == 200:
                for server in use_XSERVERS():
                    if server.ip == c["server"][0]["value"]:
                        break
                    server = c["server"]["value"]
                if type(server) == str:
                    print(f"[ERROR] server for client {c['sub_id']} not found!!! IP: {server}")
                    await notif_to_admins(f"[ERROR] server for client {c['subId']} not found!!! IP: {server}")
                return Client(pk_id=int(c["id"]), subId=c["sub_id"], uuid=c["uuid"],
                              protocol=c["protocol"]["value"], key=c["key"],
                              server=server)
            else:
                print(f"##########\nException: Get request ERROR! {client_row_id=}\n{text}\n##########")
                return None


    @classmethod
    async def create_client(cls, xclient: XClient) -> XClient | Exception:
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/?user_field_names=true",
                headers={
                    "Authorization": f"Token {cls.DB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "sub_id": xclient.subId,
                    "enable": xclient.enable,
                    "uuid": xclient.uuid,
                    "protocol": DB_PROTOCOL_TYPES[xclient.protocol.upper()],
                    "key": xclient.key,
                    "server": xclient.server.db_pk
                }
            )
            text = await response.text()
            if response.status == 200:
                print(f"###CREATED CLIENT###\nCREATED: {text}\n#########")
                c = json.loads(text)
                return XClient(subId=c["sub_id"], enable=xclient.enable, uuid=c["uuid"],
                               protocol=c["protocol"]["value"], key=c["key"],
                               server=c["server"], email=xclient.email, password=xclient.password,
                               tgId=xclient.tgId, totalGB=xclient.totalGB, expiryTime=xclient.expiryTime,
                               limitIp=xclient.limitIp, flow=xclient.flow, reset=xclient.reset, pk_id=int(c["id"]))
            else:
                raise Exception(f"Create client request ERROR!\n{text}")

    @classmethod
    async def update_client(cls, client: Client|XClient) -> Client | Exception:
        async with aiohttp.ClientSession() as session:
            response = await session.patch(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/{client.pk_id}/?user_field_names=true",
                headers={
                    f"Authorization": f"Token {cls.DB_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "sub_id": client.subId,
                    "enable": client.enable,
                    "uuid": client.uuid,
                    "protocol": DB_PROTOCOL_TYPES[client.protocol],
                    "key": client.key,
                    "server": client.server.db_pk
                }
            )
            text = await response.text()
            if response.status == 200:
                print(f"###UPDATED CLIENT###\nUPDATED: {text}\n#########")
                u = json.loads(text)
                if type(client) is XClient:
                    return XClient(pk_id=int(u["pk_id"]), subId=u["subId"], enable=u["enable"], uuid=u["uuid"],
                                   protocol=u["protocol"]["value"], key=u["key"],
                                   server=u["server"], email=client.email, password=client.password,
                                   expiryTime=client.expiryTime, limitIp=client.limitIp, flow=client.flow,
                                   reset=client.reset, tgId=client.tgId, totalGB=client.totalGB)

                return Client(pk_id=int(u["pk_id"]), subId=u["subId"], uuid=u["uuid"],
                              protocol=u["protocol"]["value"], key=u["key"],
                              server=u["server"])
            else:
                raise Exception(f"!!! Update client request ERROR!\n{text}")

    @classmethod
    async def delete_client(cls, client: Client|XClient) -> Client| XClient | Exception:
        async with aiohttp.ClientSession() as session:
            response = await session.delete(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/{client.pk_id}/",
                headers={
                    f"Authorization": f"Token {cls.DB_TOKEN}"
                }
            )
            text = response.status
            if response.status == 204:
                print(f"###DELETED CLIENT###\nCLIENT: {client}\n#########")
                return client
            else:
                return Exception(f"Delete client request ERROR!\n{text}")
