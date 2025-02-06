import asyncio

import aiogram
import websockets
import json
import requests
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import ClientSession
from backend.database.users import UsersDatabase
from frontend.replys import NEW_DONATION_ADMIN_REPLY, BALANCE_TOPUP_USER_REPLY
from globals import ADMINS, DONATPAY_API_KEY, TOKEN, SHUTDOWN

_bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

async def send_bot_message(text: str, chat_id: int, kb: InlineKeyboardMarkup = None) -> None:
    # async with ClientSession() as session:
    #     session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    #     session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0'
    #     print(f"[INFO] {text=}\n???")
    #     await session.post(
    #         "https://api.telegram.org/bot" + TOKEN + "/sendMessage?chat_id=" + str(chat_id) + "&parse_mode=html&text=" + text)
    await _bot.send_message(chat_id=chat_id, text=text, reply_markup=kb)

def get_token():
    url = 'https://donatepay.ru/api/v2/socket/token'
    data = {'access_token': DONATPAY_API_KEY}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)
    return response.json()['token']

def get_sub_token(client, channel):
    url = f"https://donatepay.ru/api/v2/socket/token?access_token={DONATPAY_API_KEY}"
    data = {"client": client, "channels": [channel]}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)
    return response.json()["channels"][0]["token"]


async def listen_to_centrifugo():
    print("[INFO] Initializing Centrifugo")
    uri = "wss://centrifugo.donatepay.ru:43002/connection/websocket"
    client_token = get_token()
    channel = "$public:1304427"
    async with websockets.connect(uri) as websocket:
        auth_data = {
            "id": 1,
            "params": {
                "name": "python",
                "token": client_token
            }
        }
        await websocket.send(json.dumps(auth_data))

        resp = await websocket.recv()
        client = json.loads(resp)["result"]["client"]
        print(f"{client=}")
        sub_token = get_sub_token(client=client, channel=channel)

        subscribe_data = {
            "id": 2,
            "method": 1,
            "params": {
                "channel": channel,
                "token": sub_token
            }
        }
        await websocket.send(json.dumps(subscribe_data))

        # Обрабатываем входящие сообщения
        while True:
            try:
                if SHUTDOWN[0]:
                    break
                await asyncio.sleep(2)
                message = await websocket.recv()
                print(f"Получено сообщение от DonatPAY: {message=}")
                message_dict = json.loads(message)
                if "result" in message_dict.keys():
                    if "data" in message_dict["result"].keys():
                        result = message_dict["result"]
                        if "data" in result["data"].keys():
                            if "notification" in result["data"]["data"].keys():
                                notification = result["data"]["data"]["notification"]
                                if notification["type"] == "donation":
                                    name = notification["vars"]["name"]
                                    comment = notification["vars"]["comment"]
                                    sum = notification["vars"]["sum"]
                                    print(f"Donation: {name=} {comment=} {sum=}руб")
                                    user = await UsersDatabase.get_user_by(ID=comment)
                                    error = ""
                                    success = False
                                    if not user:
                                        user = await UsersDatabase.get_user_by(TG=f"@{name}")
                                    if user:
                                        try:
                                            user = await UsersDatabase.update_user(user, change={"moneyBalance": user.moneyBalance + float(sum)})
                                            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👤 Меню", callback_data="to_menu")]])
                                            await send_bot_message(chat_id=user.userID, text=BALANCE_TOPUP_USER_REPLY(user, sum), kb=kb)
                                            success = True
                                        except Exception as e:
                                            print(f"[ERROR] {e}")
                                            error = e
                                    for adm in ADMINS:
                                        print(f"[INFO] TRYING TO SEND DONATION MESSAGE TO ADMIN {adm}")
                                        await send_bot_message(chat_id=adm, text=NEW_DONATION_ADMIN_REPLY(name, comment, sum, user, success, error))

            except websockets.ConnectionClosed as e:
                if e.rcvd.code == 3005:
                    """
                    Ошибка при обработке сообщения: received 3005 (registered) {"reason":"expired","reconnect":true}
                    """
                    print("[3005 ERROR] receiving new tokens")
                    client_token = get_token()
                    auth_data = {
                        "id": 1,
                        "params": {
                            "name": "python",
                            "token": client_token
                        }
                    }
                    await websocket.send(json.dumps(auth_data))

                    resp = await websocket.recv()
                    client = json.loads(resp)["result"]["client"]
                    print(f"{client=}")
                    sub_token = get_sub_token(client=client, channel=channel)

                    subscribe_data = {
                        "id": 2,
                        "method": 1,
                        "params": {
                            "channel": channel,
                            "token": sub_token
                        }
                    }
                    await websocket.send(json.dumps(subscribe_data))
                else:
                    print(f"Ошибка при обработке donatPAY: {e}")
                continue
            except Exception as e:
                print(f"[donatPAY ERROR] {e}")
                break