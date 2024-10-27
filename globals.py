from dotenv import load_dotenv
from os import getenv
load_dotenv()

"""DEBUG MODE MUST BE DISABLED ON PROD"""
DEBUG = False
"""###################################"""

TOKEN = getenv("BOT_TOKEN") if not DEBUG else getenv("DEBUG_BOT_TOKEN")
ADMINS = [902448626, 1124386913]
OUTLINE_API_URL_1 = getenv('API_URL_1')
OUTLINE_CERT_SHA256_1 = getenv('CERT_SHA_1')


if __name__ == "globals":
    if DEBUG:
        print(f"###DEBUG MODE MUST BE DISABLED ON PROD {__name__}.py###\n{DEBUG=}\n#########################################")

