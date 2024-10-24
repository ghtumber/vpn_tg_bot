from outline_vpn.outline_vpn import OutlineVPN
from dotenv import load_dotenv
from os import getenv


class OutlineManager:
    @classmethod
    def gb_to_bytes(cls, gb: float):
        return gb * 1024 ** 3

    load_dotenv()
    api_url = getenv('API_URL')
    cert_sha256 = getenv('CERT_SHA')
    client = OutlineVPN(api_url=api_url, cert_sha256=cert_sha256)

    @classmethod
    def get_key_info(cls, key_id: str):
        return cls.client.get_key(key_id)

    @classmethod
    def create_new_key(cls, key_id: str, name: str = None, data_limit_gb: float = None):
        return cls.client.create_key(key_id=key_id, name=name, data_limit=cls.gb_to_bytes(data_limit_gb))

    @classmethod
    def delete_key(cls, key_id: str):
        return cls.delete_key(key_id)

    @classmethod
    def upd_limit(cls, key_id: str, data_limit_bytes: int):
        return cls.client.add_data_limit(key_id, data_limit_bytes)
