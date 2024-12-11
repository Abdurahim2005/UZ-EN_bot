import telebot
import json
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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
        }
        save_users(users)
        # Genderni so'rash
        bot.send_message(
            message.chat.id,
            "🙂Assalomu alaykum! Jinsingizni tanlang:",
            reply_markup=gender_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            f"😇Xush kelibsiz, {users[user_id]['name']}! Qaytib kelganingizdan xursandmiz."
        )
        show_main_menu(message)

# Gender tugmachalari
def gender_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Erkak", "Ayol")
    return markup

# Tugmachalar uchun asosiy menyu
def show_main_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🇺🇿UZ-🏴󠁧󠁢󠁥󠁮󠁧󠁿EN", "🏴󠁧󠁢󠁥󠁮󠁧󠁿EN-🇺🇿UZ")
    bot.send_message(
        message.chat.id,
        "❓Qaysi usulda savol-javob qilishni xohlaysiz?",
        reply_markup=markup
    )

# Genderni qayta ishlash
@bot.message_handler(func=lambda message: message.text in ["🙋‍♂️Erkak", "🙋‍♀️Ayol"])
def handle_gender(message):
    user_id = str(message.from_user.id)
    users[user_id]["gender"] = message.text
    save_users(users)
    bot.send_message(
        message.chat.id,
        f"🙆‍♂️Rahmat! Jinsingiz: {message.text}.",
    )
    show_main_menu(message)
# Lug'at ma'lumotlari
word_list = [
    {"uz": "kitob", "en": "book"},
    {"uz": "o'qituvchi", "en": "teacher"},
    {"uz": "talaba", "en": "student"},
    {"uz": "uy", "en": "house"},
    {"uz": "stol", "en": "table"}
]

@bot.message_handler(func=lambda message: message.text in ["🇺🇿UZ-🏴󠁧󠁢󠁥󠁮󠁧󠁿EN", "🏴󠁧󠁢󠁥󠁮󠁧󠁿EN-🇺🇿UZ"])
def start_quiz_session(message):
    user_id = str(message.from_user.id)
    quiz_type = message.text  # UZ-EN yoki EN-UZ

    # Foydalanuvchidan savollar sonini kiritishni so'rash
    bot.send_message(message.chat.id, f"✍️Savollar sonini kiriting (1 dan {len(word_list)} gacha):")
    bot.register_next_step_handler(message, lambda msg: get_question_count(msg, quiz_type))

def get_question_count(message, quiz_type):
    try:
        question_count = int(message.text)
        if question_count < 1 or question_count > len(word_list):
            raise ValueError

        # Random savollar tanlash
        selected_questions = random.sample(word_list, question_count)

        # Savol-javob sessiyasini boshlash
        bot.send_message(message.chat.id, "👌Savollar boshlandi! Javoblaringizni kiriting.")
        start_questions(message, selected_questions, quiz_type, 0, 0, 0)

    except ValueError:
        bot.send_message(message.chat.id, "❗️🥸Iltimos, 1 dan 5 gacha bo'lgan butun son kiriting.")
        bot.register_next_step_handler(message, lambda msg: get_question_count(msg, quiz_type))

def start_questions(message, questions, quiz_type, index, correct, incorrect):
    if index >= len(questions):
        # Natijalarni ko'rsatish
        total = len(questions)
        percentage = (correct / total) * 100
        result_message = (
            f"✅ To'g'ri javoblar: {correct}\n"
            f"❌ Noto'g'ri javoblar: {incorrect}\n"
            f"📊Umumiy natija: {percentage:.2f}%\n\n"
        )
        if percentage <= 25:
            result_message += "Telefonni kamroq o'ynab, ko'proq dars qilishingiz kerak. 📖"
        elif percentage <= 50:
            result_message += "Dangasalik qilmang, yaxshiroq o'qing! 📘"
        elif percentage <= 75:
            result_message += "Yaxshi natija, lekin baribir zo'r emas. 😊"
        else:
            result_message += "Zo'r, o'qisa bo'larkanuu! 🥳"

        bot.send_message(message.chat.id, result_message)
        return

    # Savolni ko'rsatish
    question = questions[index]
    question_text = (
        question["uz"] if quiz_type == "🇺🇿UZ-🏴󠁧󠁢󠁥󠁮󠁧󠁿EN" else question["en"]
    )
    bot.send_message(
        message.chat.id,
        f"❓{index + 1}-savol : {question_text}"
    )
    bot.register_next_step_handler(
        message,
        lambda msg: check_answer(msg, questions, quiz_type, index, correct, incorrect)
    )

def check_answer(message, questions, quiz_type, index, correct, incorrect):
    user_answer = message.text.strip().lower()
    correct_answer = (
        questions[index]["en"] if quiz_type == "🇺🇿UZ-🏴󠁧󠁢󠁥󠁮󠁧󠁿EN" else questions[index]["uz"]
    ).lower()

    if user_answer == correct_answer:
        bot.send_message(message.chat.id, "✅ To'g'ri!")
        correct += 1
    else:
        bot.send_message(message.chat.id, f"❌ Noto'g'ri! To'g'ri javob: {correct_answer}")
        incorrect += 1

    # Keyingi savolga o'tish
    start_questions(message, questions, quiz_type, index + 1, correct, incorrect) 
    
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
