
## Centrifugo enabling instruction
This module supports DonatPAY donations

# main.py
```python
from threading import Thread
from backend.DonatPAY.centrifugo_websocket import listen_to_centrifugo 


async def admin_menu(message: Message):
    ...
    await message.answer(ADMIN_GREETING_REPLY(next_ws_update=NEXT_WS_UPDATE, ...)

def update_global_next_ws_update(new):
    global NEXT_WS_UPDATE
    NEXT_WS_UPDATE = get_utc_time(new)

async def restart_ws_thread(task: asyncio.Future):
    print(f"[TESTING FUNC restart_ws_thread()] Sleep for 20 secs now")
    await asyncio.sleep(20)
    was = task.cancel()
    print(f"[TESTING FUNC restart_ws_thread()] TASK CANCELED? {was=}")

    
def between_callback(callback_func, restart_ws_thread):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen_to_centrifugo(callback_func))
    # loop.close()

if __name__ == "__main__":
    ...
    centrifugo_thread = Thread(target=between_callback, args=[update_global_next_ws_update, restart_ws_thread], name="Centrifugo listener")
        try:
            centrifugo_thread.start()
            asyncio.run(main())
        except KeyboardInterrupt:
            SHUTDOWN = True
            print("Shutting down...")
            centrifugo_thread.join()
```


# globals.py
```python
def get_donat_pay_token() -> str:
    DONATPAY_API_KEY = getenv('DONATPAY_API_KEY')
    if DONATPAY_API_KEY:
        return DONATPAY_API_KEY
    asyncio.get_event_loop().stop()
    raise Exception(f"[GLOBAL EXCEPTION] NO DonatPAY TOKEN {DONATPAY_API_KEY=}")

DONATPAY_API_KEY = get_donat_pay_token()
DONATION_WIDGET_URL = getenv('DONATION_WIDGET_URL')

NEXT_WS_UPDATE = datetime.datetime.now()
```


## frontend/user/handlers.py
```python
from backend.DonatPAY.donations import DonatPAYHandler


async def handle_topup_user_balance(callback: CallbackQuery):
    ...
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплата", url=DonatPAYHandler.form_link(user=user))]
        ]
    )

async def handle_key_payment_confirmation(message: Message, state: FSMContext):
    ...
    kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пополнить баланс", url=DonatPAYHandler.form_link(user=user))]
        ])
    ...


async def handle_regain_user_access(callback: CallbackQuery):
    ...
    kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Пополнить баланс", url=DonatPAYHandler.form_link(user=user))]
            ])
    ...

```


## frontend/admin/handlers.py
```python
from backend.DonatPAY.donations import DonatPAYHandler


@router.callback_query((F.data == "admin_test_donatPAY") & (F.message.from_user.id in ADMINS))
async def handle_test_donatPAY(callback: CallbackQuery):
    await callback.answer("")
    await DonatPAYHandler.get_notifications(message=callback.message)
```

## frontend/admin/payment_manager_handlers.py
```python
from globals import DONATION_WIDGET_URL

async def handle_admin_manage_payment_defaults(callback: CallbackQuery):
    ...
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👀 Виджет с донатами", url=DONATION_WIDGET_URL)],
            ...
        ]
    )
```

## frontend/notifications/handlers.py
```python
from backend.DonatPAY.donations import DonatPAYHandler

async def payment_system():
    ...
    for page in range(1, rng + 1):
        ...
        for user in all_users:
            ...
            if user.xclient:
                ...
                if user.moneyBalance >= user.PaymentSum:
                    ...
                else:
                    ...
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💰 Пополнить баланс", url=DonatPAYHandler.form_link(user=user))]
                        ])
                    await bot.send_message(chat_id=user.userID, text=NO_MONEY_LEFT(user), reply_markup=kb)

async def check_period():
    ...
    for page in range(1, rng + 1):
        ...
        for user in all_users:
            ...
            if user.xclient:
                ...
                    if timedelta(days=3) > (datetime.datetime.fromtimestamp(user.xclient.expiryTime // 1000) - now) >= timedelta(days=-2):
                        if user.xclient.enable:
                            ...
                        else:
                            if user.moneyBalance < user.PaymentSum:
                                kb = InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text="💳 Пополнить баланс", url=DonatPAYHandler.form_link(user=user))]
                                ])
                                ...
```
