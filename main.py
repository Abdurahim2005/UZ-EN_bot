import telebot
import json
import random
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# Bot tokenini kiriting
TOKEN = "7928658663:AAHIFCzzL-2qjkZJwxvoVQ0TQtXqsr3XRr0"
bot = telebot.TeleBot(TOKEN)


# Foydalanuvchi ma'lumotlari fayli
USERS_FILE = "users.json"

# Foydalanuvchi ma'lumotlarini yuklash
def load_users():
    try:
        with open(USERS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Foydalanuvchi ma'lumotlarini saqlash
def save_users(users):
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file, indent=4)

# Global foydalanuvchi ma'lumotlari
users = load_users()

#####################################################################################
@bot.message_handler(commands=['bot_info'])
def bot_info(message):
    info_text = (
        "ℹ️Bot haqida qisqacha.\n"
        "——————————————-\n"
        "🤖Bu botda \"Uzbekcha -> Inglizcha\" yoki \"Inglizcha -> Uzbekcha\" testlar topshirish orqali bilimingizni sinashingiz mumkin.\n"
        "🤞Botda 2 ta usulda testni boshlash mumkin (UZ-EN yoki EN-UZ).\n"
        "✅Har bir yo'nalishda to'plangan ballar alohida hisoblanadi.\n"
        "———————————————\n"
        "📊ALL Reyting esa ikkala natijalarni yig'indisi hisoblanib Top 10 talikni aniqlaydi.\n\n"
        "🖼UZ-EN yoki EN-UZ yo'nalishidagi har bir to'g'ri javob uchun   \n🎉+1 bal qo'shiladi, xato javob uchun ayrilmaydi.\n\n"
        "🌟Stars ballari:\n"
        "⚠️Diqqat hushyor bo'ling bu ballar o'zgaruvchandir.\n"
        "✅Har bir tog'ri javob uchun 0.1 bal beriladi.\n"
        "❌Xato javob uchun -0.1 bal ayriladi (ikkala yo'nalishda ham).\n\n"
        "@savol_javob2_bot"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    start_button = telebot.types.InlineKeyboardButton("🏃‍♂️‍➡️ Testni boshlash", callback_data="restart:quiz")
    markup.add(start_button)
    bot.send_message(message.chat.id, info_text, reply_markup=markup)
    
@bot.message_handler(commands=["reyting"])
def show_rating_buttons(message):
    # Reyting tugmalarini yaratish
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔄 Testni qaytadan boshlash", callback_data="restart:quiz")
    )
    keyboard.add(
        InlineKeyboardButton("✨ ALL Reyting", callback_data="rating:all"),
        InlineKeyboardButton("🇺🇿 UZ-EN Reyting", callback_data="rating:uz_en"),
        InlineKeyboardButton("🇬🇧 EN-UZ Reyting", callback_data="rating:en_uz"),
        InlineKeyboardButton("🌟 Stars", callback_data="rating:stars")
    )

    # Xabarni o'zimiz yozamiz
    bot.send_message(
        chat_id=message.chat.id,
        text="Mana reytinglar:",
        reply_markup=keyboard
    )
#####################################################################################

# Start xabari
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        # Yangi foydalanuvchi qo'shish
        users[user_id] = {
            "id": message.from_user.id,
            "name": message.from_user.first_name,
            "username": message.from_user.username,
            "gender": None,  # Erkak yoki ayol kiritiladi
            "admin": False,  # Admin flagi
            "pointsUZ_EN": 0,  # Default qiymat 0
            "pointsEN_UZ": 0,   # Default qiymat 0
            "all_points": 0,  # Default qiymat 0
            "stars": 0.0  # Default qiymat 0.0
        }
        save_users(users)
        # Genderni so'rash
        bot.send_message(
            message.chat.id,
            "🙂Assalomu alaykum! Jinsingizni tanlang:",
            reply_markup=gender_inline_keyboard()
        )
    elif users[user_id]["gender"] is None:
        bot.send_message(
            message.chat.id,
            "Iltimos, avval jinsingizni tanlang:",
            reply_markup=gender_inline_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            f"😇Xush kelibsiz, {users[user_id]['name']}! Qaytib kelganingizdan xursandmiz."
        )
        show_inline_main_menu(message)

# Gender inline tugmachalari
def gender_inline_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Erkak", callback_data="gender_Erkak"),
        InlineKeyboardButton("Ayol", callback_data="gender_Ayol")
    )
    return markup

# Genderni qayta ishlash
@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def handle_gender(call):
    user_id = str(call.from_user.id)
    if user_id in users:
        selected_gender = call.data.split("_")[1]
        users[user_id]["gender"] = selected_gender
        save_users(users)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🙆‍♂️Rahmat! Jinsingiz: {selected_gender}."
        )
        show_inline_main_menu(call.message)
    else:
        bot.send_message(
            call.message.chat.id,
            "Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta yuboring."
        )

# Foydalanuvchi jinsini tekshirish
def check_gender(message):
    user_id = str(message.from_user.id)
    if user_id not in users or users[user_id].get("gender") is None:
        bot.send_message(
            message.chat.id,
            "❗️Iltimos, avval jinsingizni tanlang!",
            reply_markup=gender_inline_keyboard()
        )
        return False
    return True
# Barcha xabarlarni qayta ishlash
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if not check_gender(message):
        return

# Global dictionaries for user sessions
user_sessions = {}

@bot.callback_query_handler(func=lambda call: call.data == "restart:quiz")
def restart_quiz(call):
    show_inline_main_menu(call.message)

# Asosiy menyuni yaratish funksiyasi
def show_inline_main_menu(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🇺🇿UZ-EN", callback_data="start:🇺🇿UZ-EN"),
        InlineKeyboardButton("🇬🇧EN-UZ", callback_data="start:🇬🇧EN-UZ")
    )
    bot.send_message(
        message.chat.id,
        "\u2753 Qaysi usulda savol-javob qilishni xohlaysiz?",
        reply_markup=keyboard
    )

word_list = [
    {"uz": "kitob", "en": "book"},
    {"uz": "o'qituvchi", "en": "teacher"},
    {"uz": "talaba", "en": "student"},
    {"uz": "uy", "en": "house"},
    {"uz": "stol", "en": "table"},
    {"uz": "qalam", "en": "pen"},
    {"uz": "dastur", "en": "program"},
    {"uz": "maktab", "en": "school"},
    {"uz": "kompyuter", "en": "computer"},
    {"uz": "telefon", "en": "phone"},
    {"uz": "deraza", "en": "window"},
    {"uz": "eshik", "en": "door"},
    {"uz": "bozor", "en": "market"},
    {"uz": "yil", "en": "year"},
    {"uz": "oy", "en": "month"},
    {"uz": "hafta", "en": "week"},
    {"uz": "kun", "en": "day"},
    {"uz": "soat", "en": "hour"},
    {"uz": "minut", "en": "minute"},
    {"uz": "soniya", "en": "second"},
    {"uz": "do'st", "en": "friend"},
    {"uz": "aka", "en": "brother"},
    {"uz": "opa", "en": "sister"},
    {"uz": "ota", "en": "father"},
    {"uz": "ona", "en": "mother"},
    {"uz": "o'g'il", "en": "son"},
    {"uz": "qiz", "en": "daughter"},
    {"uz": "shahar", "en": "city"},
    {"uz": "qishloq", "en": "village"},
    {"uz": "yo'l", "en": "road"}
]
def start_quiz(message, quiz_type, num_questions):
    user_id = message.chat.id
    questions = random.sample(word_list, num_questions)
    user_sessions[user_id] = {
        "quiz_type": quiz_type,
        "questions": questions,
        "current_index": 0,
        "correct": 0,
        "incorrect": 0,
        "answered": [None] * num_questions,
        "answers": [None] * num_questions,
        "message_id": None
    }
    send_question(message, user_id)
    
def set_question_count(message, quiz_type):
    try:
        num_questions = int(message.text)
        if num_questions < 5 or num_questions > len(word_list):
            raise ValueError
        start_quiz(message, quiz_type, num_questions)
    except ValueError:
        bot.send_message(
            message.chat.id,
            f"Noto'g'ri son kiritildi. Iltimos, sonni qayta kiriting (min: 5, max: {len(word_list)}):"
        )
        bot.register_next_step_handler(
            message, lambda msg: set_question_count(msg, quiz_type)
        )    
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("start"))
def choose_quiz_type(call):
    quiz_type = call.data.split(":")[1]
    bot.send_message(
        call.message.chat.id,
        f"Test savollar sonini kiriting (min: 5, max: {len(word_list)}):"
    )
    bot.register_next_step_handler(
        call.message, lambda message: set_question_count(message, quiz_type)
    )

def send_question(message, user_id):
    session = user_sessions[user_id]
    index = session["current_index"]
    question = session["questions"][index]
    quiz_type = session["quiz_type"]

    question_text = question["uz"] if quiz_type == "🇺🇿UZ-EN" else question["en"]
    correct_answer = question["en"] if quiz_type == "🇺🇿UZ-EN" else question["uz"]

    # Javoblar tartibini saqlash
    if "options_order" not in session:
        session["options_order"] = {}

    if index not in session["options_order"]:
        # Javoblar faqat birinchi marta random qilinadi
        options = [correct_answer] + random.sample(
            [q["en"] if quiz_type == "🇺🇿UZ-EN" else q["uz"] for q in word_list if q != question], 3
        )
        random.shuffle(options)
        session["options_order"][index] = options
    else:
        # Avvalgi tartibni qayta yuklash
        options = session["options_order"][index]

    keyboard = InlineKeyboardMarkup()
    for i, option in enumerate(options):
        # Tugmalar matnini tayyorlash
        if session["answered"][index] is not None:
            is_correct_option = option == correct_answer
            if session["answers"][index] == option:
                # Javob foydalanuvchi tanlagan javobga mos kelsa, stiker qo‘shiladi
                button_text = f"✅ {option}" if session["answered"][index] else f"❌ {option}"
            elif is_correct_option:
                # To‘g‘ri javob stiker bilan belgilanadi
                button_text = f"✅ {option}"
            else:
                # Oddiy tugma matni
                button_text = option
        else:
            # Javob berilmagan holatda oddiy tugma
            button_text = option

        callback_data = f"answer:{index}:{i}:{option == correct_answer}"
        button = InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        )
        keyboard.add(button)

    # Navigatsiya tugmalarini qo‘shish
    if index == len(session["questions"]) - 1:
        keyboard.add(
            InlineKeyboardButton("\u2b05\ufe0f Orqaga", callback_data="navigate:back"),
            InlineKeyboardButton("\ud83d\udcca Natijalar", callback_data="navigate:results")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("\u2b05\ufe0f Orqaga", callback_data="navigate:back"),
            InlineKeyboardButton("\u27a1\ufe0f Keyingi", callback_data="navigate:next")
        )

    # Xabar matni
    text = f"\u2753 {index + 1}-Savol:\n\n🧐 {question_text} - ?"
    if session["answered"][index] is not None:
        if session["answered"][index]:
            text += "\n\n✅ To'g'ri javob bergansiz!"
        else:
            text += "\n\n❌ Noto'g'ri javob bergansiz!"

    # Xabarni tahrirlash yoki yangi xabar yuborish
    if session.get("message_id"):
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=session["message_id"],
                text=text,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Xabarni qayta tahrirlashda xatolik: {e}")
            sent_message = bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=keyboard
            )
            session["message_id"] = sent_message.message_id
    else:
        sent_message = bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
        session["message_id"] = sent_message.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer"))
def handle_answer(call):
    user_id = call.message.chat.id
    session = user_sessions[user_id]
    _, index, chosen_idx, is_correct = call.data.split(":")
    index, chosen_idx = int(index), int(chosen_idx)
    is_correct = is_correct == "True"

    if session["answered"][index] is not None:
        bot.answer_callback_query(call.id, "Bu savolga javob berdingiz!")
        return

    session["answered"][index] = is_correct
    session["answers"][index] = call.message.reply_markup.keyboard[chosen_idx][0].text

    # Javob to'g'rimi yoki noto'g'ri ekanligini tekshirish
    update_user_points(user_id, session["quiz_type"], is_correct)

    if is_correct:
        session["correct"] += 1
    else:
        session["incorrect"] += 1

    # Javob belgilari (✅ yoki ❌) ni tiklash
    keyboard = call.message.reply_markup
    for i, button_row in enumerate(keyboard.keyboard):
        button = button_row[0]
        if session["answered"][index] is not None:  # Agar javob allaqachon berilgan bo'lsa
            if i == chosen_idx:
                button.text = f"✅ {button.text.strip('✅ ❌')}" if is_correct else f"❌ {button.text.strip('✅ ❌')}"
            elif button.text.strip("✅ ❌") == session["questions"][index]["en" if session["quiz_type"] == "🇺🇿UZ-EN" else "uz"]:
                button.text = f"✅ {button.text.strip('✅ ❌')} "
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    except Exception as e:
        print(f"Xabarni qayta tahrirlashda xatolik: {e}")
        
def update_user_points(user_id, quiz_type, is_correct):
    try:
        with open("users.json", "r") as f:
            users_data = json.load(f)
    except FileNotFoundError:
        users_data = {}

    if str(user_id) not in users_data:
        users_data[str(user_id)] = {"pointsUZ_EN": 0, "pointsEN_UZ": 0, "stars": 0.0}

    user_data = users_data[str(user_id)]
    
    # ballarni tanlovga qarab belgilanadi
    points_key = "pointsUZ_EN" if quiz_type == "🇺🇿UZ-EN" else "pointsEN_UZ"
    
    if is_correct:
        user_data[points_key] += 1  # Ballarni qo'shish
        user_data["stars"] += 0.1  # Yulduz ballarini qo'shish
    else:
        user_data["stars"] -= 0.1  # Noto'g'ri javobda yulduz ballarini kamaytirish

    # Foydalanuvchi ma'lumotlarini qayta saqlash
    with open("users.json", "w") as f:
        json.dump(users_data, f, indent=4)

@bot.callback_query_handler(func=lambda call: call.data.startswith("navigate"))
def handle_navigation(call):
    user_id = call.message.chat.id
    session = user_sessions[user_id]
    action = call.data.split(":")[1]

    if action == "back":
        if session["current_index"] > 0:
            session["current_index"] -= 1
            send_question(call.message, user_id)
        else:
            bot.answer_callback_query(call.id, "Orqaga qaytish imkoni yo'q!")
    elif action == "next":
        if session["current_index"] < len(session["questions"]) - 1:
            session["current_index"] += 1
            send_question(call.message, user_id)
        else:
            show_results(call.message, user_id)
    elif action == "results":
        show_results(call.message, user_id)

def show_results(message, user_id):
    session = user_sessions[user_id]

    total = len(session["questions"])
    correct = session["correct"]
    incorrect = session["incorrect"]
    percentage = (correct / total) * 100

    result_message = (
        f"✅ To'g'ri javoblar: {correct}\n"
        f"❌ Noto'g'ri javoblar: {incorrect}\n"
        f"📊 Umumiy natija: {percentage:.2f}%\n\n"
    )

    if percentage <= 25:
        result_message += "Telefonni kamroq o'ynab, ko'proq dars qilishingiz kerak. 📚"
    elif percentage <= 50:
        result_message += "Dangasalik qilmang, yaxshiroq o'qing! 📘"
    elif percentage <= 75:
        result_message += "Yaxshi natija, lekin baribir zo'r emas. 😊"
    else:
        result_message += "Zo'r, o'qisa bo'larkanuu! 🥳"

    # Reyting tugmalarini yaratish
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔄 Testni qaytadan boshlash", callback_data="restart:quiz")
    )
    keyboard.add(
        InlineKeyboardButton("✨ ALL Reyting", callback_data="rating:all"),
        InlineKeyboardButton("🇺🇿 UZ-EN Reyting", callback_data="rating:uz_en"),
        InlineKeyboardButton("🇬🇧 EN-UZ Reyting", callback_data="rating:en_uz"),
        InlineKeyboardButton("🌟 Stars", callback_data="rating:stars")
    )

    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=session["message_id"],
            text=result_message,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Natijalarni chiqarishda xatolik: {e}")
        session["message_id"] = bot.send_message(
            chat_id=message.chat.id,
            text=result_message,
            reply_markup=keyboard
        ).message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("rating"))
def show_rating(call):
    rating_type = call.data.split(":")[1]
    user_id = call.message.chat.id

    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)

        # Foydalanuvchilar ma'lumotlarini yig'ish
        if rating_type == "all":
            scores = [(u["name"], u["pointsUZ_EN"] + u["pointsEN_UZ"]) for u in users.values()]
            title = "✨ ALL Reyting (Umumiy ballar):"
        elif rating_type == "uz_en":
            scores = [(u["name"], u["pointsUZ_EN"]) for u in users.values()]
            title = "🇺🇿 UZ-EN Reyting:"
        elif rating_type == "en_uz":
            scores = [(u["name"], u["pointsEN_UZ"]) for u in users.values()]
            title = "🇬🇧 EN-UZ Reyting:"
        elif rating_type == "stars":
            # Foydalanuvchilarni username va rounded stars bilan olish
            scores = [(u["name"], round(u["stars"], 2)) for u in users.values()]
            title = "🌟 Stars Reyting:"

            # Reytingni saralash (yaxshiroq reyting yuqorida bo'ladi)
            scores = sorted(scores, key=lambda x: x[1], reverse=True)

            # Reyting xabarini yaratish
            if scores:
                message_text = f"{title}\n\n" + "\n".join(
                    [f"{idx + 1}. {username}: 💰{score}" for idx, (username, score) in enumerate(scores)]
                )
            else:
                message_text = f"{title}\n\nHech qanday foydalanuvchi reytingga ega emas."
        else:
            bot.answer_callback_query(call.id, "Xato: Reyting turi noto'g'ri.")
            return

        # Reytingni saralash va birinchi 10 foydalanuvchini olish
        top_scores = sorted(scores, key=lambda x: x[1], reverse=True)[:10]

        # Natijalarni tayyorlash
        rating_message = f"{title}\n\n"
        for i, (nickname, score) in enumerate(top_scores, start=1):
            rating_message += f"{i}. {nickname}: 💰{score}\n"

        # Xabarni tahrirlash
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=rating_message,
                reply_markup=call.message.reply_markup
            )
        except Exception as e:
            print(f"Reytingni tahrirlashda xatolik: {e}")
            bot.answer_callback_query(call.id, "Xabarni tahrirlashda xatolik yuz berdi.")
    except Exception as e:
        print(f"Reytingni ko'rsatishda xatolik: {e}")
        bot.answer_callback_query(call.id, "Reytingni ko'rsatishda xatolik yuz berdi.")

#--------------------------------------------------------------------------

# Admin kodi
ADMIN_CODE = "AAABBB2025"

# Admin panel tugmachalari
def admin_panel_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👬Foydalanuvchilar haqida", "📤Usersga xabar yuborish", "🤓Savollarni boshqarish", "⬅️Ortga qaytish")
    return markup

# Admin panelga kirish
@bot.message_handler(func=lambda message: message.text == ADMIN_CODE)
def handle_admin_code(message):
    user_id = str(message.from_user.id)

    if user_id in users:
        users[user_id]["admin"] = True
        save_users(users)
        bot.send_message(
            message.chat.id,
            "🫡 XUSH KELIBSIZ ADMIN!",
            reply_markup=admin_panel_keyboard()
        )
    else:
        bot.send_message(message.chat.id, "❗️Admin kodni kiritish uchun foydalanuvchi ro'yxatdan o'tishi kerak.")

# Admin panelni boshqarish
@bot.message_handler(func=lambda message: users.get(str(message.from_user.id), {}).get("admin", False))
def handle_admin_panel(message):
    if message.text == "👬Foydalanuvchilar haqida":
        user_stats_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        user_stats_keyboard.add("👥Jami foydalanuvchilar soni", "🙋‍♂️Erkak foydalanuvchilar soni", "🙋‍♀️Ayol foydalanuvchilar soni","⛄️ALL users haqida", "⬅️Ortga qaytish")
        bot.send_message(message.chat.id, "👥Foydalanuvchilar haqida tanlang:", reply_markup=user_stats_keyboard)
    elif message.text == "⬅️Ortga qaytish":
        bot.send_message(message.chat.id, "🫡 Admin panelga qaytdingiz.", reply_markup=admin_panel_keyboard())
    elif message.text == "📤Usersga xabar yuborish":
        ask_broadcast_message(message)
    elif message.text == "👥Jami foydalanuvchilar soni":
        total = len(users)
        bot.send_message(message.chat.id, f"👥Jami foydalanuvchilar soni: {total}")
    elif message.text == "🙋‍♂️Erkak foydalanuvchilar soni":
        males = sum(1 for user in users.values() if user.get("gender") == "Erkak")
        bot.send_message(message.chat.id, f"🙋‍♂️Erkak foydalanuvchilar soni: {males}")
    elif message.text == "🙋‍♀️Ayol foydalanuvchilar soni":
        females = sum(1 for user in users.values() if user.get("gender") == "Ayol")
        bot.send_message(message.chat.id, f"🙋‍♀️Ayol foydalanuvchilar soni: {females}")
    elif message.text == "⛄️ALL users haqida":
        # Birinchi sahifani ko'rsatish uchun
        generate_users_page(message.chat.id, 0)
    elif message.text == "🤓Savollarni boshqarish":
        generate_questions_menu(message)
    else:
        bot.send_message(message.chat.id, "👇Iltimos, menyudagi tugmalardan birini tanlang.")
##########################################################
# Foydalanuvchilarni sahifalash uchun yordamchi funksiya
def generate_users_page(chat_id, page, message_id=None):
    page_size = 10
    start_index = page * page_size
    end_index = start_index + page_size
    user_ids = list(users.keys())

    if not user_ids:
        if message_id:
            bot.edit_message_text(
                "🤷‍♂️Foydalanuvchilar ro'yxati bo'sh.",
                chat_id=chat_id,
                message_id=message_id
            )
        else:
            bot.send_message(chat_id, "🤷‍♂️Foydalanuvchilar ro'yxati bo'sh.")
        return

    page_users = user_ids[start_index:end_index]
    if not page_users:
        if message_id:
            bot.edit_message_text(
                "🤷‍♂️Bu sahifada foydalanuvchilar mavjud emas.",
                chat_id=chat_id,
                message_id=message_id
            )
        else:
            bot.send_message(chat_id, "🤷‍♂️Bu sahifada foydalanuvchilar mavjud emas.")
        return

    total_users = len(user_ids)
    results_text = f"📊Natijalar {start_index + 1}-{min(end_index, total_users)} {total_users} dan:\n"

    user_details = []
    for idx, user_id in enumerate(page_users, start=start_index + 1):
        user = users[user_id]
        username = user.get('username', 'Noma’lum')  # Agar username mavjud bo'lmasa, "Noma’lum" yoziladi.
        user_info = (
            f"___________________\n"
            f"{idx}. 🆔 {user_id},\n"
            f"🧿Ism: {user.get('name', 'Noma’lum')}, \n"
            f"🧞Jins: {user.get('gender', '🤷‍♂️Noma’lum')}, \n"
            f"📧 Username: @{username if username != 'Noma’lum' else 'Noma’lum'}"
        )
        user_details.append(user_info)


    message_text = results_text + "\n".join(user_details)
    keyboard = create_pagination_keyboard(page, total_users, page_size)

    if message_id:
        bot.edit_message_text(
            message_text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )
    else:
        bot.send_message(chat_id, message_text, reply_markup=keyboard)

# Tugmalarni yaratish
def create_pagination_keyboard(current_page, total_users, page_size):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = []

    if current_page > 0:
        buttons.append(telebot.types.InlineKeyboardButton(
            "⬅ Oldingi", callback_data=f"users_page_{current_page - 1}"
        ))

    if (current_page + 1) * page_size < total_users:
        buttons.append(telebot.types.InlineKeyboardButton(
            "Keyingi ➡", callback_data=f"users_page_{current_page + 1}"
        ))

    keyboard.add(*buttons)
    return keyboard

# Sahifalashni boshqarish
@bot.callback_query_handler(func=lambda call: call.data.startswith("users_page_"))
def handle_users_pagination(call):
    page = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    generate_users_page(chat_id, page, message_id=message_id)

##########################################################  



#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Savollar menyusi (inline tugmalar bilan)
def generate_questions_menu(message):
    question_keyboard = InlineKeyboardMarkup(row_width=2)
    question_keyboard.add(
        InlineKeyboardButton("✅Savol qo‘shish", callback_data="add_question"),
        InlineKeyboardButton("🔰Bir nechtalab so‘z qo‘shish", callback_data="add_multiple_questions"),
        InlineKeyboardButton("❌Savol o‘chirish", callback_data="delete_question"),
        InlineKeyboardButton("🌐Barcha savollar", callback_data="view_all_questions"),
        InlineKeyboardButton("⬅️Ortga qaytish", callback_data="back_to_admin_panel")
    )
    bot.send_message(
        message.chat.id,
        "⁉️Savollar bo‘limidan kerakli bo‘limni tanlang:",
        reply_markup=question_keyboard
    )
# Inline tugmalar uchun handler
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    if call.data == "add_question":
        bot.answer_callback_query(call.id)
        add_question(call.message)  # Savol qo‘shish jarayonini boshlash
    elif call.data == "add_multiple_questions":
        bot.answer_callback_query(call.id)
        add_multiple_questions(call.message)  # Bir nechtalab savol qo‘shish
    elif call.data == "delete_question":
        bot.answer_callback_query(call.id)
        delete_question(call.message)  # Savol o‘chirish jarayonini boshlash
    elif call.data == "view_all_questions":
        bot.answer_callback_query(call.id)
        view_all_questions(call.message)  # Barcha savollarni ko‘rsatish
    elif call.data == "back_to_admin_panel":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🫡Admin panelga qaytdingiz.", reply_markup=admin_panel_keyboard())

# Bir nechtalab savol qo‘shish
def add_multiple_questions(message):
    bot.send_message(
        message.chat.id,
        "👇Savollarni qo‘shish uchun quyidagi formatda yuboring:\n\n" +
        "`uz1|en1`\n`uz2|en2`\n`uz3|en3`\n\n" +
        "Har bir qator yangi so‘zni ifodalaydi. Uz qismi va en qismini `|` bilan ajrating.",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_multiple_questions)

def process_multiple_questions(message):
    try:
        entries = message.text.split("\n")
        added_questions = []
        for entry in entries:
            uz, en = entry.split("|")
            word_list.append({"uz": uz.strip(), "en": en.strip()})
            added_questions.append(f"uz: {uz.strip()}, en: {en.strip()}")
        
        if added_questions:
            bot.send_message(
                message.chat.id,
                "👇🥸Quyidagi savollar qo‘shildi:\n" + "\n".join(added_questions)
            )
        else:
            bot.send_message(message.chat.id, "Hech qanday savol qo‘shilmadi.")
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌Noto‘g‘ri formatda ma’lumot kiritildi. Iltimos, yuqoridagi formatga rioya qiling."
        )
    generate_questions_menu(message)

# Savol qo‘shish
def add_question(message):
    bot.send_message(message.chat.id, "✍️Savolni yozing (uz qismni kiriting):")
    bot.register_next_step_handler(message, save_question_uz)

def save_question_uz(message):
    uz_question = message.text
    bot.send_message(message.chat.id, "🤝Endi shu savolga javobni kiriting (en):")
    bot.register_next_step_handler(message, save_question_en, uz_question)

def save_question_en(message, uz_question):
    en_answer = message.text
    word_list.append({"uz": uz_question, "en": en_answer})
    bot.send_message(message.chat.id, f"✅Savol qo‘shildi: uz: {uz_question}, en: {en_answer}")
    generate_questions_menu(message)

# Savol o‘chirish
def delete_question(message):
    if not word_list:
        bot.send_message(message.chat.id, "☹️Hozircha hech qanday savol mavjud emas.")
        generate_questions_menu(message)
        return
    questions = "\n".join([f"{idx + 1}. uz: {item['uz']}, en: {item['en']}" for idx, item in enumerate(word_list)])
    bot.send_message(message.chat.id, f"❓Qaysi savolni o‘chirmoqchisiz? ID raqamini kiriting:\n\n{questions}")
    bot.register_next_step_handler(message, process_question_deletion)

def process_question_deletion(message):
    try:
        question_id = int(message.text) - 1
        if 0 <= question_id < len(word_list):
            deleted_question = word_list.pop(question_id)
            bot.send_message(message.chat.id, f"✅Savol o‘chirildi: uz: {deleted_question['uz']}, en: {deleted_question['en']}")
        else:
            bot.send_message(message.chat.id, "❌Noto‘g‘ri ID raqami.")
    except ValueError:
        bot.send_message(message.chat.id, "☝️🧐Faqat ID raqamini kiriting.")
    generate_questions_menu(message)

# Barcha savollar
def view_all_questions(message):
    if not word_list:
        bot.send_message(message.chat.id, "👌Hozircha hech qanday savol mavjud emas.")
    else:
        questions = "\n".join([f"{idx + 1}. uz: {item['uz']}, en: {item['en']}" for idx, item in enumerate(word_list)])
        bot.send_message(message.chat.id, f"📝Barcha savollar ro‘yxati:\n{questions}")
    generate_questions_menu(message)

@bot.message_handler(func=lambda message: message.text == "Ortga qaytish" and users.get(str(message.from_user.id), {}).get("admin", False))
def back_to_admin_panel(message):
    bot.send_message(message.chat.id, "🫡Admin panelga qaytdingiz.", reply_markup=admin_panel_keyboard())

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Admindan xabar kiritishni so'rash
def ask_broadcast_message(message):
    bot.send_message(
        message.chat.id,
        "✍️Iltimos, barcha foydalanuvchilarga yuboriladigan xabarni kiriting."
    )
    bot.register_next_step_handler(message, broadcast_message)

# Xabarni barcha foydalanuvchilarga yuborish
def broadcast_message(message):
    text = message.text
    if not text:
        bot.send_message(message.chat.id, "❗️Xabar matni bo'sh bo'lmasligi kerak.")
        return

    sent_count = 0
    for user_id in users.keys():
        try:
            bot.send_message(user_id, text)
            sent_count += 1
        except Exception as e:
            print(f"❌Xabar {user_id} ga yuborilmadi. Xato: {e}")

    bot.send_message(
        message.chat.id,
        f"✅Xabar {sent_count} ta foydalanuvchiga muvaffaqiyatli yuborildi."
    )


# Botni doimiy ishga tushirish
if __name__ == "__main__":
    print("Bot ishga tushirilmoqda...")
    bot.infinity_polling()

