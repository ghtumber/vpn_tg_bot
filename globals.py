from dotenv import load_dotenv
from os import getenv
load_dotenv()

TOKEN = getenv("BOT_TOKEN")
ADMINS = ["902448626", "1124386913"]
OUTLINE_API_URL = getenv('API_URL')
OUTLINE_CERT_SHA256 = getenv('CERT_SHA')
