from __future__ import annotations
import re
from datetime import date
from dataclasses import dataclass
from types import NoneType
from typing import List


@dataclass()
class Client:
    pk_id: int
    uuid: str
    subId: str
    protocol: str
    server: object | str
    key: str

    def get_server_ip(self):
        if type(self.server) == str:
            return self.server
        return self.server.ip

    def get_link(self):
        if type(self.server) == str:
            return "No server evolved"
        return f"http://{self.server.ip}:{self.server.sub_port}{self.server.SUB_URL}{self.subId}"

@dataclass()
class XClient(Client):
    enable: bool
    tgId: int
    totalGB: int
    expiryTime: int
    email: str
    limitIp: int
    flow: str
    password: str = ""
    reset: int = 0

    @staticmethod
    def create_from_dict(client: Client, dct: dict) -> XClient:
        flow = dct["flow"] if "flow" in dct.keys() else None
        password = dct["password"] if "password" in dct.keys() else None
        email = dct["email"]
        totalGB = dct["totalGB"] if "totalGB" in dct.keys() else None
        expiry_time = dct["expiryTime"] if "expiryTime" in dct.keys() else None
        server = client.server if client.server else None
        return XClient(uuid=dct["id"], reset=dct["reset"], enable=dct["enable"], totalGB=totalGB, expiryTime=expiry_time,
                       tgId=dct["tgId"], limitIp=dct["limitIp"], email=email, flow=flow, password=password, subId=dct["subId"],
                       server=server, key=client.key, protocol=client.protocol, pk_id=client.pk_id)

    def for_api(self) -> dict:
        if self.flow:
            return {"id": self.uuid, "email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "flow": self.flow,
                    "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB, "subId": self.subId}

        """
        {"clients":[
        {
        "pk_id":"SHAD_test", 
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
        return {"pk_id": self.email, "email": self.email, "enable": self.enable, "expiryTime": self.expiryTime, "password": self.password, "flow": "",
                "limitIp": self.limitIp, "reset": self.reset, "tgId": self.tgId, "totalGB": self.totalGB, "subId": self.subId}



class User:
    def __init__(self, userID: int, userTG: str, PaymentSum: int, PaymentDate: date|None, who_invited: str | None,
                referBonus: int, moneyBalance: float, paying: bool, tariff: str, UserReliability: bool = False,
                 id: int = None, clients: list[int] = List[int]):
        self.id = id
        self.moneyBalance = moneyBalance
        self.reliability = UserReliability
        self.tariff = tariff
        self.who_invited = who_invited
        self.referBonus = referBonus
        self.userID = userID
        if re.fullmatch(r'@*[a-zA-Z0-9_]+', r''.join(userTG)):
            self.userTG = userTG
        else:
            raise Exception("UserTG Regular Error")
        self.PaymentSum = PaymentSum
        self.paying = paying
        if type(PaymentDate) is date or type(PaymentDate) is NoneType:
            self.PaymentDate = PaymentDate
        else:
            raise Exception(f"PaymentDate is not a [datetime.date or None] {type(PaymentDate)}")
        self.clients = clients


    def change(self, field, new_value):
        match field:
            case "moneyBalance":
                print(f"[WARNING] {self.userTG} moneyBalance changed from {self.moneyBalance} to {new_value}")
                self.moneyBalance = new_value
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
        raise Exception(f"Non changeable field {field} or etc...")


    def __str__(self):
        value = f"""
{self.userID=}
{self.userTG=}
{self.id=}
{self.clients=}
"""
        return value
