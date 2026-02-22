from globals import All_Tariffs, use_PREFERRED_PAYMENT_SETTINGS

REPLY_REGISTRATION = lambda who_invited: f"""
👋 Приветствуем в proxym1ty!
{f'''
😎 {who_invited} уже пользуется нашим VPN!''' if who_invited else ''}

Мы рады, что вы выбрали нас для безопасного и приватного интернет-серфинга. Перед началом работы позвольте рассказать немного о том, что мы предлагаем:

🔐 Анонимность и безопасность – без лишних вопросов и сложностей
⏳ Быстрая настройка – начните пользоваться в пару кликов
🌱 Подключение по безопасным протоколам Shadowsocks и VLESS

Нажмите кнопку ниже, чтобы начать свое путешествие с 🚀 Proxym1ty VPN.
"""

REGISTRATION_FSM_REPLY = """
💥 Начнём регистрацию в Proxym1ty!
Чтобы активировать ваш аккаунт, отправьте ваш ключ от VPN в ответ на это сообщение.
"""

ADMIN_GREETING_REPLY = lambda username, online_users_count, servers_count:f"""
✨ <b>Привет</b> {username}

📋 Это <b>админка Proxym1ty</b>

Здесь ты можешь управлять клиентами и настройками продаж

📊 <b>Онлайн сейчас</b>: {online_users_count}
🌐 <b>Подключено серверов</b>: {servers_count}
"""

ADMIN_PAYMENTS_MANAGER_REPLY = lambda default_server, default_protocol, default_coast, xtr_rate, Available_Tariffs:f"""
🧾 Сейчас установлены следующие значения.

Здесь ты можешь <b>управлять</b> ими.

🌐 <b>Сервера сейчас</b>: {default_server}
⛓ <b>Протокола сейчас</b>: {default_protocol}
🏧 <b>Цены сейчас</b>: {default_coast}
🌟 <b>Курс XTR</b>: {xtr_rate}руб.
🟢 <b>Активных тарифов</b>: {len(Available_Tariffs)}
🟡 <b>Отключено тарифов</b>: {len(All_Tariffs) - len(Available_Tariffs)}
"""

INSTRUCTIONS_TEXT = """
🔗 Как подключиться к VPN?

Выберите инструкцию для вашей платформы и настройте VPN за пару минут:

📱 Android | iOS
💻 Windows (c/без раздельного туннелирования) | MacOS

Если возникли вопросы — обратитесь в поддержку. 🚀
"""


USER_GREETING_REPLY = lambda username, paymentSum, paymentDate, tariff, user_balance: f"""
✨ <b>Привет</b> {username}

📋 Это <b>главное меню Proxym1ty</b>

Здесь ты можешь управлять своим VPN и следить за использованием

💵 <b>Баланс</b>: {user_balance}🌟XTR
⚡ <b>Тариф</b>: {tariff}
💳 <b>Следующая оплата</b> — {paymentSum}🌟XTR {paymentDate.strftime("%d.%m.%Y")}

⚡ Вот что можно посмотреть.
"""

CLIENTS_LIST_REPLY = lambda username, clients: f"""
🌚 Это <b>список ваших соединений</b>

Здесь ты можешь управлять своим VPN

è Соединения:
{''.join(f'🌐Сервер: <i>{client.get_server_ip()}</i> 🚪{client.protocol} {f"\n/client_{client.pk_id}"}\n' for client in clients)}
"""


CLIENT_INFO_REPLY = lambda client_enable, sub_key, key, server_ip, expiry_date, ip_limit, traffic_info=None: f"""

📊 Статус клиента: {'🟢Активный' if client_enable else '🔴Неактивен'}
🌐 Сервер: <i>{server_ip}</i>
⏳ Истекает: <b>17:00 {expiry_date} MSK</b>
🖥️ Ограничение устройств: <b>{ip_limit if ip_limit else '♾️'}</b>
{f'''📈 <b>Использование</b> за месяц:
<b>{round(traffic_info['traffic'] / 1024**3, 2)}GB</b>/<b>{traffic_info['total'] // 1024**3}GB</b>
[{''.join('☁' for i in range(int(traffic_info['progress'] * 10)))}{''.join('✦' for i in range(10 - int(traffic_info['progress'] * 10)))}]
''' if traffic_info else ''}

📋 Нажми на ключ, чтобы скопировать!
🔗 <b>sub-ключ</b>:
<blockquote expandable><code>{sub_key}</code></blockquote>
🗿 <b>Обычный ключ</b>:
<blockquote expandable><code>{key}</code></blockquote>
"""


CLEAN_USER_GREETING_REPLY = lambda username, user_balance: f"""
✨ <b>Привет</b> {username}

📋 Это <b>главное меню Proxym1ty</b>

🔥 Сейчас доступен FREE период!
💵 <b>Баланс</b>: {user_balance}🌟XTR

⚡ Чтобы купить VPN, просто выбери нужный пункт.
"""


EXHAUSTED_USER_GREETING_REPLY = lambda user: f"""
✨ <b>Привет</b> {user.userTG}

📋 Это <b>главное меню Proxym1ty</b>

🔴 <b>Статус</b>: Отключен
🧾 <b>Нужно оплатить</b>: {user.PaymentSum}🌟XTR
💵 <b>Баланс</b>: {user.moneyBalance}🌟XTR

⚡ Чтобы возобновить доступ, просто выбери нужный пункт.
"""


## TODO rework server error notif sys (multi client)
SERVER_ERROR_USER_GREETING_REPLY = lambda user: f"""
✨ <b>Привет</b> {user.userTG}

📋 Это <b>главное меню Proxym1ty</b>

🔴 Сейчас ваш сервер <b>Недоступен</b>
🌐 <b>Сервер</b>: <pre>{user.serverName}</pre>
💵 <b>Баланс</b>: {user.moneyBalance}🌟XTR

Мы уже работаем над решением проблемы.

⚡ В случае <b>дополнительных проблем</b> обратитесь в <b>тех. поддержку</b>.
"""


TECH_ASSISTANCE_RESPONSE = lambda user: f"""
🛠️ Техническая поддержка Proxym1ty

Если у вас возникли вопросы или проблемы, наша команда готова помочь!

📩 Контакты для связи:
🔹 Чат поддержки: {'@proxym1ty_support'}

Мы всегда готовы решить любые вопросы. 🚀
"""


PAYMENT_SUCCESS = lambda user: f"""
🌝 <b>{user.userTG}</b>!
✅ <i>Подписка оплачена!</i>
📅 Следующая оплата <b>{user.PaymentDate.strftime("%d.%m.%Y")}</b>
💰 Остаток баланса <b>{user.moneyBalance}🌟XTR</b>
"""

NO_MONEY_LEFT =  lambda user: f"""
💔 <b>{user.userTG}</b>!
⛔ <i>VPN отключён!</i>
💰 Баланс <b>{user.moneyBalance}🌟XTR</b>
🧾 Тариф <b>{user.PaymentSum}🌟XTR</b>
📅 Оплата <b>{user.PaymentDate.strftime("%d.%m.%Y")}</b> просрочена!

Чтобы возобновить доступ пополните баланс 👇
"""

MONEY_ENDING = lambda user: f"""
<b>{user.userTG} внимание!</b>
⌚ <i>У вас заканчиваются средства на балансе!</i>
💳 Баланс необходимо пополнить до <b>{user.PaymentDate.strftime("%d.%m.%Y")}</b>
💸 В этом месяце вам нужно заплатить <b>{user.PaymentSum}🌟XTR</b>
"""

FREE_PERIOD_TARIFFS = lambda: f"""
🌟 Выбор <b>тарифа</b>.
Выбери подходящий вам тариф:
👉 <b>🔥7 дней</b> <b>🗿PROMO</b> подходит для тех, кто редко использует VPN (к примеру для просмотра Youtube)
- <b>1</b> ключ в комплекте
- <b>100 МБ/с</b> канал на сервере (ограничены вашим соединением)
- подключение <b>до 2 устройств одновременно</b>
- обычная тех. поддержка
- возможны подвисания
👉 <b>3 дня</b> <b>😎FULL</b> подходит для активных пользователей
- <b>2</b> ключа в комплекте
- <b>10 Gbit/s</b> канал на сервере (ограничены вашим соединением)
- подключение <b>до 5 устройств одновременно</b>
- приоритетная тех. поддержка
- стабильный uptime 99%
"""

PERIOD_ENDED = lambda user: f"""
<b>{user.userTG} внимание!</b>
⛔ <i>VPN недоступен!</i>
💳 Баланс сейчас <b>{user.moneyBalance}</b>
💸 В этом месяце вам нужно заплатить <b>{user.PaymentSum}🌟XTR</b>
"""

TRAFFICS_ENDING = lambda user, delta: f"""
<b>{user.userTG} внимание!</b>
📉 <i>У вас заканчивается VPN трафик!</i>
🔋 Остаток <b>{delta//1024**3}GB</b>
⚡ Не переживайте <b>мы добавим ещё 50гб трафика</b>
❔ <b>Почему так?</b> Всё просто! Мы понимаем, что иногда требуется большой объём трафика, и мы поддерживаем наших пользователей.
❕ <b>Однако это лишь временное решение</b>, так как такое расширение может привести к перегрузке серверов.
"""


GLOBAL_ALERT = lambda user, alert: f"""
<b>{user.userTG} внимание!</b>
‼ {alert}
"""

AWAIT_DONAT_FETCH = lambda user: f"""
<b>{user}</b> сервис под нагрузкой.
🕓 Попробуйте нажать кнопку чуть позже
"""


NEW_PRE_PAYMENT_ADMIN_REPLY = lambda name, currency, sum, ID: f"""
💸 Новая оплата!
🚹 Name: {name}
🆔 ID: <code>{ID}</code>
🧾 Валюта: {currency}
💰 Сумма: {sum}
"""


NEW_DONATION_ADMIN_REPLY = lambda name, comment, sum, user, success, error: f"""
💸 Новая оплата!
🚹 Name: {name}
🧾 Comment: {comment}
💰 Манесы: {sum}руб
{f'⛔ Error: {error}' if error else ''}
{f'''User DB:
🔗TG: {user.userTG}
🌐 Svr name: {user.serverName}
🧾 Tariff: {user.tariff}
💰New balance: {user.moneyBalance}''' if success else '⛔ User не найден'}"""


CENTRIFUGO_ERROR = lambda exception, equivalent: f"""
🆘 <b>Centifugo error!!!</b>
🕓 Time out: {equivalent}
Trying to avoid and restart...
🔴 Exception: <pre><code>{exception}</code></pre>
"""

BALANCE_TOPUP_INVITER_REPLY = lambda user, sum: f"""
🤝 Бонус за реферала на сумму {sum}🌟XTR!
💵 <b>Баланс</b>: {user.moneyBalance}🌟XTR"""

KEY_UPDATE_USER_REPLY = lambda user, sub_key, key: f"""
‼ {user.userTG}
<b>Вам выдан новый ключ!</b>!
📋 Нажми на ключ, чтобы скопировать!
🔗 <b>sub-ключ</b>:
<blockquote expandable><code>{sub_key}</code></blockquote>
🗿 <b>Обычный ключ</b>:
<blockquote expandable><code>{key}</code></blockquote>
"""

BALANCE_TOPUP_USER_REPLY = lambda user, summ: f"""
✅ <b>Пополнение баланса</b> на сумму {summ}🌟XTR!
💵 <b>Баланс</b>: {user.moneyBalance}🌟XTR"""

BALANCE_TOPUP_BY_RELIABLE_USER = lambda userTG, userID, comment, user: f"""
⌚ Пополнение переводом ожидает!
👤 <b>User</b>: {userTG}
🆔 <b>userID</b>: 📋<code>{userID}</code>
💸 <b>Подписка</b>: {user.PaymentSum}🌟XTR (~ {user.PaymentSum*float(use_PREFERRED_PAYMENT_SETTINGS()["XTR_exchange_rate"])}руб)
📈 <b>Курс XTR</b>: 100р - {int(100/use_PREFERRED_PAYMENT_SETTINGS()["XTR_exchange_rate"])}🌟XTR
🧾 <b>Коммент</b>: <pre>{comment}</pre>"""
