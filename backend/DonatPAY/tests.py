import asyncio
import websockets
import json
import requests

def get_token():
    url = 'https://donatepay.ru/api/v2/socket/token'
    data = {'access_token': 'RNwPVmd2LdzV6B356Fdxc9fAIXFRlpmf06qwlyr9FEGcnQEPcVvUJtEO3pWe'}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)
    return response.json()['token']

def get_sub_token(client, channel):
    url = "https://donatepay.ru/api/v2/socket/token?access_token=RNwPVmd2LdzV6B356Fdxc9fAIXFRlpmf06qwlyr9FEGcnQEPcVvUJtEO3pWe"
    data = {"client": client, "channels": [channel]}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)
    return response.json()["channels"][0]["token"]


async def listen_to_centrifugo():
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
                await asyncio.sleep(5)
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
            except Exception as e:
                print(f"Ошибка при обработке сообщения: {e}")
                break


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(listen_to_centrifugo())
    except KeyboardInterrupt:
        pass