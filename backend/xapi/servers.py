import asyncio
import ssl
import string, random
import os
from dataclasses import dataclass
import json
import uuid
from http.cookies import SimpleCookie
import aiohttp
import base64
from dotenv import load_dotenv
from os import getenv
from datetime import datetime, timedelta
from backend.models import XClient
load_dotenv()

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

@dataclass()
class XServer:
    LOGIN = getenv("SERVER_LOGIN")
    PASSWORD = getenv("SERVER_PASSWORD")
    def __init__(self, ip, port, path, location="🇩🇪Germany"):
        self.name = f"XServer@{ip}"
        self.location = location
        self.ip = ip
        self.port = port
        self.path = path
        self.inbounds = list()
        self.login_cookies = SimpleCookie()
        self.session_start_time = datetime(2000, 1, 1)
        self.last_update_time = datetime(2000, 1, 1)

    async def get_session(self) -> SimpleCookie:
        now = datetime.today()
        if (now - self.session_start_time) > timedelta(hours=1):
            await self.login()
            self.session_start_time = now
        return self.login_cookies

    async def check_data(self):
        now = datetime.today()
        if (now - self.last_update_time) > timedelta(minutes=10):
            await self.get_inbounds()
            self.last_update_time = now

    async def login(self):
        """Logins into system and returns self"""
        async with aiohttp.ClientSession() as session:
            data = {"username": self.LOGIN, "password": self.PASSWORD}
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

    async def get_client_traffics(self, email: str = None, uuid: str = None) -> dict:
        """Return client traffics data by email or uuid"""
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
            return js["obj"] if type(js["obj"]) == dict else js["obj"][0]
        raise Exception("Get data exception! Check: URI, COOKIES")

    async def get_client_info(self, identifier: str) -> XClient | None:
        """
        Returns XClient object or None(if not found)
        identifier = UUID or email!!!
        """
        await self.check_data()
        for inb in self.inbounds:
            clients = inb.settings["clients"]
            for client_dict in clients:
                if "id" in client_dict.keys():
                    if client_dict["id"] == identifier:
                        # print(f"get_client_info() -> {client_dict}")
                        return XClient.create_from_dict(dct=client_dict)
                elif "password" in client_dict.keys():
                    if client_dict["email"] == identifier:
                        return  XClient.create_from_dict(dct=client_dict)
        return None

    async def get_all_clients(self) -> list[XClient]:
        """Returns list of XClients or None"""
        await self.check_data()
        res = []
        for inb in self.inbounds:
            clients = inb.settings["clients"]
            print(f"{clients=}")
            for client in clients:
                res.append(XClient.create_from_dict(dct=client))
        return res if res else None

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
                        predata["clientStats"] = inb["clientStats"]
                        if inb["allocate"] != '':
                            predata["allocate"] = json.loads(inb["allocate"])
                        self.inbounds.append(Inbound(id=inb_id, server=self, predata=predata))
                self.last_update_time = datetime.today()
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
        self.clientStats = list()
        self._process_predata(predata=predata)

    def _process_predata(self, predata: dict):
        if predata:
            self.protocol = predata["protocol"]
            self.vpn_port = predata["vpn_port"]
            self.settings = predata["settings"]
            self.streamSettings = predata["streamSettings"]
            self.sniffing = predata["sniffing"]
            self.clientStats = predata["clientStats"]
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
                # супер странная часть кода
                # ------------------------------------
                clients = []
                for c in self.settings["clients"]:
                    client = XClient.create_from_dict(c)
                    clients.append(client)
                # self.settings["clients"] = clients
                # -------------------------------------
                self.streamSettings = json.loads(obj["streamSettings"])
                self.sniffing = json.loads(obj["sniffing"])
                self.protocol = obj["protocol"]
                self.vpn_port = obj["port"]
                if obj["allocate"] != '':
                    self.allocate = json.loads(obj["allocate"])
                return self
        raise Exception(f"[{resp.status}]Get data exception! Check: URI, COOKIES")\

    async def add_client(self, email: str, tgId: int = 0, expiryTime: int = 0, totalBytes: int = 0) -> XClient:
        """Adds client to inbound, returns client with key"""
        await self.server.get_session()
        if self.protocol == "vless":
            client = XClient(uuid=str(uuid.uuid4()), flow="xtls-rprx-vision", email=email, limitIp=0, totalGB=totalBytes, expiryTime=expiryTime,
                            enable=True, tgId=tgId, reset=0)
            settings = {"clients": [client.for_api()]}
            data = {
                "id": self.id,
                "settings": json.dumps(obj=settings)
            }
        if self.protocol == "shadowsocks":
            random_bytes = os.urandom(32)
            l = string.ascii_lowercase + string.digits
            password = base64.standard_b64encode(random_bytes).decode()
            subId = "".join(random.choice(l) for _ in range(16))
            client = XClient(uuid=email, email=email, limitIp=0, totalGB=totalBytes, expiryTime=expiryTime, enable=True, tgId=tgId, reset=0,
                             password=password, subId=subId)
            settings = {"clients": [client.for_api()]}
            data = {
                "id": self.id,
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

    async def update_client(self, client: XClient, changes: dict) -> bool:
        """keys from user same to keys in changes!"""
        await self.server.get_session()
        u = client.for_api()
        u_keys = u.keys()
        for k, v  in changes.items():
            if k in u_keys and k != 'id':
                u[k] = v
        settings = {"clients": [u]}
        data = {
            "id": self.id,
            "settings": json.dumps(obj=settings)
        }
        async with aiohttp.ClientSession() as s:
            resp = await s.post(url=f"https://{self.server.ip}:{self.server.port}/{self.server.path}/panel/api/inbounds/updateClient/{client.uuid}",
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
                await self.get_data()
                return True
        raise Exception(f"[{resp.status}]REMOVING client exception! Check: URI, COOKIES")

    def form_key(self, client_data: dict[str: list[dict]]):
        """client_data = {"clients": [client.for_api()]}"""
        if self.protocol == "vless":
            type = self.streamSettings["network"]
            security = self.streamSettings["security"]
            pbk = self.streamSettings["realitySettings"]["settings"]["publicKey"]
            fp = self.streamSettings["realitySettings"]["settings"]["fingerprint"]
            sni = self.streamSettings["realitySettings"]["serverNames"][0]
            sid = self.streamSettings["realitySettings"]["shortIds"][0]
            spx = self.streamSettings["realitySettings"]["settings"]["spiderX"]
            flow = client_data["clients"][0]["flow"]
            client_id = client_data["clients"][0]["id"]
            key = f"{self.protocol}://{client_id}@{self.server.ip}:{self.vpn_port}?type={type}&security={security}&pbk={pbk}&fp={fp}&sni={sni}&sid={sid}&spx={spx}&flow={flow}#PROXYM1TY"
            return key
        if self.protocol == "shadowsocks":
            client_password = client_data['clients'][0]['password']
            auth_info = f"{self.settings['method']}:{self.settings['password']}:{client_password}"
            print(f"{auth_info=}")
            auth_info_base64 = base64.standard_b64encode(auth_info.encode())
            auth_info_base64 = str(auth_info_base64)[2:-1]
            auth_info_base64 = auth_info_base64.replace("=", "")
            network = self.streamSettings["network"]
            key = f"ss://{auth_info_base64}@{self.server.ip}:{self.vpn_port}?type={network}#PROXYM1TY"
            return key
        raise Exception(f"Key forming error. Check data exist! {self.protocol=}")



async def GET_XSERVERS() -> list[XServer]:
    XSERVERS = [XServer(ip="94.159.100.60", port=59999, path="PROXY")]
    for server in XSERVERS:
        await server.get_inbounds()
    return XSERVERS