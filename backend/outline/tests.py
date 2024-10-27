from outline_vpn.outline_vpn import OutlineVPN
from outline_vpn.outline_vpn import OutlineServerErrorException
from dotenv import load_dotenv
from os import getenv
load_dotenv()

OUTLINE_API_URL = getenv('API_URL')
OUTLINE_CERT_SHA256 = getenv('CERT_SHA')


class OutlineManager:
    @classmethod
    def gb_to_bytes(cls, gb: float):
        return gb * 1024 ** 3

    client = OutlineVPN(api_url=OUTLINE_API_URL, cert_sha256=OUTLINE_CERT_SHA256)

    @classmethod
    def get_key_info_by_key(cls, key: str):
        for k in cls.client.get_keys():
            if k.access_url == key:
                return k

    @classmethod
    def get_key_info(cls, key_id: str):
        try:
            return cls.client.get_key(key_id)
        except OutlineServerErrorException:
            return None

    @classmethod
    def create_new_key(cls, name: str = None, data_limit_gb: float = None):
        return cls.client.create_key(name=name, data_limit=cls.gb_to_bytes(data_limit_gb))

    @classmethod
    def delete_key(cls, key_id: str) -> bool:
        return cls.client.delete_key(key_id)

    @classmethod
    def update_limit(cls, key_id: str, data_limit_bytes: int):
        return cls.client.add_data_limit(key_id, data_limit_bytes)


k = OutlineManager.update_limit(key_id="25", data_limit_bytes=0)
print(k)
