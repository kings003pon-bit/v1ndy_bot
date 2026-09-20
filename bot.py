import telebot
import random
import time
import os
import datetime
import threading
import psycopg2
from telebot import types

TOKEN = os.environ.get("TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

ADMIN_ID = 5525844033
SECRET_CODE = "v1ndyfire"

bot = telebot.TeleBot(TOKEN)
pending_admin = {}
pending_coins = {}
games = {}

DOG_ART = """\\
╱▔▔╲▂▂▂╱▔▔╲
╲╱╳╱▔╲╱▔╲╱▔
┈┈┃▏▕▍▏▕▍▏
┈┈┃╲▂╱╲▂╱╲┈╭━╮
┈┈┃┊┳┊┊┊┊┊▔╰┳╯
┈┈┃┊╰━━━┳━━━╯
┈┈┃┊┊┊┊╭╯"""

CAT_ART = """\\
─────────────────────────
───────▄▀▄─────▄▀▄───────
──────▄█░░▀▀▀▀▀░░█▄──────
──▄▄──█░░░░░░░░░░░█──▄▄──
─█▄▄█─█░░▀░░┬░░▀░░█─█▄▄█─"""

SNAKE_ART = """\\
──────────────────────
▄▄▀█▄───▄───────▄─────
▀▀▀██──███─────███────
░▄██▀░█████░░░█████░░░
███▀▄███░███░███░███░▄
▀█████▀░░░▀███▀░░░▀██▀"""

PETS = {
    "dog": {"name": "Собака", "emoji": "🐶", "art": DOG_ART},
    "cat": {"name": "Кошка", "emoji": "🐱", "art": CAT_ART},
    "snake": {"name": "Змея", "emoji": "🐍", "art": SNAKE_ART},
}

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
        CREATE TABLE IF NOT EXISTS balance (
            uid BIGINT PRIMARY KEY,
            coins INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS duo_fires (
            uid1 BIGINT,
            uid2 BIGINT,
            fire INTEGER DEFAULT 1,
            is_grey INTEGER DEFAULT 0,
            last_uid1 BIGINT DEFAULT 0,
            last_uid2 BIGINT DEFAULT 0,
            last_extend BIGINT DEFAULT 0,
            PRIMARY KEY (uid1, uid2)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS duo_break (
            uid1 BIGINT,
            uid2 BIGINT,
            agree1 INTEGER DEFAULT 0,
            agree2 INTEGER DEFAULT 0,
            PRIMARY KEY (uid1, uid2)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS divorce_votes (
            uid1 BIGINT,
            uid2 BIGINT,
            agree1 INTEGER DEFAULT 0,
            agree2 INTEGER DEFAULT 0,
            PRIMARY KEY (uid1, uid2)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            uid BIGINT PRIMARY KEY,
            pet_type TEXT,
            pet_name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pet_skins (
            uid BIGINT,
            pet_type TEXT,
            PRIMARY KEY (uid, pet_type)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fire_system (
            id INTEGER PRIMARY KEY,
            last_expire BIGINT DEFAULT 0
        )
    """)
    cur.execute("""
        INSERT INTO fire_system (id, last_expire) VALUES (1, 0)
        ON CONFLICT (id) DO NOTHING
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_user(uid, name, tag):
    if not uid:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (uid, name, tag) VALUES (%s, %s, %s)
        ON CONFLICT (uid) DO UPDATE SET name = EXCLUDED.name, tag = EXCLUDED.tag
    """, (uid, name, tag))
    cur.execute("""
        INSERT INTO balance (uid, coins, wins) VALUES (%s, 0, 0)
        ON CONFLICT (uid) DO NOTHING
    """, (uid,))
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

def get_uid_by_tag(tag):
    tag = tag.replace("@", "")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid FROM users WHERE LOWER(tag) = LOWER(%s)", (tag,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_all_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid, tag FROM users WHERE tag IS NOT NULL")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# ========== БАЛАНС ==========

def get_balance(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT coins, wins FROM balance WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0], row[1]
    return 0, 0

def add_coins(uid, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO balance (uid, coins, wins) VALUES (%s, %s, 0)
        ON CONFLICT (uid) DO UPDATE SET coins = balance.coins + %s
    """, (uid, amount, amount))
    conn.commit()
    cur.close()
    conn.close()

def set_coins(uid, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO balance (uid, coins, wins) VALUES (%s, %s, 0)
        ON CONFLICT (uid) DO UPDATE SET coins = %s
    """, (uid, amount, amount))
    conn.commit()
    cur.close()
    conn.close()

def add_win(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO balance (uid, coins, wins) VALUES (%s, 0, 1)
        ON CONFLICT (uid) DO UPDATE SET wins = balance.wins + 1
    """, (uid,))
    conn.commit()
    cur.close()
    conn.close()

def get_level(coins):
    if coins <= 100:
        return 1
    level = 1
    high = 100
    while level < 50:
        next_high = high * 2
        if coins <= next_high:
            return level + 1
        level += 1
        high = next_high
    return 50

def get_balance_top():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid, coins FROM balance ORDER BY coins DESC LIMIT 5")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# ========== ПИТОМЦЫ ==========

def get_pet(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT pet_type, pet_name FROM pets WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def create_pet(uid, pet_type):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pets (uid, pet_type, pet_name) VALUES (%s, %s, NULL)
        ON CONFLICT (uid) DO NOTHING
    """, (uid, pet_type))
    cur.execute("""
        INSERT INTO pet_skins (uid, pet_type) VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (uid, pet_type))
    conn.commit()
    cur.close()
    conn.close()

def set_pet_name(uid, name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE pets SET pet_name = %s WHERE uid = %s", (name, uid))
    conn.commit()
    cur.close()
    conn.close()

def set_pet_type(uid, pet_type):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE pets SET pet_type = %s WHERE uid = %s", (pet_type, uid))
    cur.execute("""
        INSERT INTO pet_skins (uid, pet_type) VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (uid, pet_type))
    conn.commit()
    cur.close()
    conn.close()

def get_pet_skins(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT pet_type FROM pet_skins WHERE uid = %s", (uid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

# ========== ПАРНЫЙ ОГОНЁК ==========

def get_all_duo_fires(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT uid1, uid2, fire, is_grey, last_uid1, last_uid2, last_extend
        FROM duo_fires WHERE uid1 = %s OR uid2 = %s
    """, (uid, uid))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_duo_fire_with(uid, partner_uid):
    a, b = sorted([uid, partner_uid])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT uid1, uid2, fire, is_grey, last_uid1, last_uid2, last_extend
        FROM duo_fires WHERE uid1 = %s AND uid2 = %s
    """, (a, b))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def count_duo_fires(uid):
    return len(get_all_duo_fires(uid))

def create_duo_fire(uid1, uid2):
    a, b = sorted([uid1, uid2])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO duo_fires (uid1, uid2, fire, is_grey, last_uid1, last_uid2, last_extend)
        VALUES (%s, %s, 1, 0, %s, %s, %s)
        ON CONFLICT (uid1, uid2) DO NOTHING
    """, (a, b, int(time.time()), int(time.time()), int(time.time())))
    conn.commit()
    cur.close()
    conn.close()

def update_duo_fire(uid1, uid2, fire, is_grey, last_uid1, last_uid2, last_extend):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE duo_fires SET fire = %s, is_grey = %s, last_uid1 = %s, last_uid2 = %s, last_extend = %s
        WHERE uid1 = %s AND uid2 = %s
    """, (fire, is_grey, last_uid1, last_uid2, last_extend, uid1, uid2))
    conn.commit()
    cur.close()
    conn.close()

def delete_duo_fire(uid1, uid2):
    a, b = sorted([uid1, uid2])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM duo_fires WHERE uid1 = %s AND uid2 = %s", (a, b))
    cur.execute("DELETE FROM duo_break WHERE uid1 = %s AND uid2 = %s", (a, b))
    conn.commit()
    cur.close()
    conn.close()

def get_duo_top():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid1, uid2, fire FROM duo_fires ORDER BY fire DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_last_expire():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT last_expire FROM fire_system WHERE id = 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 0

def set_last_expire(ts):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE fire_system SET last_expire = %s WHERE id = 1", (ts,))
    conn.commit()
    cur.close()
    conn.close()

def expire_all_fires():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE duo_fires SET is_grey = 1, last_uid1 = 0, last_uid2 = 0 WHERE is_grey = 0")
    conn.commit()
    cur.close()
    conn.close()

def background_fire_check():
    while True:
        try:
            now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
            today_start = datetime.datetime(now.year, now.month, now.day, 0, 1).timestamp()
            last = get_last_expire()
            if now.hour == 0 and now.minute == 1 and int(last) < int(today_start):
                expire_all_fires()
                set_last_expire(int(now.timestamp()))
        except Exception as e:
            print("Fire check error:", e)
        time.sleep(60)

# ========== БРАК ==========

def get_marriage(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid1, uid2, count, since FROM marriages WHERE uid1 = %s OR uid2 = %s", (uid, uid))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

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

def delete_marriage(uid1, uid2):
    a, b = sorted([uid1, uid2])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM marriages WHERE uid1 = %s AND uid2 = %s", (a, b))
    cur.execute("DELETE FROM divorce_votes WHERE uid1 = %s AND uid2 = %s", (a, b))
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
    return str(minutes) + " мин."

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

# ========== РАЗВОД ==========

def divorce_request(message):
    me = message.from_user.id
    row = get_marriage(me)
    if not row:
        bot.send_message(message.chat.id, "У тебя нет брака")
        return
    uid1, uid2 = row[0], row[1]
    a = get_user_tag(uid1)
    b = get_user_tag(uid2)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO divorce_votes (uid1, uid2, agree1, agree2) VALUES (%s, %s, 0, 0)
        ON CONFLICT (uid1, uid2) DO UPDATE SET agree1 = 0, agree2 = 0
    """, (uid1, uid2))
    conn.commit()
    cur.close()
    conn.close()
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Да", callback_data="divorce_yes_" + str(uid1) + "_" + str(uid2)),
        types.InlineKeyboardButton("Нет", callback_data="divorce_no_" + str(uid1) + "_" + str(uid2)),
    )
    text = a + " и " + b + ", вы хотите разрушить брак?"
    bot.send_message(message.chat.id, text, reply_markup=kb)

# ========== ПОТУШЕНИЕ ОГОНЬКА ==========

def extinguish_request(message, target_id):
    me = message.from_user.id
    row = get_duo_fire_with(me, target_id)
    if not row:
        partner = get_user_tag(target_id)
        bot.send_message(message.chat.id, "У тебя нет огонька с " + partner)
        return
    uid1, uid2 = row[0], row[1]
    a = get_user_tag(uid1)
    b = get_user_tag(uid2)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO duo_break (uid1, uid2, agree1, agree2) VALUES (%s, %s, 0, 0)
        ON CONFLICT (uid1, uid2) DO UPDATE SET agree1 = 0, agree2 = 0
    """, (uid1, uid2))
    conn.commit()
    cur.close()
    conn.close()
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Да", callback_data="ext_yes_" + str(uid1) + "_" + str(uid2)),
        types.InlineKeyboardButton("Нет", callback_data="ext_no_" + str(uid1) + "_" + str(uid2)),
    )
    text = a + " и " + b + ", вы хотите потушить огонёк?"
    bot.send_message(message.chat.id, text, reply_markup=kb)

# ========== ИГРА «УГАДАЙ ЧИСЛО» ==========

def start_game(message):
    me = message.from_user.id
    if me in games:
        bot.send_message(message.chat.id, "Игра уже началась")
        return
    games[me] = {"num": random.randint(1, 100), "attempts": 7}
    text = "🎲 Я загадал число от 1 до 100!\n\n"
    text += "Пиши числа в ответ на это сообщение.\n"
    text += "У тебя 7 попыток."
    bot.send_message(message.chat.id, text)

def guess_number(message):
    me = message.from_user.id
    if me not in games:
        return
    try:
        num = int(message.text.strip())
    except:
        return
    if num < 1 or num > 100:
        return
    game = games[me]
    secret = game["num"]
    game["attempts"] -= 1
    if num == secret:
        reward = random.randint(10, 20)
        add_coins(me, reward)
        add_win(me)
        del games[me]
        bot.reply_to(message, "🎉 Угадал! Число " + str(secret) + "\n\n+" + str(reward) + " монет 💰")
        return
    if game["attempts"] <= 0:
        del games[me]
        bot.reply_to(message, "❌ Не угадал! Число было " + str(secret) + ".")
        return
    if num < secret:
        bot.reply_to(message, "Больше ⬆️ (" + str(game["attempts"]) + " попыток)")
    else:
        bot.reply_to(message, "Меньше ⬇️ (" + str(game["attempts"]) + " попыток)")

# ========== РАНДОМ ==========

def coin_flip(message):
    bot.send_message(message.chat.id, random.choice(["🪙 Орёл!", "🪙 Решка!"]))

def yes_no(message):
    bot.send_message(message.chat.id, random.choice(["✅ Да!", "❌ Нет!"]))

# ========== СТАРТ ==========

@bot.message_handler(commands=["start"])
def start(message):
    save_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    text = "Я — Винди.\n\n"
    text += "Со мной ты можешь растить огонёк, обниматься, играть и многое другое.\n\n"
    text += "Напиши «винди огонёк @user», чтобы начать."
    bot.send_message(message.chat.id, text)

# ========== ПРОФИЛЬ И БАЛИК ==========

def show_profile(message):
    me = message.from_user.id
    save_user(me, message.from_user.first_name, message.from_user.username)
    coins, wins = get_balance(me)
    level = get_level(coins)
    t = "👤 Профиль " + get_user_tag(me) + "\n\n"
    t += "🆙 Уровень: " + str(level) + "\n"
    t += "💰 Монеты: " + str(coins) + "\n"
    t += "🎲 Побед: " + str(wins) + "\n"
    fires = get_all_duo_fires(me)
    if fires:
        for i, f in enumerate(fires, 1):
            uid1, uid2, fire, is_grey, last1, last2, last_ext = f
            partner_id = uid2 if me == uid1 else uid1
            partner = get_user_tag(partner_id)
            status = "серый ⚫" if is_grey else "зажжён 🔴"
            t += "🔥 Огонёк " + str(i) + ": " + partner + " (" + status + ", " + str(fire) + ")\n"
    mar = get_marriage(me)
    if mar:
        uid1, uid2, cnt, since = mar
        partner_id = uid2 if me == uid1 else uid1
        partner = get_user_tag(partner_id)
        together = time_together(time.time() - since)
        t += "💍 Брак: " + partner + " (вместе " + together + ")\n"
    score, last = get_shaker(me)
    if score > 0:
        t += "🎮 Шейкер: " + str(score) + "\n"
    pet = get_pet(me)
    if pet:
        pet_type, pet_name = pet
        info = PETS.get(pet_type)
        if info:
            t += info["emoji"] + " Питомец: " + info["name"] + "\n"
    bot.send_message(message.chat.id, t)

def show_balance(message):
    me = message.from_user.id
    save_user(me, message.from_user.first_name, message.from_user.username)
    coins, _ = get_balance(me)
    bot.send_message(message.chat.id, "💰 Балик: " + str(coins))

def show_balance_top(message):
    rows = get_balance_top()
    if not rows:
        bot.send_message(message.chat.id, "Пока нет баликов.")
        return
    t = "🏆 Топ баликов\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, coins) in enumerate(rows):
        prefix = medals[i] if i < 3 else str(i + 1) + "."
        t += prefix + " " + get_user_tag(uid) + " — " + str(coins) + "\n"
    bot.send_message(message.chat.id, t)

# ========== ПИТОМЕЦ — КОМАНДЫ ==========

def buy_pet(message):
    me = message.from_user.id
    save_user(me, message.from_user.first_name, message.from_user.username)
    if get_pet(me):
        bot.send_message(message.chat.id, "У тебя уже есть питомец")
        return
    coins, _ = get_balance(me)
    if coins < 45:
        bot.send_message(message.chat.id, "Недостаточно монет. Нужно 45")
        return
    set_coins(me, coins - 45)
    r = random.randint(1, 100)
    if r <= 33:
        pet_type = "dog"
    elif r <= 66:
        pet_type = "cat"
    else:
        pet_type = "snake"
    create_pet(me, pet_type)
    info = PETS[pet_type]
    bot.send_message(message.chat.id, "🎉 Тебе выпал питомец: " + info["emoji"] + " " + info["name"] + "!")

def show_pet(message):
    me = message.from_user.id
    pet = get_pet(me)
    if not pet:
        bot.send_message(message.chat.id, "У тебя нет питомца. Купи: винди заведи питомца")
        return
    pet_type, pet_name = pet
    info = PETS.get(pet_type)
    if not info:
        return
    t = info["emoji"] + " " + info["name"] + "\n\n"
    t += info["art"] + "\n\n"
    if pet_name:
        t += "Имя: " + pet_name
    else:
        t += "Имя: не задано\nНапиши: изменить имя питомца [имя]"
    bot.send_message(message.chat.id, t)

def change_pet_name(message, new_name):
    me = message.from_user.id
    pet = get_pet(me)
    if not pet:
        bot.send_message(message.chat.id, "У тебя нет питомца. Купи: винди заведи питомца")
        return
    set_pet_name(me, new_name)
    bot.send_message(message.chat.id, "✅ Имя питомца изменено на " + new_name)

def show_pet_skins(message):
    me = message.from_user.id
    pet = get_pet(me)
    if not pet:
        bot.send_message(message.chat.id, "У тебя нет питомца. Купи: винди заведи питомца")
        return
    current_type, _ = pet
    skins = get_pet_skins(me)
    if not skins:
        bot.send_message(message.chat.id, "У тебя нет скинов.")
        return
    if len(skins) == 1:
        info = PETS.get(skins[0])
        bot.send_message(message.chat.id, info["emoji"] + " " + info["name"] + " (сейчас)")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for s in skins:
        info = PETS.get(s)
        label = info["emoji"] + " " + info["name"]
        if s == current_type:
            label += " (сейчас)"
        buttons.append(types.InlineKeyboardButton(label, callback_data="skin_" + s))
    kb.add(*buttons)
    bot.send_message(message.chat.id, "Выбери скин:", reply_markup=kb)

# ========== ДЕЙСТВИЯ ==========

def kiss(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя целовать нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " страстно поцеловал " + b + " 💋", a + " нежно поцеловал " + b + " 💞",
        a + " поцеловал " + b + " в щёчку 😘", a + " поцеловал " + b + " в губы 💋",
        a + " чмокнул " + b + " 😚",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def hug(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя обнять нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " нежно обнял " + b + " 💞", a + " крепко обнял " + b + " 🤗",
        a + " тепло обнял " + b + " 💖", a + " обнял " + b + " от всей души ❤️",
        a + " крепко-крепко обнял " + b + " 🫂", a + " мило обнял " + b + " 💕",
        a + " по-дружески обнял " + b + " 🤝", a + " сжал " + b + " в объятиях 💗",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def hit(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя бить нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " ударил " + b + " 💥", a + " сильно ударил " + b + " ⚡",
        a + " ударил " + b + " в плечо 🥊", a + " дал " + b + " пощёчину ✋",
        a + " ударил " + b + " кулаком 👊", a + " заехал " + b + " по голове 💢",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def kick(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя пинать нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " пнул " + b + " 🦵", a + " пнул " + b + " под зад 🦶",
        a + " сильно пнул " + b + " 🦿", a + " пнул " + b + " в бок 💨",
        a + " пнул " + b + " ногой 🦵", a + " дал " + b + " пинка 👟",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def slap(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя шлёпать нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " шлёпнул " + b + " 🖐", a + " звонко шлёпнул " + b + " 👋",
        a + " шлёпнул " + b + " по попе ✋", a + " шлёпнул " + b + " 🍑",
        a + " дал " + b + " шлепок 🖐️", a + " шлёпнул " + b + " ладонью 🤚",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def bite(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя кусать нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " укусил " + b + " 🦷", a + " сильно укусил " + b + " 😬",
        a + " укусил " + b + " за руку 🩸", a + " укусил " + b + " за плечо 🦷",
        a + " куснул " + b + " 🐾", a + " укусил " + b + " до крови 🩹",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def pat(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя гладить нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " погладил " + b + " 🤍", a + " нежно погладил " + b + " 🕊",
        a + " погладил " + b + " по голове 🌿", a + " ласково погладил " + b + " ✨",
        a + " погладил " + b + " по спине 🍃", a + " мягко погладил " + b + " 🤍",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def wink(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себе подмигивать нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " подмигнул " + b + " 😉", a + " игриво подмигнул " + b + " 🎭",
        a + " загадочно подмигнул " + b + " 🌙", a + " весело подмигнул " + b + " ✨",
        a + " хитро подмигнул " + b + " 🃏", a + " подмигнул " + b + " 🌟",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def pinch(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя щипать нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " ущипнул " + b + " 🤏", a + " ущипнул " + b + " за бок 😄",
        a + " больно ущипнул " + b + " 😆", a + " ущипнул " + b + " за щёку 🌸",
        a + " ущипнул " + b + " за руку 🤏", a + " слегка ущипнул " + b + " 😊",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def tickle(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя щекотать нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " защекотал " + b + " до слёз 😂", a + " щекочет " + b + " 🪶",
        a + " защекотал " + b + " 🤣", a + " щекочет " + b + " под рёбрами 🪶",
        a + " защекотал " + b + " до икоты 🤭", a + " щекочет " + b + " 🌾",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def feed(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя кормить нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " покормил " + b + " 🍰", a + " накормил " + b + " 🍲",
        a + " покормил " + b + " с ложечки 🥄", a + " угостил " + b + " 🍫",
        a + " покормил " + b + " вкусненьким 🍓", a + " накормил " + b + " до отвала 🍕",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def love(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя любить нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " признался в чувствах " + b + " 💌", a + " признался в любви " + b + " 💘",
        a + " признался в своих чувствах " + b + " 🌹", a + " открыто признался в чувствах " + b + " 💫",
        a + " нежно признался в чувствах " + b + " 💞", a + " искренне признался в чувствах " + b + " ✨",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def steal(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя украсть нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " украл сердце " + b + " 💘", a + " украл " + b + " 🌙",
        a + " украл поцелуй у " + b + " 💋", a + " украл " + b + " навсегда 💫",
        a + " украл сон " + b + " 🌌", a + " украл улыбку " + b + " ✨",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def spank(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя шлёпать нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " отшлёпал " + b + " 🖐", a + " отшлёпал " + b + " ремнём ⛓",
        a + " строго отшлёпал " + b + " ✋", a + " отшлёпал " + b + " за шалости 🌿",
        a + " наказал " + b + " шлепком 🍑",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def punish(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя наказывать нельзя"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    phrases = [
        a + " наказал " + b + " ⚖", a + " строго наказал " + b + " 🖤",
        a + " наказал " + b + " за проступок 🗡", a + " наказал " + b + " по заслугам ⚔",
        a + " наказал " + b + " 🌑",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def marry(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Нельзя жениться на себе"); return
    a = get_user_tag(me); b = get_user_tag(target_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Принять", callback_data="accept_" + str(me) + "_" + str(target_id)),
        types.InlineKeyboardButton("Отказаться", callback_data="reject_" + str(me) + "_" + str(target_id)),
    )
    text = a + " делает предложение " + b + "!\n\n" + b + ", ты согласен(на)?"
    bot.send_message(message.chat.id, text, reply_markup=kb)

# ========== ШЕЙКЕР ==========

def get_shaker(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT score, last_play FROM shaker WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row if row else (0, 0)

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

def play_shaker(message):
    me = message.from_user.id
    save_user(me, message.from_user.first_name, message.from_user.username)
    score, last = get_shaker(me)
    now = int(time.time())
    if last > 0 and now - last < 1800:
        remaining = 1800 - (now - last)
        bot.reply_to(message, "Жди " + str(remaining // 60) + "м " + str(remaining % 60) + "с")
        return
    num = random.randint(1, 9)
    score += num
    update_shaker(me, score, now)
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

# ========== ОГОНЁК ==========

def offer_fire(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.send_message(message.chat.id, "Нельзя зажечь огонёк с самим собой")
        return
    existing = get_duo_fire_with(me, target_id)
    if existing:
        partner = get_user_tag(target_id)
        bot.send_message(message.chat.id, "У вас уже есть огонёк с " + partner)
        return
    if count_duo_fires(me) >= 3:
        bot.send_message(message.chat.id, "У тебя уже 3 огонька")
        return
    if count_duo_fires(target_id) >= 3:
        partner = get_user_tag(target_id)
        bot.send_message(message.chat.id, "У " + partner + " уже 3 огонька")
        return
    a = get_user_tag(me); b = get_user_tag(target_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Принять", callback_data="fire_yes_" + str(me) + "_" + str(target_id)),
        types.InlineKeyboardButton("Отказаться", callback_data="fire_no_" + str(me) + "_" + str(target_id)),
    )
    text = "🔥 " + a + " хочет зажечь огонёк с " + b + "\n\n" + b + ", ты согласен?"
    bot.send_message(message.chat.id, text, reply_markup=kb)

def extend_fire(message):
    me = message.from_user.id
    save_user(me, message.from_user.first_name, message.from_user.username)
    fires = get_all_duo_fires(me)
    if not fires:
        bot.send_message(message.chat.id, "У тебя нет огонька. Напиши: винди огонёк @user")
        return
    now = int(time.time())
    today_start = int(datetime.datetime.utcnow().replace(hour=0, minute=1, second=0, microsecond=0).timestamp())
    grey_partners = []
    all_green = True
    just_activated = []
    for f in fires:
        uid1, uid2, fire, is_grey, last1, last2, last_ext = f
        if me == uid1:
            my_last = last1; other_last = last2
        else:
            my_last = last2; other_last = last1
        if my_last >= today_start and other_last >= today_start:
            continue
        if my_last >= today_start:
            partner_id = uid2 if me == uid1 else uid1
            grey_partners.append(partner_id)
            all_green = False
            continue
        if other_last >= today_start:
            new_fire = fire + 1
            if me == uid1:
                new_last1, new_last2 = now, other_last
            else:
                new_last1, new_last2 = other_last, now
            update_duo_fire(uid1, uid2, new_fire, 0, new_last1, new_last2, now)
            partner_id = uid2 if me == uid1 else uid1
            just_activated.append((partner_id, new_fire))
        else:
            if me == uid1:
                new_last1, new_last2 = now, other_last
            else:
                new_last1, new_last2 = other_last, now
            update_duo_fire(uid1, uid2, fire, is_grey, new_last1, new_last2, last_ext)
            partner_id = uid2 if me == uid1 else uid1
            grey_partners.append(partner_id)
            all_green = False
    for partner_id, new_fire in just_activated:
        a = get_user_tag(me); b = get_user_tag(partner_id)
        bot.send_message(message.chat.id, "🔥 Огонёк зажжён!\n\n" + a + " + " + b + "\nЧисло: " + str(new_fire))
    if all_green and not just_activated and not grey_partners:
        if len(fires) == 1:
            bot.send_message(message.chat.id, "🔥 Огонёк уже горит")
        else:
            bot.send_message(message.chat.id, "🔥 Огоньки уже горят")
        return
    if grey_partners:
        partners_str = ", ".join([get_user_tag(p) for p in grey_partners])
        bot.send_message(message.chat.id, "⏳ Ждём " + partners_str)

def my_fire(message):
    me = message.from_user.id
    fires = get_all_duo_fires(me)
    if not fires:
        bot.send_message(message.chat.id, "У тебя нет огонька. Напиши: винди огонёк @user")
        return
    if len(fires) == 1:
        uid1, uid2, fire, is_grey, last1, last2, last_ext = fires[0]
        partner_id = uid2 if me == uid1 else uid1
        partner = get_user_tag(partner_id)
        status = "серый ⚫" if is_grey else "зажжён 🔴"
        t = "🔥 Твой огонёк:\n\n" + partner + " — " + status + " (" + str(fire) + ")"
        bot.send_message(message.chat.id, t)
    else:
        t = "🔥 Твои огоньки:\n\n"
        for i, f in enumerate(fires, 1):
            uid1, uid2, fire, is_grey, last1, last2, last_ext = f
            partner_id = uid2 if me == uid1 else uid1
            partner = get_user_tag(partner_id)
            status = "серый ⚫" if is_grey else "зажжён 🔴"
            t += str(i) + ". " + partner + " — " + status + " (" + str(fire) + ")\n"
        bot.send_message(message.chat.id, t)

def fire_top(message):
    rows = get_duo_top()
    if not rows:
        bot.send_message(message.chat.id, "Пока нет огоньков.")
        return
    t = "Топ огоньков:\n\n"
    for i, (u1, u2, fire) in enumerate(rows, 1):
        a = get_user_tag(u1); b = get_user_tag(u2)
        t += "Огонёк 🔥 " + a + " и " + b + " составляет " + str(fire) + "\n"
    bot.send_message(message.chat.id, t)

def who_gay(message):
    all_u = get_all_users()
    if not all_u:
        bot.send_message(message.chat.id, "Никто ещё не писал в чате.")
        return
    uid, tag = random.choice(all_u)
    p = ["Я думаю гей - @" + tag, "Радар: @" + tag, "100% гей - @" + tag]
    bot.send_message(message.chat.id, random.choice(p))

# ========== ОБРАБОТЧИК ТЕКСТА ==========

@bot.message_handler(content_types=["text"])
def echo(message):
    if message.from_user:
        save_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    if message.reply_to_message and message.reply_to_message.from_user:
        r = message.reply_to_message.from_user
        save_user(r.id, r.first_name, r.username)

    text = message.text.strip()
    low = text.lower()

    # Админ-панель (личка)
    if message.chat.type == "private" and message.from_user.id == ADMIN_ID:
        if ADMIN_ID in pending_admin:
            target_uid, target_fire = pending_admin[ADMIN_ID]
            if text == SECRET_CODE:
                fires = get_all_duo_fires(target_uid)
                if not fires:
                    tag = get_user_tag(target_uid)
                    bot.send_message(message.chat.id, "❌ У " + tag + " нет огонька.")
                else:
                    uid1, uid2, fire, is_grey, last1, last2, last_ext = fires[0]
                    update_duo_fire(uid1, uid2, target_fire, 0, last1, last2, last_ext)
                    a = get_user_tag(uid1); b = get_user_tag(uid2)
                    bot.send_message(message.chat.id, "✅ Огонёк " + str(target_fire) + " выдан:\n" + a + " + " + b)
            else:
                bot.send_message(message.chat.id, "❌ Неверный код")
            del pending_admin[ADMIN_ID]
            return

        if ADMIN_ID in pending_coins:
            target_uid, target_coins = pending_coins[ADMIN_ID]
            if text == SECRET_CODE:
                if target_uid is None:
                    bot.send_message(message.chat.id, "❌ Юзер не найден")
                else:
                    set_coins(target_uid, target_coins)
                    tag = get_user_tag(target_uid)
                    bot.send_message(message.chat.id, "✅ " + str(target_coins) + " монет выдано " + tag)
            else:
                bot.send_message(message.chat.id, "❌ Неверный код")
            del pending_coins[ADMIN_ID]
            return

        if low.startswith("винди огонёк"):
            parts = text.split()
            if len(parts) >= 4:
                tag = parts[2]
                try:
                    fire_num = int(parts[3])
                except:
                    bot.send_message(message.chat.id, "❌ Число неверное")
                    return
                target_uid = get_uid_by_tag(tag)
                if not target_uid:
                    bot.send_message(message.chat.id, "❌ Юзер не найден.")
                    return
                pending_admin[ADMIN_ID] = (target_uid, fire_num)
                bot.send_message(message.chat.id, "Введите секретный код:")
                return

        if low.startswith("винди монеты"):
            parts = text.split()
            if len(parts) >= 4:
                tag = parts[2]
                try:
                    coins_num = int(parts[3])
                except:
                    bot.send_message(message.chat.id, "❌ Число неверное")
                    return
                target_uid = get_uid_by_tag(tag)
                if not target_uid:
                    bot.send_message(message.chat.id, "❌ Юзер не найден")
                    return
                pending_coins[ADMIN_ID] = (target_uid, coins_num)
                bot.send_message(message.chat.id, "Введите секретный код:")
                return

    # Игра «Угадай число»
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot.get_me().id:
            if message.from_user.id in games:
                guess_number(message)
                return

    # Команды
    if low == "винди развод":
        divorce_request(message)
        return
    if low.startswith("винди потуши огонёк"):
        parts = text.split()
        if len(parts) >= 4:
            tag = parts[3]
            target_uid = get_uid_by_tag(tag)
            if not target_uid:
                bot.send_message(message.chat.id, "❌ Юзер не найден.")
                return
            extinguish_request(message, target_uid)
        return

    if low.startswith("винди огонёк") and message.chat.type != "private":
        parts = text.split()
        if len(parts) >= 3:
            tag = parts[2]
            target_uid = get_uid_by_tag(tag)
            if not target_uid:
                bot.send_message(message.chat.id, "❌ Юзер не найден. Пусть он напишет /start.")
                return
            offer_fire(message, target_uid)
            return

    if low == "винди загадай число":
        start_game(message)
        return
    if low == "огонёк":
        extend_fire(message)
        return
    if low == "мой огонёк":
        my_fire(message)
        return
    if low == "топ огоньков":
        fire_top(message)
        return

    # Профиль и балик
    if low == "винди профиль":
        show_profile(message)
        return
    if low == "балик":
        show_balance(message)
        return
    if low == "топ балик":
        show_balance_top(message)
        return

    # Питомец
    if low == "винди заведи питомца":
        buy_pet(message)
        return
    if low == "мой питомец":
        show_pet(message)
        return
    if low.startswith("изменить имя питомца"):
        new_name = text[len("изменить имя питомца"):].strip()
        if not new_name:
            bot.send_message(message.chat.id, "Напиши: изменить имя питомца [имя]")
            return
        change_pet_name(message, new_name)
        return
    if low == "винди скины":
        show_pet_skins(message)
        return

    # Рандом
    if low == "винди орел или решка" or low == "винди орёл или решка":
        coin_flip(message)
        return
    if low == "винди да или нет":
        yes_no(message)
        return

    # Действия
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if low == "обнять": hug(message, target_id); return
        if low == "поцеловать": kiss(message, target_id); return
        if low == "ударить": hit(message, target_id); return
        if low == "пнуть": kick(message, target_id); return
        if low == "шлёпнуть": slap(message, target_id); return
        if low == "укусить": bite(message, target_id); return
        if low == "погладить": pat(message, target_id); return
        if low == "подмигнуть": wink(message, target_id); return
        if low == "ущипнуть": pinch(message, target_id); return
        if low == "щекотать": tickle(message, target_id); return
        if low == "покормить": feed(message, target_id); return
        if low == "лавю": love(message, target_id); return
        if low == "украсть": steal(message, target_id); return
        if low == "отшлёпать": spank(message, target_id); return
        if low == "наказать": punish(message, target_id); return
        if "замуж" in low or "женись" in low or "женить" in low:
            marry(message, target_id); return

    # Шейкер
    if low == "шейкер":
        play_shaker(message)
        return
    if low == "ш топ":
        shaker_top(message)
        return

    # Остальное
    if "винди" in low and "брак" in low:
        show_marriages(message)
        return
    if "винди" in low and "гей" in low:
        who_gay(message)
        return
    if low == "ало":
        responses = [
            "Ало", "Ало, чё надо?", "Алё-алё", "Ало, я тут", "Ало? Не слышу",
            "Ало, братан", "Ало, это ты?", "Ало, не звони мне больше", "Ало, кто это?",
            "Ало, говори", "Алло, приём", "Ало, связь плохая", "Ало, ты где?",
            "Ало, перезвони", "Ало, я занят", "Ало, чё хотел?", "Ало, не слышу тебя",
            "Ало, всё, пока", "Ало, ну чё там?", "Ало, я слушаю", "Ало, слышно меня?",
            "Ало, ты молчишь?", "Ало, я на связи", "Ало, давай быстрее",
            "Ало, что случилось?", "Ало, я не один", "Ало, позже позвоню"
        ]
        bot.send_message(message.chat.id, random.choice(responses))
        return

# ========== ОБРАБОТЧИК КНОПОК ==========

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    parts = call.data.split("_")
    action = parts[0]

    if action == "skin":
        pet_type = parts[1]
        me = call.from_user.id
        pet = get_pet(me)
        if not pet:
            return
        set_pet_type(me, pet_type)
        info = PETS.get(pet_type)
        if info:
            bot.edit_message_text(
                "✅ Скин изменён на " + info["emoji"] + " " + info["name"],
                call.message.chat.id, call.message.message_id
            )
        return

    if action == "divorce":
        decision = parts[1]
        uid1 = int(parts[2]); uid2 = int(parts[3])
        if call.from_user.id not in [uid1, uid2]:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT agree1, agree2 FROM divorce_votes WHERE uid1 = %s AND uid2 = %s", (uid1, uid2))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close(); return
        agree1, agree2 = row
        if decision == "yes":
            if call.from_user.id == uid1: agree1 = 1
            else: agree2 = 1
        else:
            if call.from_user.id == uid1: agree1 = -1
            else: agree2 = -1
        cur.execute("UPDATE divorce_votes SET agree1 = %s, agree2 = %s WHERE uid1 = %s AND uid2 = %s",
                    (agree1, agree2, uid1, uid2))
        conn.commit(); cur.close(); conn.close()
        a = get_user_tag(uid1); b = get_user_tag(uid2)
        if agree1 == 1 and agree2 == 1:
            delete_marriage(uid1, uid2)
            bot.edit_message_text("Развод! " + a + " и " + b + " больше не вместе", call.message.chat.id, call.message.message_id)
        elif agree1 == -1 or agree2 == -1:
            who = a if (agree1 == -1) else b
            bot.edit_message_text("❌ Брак остался. " + who + " отказался", call.message.chat.id, call.message.message_id)
        return

    if action == "ext":
        decision = parts[1]
        uid1 = int(parts[2]); uid2 = int(parts[3])
        if call.from_user.id not in [uid1, uid2]:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT agree1, agree2 FROM duo_break WHERE uid1 = %s AND uid2 = %s", (uid1, uid2))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close(); return
        agree1, agree2 = row
        if decision == "yes":
            if call.from_user.id == uid1: agree1 = 1
            else: agree2 = 1
        else:
            if call.from_user.id == uid1: agree1 = -1
            else: agree2 = -1
        cur.execute("UPDATE duo_break SET agree1 = %s, agree2 = %s WHERE uid1 = %s AND uid2 = %s",
                    (agree1, agree2, uid1, uid2))
        conn.commit(); cur.close(); conn.close()
        a = get_user_tag(uid1); b = get_user_tag(uid2)
        if agree1 == 1 and agree2 == 1:
            delete_duo_fire(uid1, uid2)
            bot.edit_message_text("Огонёк между " + a + " и " + b + " был потушен", call.message.chat.id, call.message.message_id)
        elif agree1 == -1 or agree2 == -1:
            who = a if (agree1 == -1) else b
            bot.edit_message_text("❌ Огонёк остался. " + who + " отказался", call.message.chat.id, call.message.message_id)
        return

    if action == "fire":
        decision = parts[1]
        uid1 = int(parts[2]); uid2 = int(parts[3])
        if call.from_user.id != uid2:
            return
        a = get_user_tag(uid1); b = get_user_tag(uid2)
        if decision == "yes":
            create_duo_fire(uid1, uid2)
            text = "🔥 Огонёк создан!\n\n" + a + " + " + b + "\nЧисло: 1"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(b + " отказал(а)", call.message.chat.id, call.message.message_id)
        return

    if action in ("accept", "reject"):
        uid1 = int(parts[1]); uid2 = int(parts[2])
        if call.from_user.id != uid2:
            return
        if action == "accept":
            add_marriage(uid1, uid2)
            a = get_user_tag(uid1); b = get_user_tag(uid2)
            bot.edit_message_text("Женаты! " + a + " + " + b, call.message.chat.id, call.message.message_id)
        else:
            a = get_user_tag(uid1); b = get_user_tag(uid2)
            bot.edit_message_text(b + " отказал(а) " + a, call.message.chat.id, call.message.message_id)

# ========== ЗАПУСК ==========

init_db()

t = threading.Thread(target=background_fire_check)
t.daemon = True
t.start()

print("Бот запущен!")
bot.polling(none_stop=True)
