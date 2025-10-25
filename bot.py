import telebot

bot = telebot.TeleBot("8295636525:AAFGetVCsM0ScQY4OcfxybvH0g9KNoTEuOw")

my_button = telebot.types.InlineKeyboardButton("سازنده ربات ", url="https://t.me/V1TOW")
my_markup = telebot.types.InlineKeyboardMarkup()
my_markup.add(my_button)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_chat_action(message.chat.id, action='typing')
    bot.reply_to(message, f"سلام {message.chat.first_name} به ربات MY INFO خوش امدی 😈 \n دستورات ربات : \n /start = با این کامند ربات استارت میشود 😁 \n /info = با این کامند ربات میتوانید اطلاعات  ان را ببینید 😃 \n /me = با این دستور میتوانید اطلاعات اکانت خود را ببینید 😍 ", reply_markup=my_markup)

@bot.message_handler(commands=['info'])
def send_help(message):
    bot.send_chat_action(message.chat.id, action='typing')
    bot.reply_to(message, f"سلام {message.chat.first_name} به بخش درباره ربات  خوش امدید 😁 \n این ربات ساخته شده است با پایتون \n و این ربات به شماره اجازه میدهد تا اطلاعات اکانت خود را ببینید  ")

@bot.message_handler(commands=['me'])
def send_info(message):
    bot.send_chat_action(message.chat.id, action='typing')
    bot.reply_to(message, f"اطلاعات اکانت شما 😯\n اسم شما : {message.chat.first_name}\n فامیلی شما : {message.chat.last_name}\n یوسرنیم شما : {message.chat.user_name}\n ایدی شما : {message.chat.id}\n امیدوارم راضی باشید 🥱")
bot.polling()
