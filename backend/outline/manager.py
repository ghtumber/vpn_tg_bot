from outline_vpn.outline_vpn import OutlineVPN
from globals import OUTLINE_API_URL, OUTLINE_CERT_SHA256


class OutlineManager:
    @classmethod
    def gb_to_bytes(cls, gb: float):
        return gb * 1024 ** 3

    client = OutlineVPN(api_url=OUTLINE_API_URL, cert_sha256=OUTLINE_CERT_SHA256)

    @classmethod
    def get_key_info_by_key(cls, key: str):
        for k in cls.client.get_keys():
            print(k.access_url)
            if k.access_url.split("?")[0] == key:
                return k

    @classmethod
    def get_key_info(cls, key_id: str):
        return cls.client.get_key(key_id)

    @classmethod
    def create_new_key(cls, key_id: str, name: str = None, data_limit_gb: float = None):
        return cls.client.create_key(key_id=key_id, name=name, data_limit=cls.gb_to_bytes(data_limit_gb))

    @classmethod
    def delete_key(cls, key_id: str):
        return cls.client.delete_key(key_id)

    @classmethod
    def update_limit(cls, key_id: str, data_limit_bytes: int):
        return cls.client.add_data_limit(key_id, data_limit_bytes)
