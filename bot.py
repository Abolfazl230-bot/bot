import telebot

bot = telebot.TeleBot("8295636525:AAFGetVCsM0ScQY4OcfxybvH0g9KNoTEuOw")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_chat_action(message.chat.id, action='typing')
    bot.reply_to(message, f"**سلام {message.chat.first_name} به ربات MY INFO خوش امدی 😍 **\n اسمت شما : `{message.chat.first_name}`\n ایدی عددی شما : `{message.chat.id}`")

bot.polling()
