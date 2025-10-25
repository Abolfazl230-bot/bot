import os
import sqlite3
import threading
from datetime import datetime, timezone
import telebot
from telebot import types

BOT_TOKEN = "8171266389:AAEb8cuUBHe1gruKAyMUdiKTqKOJ-mEcMz8"
ADMIN_IDS = [8244066327]
bot = telebot.TeleBot(BOT_TOKEN)
lock = threading.Lock()

def db_connect():
    return sqlite3.connect('bot_db.db', check_same_thread=False)

def init_db():
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, username TEXT, language_code TEXT, chat_type TEXT, ts TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY, reason TEXT, date_banned TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS forced_join (channel_username TEXT PRIMARY KEY, channel_name TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS groups (chat_id INTEGER PRIMARY KEY, title TEXT, username TEXT, added_by INTEGER, date_added TEXT)')
        conn.commit()
        conn.close()

init_db()

def is_admin(uid):
    return uid in ADMIN_IDS

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def add_user_record(user, chat_type):
    try:
        with lock:
            conn = db_connect()
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?)', (
                user.id,
                getattr(user, 'first_name', None),
                getattr(user, 'last_name', None),
                getattr(user, 'username', None),
                getattr(user, 'language_code', None),
                chat_type,
                now_iso()
            ))
            conn.commit()
            conn.close()
    except:
        pass

def get_all_user_ids():
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('SELECT user_id FROM users')
        rows = [r[0] for r in c.fetchall()]
        conn.close()
    return rows

def ban_user_db(uid, reason='توسط ادمین'):
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO banned_users VALUES (?, ?, ?)', (uid, reason, now_iso()))
        conn.commit()
        conn.close()

def unban_user_db(uid):
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('DELETE FROM banned_users WHERE user_id=?', (uid,))
        conn.commit()
        conn.close()

def get_banned_list_db():
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('SELECT * FROM banned_users')
        rows = c.fetchall()
        conn.close()
    return rows

def add_forced_channel_db(username, name=None):
    username = username.strip()
    if not username:
        return False
    if not username.startswith('@'):
        username = '@' + username
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO forced_join VALUES (?, ?)', (username, name or username))
        conn.commit()
        conn.close()
    return True

def remove_forced_channel_db(username):
    username = username.strip()
    if not username:
        return False
    if not username.startswith('@'):
        username = '@' + username
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('DELETE FROM forced_join WHERE channel_username=?', (username,))
        conn.commit()
        conn.close()
    return True

def get_forced_channels_db():
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('SELECT channel_username FROM forced_join')
        rows = [r[0] for r in c.fetchall()]
        conn.close()
    return rows

def add_group_db(chat, added_by):
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO groups VALUES (?, ?, ?, ?, ?)', (
            chat.id,
            getattr(chat, 'title', None),
            getattr(chat, 'username', None),
            added_by,
            now_iso()
        ))
        conn.commit()
        conn.close()

def check_user_banned(uid):
    with lock:
        conn = db_connect()
        c = conn.cursor()
        c.execute('SELECT 1 FROM banned_users WHERE user_id=?', (uid,))
        res = c.fetchone()
        conn.close()
    return bool(res)

def check_forced_join(uid):
    channels = get_forced_channels_db()
    if not channels:
        return True, None
    for ch in channels:
        try:
            member = bot.get_chat_member(ch, uid)
            if getattr(member, 'status', '') in ['left', 'kicked']:
                return False, ch
        except Exception as e:
            return False, ch
    return True, None

def send_join_request(chat_id, channel_username):
    keyboard = types.InlineKeyboardMarkup()
    url = f'https://t.me/{channel_username.strip("@")}'
    keyboard.row(types.InlineKeyboardButton('ورود به کانال', url=url))
    keyboard.row(types.InlineKeyboardButton('✅ بررسی عضویت', callback_data=f'check_join:{channel_username}'))
    text = f'❌ برای استفاده از ربات ابتدا باید در کانال {channel_username} عضو شوید. لطفا روی «ورود به کانال» کلیک کنید سپس «✅ بررسی عضویت» را بزنید.'
    try:
        bot.send_message(chat_id, text, reply_markup=keyboard)
    except:
        pass

@bot.message_handler(commands=['start'])
def cmd_start(message):
    add_user_record(message.from_user, message.chat.type)
    if check_user_banned(message.from_user.id):
        try:
            bot.send_message(message.chat.id, '🚫 شما از ربات مسدود شده‌اید')
        except:
            pass
        return
    joined, channel = check_forced_join(message.from_user.id)
    if not joined:
        send_join_request(message.chat.id, channel)
        return
    text = (
        "سلام! 👋\n\n"
        "این ربات برای دریافت اطلاعات چت و مدیریت گروه‌ها طراحی شده است.\n\n"
        "دستورات:\n"
        "• /start - نمایش این پیام\n"
        "• /help - راهنما\n"
        "• /get - در گروه‌ها شناسه گروه را نمایش می‌دهد\n\n"
        "برای دریافت اطلاعات یک کاربر، پیام آن کاربر را فوروارد کنید یا یوزرنیمش را بفرستید.\n"
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('راهنما کامل', callback_data='show_help'))
    try:
        bot.send_message(message.chat.id, text, reply_markup=keyboard)
    except:
        pass

@bot.message_handler(commands=['help'])
def cmd_help(message):
    add_user_record(message.from_user, message.chat.type)
    if check_user_banned(message.from_user.id):
        try:
            bot.send_message(message.chat.id, '🚫 شما از ربات مسدود شده‌اید')
        except:
            pass
        return
    joined, channel = check_forced_join(message.from_user.id)
    if not joined:
        send_join_request(message.chat.id, channel)
        return
    text = (
        "راهنمای سریع:\n\n"
        "• برای دریافت Chat ID گروه، ربات را به گروه اضافه کنید و دستور /get را ارسال کنید.\n"
        "• برای دریافت اطلاعات کاربر، پیام او را فوروارد کنید یا @username را ارسال کنید.\n"
        "• ادمین‌ها با /admin می‌توانند کانال‌های اجباری را مدیریت کنند.\n"
    )
    try:
        bot.send_message(message.chat.id, text)
    except:
        pass

@bot.message_handler(commands=['admin'])
def cmd_admin(message):
    if not is_admin(message.from_user.id):
        return
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton('📢 ارسال همگانی', callback_data='broadcast'),
        types.InlineKeyboardButton('🚫 بن کاربر', callback_data='ban_user')
    )
    keyboard.row(
        types.InlineKeyboardButton('✅ آنبن کاربر', callback_data='unban_user'),
        types.InlineKeyboardButton('📋 لیست بن شده‌ها', callback_data='banned_list')
    )
    keyboard.row(
        types.InlineKeyboardButton('➕ افزودن کانال اجباری', callback_data='add_channel'),
        types.InlineKeyboardButton('➡️ حذف کانال اجباری', callback_data='remove_channel')
    )
    keyboard.row(types.InlineKeyboardButton('📚 لیست کانال‌های اجباری', callback_data='list_channels'))
    try:
        bot.send_message(message.chat.id, '🛠️ پنل مدیریت', reply_markup=keyboard)
    except:
        pass

@bot.callback_query_handler(func=lambda call: True)
def all_callbacks(call):
    uid = call.from_user.id
    data = call.data or ''
    if data == 'broadcast' and is_admin(uid):
        msg = bot.send_message(call.message.chat.id, '📝 لطفا پیام همگانی را ارسال کنید:')
        bot.register_next_step_handler(msg, process_broadcast)
        bot.answer_callback_query(call.id)
        return
    if data == 'ban_user' and is_admin(uid):
        msg = bot.send_message(call.message.chat.id, '🚫 لطفا کاربر را فوروارد یا آی‌دی را ارسال کنید:')
        bot.register_next_step_handler(msg, process_ban)
        bot.answer_callback_query(call.id)
        return
    if data == 'unban_user' and is_admin(uid):
        msg = bot.send_message(call.message.chat.id, '✅ لطفا آی‌دی کاربر برای آنبن را ارسال کنید:')
        bot.register_next_step_handler(msg, process_unban)
        bot.answer_callback_query(call.id)
        return
    if data == 'banned_list' and is_admin(uid):
        rows = get_banned_list_db()
        if rows:
            text = '🚫 کاربران بن شده:\n\n'
            for r in rows:
                text += f'• <code>{r[0]}</code> - {r[1]}\n'
        else:
            text = '✅ هیچ کاربری بن نشده است'
        bot.answer_callback_query(call.id)
        try:
            bot.send_message(call.message.chat.id, text, parse_mode='HTML')
        except:
            pass
        return
    if data == 'add_channel' and is_admin(uid):
        msg = bot.send_message(call.message.chat.id, '➕ لطفا یوزرنیم کانال را ارسال کنید (مثال: @channel):')
        bot.register_next_step_handler(msg, process_add_channel)
        bot.answer_callback_query(call.id)
        return
    if data == 'remove_channel' and is_admin(uid):
        msg = bot.send_message(call.message.chat.id, '➡️ لطفا یوزرنیم کانال را برای حذف ارسال کنید:')
        bot.register_next_step_handler(msg, process_remove_channel)
        bot.answer_callback_query(call.id)
        return
    if data == 'list_channels' and is_admin(uid):
        channels = get_forced_channels_db()
        if channels:
            text = '📢 کانال‌های اجباری:\n\n'
            for ch in channels:
                text += f'• {ch}\n'
        else:
            text = '❌ کانالی تنظیم نشده است'
        bot.answer_callback_query(call.id)
        try:
            bot.send_message(call.message.chat.id, text)
        except:
            pass
        return
    if data.startswith('check_join:'):
        channel = data.split(':',1)[1]
        try:
            member = bot.get_chat_member(channel, call.from_user.id)
            if getattr(member, 'status', '') not in ['left', 'kicked']:
                bot.answer_callback_query(call.id, '✅ عضویت تایید شد')
                try:
                    bot.send_message(call.message.chat.id, '🎉 شما عضو کانال هستید. اکنون می‌توانید از ربات استفاده کنید.')
                except:
                    pass
            else:
                bot.answer_callback_query(call.id, '❌ شما عضو کانال نیستید')
                send_join_request(call.message.chat.id, channel)
        except Exception:
            bot.answer_callback_query(call.id, '❌ امکان بررسی وجود ندارد')
            send_join_request(call.message.chat.id, channel)
        return

def process_broadcast(message):
    if not is_admin(message.from_user.id):
        return
    user_ids = get_all_user_ids()
    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            if message.content_type == 'text':
                bot.send_message(uid, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(uid, message.video.file_id, caption=message.caption)
            elif message.content_type == 'animation':
                bot.send_animation(uid, message.animation.file_id, caption=message.caption)
            elif message.content_type == 'document':
                bot.send_document(uid, message.document.file_id, caption=message.caption)
            sent += 1
        except:
            failed += 1
    try:
        bot.send_message(message.chat.id, f'📊 ارسال همگانی انجام شد:\n✅ موفق: {sent}\n❌ ناموفق: {failed}')
    except:
        pass

def process_ban(message):
    if not is_admin(message.from_user.id):
        return
    target = None
    if message.forward_from:
        target = message.forward_from
    elif message.text and message.text.strip().isdigit():
        target = type('obj', (), {'id': int(message.text.strip())})
    if target:
        ban_user_db(target.id)
        try:
            bot.send_message(message.chat.id, f'🚫 کاربر <code>{target.id}</code> بن شد', parse_mode='HTML')
        except:
            pass
    else:
        try:
            bot.send_message(message.chat.id, '❌ کاربر یافت نشد')
        except:
            pass

def process_unban(message):
    if not is_admin(message.from_user.id):
        return
    if message.text and message.text.strip().isdigit():
        uid = int(message.text.strip())
        unban_user_db(uid)
        try:
            bot.send_message(message.chat.id, f'✅ کاربر <code>{uid}</code> آنبن شد', parse_mode='HTML')
        except:
            pass

def process_add_channel(message):
    if not is_admin(message.from_user.id):
        return
    username = (message.text or '').strip()
    if add_forced_channel_db(username):
        try:
            bot.send_message(message.chat.id, f'✅ کانال {username} افزوده شد')
        except:
            pass
    else:
        try:
            bot.send_message(message.chat.id, '❌ ورودی نامعتبر است')
        except:
            pass

def process_remove_channel(message):
    if not is_admin(message.from_user.id):
        return
    username = (message.text or '').strip()
    if remove_forced_channel_db(username):
        try:
            bot.send_message(message.chat.id, f'➡️ کانال {username} حذف شد')
        except:
            pass
    else:
        try:
            bot.send_message(message.chat.id, '❌ ورودی نامعتبر است')
        except:
            pass

@bot.message_handler(commands=['get'], chat_types=['group', 'supergroup'])
def cmd_get(message):
    add_group_db(message.chat, message.from_user.id)
    add_user_record(message.from_user, message.chat.type)
    if check_user_banned(message.from_user.id):
        try:
            bot.send_message(message.chat.id, '🚫 شما از ربات مسدود شده‌اید')
        except:
            pass
        return
    joined, channel = check_forced_join(message.from_user.id)
    if not joined:
        send_join_request(message.chat.id, channel)
        return
    text = (
        '💬 اطلاعات این گروه:\n'
        f'• Chat ID: <code>{message.chat.id}</code>\n'
        f'• Title: {getattr(message.chat, "title", "-")}\n'
        f'• Username: @{getattr(message.chat, "username", "-")}'
    )

    try:
        bot.send_message(message.chat.id, text, parse_mode='HTML')
    except:
        pass

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    add_user_record(message.from_user, message.chat.type)
    if check_user_banned(message.from_user.id):
        try:
            bot.send_message(message.chat.id, '🚫 شما از ربات مسدود شده‌اید')
        except:
            pass
        return
    joined, channel = check_forced_join(message.from_user.id)
    if not joined:
        send_join_request(message.chat.id, channel)
        return
    if message.forward_from_chat and getattr(message.forward_from_chat, 'type', '') == "channel":
        ch = message.forward_from_chat
        text = (
            "📢 اطلاعات کانال فوروارد شده:\n\n"
            f"🆔 Chat ID: <code>{getattr(ch,'id','-')}</code>\n"
            f"📛 Title: {getattr(ch, 'title', '-')}\n"
            f"🔖 Username: @{getattr(ch, 'username', '-')}\n"
            f"📝 Type: {getattr(ch, 'type', '-')}"
        )
        try:
            bot.reply_to(message, text, parse_mode='HTML')
        except:
            pass
        return
    if message.forward_from:
        f = message.forward_from
        text = (
            '🔄 اطلاعات کاربر فوروارد شده:\n\n'
            f'👤 User ID: <code>{getattr(f,"id","-")}</code>\n'
            f'📛 First Name: {getattr(f, "first_name", "-")}\n'
            f'🏷️ Last Name: {getattr(f, "last_name", "-")}\n'
            f'🔖 Username: @{getattr(f, "username", "-")}'
        )
        try:
            bot.reply_to(message, text, parse_mode='HTML')
        except:
            pass
        return
    if message.text and message.text.startswith('@'):
        username = message.text.strip()
        try:
            info = bot.get_chat(username)
            text = (
                f'🔍 اطلاعات {username}:\n\n'
                f'👤 Chat ID: <code>{getattr(info,"id","-")}</code>\n'
                f'📛 First Name: {getattr(info, "first_name", "-")}\n'
                f'🏷️ Last Name: {getattr(info, "last_name", "-")}\n'
                f'🔖 Type: {getattr(info, "type", "-")}'
            )
        except:
            text = '❌ کاربر یافت نشد'
        try:
            bot.reply_to(message, text, parse_mode='HTML')
        except:
            pass
        return
    if message.text and message.text.replace('-', '').isdigit():
        try:
            chat_id = int(message.text)
            info = bot.get_chat(chat_id)
            text = (
                '💬 اطلاعات چت:\n\n'
                f'👤 Chat ID: <code>{getattr(info,"id","-")}</code>\n'
                f'📛 Title: {getattr(info, "title", "-")}\n'
                f'🔖 Username: @{getattr(info, "username", "-")}\n'
                f'📝 Type: {getattr(info, "type", "-")}'
            )
        except:
            text = '❌ چت یافت نشد'
        try:
            bot.reply_to(message, text, parse_mode='HTML')
        except:
            pass
        return
    if message.animation:
        a = message.animation
        text = (
            '🎬 اطلاعات گیف:\n\n'
            f'🆔 File ID: <code>{getattr(a,"file_id","-")}</code>\n'
            f'📊 File Size: {getattr(a, "file_size", "-")}\n'
            f'⏱️ Duration: {getattr(a, "duration", "-")}s\n'
            f'📏 Width: {getattr(a, "width", "-")}\n'
            f'📐 Height: {getattr(a, "height", "-")}'
        )
        try:
            bot.reply_to(message, text, parse_mode='HTML')
        except:
            pass
        return
    text = (
        '👤 اطلاعات شما:\n\n'
        f'🆔 User ID: <code>{message.from_user.id}</code>\n'
        f'📛 First Name: {getattr(message.from_user, "first_name", "-")}\n'
        f'🏷️ Last Name: {getattr(message.from_user, "last_name", "-")}\n'
        f'🔖 Username: @{getattr(message.from_user, "username", "-")}\n\n'
        '💬 اطلاعات چت:\n'
        f'🆔 Chat ID: <code>{message.chat.id}</code>\n'
        f'📝 Chat Type: {message.chat.type}'
    )
    try:
        bot.reply_to(message, text, parse_mode='HTML')
    except:
        pass

print("bot is starting")
bot.infinity_polling()
