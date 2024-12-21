import asyncio
from dataclasses import dataclass
import json
import ssl
import uuid
from http.cookies import SimpleCookie
import aiohttp
from dotenv import load_dotenv
from os import getenv
from datetime import datetime, timedelta

load_dotenv()

LOGIN = "admin"
PASSWORD = "toor3640"
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

@dataclass()
class Client:
    email: str
    enable: bool
    expiryTime: int
    limitIp: int
    reset: int
    tgId: int
    totalGB: int
    subId: str
    flow: str =  None
    password: str = None
    id: str = None
    key: str = None

    @staticmethod
    def create_from_dict(dct):
        flow = None
        if "flow" in dct.keys():
            flow = dct["flow"]
        password = None
        if "password" in dct.keys():
            password = dct["password"]
        subId = None
        if "subId" in dct.keys():
            subId = dct["subId"]
        return Client(id=dct["id"], reset=dct["reset"], enable=dct["enable"], totalGB=dct["totalGB"], expiryTime=dct["expiryTime"],
                                tgId=dct["tgId"], limitIp=dct["limitIp"], email=dct["email"], flow=flow, password=password, subId=subId)

    def for_api(self):
        if self.flow:
            return {"uuid": self.id,"email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "flow": self.flow,
                    "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB}
        return {"email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "password": self.password,
                "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB}


class XServer:
    def __init__(self, login, password, ip, port, path):
        self.name = f"XServer@{ip}"
        self.username = login
        self.password = password
        self.ip = ip
        self.port = port
        self.path = path
        self.inbounds = list()
        self.login_cookies = SimpleCookie()
        self.session_start_time = datetime(2000, 1, 1)

    async def get_session(self) -> SimpleCookie:
        now = datetime.today()
        if (now - self.session_start_time) > timedelta(hours=1):
            await self.login()
        return self.login_cookies

    async def login(self):
        """Logins into system and returns self"""
        async with aiohttp.ClientSession() as session:
            data = {"username": self.username, "password": self.password}
            resp = await session.post(url=f"https://{self.ip}:{self.port}/{self.path}/login", data=data, ssl=ssl_context)
        if resp.status == 200:
            js = await resp.json()
            if js["success"]:
                self.login_cookies = resp.cookies
                self.session_start_time = datetime.today()
                return self
        raise Exception(f"Login exception! Check: URI, LOGIN, PASSWORD, ENV")

    async def get_online_users(self) -> list:
        await self.get_session()
        """Returns list off all online users"""
        async with aiohttp.ClientSession() as s:
            resp = await s.post(url=f"https://{self.ip}:{self.port}/{self.path}/panel/api/inbounds/onlines", ssl=ssl_context, cookies=self.login_cookies)
        if resp.status == 200:
            print(await resp.text())
            js = await resp.json()
            return js["obj"]
        raise Exception("Get data exception! Check: URI, COOKIES")

    async def get_client_traffics(self, email: str = None, uuid: str = None) -> dict | None:
        """
        Return client traffics data by email or uuid
        USED = DOWN + UP
        """
        if email:
            link = f"https://{self.ip}:{self.port}/{self.path}/panel/api/inbounds/getClientTraffics/{email}"
        elif uuid:
            link = f"https://{self.ip}:{self.port}/{self.path}/panel/api/inbounds/getClientTrafficsById/{uuid}"
        else:
            raise Exception("No identify data provided!!! Add: email or uuid")
        async with aiohttp.ClientSession() as s:
            resp = await s.get(url=link, ssl=ssl_context, cookies=self.login_cookies)
        if resp.status == 200:
            js = await resp.json()
            if not js["obj"]:
                return None
            return js["obj"] if type(js["obj"]) == dict else js["obj"][0]
        raise Exception("Get data exception! Check: URI, COOKIES")

    async def get_client_ips(self, email: str):
        """Must return all clients devices ips, but returns nothing :)"""
        async with aiohttp.ClientSession() as s:
            resp = await s.post(url=f"https://{self.ip}:{self.port}/{self.path}/panel/api/inbounds/clientIps/{email}", ssl=ssl_context,
                                cookies=self.login_cookies)
        if resp.status == 200:
            js = await resp.json()
            return js["obj"]
        raise Exception("Get data exception! Check: URI, COOKIES")

    async def get_inbounds(self):
        """Gets all XServer inbounds, returns self"""
        await self.get_session()
        async with aiohttp.ClientSession() as s:
            resp = await s.get(url=f"https://{self.ip}:{self.port}/{self.path}/panel/api/inbounds/list", ssl=ssl_context, cookies=self.login_cookies)
            if resp.status == 200:
                js = await resp.json()
                obj = js["obj"]
                if not js["success"]:
                    raise Exception(f"[{resp.status}]Get inbound data exception! {js['msg']}")
                if len(obj) > 0:
                    for inb in obj:
                        inb_id = inb["id"]
                        predata = dict()
                        predata["settings"] = json.loads(inb["settings"])
                        predata["streamSettings"] = json.loads(inb["streamSettings"])
                        predata["sniffing"] = json.loads(inb["sniffing"])
                        predata["protocol"] = inb["protocol"]
                        predata["vpn_port"] = inb["port"]
                        if inb["allocate"] != '':
                            predata["allocate"] = json.loads(inb["allocate"])
                        self.inbounds.append(Inbound(id=inb_id, server=self, predata=predata))
                return self
        raise Exception(f"[{resp.status}]Get data exception! Check: URI, COOKIES")


class Inbound:
    def __init__(self, id: int, server: XServer, predata: dict = None):
        self.id = id
        self.server = server
        self.protocol = str()
        self.vpn_port = int()
        self.settings = dict()
        self.streamSettings = dict()
        self.sniffing = dict()
        self.allocate = dict()
        self._process_predata(predata=predata)

    def _process_predata(self, predata: dict):
        if predata:
            self.protocol = predata["protocol"]
            self.vpn_port = predata["vpn_port"]
            self.settings = predata["settings"]
            self.streamSettings = predata["streamSettings"]
            self.sniffing = predata["sniffing"]
            if "allocate" in predata.keys():
                self.allocate = predata["allocate"]

    async def get_data(self):
        await self.server.get_session()
        async with aiohttp.ClientSession() as s:
            resp = await s.get(url=f"https://{self.server.ip}:{self.server.port}/{self.server.path}/panel/api/inbounds/get/{self.id}",
                               ssl=ssl_context, cookies=self.server.login_cookies)
            if resp.status == 200:
                js = await resp.json()
                if not js["success"]:
                    raise Exception(f"[{resp.status}]Get inbound data exception! {js['msg']}")
                obj = js["obj"]
                self.settings = json.loads(obj["settings"])
                clients = []
                for c in self.settings["clients"]:
                    client = Client.create_from_dict(c)
                    clients.append(client)
                self.settings["clients"] = clients
                self.streamSettings = json.loads(obj["streamSettings"])
                self.sniffing = json.loads(obj["sniffing"])
                self.protocol = obj["protocol"]
                self.vpn_port = obj["port"]
                if obj["allocate"] != '':
                    self.allocate = json.loads(obj["allocate"])
                return self
        raise Exception(f"[{resp.status}]Get data exception! Check: URI, COOKIES")\

    async def add_client(self, email: str, tgId: int = None, expiryTime: int = 0, totalBytes: int = 0) -> Client:
        """Adds client to inbound, returns client with key"""
        await self.server.get_session()
        client = Client(id=str(uuid.uuid4()), flow="xtls-rprx-vision", email=email, limitIp=0, totalGB=totalBytes, expiryTime=expiryTime,
                        enable=True, tgId=tgId, reset=0)
        settings = {"clients": [client.for_api()]}
        data = {
            "uuid": self.id,
            "settings": json.dumps(obj=settings)
        }
        async with aiohttp.ClientSession() as s:
            resp = await s.post(url=f"https://{self.server.ip}:{self.server.port}/{self.server.path}/panel/api/inbounds/addClient",
                                ssl=ssl_context, data=data, cookies=self.server.login_cookies)
        if resp.status == 200:
            await self.get_data()
            client.key = self.form_key(client_data=settings)
            return client
        raise Exception(f"[{resp.status}]Add user exception! Check: URI, COOKIES")

    async def update_client(self, client: Client, changes: dict) -> bool:
        """keys from user same to keys in changes!"""
        await self.server.get_session()
        u = client.for_api()
        u_keys = u.keys()
        for k, v  in changes.items():
            if k in u_keys and k != 'uuid':
                u[k] = v
        settings = {"clients": [u]}
        data = {
            "uuid": self.id,
            "settings": json.dumps(obj=settings)
        }
        async with aiohttp.ClientSession() as s:
            resp = await s.post(url=f"https://{self.server.ip}:{self.server.port}/{self.server.path}/panel/api/inbounds/updateClient/{client.id}",
                                ssl=ssl_context, data=data, cookies=self.server.login_cookies)
            if resp.status == 200:
                await self.get_data()
                return True
        raise Exception(f"[{resp.status}]Update user exception! Check: URI, COOKIES")

    async def reset_client_traffic(self, client: dict) -> bool:
        """Resets client traffic, returns success bool"""
        await self.server.get_session()
        async with aiohttp.ClientSession() as s:
            resp = await s.post(url=f"https://{self.server.ip}:{self.server.port}/{self.server.path}/panel/api/inbounds/{self.id}/resetClientTraffic/{client['email']}",
                                ssl=ssl_context, cookies=self.server.login_cookies)
            if resp.status == 200:
                return True
        raise Exception(f"[{resp.status}]Reset client traffic exception! Check: URI, COOKIES")

    async def delete_client(self, client_id: str):
        """Fully REMOVES client!!! If disabling use update func!!!!"""
        await self.server.get_session()
        async with aiohttp.ClientSession() as s:
            resp = await s.post(
                url=f"https://{self.server.ip}:{self.server.port}/{self.server.path}/panel/api/inbounds/{self.id}/delClient/{client_id}",
                ssl=ssl_context, cookies=self.server.login_cookies)
            if resp.status == 200:
                return True
        raise Exception(f"[{resp.status}]REMOVING client exception! Check: URI, COOKIES")

    def form_key(self, client_data: dict[str: list[dict]]):
        if self.protocol == "vless":
            type = self.streamSettings["network"]
            security = self.streamSettings["security"]
            pbk = self.streamSettings["realitySettings"]["settings"]["publicKey"]
            fp = self.streamSettings["realitySettings"]["settings"]["fingerprint"]
            sni = self.streamSettings["realitySettings"]["serverNames"][0]
            sid = self.streamSettings["realitySettings"]["shortIds"][0]
            spx = self.streamSettings["realitySettings"]["settings"]["spiderX"]
            flow = client_data["clients"][0]["flow"]
            client_id = client_data["clients"][0]["uuid"]
            key = f"{self.protocol}://{client_id}@{self.server.ip}:{self.vpn_port}?type={type}&security={security}&pbk={pbk}&fp={fp}&sni={sni}&sid={sid}&spx={spx}&flow={flow}#PROXYM1TY"
            return key
        raise Exception(f"Key forming error. Check data exist! {self.protocol=}")


async def main():
    server = XServer(ip="94.159.100.60", port=59999, path="PROXY", login=LOGIN, password=PASSWORD)
    await server.get_inbounds()
    inb: Inbound = server.inbounds[0]
    client = Client.create_from_dict(inb.settings["clients"][2])
    traffic = await server.get_client_traffics(uuid=client.id)
    print(traffic)
    # await inb.update_client(client=client, changes={})
    # client = await inb.add_client(email="OK_now", expiryTime=1733832000000, totalBytes=600*1024**3)
    # print(client)
    # client = inb.settings["clients"][1]
    # print("Before", client)
    # await inb.update_client(client=client, changes={"email": "letsTest"})
    # print("After", inb.settings["clients"][1])
#asyncio.run(main())


async def GET_XSERVERS() -> list[XServer]:
    XSERVERS = [XServer(ip="94.159.100.60", port=59999, path="PROXY", login=LOGIN, password=PASSWORD)]
    for server in XSERVERS:
        await server.get_inbounds()
    return XSERVERS


