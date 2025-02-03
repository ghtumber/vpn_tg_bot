
REPLY_REGISTRATION = f"""
👋 Приветствуем в proxym1ty!

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

USER_GREETING_REPLY = lambda username, paymentSum, paymentDate, serverName, serverLocation, user_balance: f"""
✨ <b>Привет</b> {username}

📋 Это <b>главное меню Proxym1ty</b>

Здесь ты можешь управлять своим VPN и следить за использованием

💵 <b>Баланс</b>: {user_balance}руб.
🛰 <b>Сервер</b>: {serverName}
🏳 <b>Страна VPN</b>: {serverLocation}
💳 <b>Следующая оплата</b> — {paymentSum}руб. {paymentDate.strftime("%d.%m.%Y")}

⚡ Вот что можно посмотреть.
"""

CLEAN_USER_GREETING_REPLY = lambda username, user_balance: f"""
✨ <b>Привет</b> {username}

📋 Это <b>главное меню Proxym1ty</b>

Здесь ты можешь управлять своим VPN

💵 <b>Баланс</b>: {user_balance}руб.

⚡ Чтобы купить VPN, просто выбери нужный пункт.
"""

PAYD_PERIOD_ENDING = lambda user: f"""
<b>{user.userTG} внимание!</b>
⌚ <i>У вас заканчивается оплаченный период использования VPN!</i>
💳 Подписку нужно оплатить до <b>{user.PaymentDate.strftime("%d.%m.%Y")}</b>
💸 В этом месяце вам нужно заплатить <b>{user.PaymentSum}руб.</b>
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

NEW_DONATION_ADMIN_REPLY = lambda name, comment, sum, user, success, error: f"""
💸 Новая оплата!
🚹 Name: {name}
🧾 Comment: {comment}
💰 Манесы: {sum}руб
{f'⛔ Error: {error}' if error else ''}
{f'''User DB:
🔗TG: {user.userTG}
🌐 Svr name: {user.serverName}
💰New balance: {user.moneyBalance}''' if success else '⛔ User не найден'}"""


BALANCE_TOPUP_USER_REPLY = lambda user, sum: f"""
✅ <b>Пополнение баланса</b> на сумму {sum} руб!
💵 <b>Баланс</b>: {user.moneyBalance} руб."""