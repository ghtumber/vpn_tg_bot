from outline_vpn.outline_vpn import OutlineVPN, OutlineKey, OutlineServerErrorException
from globals import OUTLINE_API_URL_1, OUTLINE_CERT_SHA256_1, OUTLINE_API_URL_2, OUTLINE_CERT_SHA256_2


class OutlineManager:
    def __init__(self, api_url: str, cert_sha256: str, name: str, location: str):
        self.name = name
        self.location = location
        self.client = OutlineVPN(api_url=api_url, cert_sha256=cert_sha256)

    @staticmethod
    def gb_to_bytes(gb: float):
        return gb * 1024 ** 3

    def get_key_info_by_key(self, key: str) -> OutlineKey | None:
        for k in self.client.get_keys():
            if k.access_url.split("?")[0] == key:
                return k
        return None

    def get_key_info(self, key_id: str) -> OutlineKey | None:
        try:
            return self.client.get_key(key_id)
        except OutlineServerErrorException:
            return None

    def create_new_key(self, name: str = None, data_limit_gb: float = None) -> OutlineKey:
        return self.client.create_key(name=name, data_limit=self.gb_to_bytes(data_limit_gb))

    def delete_key(self, key_id: str) -> bool:
        return self.client.delete_key(key_id)

    def update_limit(self, key_id: str, data_limit_bytes: int) -> bool:
        return self.client.add_data_limit(key_id, data_limit_bytes)


OutlineManager_2 = OutlineManager(api_url=OUTLINE_API_URL_2, cert_sha256=OUTLINE_CERT_SHA256_2, name="Start", location="🇩🇪Germany")

SERVERS = [OutlineManager_2]

