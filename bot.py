import telebot
import random
import time
import os
import psycopg2
from telebot import types

TOKEN = os.environ.get("TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
bot = telebot.TeleBot(TOKEN)

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid BIGINT PRIMARY KEY,
            name TEXT,
            tag TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shaker (
            uid BIGINT PRIMARY KEY,
            score INTEGER DEFAULT 0,
            last_play BIGINT DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marriages (
            uid1 BIGINT,
            uid2 BIGINT,
            count INTEGER DEFAULT 1,
            since BIGINT,
            PRIMARY KEY (uid1, uid2)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_user(uid, name, tag):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (uid, name, tag) VALUES (%s, %s, %s)
        ON CONFLICT (uid) DO UPDATE SET name = EXCLUDED.name, tag = EXCLUDED.tag
    """, (uid, name, tag))
    conn.commit()
    cur.close()
    conn.close()

def get_user_tag(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT tag FROM users WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and row[0]:
        return "@" + row[0]
    return "пользователь"

def get_all_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid, tag FROM users WHERE tag IS NOT NULL")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_shaker(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT score, last_play FROM shaker WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0], row[1]
    return 0, 0

def update_shaker(uid, score, last_play):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO shaker (uid, score, last_play) VALUES (%s, %s, %s)
        ON CONFLICT (uid) DO UPDATE SET score = EXCLUDED.score, last_play = EXCLUDED.last_play
    """, (uid, score, last_play))
    conn.commit()
    cur.close()
    conn.close()

def get_shaker_top():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid, score FROM shaker ORDER BY score DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def add_marriage(uid1, uid2):
    a, b = sorted([uid1, uid2])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT count FROM marriages WHERE uid1 = %s AND uid2 = %s", (a, b))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE marriages SET count = count + 1 WHERE uid1 = %s AND uid2 = %s", (a, b))
    else:
        cur.execute("INSERT INTO marriages (uid1, uid2, count, since) VALUES (%s, %s, 1, %s)", (a, b, int(time.time())))
    conn.commit()
    cur.close()
    conn.close()

def get_marriages():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid1, uid2, count, since FROM marriages ORDER BY count DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def time_together(seconds):
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    if days > 0:
        return str(days) + " дн. " + str(hours) + " ч."
    elif hours > 0:
        return str(hours) + " ч. " + str(minutes) + " мин."
    else:
        return str(minutes) + " мин."

@bot.message_handler(commands=["start"])
def start(message):
    save_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    bot.send_message(message.chat.id, "Привет! Я бот Винди.")

@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(message.chat.id, "винди кто гей / винди браки / шейкер / ш топ")

def who_gay(message):
    all_u = get_all_users()
    if not all_u:
        bot.send_message(message.chat.id, "Никто ещё не писал в чате.")
        return
    uid, tag = random.choice(all_u)
    p = ["Я думаю гей - @" + tag, "Радар: @" + tag, "100% гей - @" + tag]
    bot.send_message(message.chat.id, random.choice(p))

def marry(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Нельзя жениться на себе")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Принять", callback_data="accept_" + str(me) + "_" + str(target_id)),
        types.InlineKeyboardButton("Отказаться", callback_data="reject_" + str(me) + "_" + str(target_id)),
    )
    text = a + " делает предложение " + b + "!\n\n" + b + ", ты согласен(на)?"
    bot.send_message(message.chat.id, text, reply_markup=kb)

def kiss(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя целовать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " страстно поцеловал " + b,
        a + " нежно поцеловал " + b,
        a + " поцеловал " + b + " в щёчку",
        a + " поцеловал " + b + " в губы",
        a + " чмокнул " + b,
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def show_marriages(message):
    rows = get_marriages()
    if not rows:
        bot.send_message(message.chat.id, "Пока никто не женился.")
        return
    now = time.time()
    t = "Список браков:\n\n"
    for i, (u1, u2, cnt, since) in enumerate(rows, 1):
        a = get_user_tag(u1)
        b = get_user_tag(u2)
        together = time_together(now - since)
        t += str(i) + ". " + a + " + " + b + "\n"
        t += "   Браков: " + str(cnt) + ", вместе: " + together + "\n\n"
    bot.send_message(message.chat.id, t)

def play_shaker(message):
    me = message.from_user.id
    save_user(me, message.from_user.first_name, message.from_user.username)
    score, last = get_shaker(me)
    now = int(time.time())
    if last > 0 and now - last < 1800:
        remaining = 1800 - (now - last)
        m = remaining // 60
        s = remaining % 60
        bot.reply_to(message, "Жди " + str(m) + "м " + str(s) + "с")
        return
    num = random.randint(1, 9)
    score += num
    update_shaker(me, score, now)
    name = message.from_user.first_name
    bot.send_message(message.chat.id, "Кинул шейкер: " + str(num) + "\nВсего: " + str(score))

def shaker_top(message):
    rows = get_shaker_top()
    if not rows:
        bot.send_message(message.chat.id, "Пока никто не играл.")
        return
    t = "Топ Шейкера:\n\n"
    for i, (uid, score) in enumerate(rows, 1):
        t += str(i) + ". " + get_user_tag(uid) + " - " + str(score) + "\n"
    bot.send_message(message.chat.id, t)

@bot.message_handler(content_types=["text"])
def echo(message):
    if message.from_user:
        save_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    if message.reply_to_message and message.reply_to_message.from_user:
        r = message.reply_to_message.from_user
        save_user(r.id, r.first_name, r.username)
    text = message.text.lower().strip()
    if text == "шейкер":
        play_shaker(message)
        return
    if text == "ш топ":
        shaker_top(message)
        return
    if "винди" in text and "брак" in text:
        show_marriages(message)
        return
    if "винди" in text and "гей" in text:
        who_gay(message)
        return
    if "ало" in text:
        responses = ["Ало", "Ало, чё надо?", "Алё-алё", "Ало, я тут", "Ало, не слышу"]
        bot.send_message(message.chat.id, random.choice(responses))
        return
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if "замуж" in text or "женись" in text or "женить" in text:
            marry(message, target_id)
        elif "поцеловать" in text or "поцелуй" in text or "чмок" in text:
            kiss(message, target_id)

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    parts = call.data.split("_")
    action = parts[0]
    uid1 = int(parts[1])
    uid2 = int(parts[2])
    if call.from_user.id != uid2:
        return
    if action == "accept":
        add_marriage(uid1, uid2)
        a = get_user_tag(uid1)
        b = get_user_tag(uid2)
        bot.edit_message_text("Женаты! " + a + " + " + b, call.message.chat.id, call.message.message_id)
    elif action == "reject":
        a = get_user_tag(uid1)
        b = get_user_tag(uid2)
        bot.edit_message_text(b + " отказал(а) " + a, call.message.chat.id, call.message.message_id)

init_db()
print("Бот запущен!")
bot.polling(none_stop=True)
