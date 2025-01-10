from frontend.replys import GLOBAL_ALERT, PAYD_PERIOD_ENDING
from globals import bot, ADMINS, MENU_KEYBOARD_MARKUP
from backend.models import XClient, User


class PeriodEndingNotification:
    def __init__(self, users_to: list[User]):
        self.users_to = users_to
        self.callback_to = ADMINS

    async def send(self):
        try:
            for user in self.users_to:
                text = PAYD_PERIOD_ENDING(user=user)
                await bot.send_message(chat_id=user.userID, text=text)
            receivers = "".join([f"{i.userTG}, " for i in self.users_to])
            for adm in self.callback_to:
                await bot.send_message(chat_id=adm, text=f"✅ Оповещения об оплате разосланы! Получатели: {receivers}", reply_markup=MENU_KEYBOARD_MARKUP)
            return True
        except Exception as e:
            for adm in self.callback_to:
                await bot.send_message(chat_id=adm, text=f"⛔ Оповещения не отправлены, ошибка:\n\n {e}", reply_markup=MENU_KEYBOARD_MARKUP)
            return False


class GlobalNotification:
    def __init__(self, text: str, users_to: list[User], callback_to: int):
        self.text = text
        self.users_to = users_to
        self.callback_to = callback_to

    async def send(self):
        try:
            for user in self.users_to:
                text = GLOBAL_ALERT(user=user, alert=self.text)
                await bot.send_message(chat_id=user.userID, text=text)
            receivers = "".join([f"{i.userTG}, " for i in self.users_to])
            await bot.send_message(chat_id=self.callback_to, text=f"✅ Глобальные оповещения разосланы! Получатели: {receivers}", reply_markup=MENU_KEYBOARD_MARKUP)
            return True
        except Exception as e:
            await bot.send_message(chat_id=self.callback_to, text=f"⛔ Оповещений не отправлена, ошибка:\n\n {e}", reply_markup=MENU_KEYBOARD_MARKUP)
            return False



