import asyncio
from datetime import datetime, timedelta

import websockets
import json
import requests
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from backend.database.users import UsersDatabase
from frontend.replys import NEW_DONATION_ADMIN_REPLY, BALANCE_TOPUP_USER_REPLY, CENTRIFUGO_ERROR, BALANCE_TOPUP_INVITER_REPLY
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
                                # Referral system
                                # if user.who_invited:
                                #     inviter = await UsersDatabase.get_user_by(ID=user.who_invited)
                                #     await UsersDatabase.update_user(inviter, {"moneyBalance": inviter.moneyBalance + (inviter.referBonus*float(sum)) })
                                #     await send_bot_message(chat_id=inviter.userID, text=BALANCE_TOPUP_INVITER_REPLY(user, sum), kb=kb)

                                await send_bot_message(chat_id=user.userID, text=BALANCE_TOPUP_USER_REPLY(user, sum), kb=kb)
                                success = True
                            except Exception as e:
                                print(f"[ERROR] {e}")
                                error = e
                        for adm in ADMINS:
                            print(f"[INFO] TRYING TO SEND DONATION MESSAGE TO ADMIN {adm}")
                            await send_bot_message(chat_id=adm, text=NEW_DONATION_ADMIN_REPLY(name, comment, sum, user, success, error))
    await asyncio.sleep(2)


async def listen_to_centrifugo(update_global_next_ws_update, restart_ws_thread=None):
    print("[INFO] Initializing Centrifugo")
    uri = "wss://centrifugo.donatepay.ru:43002/connection/websocket"
    channel = "$public:1304427"

    task = asyncio.current_task()


    while not SHUTDOWN:
        try:
            async with websockets.connect(uri) as websocket:
                client_token = get_token()
                auth_data = {
                    "id": 1,
                    "params": {
                        "name": "python",
                        "token": client_token
                    }
                }
                await websocket.send(json.dumps(auth_data))

                if restart_ws_thread:
                    print(f"{task._state=}")

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

                if restart_ws_thread:
                    await restart_ws_thread(task)

                # Обрабатываем входящие сообщения
                while True:
                    try:
                        if datetime.now() >= next_update_time:
                            print(f"[TTL UPDATE {ttl=}] TTL of Centrifuge exhausted, reloading connection")
                            break
                        await handle_donat_pay_message(websocket=websocket)
                    except websockets.ConnectionClosed as e:
                        if e.rcvd:
                            if e.rcvd.code == 3005:
                                print(f"[TTL ERROR {ttl=}] TTL of Centrifuge exhausted, reloading connection")
                        elif e.sent is None:
                            print(f"[TimeoutError ERROR {e.rcvd_then_sent=}] Trying to reload connection")
                            break
                        else:
                            print(f"[ConnectionClosed ERROR] {e}")
                        break
                    except Exception as e:
                        print(f"[donatPAY ERROR] {e}")
                        eqv = datetime.now() > next_update_time
                        for adm in ADMINS:
                            print(f"[INFO] TRYING TO SEND ERROR MESSAGE TO ADMIN {adm}")
                            await send_bot_message(chat_id=adm, text=CENTRIFUGO_ERROR(exception=e, equivalent=eqv))
                        break
        except asyncio.CancelledError as e:
            print(f"[TASK CancelledError {e.args=}] Trying to avoid...")
            eqv = datetime.now() > next_update_time
            for adm in ADMINS:
                print(f"[INFO] TRYING TO SEND ERROR MESSAGE TO ADMIN {adm}")
                await send_bot_message(chat_id=adm, text=CENTRIFUGO_ERROR(exception="asyncio.CancelledError", equivalent=eqv))
            await asyncio.sleep(1)
            continue