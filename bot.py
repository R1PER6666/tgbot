import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from flask import Flask, request

API_TOKEN = os.getenv('BOT_TOKEN', '8180343293:AAEnH5aGstLSYZ0RvBRrr8Wx1AQRubRsat4')  # Токен бота из переменных окружения
ADMIN_ID = int(os.getenv('ADMIN_ID', '7018589360'))  # Telegram ID админа из переменных окружения

bot = telebot.TeleBot(API_TOKEN)

# Хранилище для заблокированных пользователей
blocked_users = set()

# Создаем Flask приложение
app = Flask(__name__)

# Функция для блокировки пользователя
def block_user(user_id):
    blocked_users.add(user_id)

# Хэндлер для приема сообщений от пользователей
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    # Проверяем, не заблокирован ли пользователь
    if user_id in blocked_users:
        try:
            bot.send_message(message.chat.id, "Вы заблокированы и не можете использовать этого бота.")
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 403:
                print(f"Пользователь {user_id} заблокировал бота.")
        return

    # Пересылаем сообщение администратору
    forwarded_message = f"Сообщение от @{message.from_user.username or message.from_user.first_name} (ID: {user_id}): {message.text or 'Сообщение без текста'}"
    markup = InlineKeyboardMarkup()
    block_button = InlineKeyboardButton(text="Заблокировать", callback_data=f"block_{user_id}")
    markup.add(block_button)
    
    try:
        # Отправляем сообщение с кнопкой "Заблокировать" админу
        bot.send_message(chat_id=ADMIN_ID, text=forwarded_message, reply_markup=markup)
        
        # Подтверждение пользователю, что сообщение отправлено админу
        bot.send_message(message.chat.id, "Ваше сообщение отправлено администратору. Вы получите ответ в ближайшее время.")
        
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            print(f"Пользователь {user_id} заблокировал бота.")
        else:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

# Обработчик для нажатия на кнопку "Заблокировать"
@bot.callback_query_handler(func=lambda call: call.data.startswith('block_'))
def handle_block(call):
    user_id = int(call.data.split('_')[1])
    
    # Блокируем пользователя
    block_user(user_id)
    
    try:
        # Уведомляем админа о блокировке
        bot.send_message(ADMIN_ID, f"Пользователь с ID {user_id} был заблокирован.")
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Ошибка при отправке сообщения админу: {e}")
    
    # Закрываем запрос нажатия на кнопку
    bot.answer_callback_query(call.id, "Пользователь заблокирован.")

# Вебхуки для Heroku
@app.route('/' + API_TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200

@app.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://<your-heroku-app>.herokuapp.com/{API_TOKEN}")
    return 'Webhook set!', 200

# Запуск Flask приложения
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))