import re
from datetime import date
from dataclasses import dataclass
from types import NoneType


@dataclass()
class XClient:
    email: str
    enable: bool
    expiryTime: int
    reset: int
    tgId: int
    totalGB: int
    subId: str = ""
    limitIp: int = 0
    flow: str =  ""
    password: str = ""
    uuid: str = ""
    key: str = ""

    async def get_key(self, servers: list) -> str:
        inb = await self.get_server_and_inbound(servers=servers)
        self.key = inb["inbound"].form_key({"clients": [self.for_api()]})
        return self.key

    async def get_server_and_inbound(self, servers: list) -> dict:
        for s in servers:
            await s.get_inbounds()
            for inb in s.inbounds:
                for cl in inb.settings["clients"]:
                    if "id" in cl.keys():
                        # print(f"finding {cl} {self.uuid=}")
                        if cl["id"] == self.uuid:
                            return {"server": s, "inbound": inb}
                    elif "password" in cl.keys():
                        if cl["password"] == self.password:
                            return {"server": s, "inbound": inb}

    @staticmethod
    def create_from_dict(dct):
        flow = None
        id = str()
        if "flow" in dct.keys():
            flow = dct["flow"]
        password = None
        if "password" in dct.keys():
            password = dct["password"]
        subId = None
        if "subId" in dct.keys():
            subId = dct["subId"]
        if "id" in dct.keys():
            id = dct["id"]
        return XClient(uuid=id, reset=dct["reset"], enable=dct["enable"], totalGB=dct["totalGB"], expiryTime=dct["expiryTime"],
                       tgId=dct["tgId"], limitIp=dct["limitIp"], email=dct["email"], flow=flow, password=password, subId=subId)

    def for_api(self):
        if self.flow:
            return {"id": self.uuid, "email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "flow": self.flow,
                    "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB}
        return {"email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "password": self.password, "flow": self.flow,
                "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB, "id": self.email, "subId": self.subId}

@dataclass()
class OutlineClient:
    keyID: int
    keyLimit: float
    key: str


class User:
    def __init__(self, userID: int, userTG: str, PaymentSum: int, PaymentDate: date, lastPaymentDate: date, serverName: str, serverType: str,
                 Protocol: str, moneyBalance: float, xclient: XClient = None, outline_client: OutlineClient = None, id: int = None, uuid: str = ""):
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
            case "Protocol":
                self.Protocol = new_value
                return
            case "serverType":
                self.serverType = new_value
                return
            case "PaymentSum":
                self.PaymentSum = new_value
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
