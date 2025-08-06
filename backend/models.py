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
    sub_key: str = ""

    @staticmethod
    def create_from_dict(dct):
        flow = None
        id = str()
        if "flow" in dct.keys():
            flow = dct["flow"]
        password = None
        if "password" in dct.keys():
            password = dct["password"]
        # subId = None
        # if "subId" in dct.keys():
        #     subId = dct["subId"]
        subId = dct["subId"]
        if "id" in dct.keys():
            id = dct["id"]
        return XClient(uuid=id, reset=dct["reset"], enable=dct["enable"], totalGB=dct["totalGB"], expiryTime=dct["expiryTime"],
                       tgId=dct["tgId"], limitIp=dct["limitIp"], email=dct["email"], flow=flow, password=password, subId=subId)

    def for_api(self):
        if self.flow:
            return {"id": self.uuid, "email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "flow": self.flow,
                    "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB, "subId": self.subId}

        """
        {"clients":[
        {
        "id":"SHAD_test", 
        "email":"SHAD_test",
        "password": "dNUuvSpHcoB926CpA+TQiFlAC8MJgWWTOSv+TK20CEI=", 
        "limitIp":2,
        "totalGB":42949672960,
        "expiryTime":1745607600000,
        "enable":true,
        "tgId":"",
        "subId":"8t9lcsk0kysdt3rt",
        "reset": 0
        }
        ]
        }
        """
        return {"id": self.email, "email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "password": self.password, "flow": "",
                "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB, "subId": self.subId}

# Deprecated
@dataclass()
class OutlineClient:
    keyID: int
    keyLimit: float
    key: str


class User:
    def __init__(self, userID: int, userTG: str, PaymentSum: int, PaymentDate: date, serverName: str, serverType: str, who_invited: str | None, referBonus: int, subId: str,
                 Protocol: str, moneyBalance: float, tariff: str, UserReliability: bool = False, xclient: XClient = None, outline_client: OutlineClient = None, id: int = None, uuid: str = ""):
        self.id = id
        self.uuid = uuid
        self.moneyBalance = moneyBalance
        self.reliability = UserReliability
        self.tariff = tariff
        self.who_invited = who_invited
        self.referBonus = referBonus
        self.Protocol = Protocol
        self.serverType = serverType
        self.userID = userID
        self.subId = subId
        if re.fullmatch(r'[@]*[a-zA-Z0-9_]+', r''.join(userTG)):
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

    async def get_server_and_inbound(self, servers: list) -> dict:
        """Returns dict {`server`: s, `inbound`: inb}"""
        for s in servers:
            if s.name == self.serverName:
                await s.get_inbounds()
                for inb in s.inbounds:
                    if inb.protocol.lower() == self.Protocol.lower():
                        return {'server': s, 'inbound': inb}
        return None

    async def get_key(self, servers: list) -> str:
        if self.xclient.key:
            return self.xclient.key
        d = await self.get_server_and_inbound(servers=servers)
        self.xclient.key = d["inbound"].form_key({"clients": [self.xclient.for_api()]})
        return self.xclient.key

    async def get_sub_key(self, servers: list) -> str:
        if self.xclient.sub_key:
            return self.xclient.sub_key
        d = await self.get_server_and_inbound(servers=servers)
        self.xclient.sub_key = f"http://{d['server'].ip}:80{d['server'].SUB_URL}{self.subId}"
        return self.xclient.sub_key

    def change(self, field, new_value):
        match field:
            case "moneyBalance":
                print(f"[WARNING] {self.userTG} moneyBalance changed from {self.moneyBalance} to {new_value}")
                self.moneyBalance = new_value
                return
            case "Protocol":
                self.Protocol = new_value
                return
            case "configuration_type":
                self.serverType = new_value
                return
            case "PaymentSum":
                self.PaymentSum = new_value
                return
            case "tariff":
                print(f"[WARNING] {self.userTG} tariff changed from {self.tariff} to {new_value}")
                self.tariff = new_value
                return
            case "PaymentDate":
                self.PaymentDate = new_value
                return
            case "serverName":
                self.serverName = new_value
                return
            case "keyId":
                self.outline_client.keyID = new_value
                return
            case "subId":
                self.xclient.subId = new_value
                self.subId = new_value
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
{self.Protocol=}
"""
        return value
