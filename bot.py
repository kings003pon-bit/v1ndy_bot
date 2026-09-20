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

# ========== ПАРНЫЙ ОГОНЁК ==========

def get_duo_fire(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT uid1, uid2, fire, is_grey, last_uid1, last_uid2, last_extend
        FROM duo_fires WHERE uid1 = %s OR uid2 = %s
    """, (uid, uid))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

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

def break_duo_fire(uid1, uid2):
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

# ========== РАЗВЛЕЧЕНИЯ ==========

def time_together(seconds):
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    if days > 0:
        return str(days) + " дн. " + str(hours) + " ч."
    elif hours > 0:
        return str(hours) + " ч. " + str(minutes) + " мин."
    return str(minutes) + " мин."

@bot.message_handler(commands=["start"])
def start(message):
    save_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    bot.send_message(message.chat.id, "Привет! Я бот Винди.")

@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(message.chat.id, "винди кто гей / винди браки / шейкер / ш топ / винди огонёк @user / огонёк / топ огоньков / обнять / поцеловать")

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

def offer_fire(message, target_id):
    me = message.from_user.id
    if me == target_id:
        bot.reply_to(message, "Нельзя зажечь огонёк с самим собой")
        return
    if get_duo_fire(me):
        bot.send_message(message.chat.id, "У тебя уже есть огонёк")
        return
    if get_duo_fire(target_id):
        bot.send_message(message.chat.id, "У этого пользователя уже есть огонёк")
        return

    a = get_user_tag(me)
    b = get_user_tag(target_id)
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
    row = get_duo_fire(me)
    if not row:
        bot.send_message(message.chat.id, "У тебя нет огонька. Напиши: винди огонёк @user")
        return

    uid1, uid2, fire, is_grey, last1, last2, last_ext = row

    if me == uid1:
        my_last = last1
        other_last = last2
    else:
        my_last = last2
        other_last = last1

    now = int(time.time())
    today_start = int(datetime.datetime.utcnow().replace(hour=0, minute=1, second=0, microsecond=0).timestamp())

    if my_last >= today_start:
        bot.send_message(message.chat.id, "Ты уже писал огонёк сегодня. Ждём партнёра")
        return

    partner_id = uid2 if me == uid1 else uid1
    partner = get_user_tag(partner_id)

    if other_last >= today_start:
        fire += 1
        is_grey = 0
        if me == uid1:
            new_last1, new_last2 = now, other_last
        else:
            new_last1, new_last2 = other_last, now
        update_duo_fire(uid1, uid2, fire, is_grey, new_last1, new_last2, now)
        a = get_user_tag(uid1)
        b = get_user_tag(uid2)
        text = "🔥 Огонёк зажжён!\n\n" + a + " + " + b + "\nЧисло: " + str(fire) + "\n\nНе забывайте завтра 🔥"
        bot.send_message(message.chat.id, text)
    else:
        if me == uid1:
            new_last1, new_last2 = now, other_last
        else:
            new_last1, new_last2 = other_last, now
        update_duo_fire(uid1, uid2, fire, is_grey, new_last1, new_last2, last_ext)
        bot.send_message(message.chat.id, "🔥 Ты отметился. Ждём " + partner)

def fire_top(message):
    rows = get_duo_top()
    if not rows:
        bot.send_message(message.chat.id, "Пока нет огоньков.")
        return
    t = "Топ огоньков:\n\n"
    for i, (u1, u2, fire) in enumerate(rows, 1):
        a = get_user_tag(u1)
        b = get_user_tag(u2)
        t += "Огонёк 🔥 " + a + " и " + b + " составляет " + str(fire) + "\n"
    bot.send_message(message.chat.id, t)

def break_fire_request(message):
    me = message.from_user.id
    row = get_duo_fire(me)
    if not row:
        bot.send_message(message.chat.id, "У тебя нет огонька.")
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
        types.InlineKeyboardButton("Да", callback_data="break_yes_" + str(uid1) + "_" + str(uid2)),
        types.InlineKeyboardButton("Нет", callback_data="break_no_" + str(uid1) + "_" + str(uid2)),
    )
    text = "🔥 " + a + " и " + b + ", вы действительно хотите разорвать огонёк?"
    bot.send_message(message.chat.id, text, reply_markup=kb)

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

    # Админ-панель
    if message.chat.type == "private" and message.from_user.id == ADMIN_ID:
        if ADMIN_ID in pending_admin:
            target_uid, target_fire = pending_admin[ADMIN_ID]
            if text == SECRET_CODE:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO shaker (uid, score, last_play) VALUES (%s, %s, 0)
                    ON CONFLICT (uid) DO UPDATE SET score = EXCLUDED.score
                """, (target_uid, target_fire))
                conn.commit()
                cur.close()
                conn.close()
                tag = get_user_tag(target_uid)
                bot.send_message(message.chat.id, "✅ Число " + str(target_fire) + " выдано " + tag)
            else:
                bot.send_message(message.chat.id, "❌ Неверный код")
            del pending_admin[ADMIN_ID]
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

    # Предложение огонька
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

    if low == "огонёк":
        extend_fire(message)
        return
    if low == "топ огоньков":
        fire_top(message)
        return
    if low == "винди разорви огонёк":
        break_fire_request(message)
        return

    # Обнимашки
    if low == "обнять" and message.reply_to_message:
        hug(message, message.reply_to_message.from_user.id)
        return

    # Поцелуй
    if low == "поцеловать" and message.reply_to_message:
        kiss(message, message.reply_to_message.from_user.id)
        return

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
    if "ало" in low:
        responses = ["Ало", "Ало, чё надо?", "Алё-алё", "Ало, я тут", "Ало, не слышу"]
        bot.send_message(message.chat.id, random.choice(responses))
        return
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if "замуж" in low or "женись" in low or "женить" in low:
            marry(message, target_id)

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    parts = call.data.split("_")
    action = parts[0]

    if action == "fire":
        decision = parts[1]
        uid1 = int(parts[2])
        uid2 = int(parts[3])
        if call.from_user.id != uid2:
            return
        a = get_user_tag(uid1)
        b = get_user_tag(uid2)
        if decision == "yes":
            create_duo_fire(uid1, uid2)
            text = "🔥 ОГОНЁК СОЗДАН 🔥\n\n" + a + " + " + b + "\nЧисло: 1\n\nПродлевайте каждый день вместе 🔥"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(b + " отказал(а) " + a + " 💔", call.message.chat.id, call.message.message_id)
        return

    if action == "break":
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
        agree1, agree2 = row

        if decision == "yes":
            if call.from_user.id == uid1:
                agree1 = 1
            else:
                agree2 = 1
        else:
            if call.from_user.id == uid1:
                agree1 = -1
            else:
                agree2 = -1

        cur.execute("UPDATE duo_break SET agree1 = %s, agree2 = %s WHERE uid1 = %s AND uid2 = %s",
                    (agree1, agree2, uid1, uid2))
        conn.commit()
        cur.close()
        conn.close()

        a = get_user_tag(uid1)
        b = get_user_tag(uid2)

        if agree1 == 1 and agree2 == 1:
            break_duo_fire(uid1, uid2)
            bot.edit_message_text("🔥 Огонёк разорван. " + a + " и " + b + " больше не связаны.", call.message.chat.id, call.message.message_id)
        elif agree1 == -1 or agree2 == -1:
            bot.edit_message_text("Огонёк остался. Кто-то отказался разрывать.", call.message.chat.id, call.message.message_id)
        else:
            who = a if call.from_user.id == uid1 else b
            bot.edit_message_text("🔥 " + who + " выбрал(а). Ждём второго...", call.message.chat.id, call.message.message_id)
        return

    if action in ("accept", "reject"):
        uid1 = int(parts[1])
        uid2 = int(parts[2])
        if call.from_user.id != uid2:
            return
        if action == "accept":
            add_marriage(uid1, uid2)
            a = get_user_tag(uid1)
            b = get_user_tag(uid2)
            bot.edit_message_text("Женаты! " + a + " + " + b, call.message.chat.id, call.message.message_id)
        else:
            a = get_user_tag(uid1)
            b = get_user_tag(uid2)
            bot.edit_message_text(b + " отказал(а) " + a, call.message.chat.id, call.message.message_id)

# ========== ЗАПУСК ==========

init_db()

t = threading.Thread(target=background_fire_check)
t.daemon = True
t.start()

print("Бот запущен!")
bot.polling(none_stop=True)
