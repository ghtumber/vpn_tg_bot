import re


class User:
    def __init__(self, userID: int, userTG: str, keyID: int, key: str, keyLimit: float, PaymentSum: int, id: int = None):
        self.id = id
        self.userID = userID
        self.userTG = userTG if re.fullmatch(r'@[a-zA-Z0-9]+', r''.join(userTG)) else Exception("UserTG Regular Error")
        self.keyID = keyID
        self.key = key if key.startswith("ss:/") else Exception("UserTG Regular Error")
        self.keyLimit = keyLimit
        self.PaymentSum = PaymentSum

    def change(self, field, new_value):
        if field == "userID":
            self.userID = new_value
        if field == "userTG":
            self.userTG = new_value
        if field == "keyID":
            self.keyID = new_value
        if field == "key":
            self.key = new_value
        if field == "keyLimit":
            self.keyLimit = new_value
        if field == "PaymentSum":
            self.PaymentSum = new_value

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
