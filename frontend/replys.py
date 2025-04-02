from globals import All_Tariffs

REPLY_REGISTRATION = lambda who_invited: f"""
👋 Приветствуем в proxym1ty!
{f'''
😎 {who_invited} уже пользуется нашим VPN!''' if who_invited else ''}

Мы рады, что вы выбрали нас для безопасного и приватного интернет-серфинга. Перед началом работы позвольте рассказать немного о том, что мы предлагаем:

🔹 Анонимность и безопасность – без лишних вопросов и сложностей
🔹 Быстрая настройка – начните пользоваться в пару кликов
🔹 Подключение по безопасным протоколам Shadowsocks и VLESS

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


USER_GREETING_REPLY = lambda username, paymentSum, paymentDate, tariff, serverLocation, user_balance: f"""
✨ <b>Привет</b> {username}

📋 Это <b>главное меню Proxym1ty</b>

Здесь ты можешь управлять своим VPN и следить за использованием

💵 <b>Баланс</b>: {user_balance}🌟XTR
⚡ <b>Тариф</b>: {tariff}
🏳 <b>Страна VPN</b>: {serverLocation}
💳 <b>Следующая оплата</b> — {paymentSum}🌟XTR {paymentDate.strftime("%d.%m.%Y")}

⚡ Вот что можно посмотреть.
"""

CLEAN_USER_GREETING_REPLY = lambda username, user_balance: f"""
✨ <b>Привет</b> {username}

📋 Это <b>главное меню Proxym1ty</b>

Здесь ты можешь управлять своим VPN

💵 <b>Баланс</b>: {user_balance}🌟XTR

⚡ Чтобы купить VPN, просто выбери нужный пункт.
"""


EXHAUSTED_USER_GREETING_REPLY = lambda user: f"""
✨ <b>Привет</b> {user.userTG}

📋 Это <b>главное меню Proxym1ty</b>

🔴 <b>Статус</b>: Отключен
💵 <b>Баланс</b>: {user.moneyBalance}🌟XTR

⚡ Чтобы возобновить доступ, просто выбери нужный пункт.
"""

SERVER_ERROR_USER_GREETING_REPLY = lambda user: f"""
✨ <b>Привет</b> {user.userTG}

📋 Это <b>главное меню Proxym1ty</b>

🔴 Сейчас ваш сервер <b>Недоступен</b>
💵 <b>Баланс</b>: {user.moneyBalance}🌟XTR

Мы уже работаем над решением проблемы.

⚡ В случае <b>дополнительных проблем</b> обратитесь в <b>тех. поддержку</b>.
"""


TECH_ASSISTANCE_RESPONSE = lambda user: f"""
🛠️ Техническая поддержка Proxym1ty

Если у вас возникли вопросы или проблемы, наша команда готова помочь!

📩 Контакты для связи:
🔹 Чат поддержки: {'{TA_contact}'}

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
📅 Оплата <b>{user.PaymentDate.strftime("%d.%m.%Y")}</b> просрочена!

Чтобы возобновить доступ пополните баланс 👇
"""

MONEY_ENDING = lambda user: f"""
<b>{user.userTG} внимание!</b>
⌚ <i>У вас заканчиваются средства на балансе!</i>
💳 Баланс необходимо пополнить до <b>{user.PaymentDate.strftime("%d.%m.%Y")}</b>
💸 В этом месяце вам нужно заплатить <b>{user.PaymentSum}🌟XTR</b>
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


NEW_PRE_PAYMENT_ADMIN_REPLY = lambda name, currency, sum,: f"""
💸 Новая оплата!
🚹 Name: {name}
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

BALANCE_TOPUP_USER_REPLY = lambda user, summ: f"""
✅ <b>Пополнение баланса</b> на сумму {summ}🌟XTR!
💵 <b>Баланс</b>: {user.moneyBalance}🌟XTR"""