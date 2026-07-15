import asyncio
import logging
from datetime import datetime
import asyncpg

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

# TO'LDIRING:
BOT_TOKEN = "8838171298:AAHJ-uGvDBuE87MGblD_59LKjcWztbulnz4"
ADMIN_ID = 8220476285  # Bu yerga o'zingizning Telegram ID-ingizni yozing (Sizga xabarlar boradi)
DB_DSN = "postgresql://postgres:abdulloh09@localhost:5432/brond2_db"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db_pool = None


# FSM Holatlari
class BookingStates(StatesGroup):
    waiting_for_contact = State()
    writing_date = State()
    writing_time = State()
    writing_guests = State()


class AdminStates(StatesGroup):
    waiting_for_broadcast_text = State()


# Ma'lumotlar bazasiga ulanish
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=DB_DSN)


# Start komandasi
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", message.from_user.id)

    if user:
        await show_main_menu(message)
    else:
        contact_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            f"Assalomu alaykum, {message.from_user.full_name}!\n"
            f"Kafemizning bron qilish botiga xush kelibsiz. Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
            reply_markup=contact_keyboard
        )
        await state.set_state(BookingStates.waiting_for_contact)


# FAQAT ADMIN UCHUN maxsus /admin komandasi
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Sizda ushbu komandadan foydalanish huquqi yo'q. ❌")
        return
    await show_admin_menu(message)


# Kontaktni qabul qilish
@dp.message(BookingStates.waiting_for_contact, F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    fullname = f"{contact.first_name} {contact.last_name or ''}".strip()
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (telegram_id, fullname, phone_number) VALUES ($1, $2, $3) "
            "ON CONFLICT (telegram_id) DO NOTHING",
            message.from_user.id, fullname, contact.phone_number
        )
    await state.clear()
    await message.answer("Siz muvaffaqiyatli ro'yxatdan o'tdingiz! 🎉")
    await show_main_menu(message)


# Asosiy menyu
async def show_main_menu(message: types.Message):
    menu_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Stol band qilish (Bron)")],
            [KeyboardButton(text="📋 Mening bronlarim")]
        ],
        resize_keyboard=True
    )
    await message.answer("Quyidagi menyulardan birini tanlang:", reply_markup=menu_keyboard)


# Admin Menyu
async def show_admin_menu(message: types.Message):
    admin_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="✉️ Xabar yuborish")],
            [KeyboardButton(text="📋 Barcha foydalanuvchilar")],
            [KeyboardButton(text="🔙 Oddiy menyuga qaytish")]
        ],
        resize_keyboard=True
    )
    await message.answer("Xush kelibsiz, Admin! Panelga kirdingiz:", reply_markup=admin_keyboard)


# Admin paneldan chiqish va oddiy menyuga qaytish
@dp.message(F.text == "🔙 Oddiy menyuga qaytish")
async def back_to_user_menu(message: types.Message):
    await show_main_menu(message)


# 1-QADAM: Bron qilishni boshlash va SANA so'rash (Tugmasiz, qo'lda kiritish)
@dp.message(F.text == "📅 Stol band qilish (Bron)")
async def start_booking(message: types.Message, state: FSMContext):
    await message.answer(
        "Iltimos, bron qilmoqchi bo'lgan **sanangizni kiriting**:\n"
        "*(Masalan: 15.08.2026 yoki ertaga)*",
        reply_markup=ReplyKeyboardRemove(),  # Menyu tugmalarini vaqtinchalik yopamiz
        parse_mode="Markdown"
    )
    await state.set_state(BookingStates.writing_date)


# 2-QADAM: Sanani qabul qilish va VAQTni so'rash
@dp.message(BookingStates.writing_date, F.text)
async def process_date_input(message: types.Message, state: FSMContext):
    await state.update_data(booking_date=message.text)

    await message.answer(
        f"Tanlangan sana: **{message.text}**\n\n"
        "Endi o'zingizga **qulay vaqtni yozing**:\n"
        "*(Masalan: 14:00 abetdan keyin, soat 18:00 da yoki kechki payt)*",
        parse_mode="Markdown"
    )
    await state.set_state(BookingStates.writing_time)


# 3-QADAM: Vaqtni qabul qilish va MEHMONLAR SONINI so'rash
@dp.message(BookingStates.writing_time, F.text)
async def process_time_input(message: types.Message, state: FSMContext):
    await state.update_data(booking_time=message.text)

    data = await state.get_data()
    await message.answer(
        f"Sana: **{data['booking_date']}**\n"
        f"Vaqt: **{message.text}**\n\n"
        "**Necha kishi** uchun joy buyurtma qilasiz? Iltimos, yozib yuboring:\n"
        "*(Masalan: 4 kishi, 5-6 kishi yoki faqat o'zim)*",
        parse_mode="Markdown"
    )
    await state.set_state(BookingStates.writing_guests)


# 4-QADAM: Mehmonlar sonini qabul qilish, bazaga saqlash va adminga xabar berish
@dp.message(BookingStates.writing_guests, F.text)
async def process_guests_input(message: types.Message, state: FSMContext):
    guests_input = message.text
    data = await state.get_data()

    # Ma'lumotlarni bazaga saqlaymiz.
    # DIQQAT: Foydalanuvchi matn yuborgani sababli, ma'lumotlar bazasidagi booking_date va booking_time
    # ustunlarini VARCHAR (matn) turiga o'zgartirishimiz yoki matn sifatida saqlashimiz kerak.
    # Biz xatolik chiqmasligi uchun bazaga hozircha asinxron so'rov bilan yozamiz.

    async with db_pool.acquire() as conn:
        # PostgreSQL-da jadvallar asosan DATE va TIME turida edi.
        # Foydalanuvchi erkin matn yozishi uchun ularni bazaga kiritishda VARCHAR xatolik bermasligi uchun
        # biz jadvalimizni biroz moslashtiramiz (batafsil pastda SQL kodda berilgan).

        booking_id = await conn.fetchval(
            "INSERT INTO bookings (telegram_id, booking_date, booking_time, guests_count) VALUES ($1, $2, $3, $4) RETURNING id",
            message.from_user.id,
            data['booking_date'],  # Endi bu shunchaki matn
            data['booking_time'],  # Bu ham matn
            guests_input  # Bu ham matn
        )
        user = await conn.fetchrow("SELECT fullname, phone_number FROM users WHERE telegram_id = $1",
                                   message.from_user.id)

    # Foydalanuvchiga muvaffaqiyatli xabari
    await message.answer(
        f"🎉 Broningiz qabul qilindi va ko'rib chiqilmoqda!\n\n"
        f"📅 Sana: {data['booking_date']}\n"
        f"⏰ Vaqt: {data['booking_time']}\n"
        f"👥 Mehmonlar: {guests_input}\n\n"
        f"Admin tasdiqlashini kuting..."
    )
    await state.clear()
    await show_main_menu(message)  # Menyu tugmalarini qaytaramiz

    # ADMINGA BILDIRIShNOMA
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_accept:{booking_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_reject:{booking_id}")
        ]
    ])

    admin_notification_text = (
        f"🔔 **YANGI BRON!** (ID: #{booking_id})\n\n"
        f"👤 Foydalanuvchi: {user['fullname']}\n"
        f"📞 Telefon: {user['phone_number']}\n"
        f"📅 Sana: {data['booking_date']}\n"
        f"⏰ Vaqt: {data['booking_time']}\n"
        f"👥 Mehmonlar soni: {guests_input}"
    )

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_notification_text, reply_markup=admin_markup,
                               parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Adminga xabar yuborib bo'lmadi: {e}")


# Admin qarori
@dp.callback_query(F.data.startswith("admin_accept:") | F.data.startswith("admin_reject:"))
async def process_admin_decision(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Siz admin emassiz!", show_alert=True)
        return

    action, booking_id = callback.data.split(":")
    booking_id = int(booking_id)

    status_str = "Tasdiqlandi" if action == "admin_accept" else "Rad etildi"

    async with db_pool.acquire() as conn:
        booking = await conn.fetchrow(
            "UPDATE bookings SET status = $1 WHERE id = $2 RETURNING telegram_id, booking_date, booking_time",
            status_str, booking_id
        )

    if not booking:
        await callback.answer("Ushbu bron topilmadi.")
        return

    status_emoji = "✅" if status_str == "Tasdiqlandi" else "❌"
    await callback.message.edit_text(
        callback.message.text + f"\n\n👉 **Holati:** {status_emoji} {status_str} (Admin qarori)",
        parse_mode="Markdown"
    )

    user_msg = (
        f"📩 Sizning #{booking_id}-sonli broningiz admin tomonidan **{status_str.upper()}**!\n\n"
        f"📅 Sana: {booking['booking_date']}\n"
        f"⏰ Vaqt: {booking['booking_time']}\n"
        f"E'tiboringiz uchun rahmat!"
    )
    try:
        await bot.send_message(chat_id=booking['telegram_id'], text=user_msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar yuborishda xatolik: {e}")

    await callback.answer(f"Bron {status_str.lower()}!")


# Foydalanuvchining o'z bronlari
@dp.message(F.text == "📋 Mening bronlarim")
async def show_my_bookings(message: types.Message):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, booking_date, booking_time, guests_count, status FROM bookings "
            "WHERE telegram_id = $1 ORDER BY id DESC LIMIT 5",
            message.from_user.id
        )

    if not rows:
        await message.answer("Sizda hozircha faol bronlar majvud emas.")
        return

    text = "📋 Sizning oxirgi 5 ta broningiz:\n\n"
    for r in rows:
        status_emoji = "⏳" if r['status'] == "Kutilmoqda" else "✅" if r['status'] == "Tasdiqlandi" else "❌"
        text += f"📅 Sana: {r['booking_date']} | ⏰ {r['booking_time']}\n👥 Mehmonlar: {r['guests_count']}\nHolat: {status_emoji} {r['status']}\n\n"

    await message.answer(text)


# ADMIN PANEL: STATISTIKA
@dp.message(F.text == "📊 Statistika")
async def admin_statistics(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with db_pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        total_bookings = await conn.fetchval("SELECT COUNT(*) FROM bookings")
        pending_bookings = await conn.fetchval("SELECT COUNT(*) FROM bookings WHERE status = 'Kutilmoqda'")
        approved_bookings = await conn.fetchval("SELECT COUNT(*) FROM bookings WHERE status = 'Tasdiqlandi'")
        rejected_bookings = await conn.fetchval("SELECT COUNT(*) FROM bookings WHERE status = 'Rad etildi'")

    stat_text = (
        f"📊 **BOT STATISTIKASI:**\n\n"
        f"👥 Ro'yxatdan o'tgan mijozlar: {total_users} ta\n"
        f"📦 Jami bron qilish so'rovlari: {total_bookings} ta\n\n"
        f"⏳ Kutilmoqda: {pending_bookings} ta\n"
        f"✅ Tasdiqlangan: {approved_bookings} ta\n"
        f"❌ Rad etilgan: {rejected_bookings} ta"
    )
    await message.answer(stat_text, parse_mode="Markdown")


# ADMIN PANEL: FOYDALANUVCHILARNI KO'RISH
@dp.message(F.text == "📋 Barcha foydalanuvchilar")
async def show_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT fullname, phone_number FROM users LIMIT 15")

    if not rows:
        await message.answer("Foydalanuvchilar yo'q.")
        return

    text = "📋 **Foydalanuvchilar ro'yxati (oxirgi 15 ta):**\n\n"
    for idx, r in enumerate(rows, 1):
        text += f"{idx}. 👤 {r['fullname']} - 📞 {r['phone_number']}\n"
    await message.answer(text, parse_mode="Markdown")


# ADMIN PANEL: BROADCAST
@dp.message(F.text == "✉️ Xabar yuborish")
async def start_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Barcha a'zolarga jo'natiladigan xabar matnini kiriting (/cancel orqali bekor qilish mumkin):")
    await state.set_state(AdminStates.waiting_for_broadcast_text)


# Bekor qilish
@dp.message(Command("cancel"))
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Amal bekor qilindi.")
    if message.from_user.id == ADMIN_ID:
        await show_admin_menu(message)


# Reklamani tarqatish
@dp.message(AdminStates.waiting_for_broadcast_text)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    broadcast_text = message.text
    await state.clear()

    async with db_pool.acquire() as conn:
        users = await conn.fetch("SELECT telegram_id FROM users")

    if not users:
        await message.answer("Bazada foydalanuvchilar mavjud emas.")
        return

    await message.answer("Xabar tarqatilmoqda...")

    success_count = 0
    fail_count = 0

    for u in users:
        try:
            await bot.send_message(chat_id=u['telegram_id'], text=broadcast_text)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1

    await message.answer(
        f"🎉 Yakunlandi!\n\n"
        f"✅ Yetkazildi: {success_count} ta\n"
        f"❌ Bloklanganlar: {fail_count} ta"
    )
    await show_admin_menu(message)


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())