import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import json
import os

# Bot tokeningizni bu yerga kiriting
BOT_TOKEN = "8009221474:AAEuOWB8aZ98lzM6BjqDBIXPz93ZBIDHa-w"

# Kanal username va admin ID
CHANNEL_USERNAME = "@furkatova_madina"
ADMIN_ID = 348904938

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Ma'lumotlar fayli
DATA_FILE = "users_data.json"


def load_users_data():
    """Foydalanuvchilar ma'lumotlarini yuklash"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_users_data(data):
    """Foydalanuvchilar ma'lumotlarini saqlash"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_data(user_id):
    """Foydalanuvchi ma'lumotlarini olish"""
    users_data = load_users_data()
    user_id_str = str(user_id)

    if user_id_str not in users_data:
        users_data[user_id_str] = {
            "referrals": [],
            "points": 0,
            "joined_date": datetime.now().isoformat()
        }
        save_users_data(users_data)

    return users_data[user_id_str]


def update_user_data(user_id, data):
    """Foydalanuvchi ma'lumotlarini yangilash"""
    users_data = load_users_data()
    users_data[str(user_id)] = data
    save_users_data(users_data)


def add_referral(referrer_id, new_user_id):
    """Referal qo'shish va ball berish"""
    users_data = load_users_data()
    referrer_id_str = str(referrer_id)
    new_user_id_str = str(new_user_id)

    if referrer_id_str in users_data:
        if new_user_id_str not in users_data[referrer_id_str]["referrals"]:
            users_data[referrer_id_str]["referrals"].append(new_user_id_str)
            users_data[referrer_id_str]["points"] += 5
            save_users_data(users_data)
            return True
    return False


def get_leaderboard():
    """Eng ko'p ball to'plagan foydalanuvchilar"""
    users_data = load_users_data()
    sorted_users = sorted(users_data.items(), key=lambda x: x[1]["points"], reverse=True)
    return sorted_users[:10]  # Top 10


async def check_subscription(user_id: int) -> bool:
    """Foydalanuvchi kanalga obuna ekanligini tekshirish"""
    try:
        chat = await bot.get_chat(CHANNEL_USERNAME)
        channel_id = chat.id
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Obuna tekshirishda xatolik: {e}")
        return False


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """Start komandasi uchun handler"""
    user_id = message.from_user.id

    # Referal linkni tekshirish
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
        except:
            pass

    # Obuna tekshiruvi
    is_subscribed = await check_subscription(user_id)

    if not is_subscribed:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📢 Kanalga qo'shilish",
                url=f"https://t.me/furkatova_madina"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="✅ Tekshirish",
                callback_data=f"check_subscription:{referrer_id if referrer_id else 0}"
            )
        )

        await message.answer(
            f"🌟 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
            f"🤖 Botdan foydalanish uchun avval kanalimizga obuna bo'ling 👇\n\n"
            f"👉 Obuna bo'lgandan so'ng <b>\"✅ Tekshirish\"</b> tugmasini bosing",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        # Agar referal orqali kelgan bo'lsa va yangi foydalanuvchi bo'lsa
        user_data = get_user_data(user_id)
        if referrer_id and referrer_id != user_id and len(user_data["referrals"]) == 0:
            if add_referral(referrer_id, user_id):
                try:
                    await bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 <b>Tabriklaymiz!</b>\n\n"
                             f"Sizning referal linkingiz orqali yangi foydalanuvchi qo'shildi!\n"
                             f"💰 <b>+5 ball</b> qo'shildi!",
                        parse_mode="HTML"
                    )
                except:
                    pass

        await send_main_menu(message)


@dp.callback_query(F.data.startswith("check_subscription:"))
async def check_sub_callback(callback: types.CallbackQuery):
    """Obunani tekshirish tugmasi bosilganda"""
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)

    # Referal ID ni olish
    referrer_id = int(callback.data.split(":")[1])

    if is_subscribed:
        try:
            await callback.message.delete()
        except:
            pass

        # Agar referal orqali kelgan bo'lsa
        user_data = get_user_data(user_id)
        if referrer_id > 0 and referrer_id != user_id and len(user_data["referrals"]) == 0:
            if add_referral(referrer_id, user_id):
                try:
                    await bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 <b>Tabriklaymiz!</b>\n\n"
                             f"Sizning referal linkingiz orqali yangi foydalanuvchi qo'shildi!\n"
                             f"💰 <b>+5 ball</b> qo'shildi!",
                        parse_mode="HTML"
                    )
                except:
                    pass

        await send_main_menu(callback.message)
        await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)
    else:
        await callback.answer(
            "❌ Siz hali kanalga obuna bo'lmadingiz!\n\n"
            "Iltimos, avval kanalga qo'shiling va 'Tekshirish' tugmasini bosing.",
            show_alert=True
        )


async def send_main_menu(message: types.Message):
    """Asosiy menyuni yuborish"""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Mening statistikam",
                    callback_data="my_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔗 Referal linkni olish",
                    callback_data="get_referral"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Reyting jadval",
                    callback_data="leaderboard"
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ Konkurs haqida",
                    callback_data="about_contest"
                )
            ]
        ]
    )

    caption_text = (
        "🏆 <b>PSD kursi \"Maxsus konkursi\"</b>\n\n"
        f"👤 <b>{message.from_user.first_name}</b>, konkursda ishtirok etyapsiz!\n\n"
        f"💰 <b>Sizning ballingiz:</b> {user_data['points']} ball\n"
        f"👥 <b>Taklif qilganlar:</b> {len(user_data['referrals'])} kishi\n\n"
        f"🔥 <i>Do'stlaringizni taklif qiling va ko'proq ball to'plang!</i>"
    )

    try:
        photo = FSInputFile("image.png")
        await message.answer_photo(
            photo=photo,
            caption=caption_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Rasm yuborishda xatolik: {e}")
        await message.answer(
            caption_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "my_stats")
async def my_stats_callback(callback: types.CallbackQuery):
    """Statistika ko'rsatish"""
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)

    # Foydalanuvchining reyting o'rnini aniqlash
    leaderboard = get_leaderboard()
    user_rank = None
    for idx, (uid, data) in enumerate(leaderboard, 1):
        if int(uid) == user_id:
            user_rank = idx
            break

    stats_text = (
        f"📊 <b>SIZNING STATISTIKANGIZ</b>\n"
        f"{'═' * 30}\n\n"
        f"👤 <b>Ism:</b> {callback.from_user.first_name}\n"
        f"💰 <b>Jami ballar:</b> {user_data['points']} ball\n"
        f"👥 <b>Taklif qilganlar:</b> {len(user_data['referrals'])} kishi\n"
        f"🏆 <b>Reytingdagi o‘rningiz:</b> {user_rank if user_rank else 'TOP 10 dan tashqarida'}\n\n"
        f"⏰ <b>Qo‘shilgan sana:</b> {user_data['joined_date'][:10]}"
    )

    await callback.message.answer(stats_text, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "get_referral")
async def get_referral_callback(callback: types.CallbackQuery):
    """Referal linkni berish"""
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={user_id}"

    text = (
        "🔗 <b>SIZNING REFERAL LINKINGIZ</b>\n\n"
        "📣 Ushbu linkni do‘stlaringizga yuboring.\n"
        "✅ Har bir yangi a’zo uchun <b>+5 ball</b>\n\n"
        f"👉 <code>{referral_link}</code>\n\n"
        "🔥 Qancha ko‘p taklif qilsangiz, shuncha yutish imkoniyati yuqori!"
    )

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "leaderboard")
async def leaderboard_callback(callback: types.CallbackQuery):
    """Reyting jadvali"""
    leaderboard = get_leaderboard()

    if not leaderboard:
        await callback.message.answer("❌ Hozircha reyting mavjud emas.")
        return

    text = "🏆 <b>TOP 10 ISHTIROKCHILAR</b>\n"
    text += f"{'═' * 30}\n\n"

    for idx, (uid, data) in enumerate(leaderboard, 1):
        text += (
            f"{idx}. 👤 <code>{uid}</code>\n"
            f"   💰 {data['points']} ball | 👥 {len(data['referrals'])} referal\n\n"
        )

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "about_contest")
async def about_contest_callback(callback: types.CallbackQuery):
    """Konkurs haqida"""
    text = (
        "ℹ️ <b>KONKURS HAQIDA</b>\n\n"
        "🏆 <b>PSD kursi maxsus konkursi</b>\n\n"
        "📌 <b>Qanday ishtirok etiladi?</b>\n"
        "▫️ Kanalga obuna bo‘lasiz\n"
        "▫️ Referal link orqali do‘stlaringizni taklif qilasiz\n"
        "▫️ Har bir yangi a’zo uchun <b>+5 ball</b>\n\n"
        "🎁 <b>Mukofotlar:</b>\n"
        "🥇 1-o‘rin — 100% chegirma\n"
        "🥈 2-o‘rin — 70% chegirma\n"
        "🥉 3-o‘rin — 50% chegirma\n\n"
        "⏰ <b>Muddati:</b> 9-fevral 23:59\n\n"
        "🔥 Eng ko‘p ball to‘plaganlar g‘olib bo‘ladi!"
    )

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@dp.message()
async def ignore_other_messages(message: types.Message):
    """Boshqa xabarlarni e'tiborsiz qoldirish"""
    pass


async def main():
    print("=" * 50)
    print("🤖 REFERAL KONKURS BOT ISHGA TUSHDI")
    print(f"📢 Kanal: {CHANNEL_USERNAME}")
    print("=" * 50)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
