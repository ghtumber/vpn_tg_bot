import re
from datetime import date
from dataclasses import dataclass


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
    flow: str =  None
    password: str = None
    uuid: str = None
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
        return XClient(uuid=dct["uuid"], reset=dct["reset"], enable=dct["enable"], totalGB=dct["totalGB"], expiryTime=dct["expiryTime"],
                       tgId=dct["tgId"], limitIp=dct["limitIp"], email=dct["email"], flow=flow, password=password, subId=subId)

    def for_api(self):
        if self.flow:
            return {"uuid": self.uuid, "email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "flow": self.flow,
                    "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB}
        return {"email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "password": self.password,
                "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB}

@dataclass()
class OutlineClient:
    keyID: int
    keyLimit: float
    key: str


class User:
    def __init__(self, userID: int, userTG: str, PaymentSum: int, PaymentDate: date, serverName: str, xclient: XClient = None,
                 outline_client: OutlineClient = None, id: int = None):
        self.id = id
        self.userID = userID
        if re.fullmatch(r'@[a-zA-Z0-9_]+', r''.join(userTG)):
            self.userTG = userTG
        else:
            raise Exception("UserTG Regular Error")
        self.outline_client = outline_client
        self.xclient = xclient
        self.PaymentSum = PaymentSum
        if type(PaymentDate) is date:
            self.PaymentDate = PaymentDate
        else:
            raise Exception(f"PaymentDate is not a datetime.date {type(PaymentDate)}")
        self.serverName = serverName


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
            return {"id": self.id,"email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "flow": self.flow,
                    "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB}
        return {"email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "password": self.password,
                "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB}
