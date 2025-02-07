import asyncio
from datetime import datetime, timedelta

import websockets
import json
import requests
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from backend.database.users import UsersDatabase
from frontend.replys import NEW_DONATION_ADMIN_REPLY, BALANCE_TOPUP_USER_REPLY
from globals import ADMINS, DONATPAY_API_KEY, TOKEN, SHUTDOWN


_bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

async def send_bot_message(text: str, chat_id: int, kb: InlineKeyboardMarkup = None) -> None:
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


async def handle_donat_pay_message(websocket):
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


async def listen_to_centrifugo(update_global_next_ws_update):
    print("[INFO] Initializing Centrifugo")
    uri = "wss://centrifugo.donatepay.ru:43002/connection/websocket"
    client_token = get_token()
    channel = "$public:1304427"

    while not SHUTDOWN:
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
            print(f"[INFO] {client=}")
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
            await asyncio.sleep(2)

            init_message = await websocket.recv()
            print(f"Получено init_message от DonatPAY: {init_message=}")
            init_dict = json.loads(init_message)

            # {"id":2,"result":{"expires":true,"ttl":21600}}
            ttl = init_dict["result"]["ttl"]
            next_update_time = datetime.now() + timedelta(seconds=ttl)
            update_global_next_ws_update(new=next_update_time)

            # Обрабатываем входящие сообщения
            while True:
                try:
                    if datetime.now() >= next_update_time:
                        print(f"[TTL UPDATE {ttl=}] TTL of Centrifuge exhausted, reloading connection")
                        break
                    await handle_donat_pay_message(websocket=websocket)
                except websockets.ConnectionClosed as e:
                    if e.rcvd.code == 3005:
                        print(f"[TTL ERROR {ttl=}] TTL of Centrifuge exhausted, reloading connection")
                        break
                    else:
                        print(f"Ошибка при обработке donatPAY: {e}")
                    continue
                except Exception as e:
                    print(f"[donatPAY ERROR] {e}")
                    break