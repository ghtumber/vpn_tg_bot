import json
import aiohttp
from typing_extensions import Tuple

from backend.xapi.servers import XServer
from globals import DB_TOKEN, SERVERS_TABLE_ID


class ServersDatabase:
    DB_TOKEN = DB_TOKEN
    TABLE_ID = SERVERS_TABLE_ID

    @classmethod
    async def get_all_servers(cls, size=100, page=1, active: bool="all") -> None | Tuple[list[XServer], int]:
        """PARAMETER active accepts bool! Returns list[Client], count_of_rows"""
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
                    if active != "all" and active:
                        if result["alive"]:
                            res.append(XServer(ip=result["ip"], tariff=result["tariff"]))
                    else:
                        res.append(XServer(ip=result["ip"], tariff=result["tariff"]))
                return res, int(obj["count"])
            else:
                print(f"##########\nException: Get all servers request ERROR!\n{text}\n##########")
                return None

    @classmethod
    async def get_server(cls, row_id: int) -> None | XServer:
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"https://api.baserow.io/api/database/rows/table/{cls.TABLE_ID}/{row_id}/?user_field_names=true",
                headers={
                    "Authorization": f"Token {cls.DB_TOKEN}"
                }
            )
            text = await response.text()
            res = json.loads(text)
            if response.status == 200:
                return XServer(ip=res["ip"], tariff=res["tariff"])
            else:
                print(f"##########\nException: Get request ERROR! {row_id=}\n{text}\n##########")
                return None
