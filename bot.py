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
pending_pet = {}
pending_level = {}
pending_exp = {}
games = {}

DOG_ART = """\\
╱▔▔╲▂▂▂╱▔▔╲
╲╱╳╱▔╲╱▔╲╱▔
┈┈┃▏▕▍▏▕▍▏
┈┈┃╲▂╱╲▂╱╲┈╭━╮
┈┈┃┊┳┊┊┊┊┊▔╰┳╯
┈┈┃┊╰━━━┳━━━╯
┈┈┃┊┊┊┊╭╯"""

CAT_ART = """╭━╮┈╭━╮┈┈┈┈┈╭━╮
┃╭╯┈┃┊┗━━━━━┛┊┃
┃╰┳┳┫┏━▅╮┊╭━▅┓┃
┃┫┫┫┫┃┊▉┃┊┃┊▉┃┃
┃┫┫┫╋╰━━┛▅┗━━╯╋
┃┫┫┫╋┊┊┊┣┻┫┊┊┊╋
┃┊┊┊╰┈┈┈┈┈┈┈┳━╯
┃┣┳┳━━┫┣━━┳╭╯"""

SNAKE_ART = """\\
──────────────────────
▄▄▀█▄───▄───────▄─────
▀▀▀██──███─────███────
░▄██▀░█████░░░█████░░░
███▀▄███░███░███░███░▄
▀█████▀░░░▀███▀░░░▀██▀"""

ELEPHANT_ART = """┊┊┊┊┊┊╱▔▔╲▔▔╲
┊╱▔▔▔▔▏┊┊┊┈╭╮▏
╭▏┈┈┈┈▏┊┊┊┈┈┈╲
┋▏┈┈┈┈╲▂▂╱┈╰┈┊▏
╯┃┈┈┈┈┈┈┈┈╭▔▔▏▏
┊┃┈┈┈┣┫┈┈┈┃┊┊▏▏
┈┃╭┳┳┫┃╭┳┳┫┈╱╱"""

BEAR_ART = """╲╲╭━╮╲╲╲╱╱╱╭━╮╱╱
╲╲┃╮╰╯╯╯╯╯╯╯╭┃╱╱
╲╲╰╮╭━╯┊┊╰━╮╭╯╱╱
╲╲╲┃╭━╮┊┊╭━╮┃╱╱╱
╲╲╭╯┃▇┃┊┊┃▇┃╰╮╱╱
╲╲┃┊┗━┛▇▇┗━┛┊┃╱╱
╲╲┃╰━━━━━━━━╯┃╱╱"""

COW_ART = """┈┈▕╲▂▂▂▂╱▏
┈┈┈╲╱╭╱╲╱╲
┈╱▔▔┈┊▏▕▏▕
▕▂╱▔╳▔╲▊▏▊╱▔╲▔╲
┈┈┈┈▏▕▏▔▔▔▕▋▕▕▋▏
┈┈┈┈╲┈╲▂▂▂▂▂▂▂╱
┈┈┈┈▕╲▂▂▂▂▂╱
┈┈┈╱▔╲▕"""

PIG_ART = """┊┊┊┊┊┊┊┊┊┊┊┊┊┊┊┊
▂╱▔▔╲╱▔▔▔▔╲╱▔▔╲▂
╲┈▔╲┊╭╮┈┈╭╮┊╱▔┈╱
┊▔╲╱▏┈╱▔▔╲┈▕╲╱▔┊
┊┊┊┃┈┈▏┃┃▕┈┈┃┊┊┊
┊┊┊▏╲┈╲▂▂╱┈╱▕┊┊┊"""

PETS = {
    "cow": {"name": "Корова", "emoji": "🐮", "art": COW_ART, "rarity": "редкий"},
    "pig": {"name": "Свинья", "emoji": "🐷", "art": PIG_ART, "rarity": "редкий"},
    "dog": {"name": "Собака", "emoji": "🐶", "art": DOG_ART, "rarity": "обычный"},
    "cat": {"name": "Кошка", "emoji": "🐱", "art": CAT_ART, "rarity": "обычный"},
    "snake": {"name": "Змея", "emoji": "🐍", "art": SNAKE_ART, "rarity": "обычный"},
    "elephant": {"name": "Слон", "emoji": "🐘", "art": ELEPHANT_ART, "rarity": "редкий"},
    "bear": {"name": "Медведь", "emoji": "🐻", "art": BEAR_ART, "rarity": "редкий"},
}

NAME_TO_TYPE = {
    "корова": "cow", "cow": "cow",
    "свинья": "pig", "свинью": "pig", "pig": "pig",
    "собака": "dog", "пёс": "dog", "пес": "dog", "dog": "dog",
    "кошка": "cat", "кот": "cat", "cat": "cat",
    "змея": "snake", "snake": "snake",
    "слон": "elephant", "elephant": "elephant",
    "медведь": "bear", "bear": "bear",
}

CASES = {
    "common": {"name": "Обычный", "price": 45, "pets": ["dog", "cat", "snake"]},
    "rare": {"name": "Редкий", "price": 90, "pets": ["elephant", "bear", "cow", "pig"]},
}

def exp_needed(level):
    if level < 1 or level >= 50:
        return 999999
    if level <= 10:
        return 100 + (level - 1) * 50
    elif level <= 20:
        return 550 + (level - 11) * 40
    elif level <= 30:
        return 950 + (level - 21) * 30
    elif level <= 40:
        return 1250 + (level - 31) * 20
    else:
        return 1450 + (level - 41) * 10

def level_emoji(level):
    if level <= 10:
        return "⭐"
    elif level <= 20:
        return "🌟"
    elif level <= 30:
        return "✨"
    elif level <= 40:
        return "💫"
    else:
        return "🌠"

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (uid BIGINT PRIMARY KEY, name TEXT, tag TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS balance (uid BIGINT PRIMARY KEY, coins INTEGER DEFAULT 0, wins INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS shaker (uid BIGINT PRIMARY KEY, score INTEGER DEFAULT 0, last_play BIGINT DEFAULT 0)")
    cur.execute("""CREATE TABLE IF NOT EXISTS marriages (
        uid1 BIGINT, uid2 BIGINT, count INTEGER DEFAULT 1, since BIGINT, PRIMARY KEY (uid1, uid2))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS duo_fires (
        uid1 BIGINT, uid2 BIGINT, fire INTEGER DEFAULT 1, is_grey INTEGER DEFAULT 0,
        last_uid1 BIGINT DEFAULT 0, last_uid2 BIGINT DEFAULT 0, last_extend BIGINT DEFAULT 0,
        PRIMARY KEY (uid1, uid2))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS duo_break (
        uid1 BIGINT, uid2 BIGINT, agree1 INTEGER DEFAULT 0, agree2 INTEGER DEFAULT 0,
        PRIMARY KEY (uid1, uid2))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS divorce_votes (
        uid1 BIGINT, uid2 BIGINT, agree1 INTEGER DEFAULT 0, agree2 INTEGER DEFAULT 0,
        PRIMARY KEY (uid1, uid2))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS pets (
        uid BIGINT PRIMARY KEY, pet_type TEXT, pet_name TEXT,
        level INTEGER DEFAULT 1, exp INTEGER DEFAULT 0,
        food INTEGER DEFAULT 100, walk INTEGER DEFAULT 100, sleep INTEGER DEFAULT 100,
        last_update BIGINT DEFAULT 0)""")
    cur.execute("ALTER TABLE pets ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1")
    cur.execute("ALTER TABLE pets ADD COLUMN IF NOT EXISTS exp INTEGER DEFAULT 0")
    cur.execute("ALTER TABLE pets ADD COLUMN IF NOT EXISTS food INTEGER DEFAULT 100")
    cur.execute("ALTER TABLE pets ADD COLUMN IF NOT EXISTS walk INTEGER DEFAULT 100")
    cur.execute("ALTER TABLE pets ADD COLUMN IF NOT EXISTS sleep INTEGER DEFAULT 100")
    cur.execute("ALTER TABLE pets ADD COLUMN IF NOT EXISTS last_update BIGINT DEFAULT 0")
    cur.execute("ALTER TABLE pets ADD COLUMN IF NOT EXISTS pet_name TEXT")
    cur.execute("CREATE TABLE IF NOT EXISTS pet_skins (uid BIGINT, pet_type TEXT, PRIMARY KEY (uid, pet_type))")
    cur.execute("CREATE TABLE IF NOT EXISTS fire_system (id INTEGER PRIMARY KEY, last_expire BIGINT DEFAULT 0)")
    cur.execute("INSERT INTO fire_system (id, last_expire) VALUES (1, 0) ON CONFLICT (id) DO NOTHING")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS cards (
        card_id TEXT PRIMARY KEY, name TEXT, rarity TEXT,
        points INTEGER DEFAULT 0, coins INTEGER DEFAULT 0, photo TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS user_cards (
        uid BIGINT, card_id TEXT, owned_at BIGINT DEFAULT 0,
        PRIMARY KEY (uid, card_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS user_cards_state (
        uid BIGINT PRIMARY KEY, equipped_card TEXT DEFAULT NULL,
        last_income BIGINT DEFAULT 0)""")

    cur.execute("""INSERT INTO cards (card_id, name, rarity, points, coins, photo)
        VALUES ('svyaz', 'Связь', 'Редкая', 67, 11,
        'https://i.postimg.cc/zvfPF2hS/7dfcf2f1760df65d11d5fb55749cc8a4.jpg')
        ON CONFLICT (card_id) DO NOTHING""")
    
    cur.execute("""INSERT INTO cards (card_id, name, rarity, points, coins, photo)
        VALUES ('chipugai', 'chipugai', 'Ультра', 5000, 50,
        'https://i.postimg.cc/ZYQk4QQR/Screenshot-20260923-021601.png')
        ON CONFLICT (card_id) DO NOTHING""")
    
    conn.commit()
    cur.close()
    conn.close()

def save_user(uid, name, tag):
    if not uid:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO users (uid, name, tag) VALUES (%s, %s, %s)
        ON CONFLICT (uid) DO UPDATE SET name = EXCLUDED.name, tag = EXCLUDED.tag""", (uid, name, tag))
    cur.execute("INSERT INTO balance (uid, coins, wins) VALUES (%s, 0, 0) ON CONFLICT (uid) DO NOTHING", (uid,))
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

def get_balance(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT coins, wins FROM balance WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row if row else (0, 0)

def add_coins(uid, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO balance (uid, coins, wins) VALUES (%s, %s, 0)
        ON CONFLICT (uid) DO UPDATE SET coins = balance.coins + %s""", (uid, amount, amount))
    conn.commit()
    cur.close()
    conn.close()

def set_coins(uid, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO balance (uid, coins, wins) VALUES (%s, %s, 0)
        ON CONFLICT (uid) DO UPDATE SET coins = %s""", (uid, amount, amount))
    conn.commit()
    cur.close()
    conn.close()

def add_win(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO balance (uid, coins, wins) VALUES (%s, 0, 1)
        ON CONFLICT (uid) DO UPDATE SET wins = balance.wins + 1""", (uid,))
    conn.commit()
    cur.close()
    conn.close()

def get_level(coins):
    level = coins // 250 + 1
    if level > 50:
        level = 50
    return level

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
    cur.execute("""SELECT pet_type, pet_name, level, exp, food, walk, sleep, last_update
        FROM pets WHERE uid = %s""", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def create_pet(uid, pet_type):
    now = int(time.time())
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO pets (uid, pet_type, pet_name, level, exp, food, walk, sleep, last_update)
        VALUES (%s, %s, NULL, 1, 0, 100, 100, 100, %s)
        ON CONFLICT (uid) DO UPDATE SET pet_type = %s, level = 1, exp = 0, food = 100, walk = 100, sleep = 100, last_update = %s""",
        (uid, pet_type, now, pet_type, now))
    cur.execute("INSERT INTO pet_skins (uid, pet_type) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, pet_type))
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
    cur.execute("INSERT INTO pet_skins (uid, pet_type) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, pet_type))
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

def update_pet_stats(uid, food, walk, sleep, level, exp, last_update):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""UPDATE pets SET food = %s, walk = %s, sleep = %s,
        level = %s, exp = %s, last_update = %s WHERE uid = %s""",
        (food, walk, sleep, level, exp, last_update, uid))
    conn.commit()
    cur.close()
    conn.close()

def set_pet_level(uid, level):
    if level > 50:
        level = 50
    if level < 1:
        level = 1
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE pets SET level = %s, exp = 0 WHERE uid = %s", (level, uid))
    conn.commit()
    cur.close()
    conn.close()

def add_pet_exp(uid, add_exp):
    pet = get_pet(uid)
    if not pet:
        return None
    level = pet[2]
    exp = pet[3] + add_exp
    while level < 50 and exp >= exp_needed(level):
        exp -= exp_needed(level)
        level += 1
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE pets SET level = %s, exp = %s WHERE uid = %s", (level, exp, uid))
    conn.commit()
    cur.close()
    conn.close()
    return level, exp

def calc_decay(pet_row):
    """Decay применяется максимум за 24 часа"""
    pet_type, pet_name, level, exp, food, walk, sleep, last_update = pet_row
    now = int(time.time())
    hours = (now - last_update) / 3600.0
    if hours < 0:
        hours = 0
    if hours > 24:
        hours = 24
    decay_per_hour = random.uniform(10, 15)
    total_decay = int(hours * decay_per_hour)
    food = max(0, food - total_decay)
    walk = max(0, walk - total_decay)
    sleep = max(0, sleep - total_decay)
    return food, walk, sleep

def get_health(walk, sleep):
    return int((walk + sleep) / 2)
def pet_action(uid, action_type):
    pet = get_pet(uid)
    if not pet:
        return None
    food, walk, sleep = calc_decay(pet)
    if action_type == "food" and food >= 100:
        return None
    if action_type == "walk" and walk >= 100:
        return None
    if action_type == "sleep" and sleep >= 100:
        return None
    add = random.randint(10, 15)
    if action_type == "food":
        food = min(100, food + add)
    elif action_type == "walk":
        walk = min(100, walk + add)
    elif action_type == "sleep":
        sleep = min(100, sleep + add)
    add_exp = random.randint(25, 33)
    level = pet[2]
    exp = pet[3] + add_exp
    while level < 50 and exp >= exp_needed(level):
        exp -= exp_needed(level)
        level += 1
    update_pet_stats(uid, food, walk, sleep, level, exp, int(time.time()))
    return add, add_exp
    
# ========== КАРТОЧКИ ==========

def get_card(card_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT card_id, name, rarity, points, coins, photo FROM cards WHERE card_id = %s", (card_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_all_cards():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT card_id, name, rarity, points, coins, photo FROM cards")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def add_card_to_db(card_id, name, rarity, points, coins, photo):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO cards (card_id, name, rarity, points, coins, photo)
        VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (card_id) DO NOTHING""",
        (card_id, name, rarity, points, coins, photo))
    conn.commit()
    cur.close()
    conn.close()

def get_user_cards(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT card_id FROM user_cards WHERE uid = %s", (uid,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

def give_card(uid, card_id):
    now = int(time.time())
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO user_cards (uid, card_id, owned_at)
        VALUES (%s, %s, %s) ON CONFLICT (uid, card_id) DO NOTHING""",
        (uid, card_id, now))
    cur.execute("""INSERT INTO user_cards_state (uid, equipped_card, last_income)
        VALUES (%s, NULL, %s) ON CONFLICT (uid) DO NOTHING""", (uid, now))
    conn.commit()
    cur.close()
    conn.close()
    return now

def get_equipped_card(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT equipped_card FROM user_cards_state WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def set_equipped_card(uid, card_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO user_cards_state (uid, equipped_card, last_income)
        VALUES (%s, %s, 0) ON CONFLICT (uid) DO UPDATE SET equipped_card = %s""",
        (uid, card_id, card_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user_cards_state(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT equipped_card, last_income FROM user_cards_state WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row if row else (None, 0)

def get_user_total_points(uid):
    cards = get_user_cards(uid)
    total = 0
    for cid in cards:
        card = get_card(cid)
        if card:
            total += card[3]
    return total

def get_user_total_coins_per_day(uid):
    cards = get_user_cards(uid)
    total = 0
    for cid in cards:
        card = get_card(cid)
        if card:
            total += card[4]
    return total

def get_cards_top():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT uid FROM user_cards")
    uids = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for (uid,) in uids:
        points = get_user_total_points(uid)
        coins = get_user_total_coins_per_day(uid)
        result.append((uid, points, coins))
    result.sort(key=lambda x: x[1], reverse=True)
    return result[:10]
    
# ========== ОГОНЬКИ ==========

def get_all_duo_fires(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT uid1, uid2, fire, is_grey, last_uid1, last_uid2, last_extend
        FROM duo_fires WHERE uid1 = %s OR uid2 = %s""", (uid, uid))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_duo_fire_with(uid, partner_uid):
    a, b = sorted([uid, partner_uid])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT uid1, uid2, fire, is_grey, last_uid1, last_uid2, last_extend
        FROM duo_fires WHERE uid1 = %s AND uid2 = %s""", (a, b))
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
    now = int(time.time())
    cur.execute("""INSERT INTO duo_fires (uid1, uid2, fire, is_grey, last_uid1, last_uid2, last_extend)
        VALUES (%s, %s, 1, 0, %s, %s, %s) ON CONFLICT (uid1, uid2) DO NOTHING""", (a, b, now, now, now))
    conn.commit()
    cur.close()
    conn.close()

def update_duo_fire(uid1, uid2, fire, is_grey, last_uid1, last_uid2, last_extend):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""UPDATE duo_fires SET fire = %s, is_grey = %s, last_uid1 = %s, last_uid2 = %s, last_extend = %s
        WHERE uid1 = %s AND uid2 = %s""", (fire, is_grey, last_uid1, last_uid2, last_extend, uid1, uid2))
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
        t += str(i) + ". " + get_user_tag(u1) + " + " + get_user_tag(u2) + "\n"
        t += "   Браков: " + str(cnt) + ", вместе: " + time_together(now - since) + "\n\n"
    bot.send_message(message.chat.id, t)

def divorce_request(message):
    me = message.from_user.id
    row = get_marriage(me)
    if not row:
        bot.send_message(message.chat.id, "У тебя нет брака")
        return
    uid1, uid2 = row[0], row[1]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO divorce_votes (uid1, uid2, agree1, agree2) VALUES (%s, %s, 0, 0)
        ON CONFLICT (uid1, uid2) DO UPDATE SET agree1 = 0, agree2 = 0""", (uid1, uid2))
    conn.commit()
    cur.close()
    conn.close()
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Да", callback_data="divorce_yes_" + str(uid1) + "_" + str(uid2)),
        types.InlineKeyboardButton("Нет", callback_data="divorce_no_" + str(uid1) + "_" + str(uid2)),
    )
    bot.send_message(message.chat.id, get_user_tag(uid1) + " и " + get_user_tag(uid2) + ", вы хотите разрушить брак?", reply_markup=kb)

def extinguish_request(message, target_id):
    me = message.from_user.id
    row = get_duo_fire_with(me, target_id)
    if not row:
        bot.send_message(message.chat.id, "У тебя нет огонька с " + get_user_tag(target_id))
        return
    uid1, uid2 = row[0], row[1]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO duo_break (uid1, uid2, agree1, agree2) VALUES (%s, %s, 0, 0)
        ON CONFLICT (uid1, uid2) DO UPDATE SET agree1 = 0, agree2 = 0""", (uid1, uid2))
    conn.commit()
    cur.close()
    conn.close()
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Да", callback_data="ext_yes_" + str(uid1) + "_" + str(uid2)),
        types.InlineKeyboardButton("Нет", callback_data="ext_no_" + str(uid1) + "_" + str(uid2)),
    )
    bot.send_message(message.chat.id, get_user_tag(uid1) + " и " + get_user_tag(uid2) + ", вы хотите потушить огонёк?", reply_markup=kb)

# ========== ИГРА «УГАДАЙ ЧИСЛО» ==========

def start_game(message):
    me = message.from_user.id
    if me in games:
        bot.send_message(message.chat.id, "Игра уже началась")
        return
    games[me] = {"num": random.randint(1, 100), "attempts": 7}
    bot.send_message(message.chat.id, "🎲 Я загадал число от 1 до 100!\n\nПиши числа в ответ на это сообщение.\nУ тебя 7 попыток.")

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

# ========== ДЕЙСТВИЯ ==========

def kiss(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя целовать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " страстно поцеловал " + b + " 💋",
        a + " нежно поцеловал " + b + " 💞",
        a + " поцеловал " + b + " в щёчку 😘",
        a + " поцеловал " + b + " в губы 💋",
        a + " чмокнул " + b + " 😚",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def hug(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя обнять нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " нежно обнял " + b + " 💞",
        a + " крепко обнял " + b + " 🤗",
        a + " тепло обнял " + b + " 💖",
        a + " обнял " + b + " от всей души ❤️",
        a + " крепко-крепко обнял " + b + " 🫂",
        a + " мило обнял " + b + " 💕",
        a + " по-дружески обнял " + b + " 🤝",
        a + " сжал " + b + " в объятиях 💗",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def hit(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя бить нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " ударил " + b + " 💥",
        a + " сильно ударил " + b + " ⚡",
        a + " ударил " + b + " в плечо 🥊",
        a + " дал " + b + " пощёчину ✋",
        a + " ударил " + b + " кулаком 👊",
        a + " заехал " + b + " по голове 💢",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def kick(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя пинать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " пнул " + b + " 🦵",
        a + " пнул " + b + " под зад 🦶",
        a + " сильно пнул " + b + " 🦿",
        a + " пнул " + b + " в бок 💨",
        a + " пнул " + b + " ногой 🦵",
        a + " дал " + b + " пинка 👟",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def slap(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя шлёпать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " шлёпнул " + b + " 🖐",
        a + " звонко шлёпнул " + b + " 👋",
        a + " шлёпнул " + b + " по попе ✋",
        a + " шлёпнул " + b + " 🍑",
        a + " дал " + b + " шлепок 🖐️",
        a + " шлёпнул " + b + " ладонью 🤚",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def bite(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя кусать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " укусил " + b + " 🦷",
        a + " сильно укусил " + b + " 😬",
        a + " укусил " + b + " за руку 🩸",
        a + " укусил " + b + " за плечо 🦷",
        a + " куснул " + b + " 🐾",
        a + " укусил " + b + " до крови 🩹",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def pat(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя гладить нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " погладил " + b + " 🤍",
        a + " нежно погладил " + b + " 🕊",
        a + " погладил " + b + " по голове 🌿",
        a + " ласково погладил " + b + " ✨",
        a + " погладил " + b + " по спине 🍃",
        a + " мягко погладил " + b + " 🤍",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def wink(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себе подмигивать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " подмигнул " + b + " 😉",
        a + " игриво подмигнул " + b + " 🎭",
        a + " загадочно подмигнул " + b + " 🌙",
        a + " весело подмигнул " + b + " ✨",
        a + " хитро подмигнул " + b + " 🃏",
        a + " подмигнул " + b + " 🌟",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def pinch(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя щипать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " ущипнул " + b + " 🤏",
        a + " ущипнул " + b + " за бок 😄",
        a + " больно ущипнул " + b + " 😆",
        a + " ущипнул " + b + " за щёку 🌸",
        a + " ущипнул " + b + " за руку 🤏",
        a + " слегка ущипнул " + b + " 😊",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def tickle(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя щекотать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " защекотал " + b + " до слёз 😂",
        a + " щекочет " + b + " 🪶",
        a + " защекотал " + b + " 🤣",
        a + " щекочет " + b + " под рёбрами 🪶",
        a + " защекотал " + b + " до икоты 🤭",
        a + " щекочет " + b + " 🌾",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def feed(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя кормить нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " покормил " + b + " 🍰",
        a + " накормил " + b + " 🍲",
        a + " покормил " + b + " с ложечки 🥄",
        a + " угостил " + b + " 🍫",
        a + " покормил " + b + " вкусненьким 🍓",
        a + " накормил " + b + " до отвала 🍕",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def love(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя любить нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " признался в чувствах " + b + " 💌",
        a + " признался в любви " + b + " 💘",
        a + " признался в своих чувствах " + b + " 🌹",
        a + " открыто признался в чувствах " + b + " 💫",
        a + " нежно признался в чувствах " + b + " 💞",
        a + " искренне признался в чувствах " + b + " ✨",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def steal(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя украсть нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " украл сердце " + b + " 💘",
        a + " украл " + b + " 🌙",
        a + " украл поцелуй у " + b + " 💋",
        a + " украл " + b + " навсегда 💫",
        a + " украл сон " + b + " 🌌",
        a + " украл улыбку " + b + " ✨",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def spank(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя шлёпать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " отшлёпал " + b + " 🖐",
        a + " отшлёпал " + b + " ремнём ⛓",
        a + " строго отшлёпал " + b + " ✋",
        a + " отшлёпал " + b + " за шалости 🌿",
        a + " наказал " + b + " шлепком 🍑",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

def punish(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Себя наказывать нельзя")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    phrases = [
        a + " наказал " + b + " ⚖",
        a + " строго наказал " + b + " 🖤",
        a + " наказал " + b + " за проступок 🗡",
        a + " наказал " + b + " по заслугам ⚔",
        a + " наказал " + b + " 🌑",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))

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
    bot.send_message(message.chat.id, a + " делает предложение " + b + "!\n\n" + b + ", ты согласен(на)?", reply_markup=kb)

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
    cur.execute("""INSERT INTO shaker (uid, score, last_play) VALUES (%s, %s, %s)
        ON CONFLICT (uid) DO UPDATE SET score = EXCLUDED.score, last_play = EXCLUDED.last_play""",
        (uid, score, last_play))
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

def coin_flip(message):
    bot.send_message(message.chat.id, random.choice(["🪙 Орёл!", "🪙 Решка!"]))

def yes_no(message):
    bot.send_message(message.chat.id, random.choice(["✅ Да!", "❌ Нет!"]))

def who_gay(message):
    all_u = get_all_users()
    if not all_u:
        bot.send_message(message.chat.id, "Никто ещё не писал в чате.")
        return
    uid, tag = random.choice(all_u)
    bot.send_message(message.chat.id, random.choice(["Я думаю гей - @" + tag, "Радар: @" + tag, "100% гей - @" + tag]))
    
    # ========== СТАРТ ==========

def who_is_olya(message):
    phrases = [
        "Оля — королева 👑",
        "Оля — лучшая 💖",
        "Оля — звезда ⭐",
        "Оля — легенда 🔥",
        "Оля — красотка 🌹",
        "Оля — умница 🧠",
        "Оля — солнышко ☀️",
        "Оля — прекрасна ✨",
        "Оля — богиня 🌸",
        "Оля — мечта 💫",
        "Оля — сокровище 💎",
        "Оля — икона 🎀",
        "Оля — лапочка 🐱",
        "Оля — суперстар 🌟",
        "Оля — вне конкуренции 🏆",
    ]
    bot.send_message(message.chat.id, random.choice(phrases))
    
@bot.message_handler(commands=["start"])
def start(message):
    save_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    bot.send_message(message.chat.id, "Я — Винди.\n\nСо мной ты можешь растить огонёк, обниматься, играть и многое другое.\n\nНапиши «винди огонёк @user», чтобы начать.")

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
            uid1, uid2, fire, is_grey, l1, l2, le = f
            partner = get_user_tag(uid2 if me == uid1 else uid1)
            status = "серый ⚫" if is_grey else "зажжён 🔴"
            t += "🔥 Огонёк " + str(i) + ": " + partner + " (" + status + ", " + str(fire) + ")\n"
    mar = get_marriage(me)
    if mar:
        uid1, uid2, cnt, since = mar
        partner = get_user_tag(uid2 if me == uid1 else uid1)
        t += "💍 Брак: " + partner + " (вместе " + time_together(time.time() - since) + ")\n"
    score, last = get_shaker(me)
    if score > 0:
        t += "🎮 Шейкер: " + str(score) + "\n"
    pet = get_pet(me)
    if pet:
        pet_type, pet_name, lvl, exp, food, walk, sleep, last_up = pet
        info = PETS.get(pet_type)
        if info:
            emoji = level_emoji(lvl)
            t += info["emoji"] + " Питомец " + info["name"] + " (" + info["rarity"] + ") " + emoji + " Ур. " + str(lvl) + "\n"
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

# ========== КОМАНДЫ КАРТОЧЕК ==========

def show_my_cards(message):
    me = message.from_user.id
    save_user(me, message.from_user.first_name, message.from_user.username)
    user_cards = get_user_cards(me)
    if not user_cards:
        bot.send_message(message.chat.id, "У тебя нет карточек. Купи: винди кейс карточек")
        return
    equipped = get_equipped_card(me)
    total_points = get_user_total_points(me)
    total_coins = get_user_total_coins_per_day(me)
    t = "🎴 Мои карточки:\n\n"
    for i, cid in enumerate(user_cards, 1):
        card = get_card(cid)
        if not card:
            continue
        status = "✅" if cid == equipped else "❌"
        t += str(i) + ". 🃏 " + card[1] + " — " + str(card[3]) + " очков, " + str(card[4]) + " монет/день " + status + "\n"
    t += "\n━━━━━━━━━━━━━\n"
    t += "✨ Всего очков: " + str(total_points) + "\n"
    t += "💰 Монет/день: " + str(total_coins)
    kb = types.InlineKeyboardMarkup(row_width=2)
    for cid in user_cards:
        card = get_card(cid)
        if not card:
            continue
        status = "✅" if cid == equipped else "❌"
        label = card[1] + " " + status
        kb.add(types.InlineKeyboardButton(label, callback_data="card_equip_" + cid))
    bot.send_message(message.chat.id, t, reply_markup=kb)

def show_my_card(message):
    me = message.from_user.id
    equipped = get_equipped_card(me)
    if not equipped:
        bot.send_message(message.chat.id, "У тебя нет надетой карточки. Выбери в «мои карточки»")
        return
    card = get_card(equipped)
    if not card:
        return
    caption = "🃏 «" + card[1] + "» (" + card[2] + ")\n"
    caption += "✨ Очки: +" + str(card[3]) + "\n"
    caption += "💰 Монеты: +" + str(card[4]) + "/день"
    bot.send_photo(message.chat.id, card[5], caption=caption)

def show_cards_top(message):
    top = get_cards_top()
    if not top:
        bot.send_message(message.chat.id, "Пока нет карточек у юзеров.")
        return
    t = "🏆 Топ карточек:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, points, coins) in enumerate(top):
        prefix = medals[i] if i < 3 else str(i + 1) + "."
        cards = get_user_cards(uid)
        card_names = []
        for cid in cards:
            card = get_card(cid)
            if card:
                card_names.append(card[1])
        names_str = ", ".join(card_names) if card_names else "—"
        t += prefix + " " + get_user_tag(uid) + " — " + names_str + " — " + str(points) + " очков, " + str(coins) + " монет/день\n"
    bot.send_message(message.chat.id, t)

def show_case_cards(message):
    me = message.from_user.id
    save_user(me, message.from_user.first_name, message.from_user.username)
    coins, _ = get_balance(me)
    if coins < 200:
        bot.send_message(message.chat.id, "Недостаточно монет. Нужно 200")
        return
    set_coins(me, coins - 200)
    all_cards = get_all_cards()
    if not all_cards:
        bot.send_message(message.chat.id, "❌ Карточек в базе нет.")
        return
    user_owned = get_user_cards(me)
    available = [c for c in all_cards if c[0] not in user_owned]
    if not available:
        bot.send_message(message.chat.id, "У тебя уже есть все карточки!")
        return
    chosen = random.choice(available)
    card_id, name, rarity, points, coins_per_day, photo = chosen
    give_card(me, card_id)
    add_coins(me, coins_per_day)
    msg = bot.send_message(message.chat.id, "📦 Открываем кейс...")
    time.sleep(1)
    bot.edit_message_text("📦 Открываем кейс... 🔄", message.chat.id, msg.message_id)
    time.sleep(1)
    bot.edit_message_text("📦 Открываем кейс... ✨", message.chat.id, msg.message_id)
    time.sleep(1)
    bot.delete_message(message.chat.id, msg.message_id)
    caption = "🎉 Коллекция пополнилась карточкой «" + name + "»\n\n"
    caption += "💎 Редкость • " + rarity + "\n"
    caption += "✨ Очки • +" + str(points) + "\n"
    caption += "💰 Монеты • +" + str(coins_per_day) + " (зачислено)"
    bot.send_photo(message.chat.id, photo, caption=caption)

# ========== ПИТОМЕЦ ==========

def get_pet_keyboard(used=0):
    kb = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    
    if not (used & 2):
        buttons.append(types.InlineKeyboardButton("🚶 Погулять", callback_data="pet_walk"))
    if not (used & 4):
        buttons.append(types.InlineKeyboardButton("😴 Спать", callback_data="pet_sleep"))
    if buttons:
        kb.add(*buttons)
    else:
        kb.add(types.InlineKeyboardButton("✅ Всё сделано", callback_data="pet_done"))
    return kb

def build_pet_text(me):
    pet = get_pet(me)
    if not pet:
        return None, None
    pet_type, pet_name, level, exp, food, walk, sleep, last_up = pet
    food, walk, sleep = calc_decay(pet)
    health = get_health(walk, sleep)
    info = PETS.get(pet_type)
    if not info:
        return None, None
    emoji = level_emoji(level)
    sad = " 😢" if health == 0 else ""
    t = info["name"] + " " + info["emoji"] + " (" + info["rarity"] + ")" + sad + "\n\n"
    t += info["art"] + "\n\n"
    if pet_name:
        t += "Имя: " + pet_name + "\n"
    else:
        t += "Имя: не задано\nНапиши: изменить имя питомца [имя]\n"
    if level >= 50:
        t += emoji + " Ур. 50 (" + str(exp) + "/∞ exp)\n\n"
    else:
        t += emoji + " Ур. " + str(level) + " (" + str(exp) + "/" + str(exp_needed(level)) + " exp)\n\n"
       
    t += "🚶 Прогулка: " + str(walk) + "%\n"
    t += "😴 Сон: " + str(sleep) + "%\n"
    t += "❤️ Здоровье: " + str(health) + "%"
    used = 0
    if walk >= 100:
        used |= 2
    if sleep >= 100:
        used |= 4
    return t, used

def show_pet(message):
    me = message.from_user.id
    pet = get_pet(me)
    if not pet:
        bot.send_message(message.chat.id, "У тебя нет питомца. Купи: винди заведи питомца")
        return
    t, used = build_pet_text(me)
    if not t:
        return
    bot.send_message(message.chat.id, t, reply_markup=get_pet_keyboard(used))

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

def change_pet_name(message, new_name):
    me = message.from_user.id
    if not get_pet(me):
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
    current_type = pet[0]
    skins = get_pet_skins(me)
    if not skins:
        bot.send_message(message.chat.id, "У тебя нет скинов.")
        return
    if len(skins) == 1:
        info = PETS.get(skins[0])
        bot.send_message(message.chat.id, info["emoji"] + " " + info["name"] + " (" + info["rarity"] + ") (сейчас)")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for s in skins:
        info = PETS.get(s)
        label = info["emoji"] + " " + info["name"] + " (" + info["rarity"] + ")"
        if s == current_type:
            label += " (сейчас)"
        buttons.append(types.InlineKeyboardButton(label, callback_data="skin_" + s))
    kb.add(*buttons)
    bot.send_message(message.chat.id, "Выбери скин:", reply_markup=kb)

def show_cases(message):
    me = message.from_user.id
    save_user(me, message.from_user.first_name, message.from_user.username)
    t = ""
    for key in ["common", "rare"]:
        c = CASES[key]
        emojis = "".join([PETS[p]["emoji"] for p in c["pets"]])
        t += "📦 " + c["name"] + " кейс — " + str(c["price"]) + " монет\n"
        t += "Питомцы: " + emojis + "\n"
        t += "Шансы: по " + str(int(100 / len(c["pets"]))) + "%\n\n"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📦 Обычный", callback_data="case_common"),
        types.InlineKeyboardButton("📦 Редкий", callback_data="case_rare"),
    )
    bot.send_message(message.chat.id, t.strip(), reply_markup=kb)

def open_case(call, case_key):
    me = call.from_user.id
    c = CASES.get(case_key)
    if not c:
        return
    coins, _ = get_balance(me)
    if coins < c["price"]:
        bot.answer_callback_query(call.id, "Недостаточно монет. Нужно " + str(c["price"]))
        return
    owned = get_pet_skins(me)
    available = [p for p in c["pets"] if p not in owned]
    if not available:
        bot.answer_callback_query(call.id, "У тебя уже есть все питомцы из этого кейса")
        return
    set_coins(me, coins - c["price"])
    pet_type = random.choice(available)
    info = PETS[pet_type]
    msg = bot.send_message(call.message.chat.id, "📦 Открываем...")
    time.sleep(1)
    bot.edit_message_text("📦 Открываем... 🔄", call.message.chat.id, msg.message_id)
    time.sleep(1)
    bot.edit_message_text("📦 Открываем... ✨", call.message.chat.id, msg.message_id)
    time.sleep(1)
    bot.edit_message_text("🎉 Тебе выпал питомец: " + info["emoji"] + " " + info["name"] + "!", call.message.chat.id, msg.message_id)
    if not get_pet(me):
        create_pet(me, pet_type)
    else:
        set_pet_type(me, pet_type)

def pets_top(message):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid, pet_type, level FROM pets ORDER BY level DESC LIMIT 5")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        bot.send_message(message.chat.id, "Пока нет питомцев.")
        return
    t = "🏆 Топ питомцев\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, pet_type, lvl) in enumerate(rows):
        info = PETS.get(pet_type)
        if not info:
            continue
        emoji = level_emoji(lvl)
        prefix = medals[i] if i < 3 else str(i + 1) + "."
        t += prefix + " " + get_user_tag(uid) + " — " + info["emoji"] + " " + info["name"] + " (" + info["rarity"] + ") " + emoji + " Ур. " + str(lvl) + "\n"
    bot.send_message(message.chat.id, t)

# ========== ОГОНЁК ==========

def offer_fire(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.send_message(message.chat.id, "Нельзя зажечь огонёк с самим собой")
        return
    if get_duo_fire_with(me, target_id):
        bot.send_message(message.chat.id, "У вас уже есть огонёк с " + get_user_tag(target_id))
        return
    if count_duo_fires(me) >= 3:
        bot.send_message(message.chat.id, "У тебя уже 3 огонька")
        return
    if count_duo_fires(target_id) >= 3:
        bot.send_message(message.chat.id, "У " + get_user_tag(target_id) + " уже 3 огонька")
        return
    a = get_user_tag(me)
    b = get_user_tag(target_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Принять", callback_data="fire_yes_" + str(me) + "_" + str(target_id)),
        types.InlineKeyboardButton("Отказаться", callback_data="fire_no_" + str(me) + "_" + str(target_id)),
    )
    bot.send_message(message.chat.id, "🔥 " + a + " хочет зажечь огонёк с " + b + "\n\n" + b + ", ты согласен?", reply_markup=kb)

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
            my_last = last1
            other_last = last2
        else:
            my_last = last2
            other_last = last1
        if my_last >= today_start and other_last >= today_start:
            continue
        if my_last >= today_start:
            grey_partners.append(uid2 if me == uid1 else uid1)
            all_green = False
            continue
        if other_last >= today_start:
            new_fire = fire + 1
            if me == uid1:
                n1, n2 = now, other_last
            else:
                n1, n2 = other_last, now
            update_duo_fire(uid1, uid2, new_fire, 0, n1, n2, now)
            just_activated.append((uid2 if me == uid1 else uid1, new_fire))
        else:
            if me == uid1:
                n1, n2 = now, other_last
            else:
                n1, n2 = other_last, now
            update_duo_fire(uid1, uid2, fire, is_grey, n1, n2, last_ext)
            grey_partners.append(uid2 if me == uid1 else uid1)
            all_green = False
    for pid, nf in just_activated:
        bot.send_message(message.chat.id, "🔥 Огонёк зажжён!\n\n" + get_user_tag(me) + " + " + get_user_tag(pid) + "\nЧисло: " + str(nf))
    if all_green and not just_activated and not grey_partners:
        if len(fires) == 1:
            bot.send_message(message.chat.id, "🔥 Огонёк уже горит")
        else:
            bot.send_message(message.chat.id, "🔥 Огоньки уже горят")
        return
    if grey_partners:
        bot.send_message(message.chat.id, "⏳ Ждём " + ", ".join([get_user_tag(p) for p in grey_partners]))

def my_fire(message):
    me = message.from_user.id
    fires = get_all_duo_fires(me)
    if not fires:
        bot.send_message(message.chat.id, "У тебя нет огонька. Напиши: винди огонёк @user")
        return
    if len(fires) == 1:
        uid1, uid2, fire, is_grey, l1, l2, le = fires[0]
        partner = get_user_tag(uid2 if me == uid1 else uid1)
        status = "серый ⚫" if is_grey else "зажжён 🔴"
        bot.send_message(message.chat.id, "🔥 Твой огонёк:\n\n" + partner + " — " + status + " (" + str(fire) + ")")
    else:
        t = "🔥 Твои огоньки:\n\n"
        for i, f in enumerate(fires, 1):
            uid1, uid2, fire, is_grey, l1, l2, le = f
            partner = get_user_tag(uid2 if me == uid1 else uid1)
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
        t += "Огонёк 🔥 " + get_user_tag(u1) + " и " + get_user_tag(u2) + " составляет " + str(fire) + "\n"
    bot.send_message(message.chat.id, t)

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

    # АДМИН
    if message.chat.type == "private" and message.from_user.id == ADMIN_ID:
        if ADMIN_ID in pending_admin:
            target_uid, target_fire = pending_admin[ADMIN_ID]
            if text == SECRET_CODE:
                fires = get_all_duo_fires(target_uid)
                if not fires:
                    bot.send_message(message.chat.id, "❌ У юзера нет огонька.")
                else:
                    uid1, uid2, fire, is_grey, l1, l2, le = fires[0]
                    update_duo_fire(uid1, uid2, target_fire, 0, l1, l2, le)
                    bot.send_message(message.chat.id, "✅ Огонёк " + str(target_fire) + " выдан")
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
                    bot.send_message(message.chat.id, "✅ " + str(target_coins) + " монет выдано " + get_user_tag(target_uid))
            else:
                bot.send_message(message.chat.id, "❌ Неверный код")
            del pending_coins[ADMIN_ID]
            return

        if ADMIN_ID in pending_pet:
            target_uid, pet_type = pending_pet[ADMIN_ID]
            if text == SECRET_CODE:
                if target_uid is None:
                    bot.send_message(message.chat.id, "❌ Юзер не найден")
                else:
                    if not get_pet(target_uid):
                        create_pet(target_uid, pet_type)
                    else:
                        set_pet_type(target_uid, pet_type)
                    info = PETS[pet_type]
                    bot.send_message(message.chat.id, "✅ " + info["emoji"] + " " + info["name"] + " выдан " + get_user_tag(target_uid))
            else:
                bot.send_message(message.chat.id, "❌ Неверный код")
            del pending_pet[ADMIN_ID]
            return

        if ADMIN_ID in pending_level:
            target_uid, target_level = pending_level[ADMIN_ID]
            if text == SECRET_CODE:
                if target_uid is None:
                    bot.send_message(message.chat.id, "❌ Юзер не найден")
                elif not get_pet(target_uid):
                    bot.send_message(message.chat.id, "❌ У юзера нет питомца")
                else:
                    set_pet_level(target_uid, target_level)
                    bot.send_message(message.chat.id, "✅ Уровень питомца = " + str(min(target_level, 50)))
            else:
                bot.send_message(message.chat.id, "❌ Неверный код")
            del pending_level[ADMIN_ID]
            return

        if ADMIN_ID in pending_exp:
            target_uid, target_exp = pending_exp[ADMIN_ID]
            if text == SECRET_CODE:
                if target_uid is None:
                    bot.send_message(message.chat.id, "❌ Юзер не найден")
                elif not get_pet(target_uid):
                    bot.send_message(message.chat.id, "❌ У юзера нет питомца")
                else:
                    res = add_pet_exp(target_uid, target_exp)
                    if res:
                        lvl, exp = res
                        bot.send_message(message.chat.id, "✅ Ур. " + str(lvl) + " (" + str(exp) + " exp)")
            else:
                bot.send_message(message.chat.id, "❌ Неверный код")
            del pending_exp[ADMIN_ID]
            return

        if low.startswith("винди огонёк"):
            parts = text.split()
            if len(parts) >= 4:
                try:
                    fire_num = int(parts[3])
                except:
                    bot.send_message(message.chat.id, "❌ Число неверное")
                    return
                target_uid = get_uid_by_tag(parts[2])
                if not target_uid:
                    bot.send_message(message.chat.id, "❌ Юзер не найден.")
                    return
                pending_admin[ADMIN_ID] = (target_uid, fire_num)
                bot.send_message(message.chat.id, "Введите секретный код:")
                return

        if low.startswith("винди монеты"):
            parts = text.split()
            if len(parts) >= 4:
                try:
                    coins_num = int(parts[3])
                except:
                    bot.send_message(message.chat.id, "❌ Число неверное")
                    return
                target_uid = get_uid_by_tag(parts[2])
                if not target_uid:
                    bot.send_message(message.chat.id, "❌ Юзер не найден")
                    return
                pending_coins[ADMIN_ID] = (target_uid, coins_num)
                bot.send_message(message.chat.id, "Введите секретный код:")
                return

        if low.startswith("винди питомец"):
            parts = text.split()
            if len(parts) >= 4:
                pet_type = NAME_TO_TYPE.get(parts[3].lower())
                if not pet_type:
                    bot.send_message(message.chat.id, "❌ Питомец не найден")
                    return
                target_uid = get_uid_by_tag(parts[2])
                if not target_uid:
                    bot.send_message(message.chat.id, "❌ Юзер не найден")
                    return
                pending_pet[ADMIN_ID] = (target_uid, pet_type)
                bot.send_message(message.chat.id, "Введите секретный код:")
                return

        if low.startswith("винди уровень"):
            parts = text.split()
            if len(parts) >= 4:
                try:
                    lvl = int(parts[3])
                except:
                    bot.send_message(message.chat.id, "❌ Число неверное")
                    return
                target_uid = get_uid_by_tag(parts[2])
                if not target_uid:
                    bot.send_message(message.chat.id, "❌ Юзер не найден")
                    return
                pending_level[ADMIN_ID] = (target_uid, lvl)
                bot.send_message(message.chat.id, "Введите секретный код:")
                return

        if low.startswith("винди опыт"):
            parts = text.split()
            if len(parts) >= 4:
                try:
                    exp_num = int(parts[3])
                except:
                    bot.send_message(message.chat.id, "❌ Число неверное")
                    return
                target_uid = get_uid_by_tag(parts[2])
                if not target_uid:
                    bot.send_message(message.chat.id, "❌ Юзер не найден")
                    return
                pending_exp[ADMIN_ID] = (target_uid, exp_num)
                bot.send_message(message.chat.id, "Введите секретный код:")
                return

    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot.get_me().id:
            if message.from_user.id in games:
                guess_number(message)
                return

    # КОМАНДЫ
    if low == "винди профиль":
        show_profile(message)
        return
    if low == "балик":
        show_balance(message)
        return
    if low == "топ балик":
        show_balance_top(message)
        return
    if low == "винди кейсы":
        show_cases(message)
        return
    if low == "мои карточки":
       show_my_cards(message)
       return
    if low == "моя карточка":
       show_my_card(message)
       return
    if low == "топ карточек":
       show_cards_top(message)
       return
    if low == "винди кейс карточек":
       show_case_cards(message)
       return
    if low == "винди заведи питомца":
        buy_pet(message)
        return
    if low == "мой питомец":
        show_pet(message)
        return
    if low == "винди скины":
        show_pet_skins(message)
        return
    if low == "топ питомцев":
        pets_top(message)
        return
    if low.startswith("изменить имя питомца"):
        new_name = text[len("изменить имя питомца"):].strip()
        if not new_name:
            bot.send_message(message.chat.id, "Напиши: изменить имя питомца [имя]")
            return
        change_pet_name(message, new_name)
        return
    if low == "винди развод":
        divorce_request(message)
        return
    if low.startswith("винди потуши огонёк"):
        parts = text.split()
        if len(parts) >= 4:
            target_uid = get_uid_by_tag(parts[3])
            if not target_uid:
                bot.send_message(message.chat.id, "❌ Юзер не найден.")
                return
            extinguish_request(message, target_uid)
        return
    if low.startswith("винди огонёк") and message.chat.type != "private":
        parts = text.split()
        if len(parts) >= 3:
            target_uid = get_uid_by_tag(parts[2])
            if not target_uid:
                bot.send_message(message.chat.id, "❌ Юзер не найден.")
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
    if low == "винди орел или решка" or low == "винди орёл или решка":
        coin_flip(message)
        return
    if low == "винди да или нет":
        yes_no(message)
        return

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if low == "обнять":
            hug(message, target_id)
            return
        if low == "поцеловать":
            kiss(message, target_id)
            return
        if low == "ударить":
            hit(message, target_id)
            return
        if low == "пнуть":
            kick(message, target_id)
            return
        if low == "шлёпнуть":
            slap(message, target_id)
            return
        if low == "укусить":
            bite(message, target_id)
            return
        if low == "погладить":
            pat(message, target_id)
            return
        if low == "подмигнуть":
            wink(message, target_id)
            return
        if low == "ущипнуть":
            pinch(message, target_id)
            return
        if low == "щекотать":
            tickle(message, target_id)
            return
        if low == "покормить":
            feed(message, target_id)
            return
        if low == "лавю":
            love(message, target_id)
            return
        if low == "украсть":
            steal(message, target_id)
            return
        if low == "отшлёпать":
            spank(message, target_id)
            return
        if low == "наказать":
            punish(message, target_id)
            return
        if "замуж" in low or "женись" in low or "женить" in low:
            marry(message, target_id)
            return

    if low == "шейкер":
        play_shaker(message)
        return
    if low == "ш топ":
        shaker_top(message)
        return
    if "винди" in low and "брак" in low:
        show_marriages(message)
        return
    if "винди" in low and "гей" in low:
        who_gay(message)
        return
    if "винди" in low and "оля" in low:
        who_is_olya(message)
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

    if action == "pet":
        sub = parts[1]
        me = call.from_user.id
        if sub == "done":
            bot.answer_callback_query(call.id, "Все действия выполнены")
            return
        res = pet_action(me, sub)
        if res:
            add, exp_add = res
            if sub == "food":
                txt = "🍖 +" + str(add) + "% еды, +" + str(exp_add) + " exp"
            elif sub == "walk":
                txt = "🚶 +" + str(add) + "% прогулки, +" + str(exp_add) + " exp"
            else:
                txt = "😴 +" + str(add) + "% сна, +" + str(exp_add) + " exp"
            bot.answer_callback_query(call.id, txt)
            t, used = build_pet_text(me)
            if t:
                try:
                    bot.edit_message_text(t, call.message.chat.id, call.message.message_id, reply_markup=get_pet_keyboard(used))
                except:
                    pass
        return

    if action == "case":
        open_case(call, parts[1])
        return

    if action == "skin":
        pet_type = parts[1]
        me = call.from_user.id
        if not get_pet(me):
            return
        if pet_type not in get_pet_skins(me):
            return
        set_pet_type(me, pet_type)
        info = PETS.get(pet_type)
        if info:
            bot.edit_message_text("✅ Скин изменён на " + info["emoji"] + " " + info["name"], call.message.chat.id, call.message.message_id)

     if action == "card_equip":
         card_id = parts[2] if len(parts) > 2 else None
         me = call.from_user.id
         card = get_card(card_id)
         if not card:
             return
         if get_equipped_card(me) == card_id:
             set_equipped_card(me, None)
             try:
                 bot.edit_message_text("Карточка " + card[1] + " была снята ❌", call.message.chat.id, call.message.message_id)
             except:
                 pass
         else:
             set_equipped_card(me, card_id)
             try:
                 bot.edit_message_text("Карточка " + card[1] + " была надета ✅", call.message.chat.id, call.message.message_id)
             except:
                 pass
         return
                                  
    if action == "divorce":
        decision = parts[1]
        uid1 = int(parts[2])
        uid2 = int(parts[3])
        if call.from_user.id not in [uid1, uid2]:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT agree1, agree2 FROM divorce_votes WHERE uid1 = %s AND uid2 = %s", (uid1, uid2))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return
        a1, a2 = row
        if decision == "yes":
            if call.from_user.id == uid1:
                a1 = 1
            else:
                a2 = 1
        else:
            if call.from_user.id == uid1:
                a1 = -1
            else:
                a2 = -1
        cur.execute("UPDATE divorce_votes SET agree1 = %s, agree2 = %s WHERE uid1 = %s AND uid2 = %s", (a1, a2, uid1, uid2))
        conn.commit()
        cur.close()
        conn.close()
        if a1 == 1 and a2 == 1:
            delete_marriage(uid1, uid2)
            bot.edit_message_text("Развод! " + get_user_tag(uid1) + " и " + get_user_tag(uid2) + " больше не вместе", call.message.chat.id, call.message.message_id)
        elif a1 == -1 or a2 == -1:
            who = get_user_tag(uid1) if (a1 == -1) else get_user_tag(uid2)
            bot.edit_message_text("❌ Брак остался. " + who + " отказался", call.message.chat.id, call.message.message_id)
        return

    if action == "ext":
        decision = parts[1]
        uid1 = int(parts[2])
        uid2 = int(parts[3])
        if call.from_user.id not in [uid1, uid2]:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT agree1, agree2 FROM duo_break WHERE uid1 = %s AND uid2 = %s", (uid1, uid2))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return
        a1, a2 = row
        if decision == "yes":
            if call.from_user.id == uid1:
                a1 = 1
            else:
                a2 = 1
        else:
            if call.from_user.id == uid1:
                a1 = -1
            else:
                a2 = -1
        cur.execute("UPDATE duo_break SET agree1 = %s, agree2 = %s WHERE uid1 = %s AND uid2 = %s", (a1, a2, uid1, uid2))
        conn.commit()
        cur.close()
        conn.close()
        if a1 == 1 and a2 == 1:
            delete_duo_fire(uid1, uid2)
            bot.edit_message_text("Огонёк между " + get_user_tag(uid1) + " и " + get_user_tag(uid2) + " был потушен", call.message.chat.id, call.message.message_id)
        elif a1 == -1 or a2 == -1:
            who = get_user_tag(uid1) if (a1 == -1) else get_user_tag(uid2)
            bot.edit_message_text("❌ Огонёк остался. " + who + " отказался", call.message.chat.id, call.message.message_id)
        return

    if action == "fire":
        decision = parts[1]
        uid1 = int(parts[2])
        uid2 = int(parts[3])
        if call.from_user.id != uid2:
            return
        if decision == "yes":
            create_duo_fire(uid1, uid2)
            bot.edit_message_text("🔥 Огонёк создан!\n\n" + get_user_tag(uid1) + " + " + get_user_tag(uid2) + "\nЧисло: 1", call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(get_user_tag(uid2) + " отказал(а)", call.message.chat.id, call.message.message_id)
        return

    if action in ("accept", "reject"):
        uid1 = int(parts[1])
        uid2 = int(parts[2])
        if call.from_user.id != uid2:
            return
        if action == "accept":
            add_marriage(uid1, uid2)
            bot.edit_message_text("Женаты! " + get_user_tag(uid1) + " + " + get_user_tag(uid2), call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(get_user_tag(uid2) + " отказал(а) " + get_user_tag(uid1), call.message.chat.id, call.message.message_id)

# ========== ЗАПУСК ==========

init_db()
t = threading.Thread(target=background_fire_check)
t.daemon = True
t.start()
print("Бот запущен!")
bot.polling(none_stop=True)
