import asyncio
import random
import requests
import os
import json
import logging
from datetime import datetime
from io import BytesIO
from PIL import Image
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage  
from aiogram.filters import Command
from aiogram import F
import re
from database import init_db, add_user, add_stat, get_user_stats, get_all_user_stats, get_user_permission, add_user_permission

# Загружаем конфигурацию
CONFIG_FILE = "config.json"

with open(CONFIG_FILE, "r", encoding="utf-8") as file:
    config = json.load(file)

TOKEN = config["token"]
API_URL = config["api_url"]
MAX_RETRIES = config["max_retries"]
VIDEO_TITLES_FILE = config["video_titles_file"]
DEBUG_MODE = config["debug"]

# Настройка логирования
LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"log-{datetime.now().strftime('%Y-%m-%d')}.log")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(file_handler)
logger.addHandler(console_handler)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Аниме")]],
    resize_keyboard=True
)

pending_codes = {}
def has_permission(user_id, command):
    return get_user_permission(user_id, command)

def escape_markdown(text: str) -> str:
    special_chars = r"[_*`~\[\](){}#+.!-]"
    return re.sub(f"({special_chars})", r"\\\1", text)

def is_missing_image(image_url):
    return "/assets/globals/missing_original.jpg" in image_url

async def fetch_data():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        for attempt in range(MAX_RETRIES):
            random_page = random.randint(1, 5900)
            url = API_URL.format(page=random_page)
            logger.debug(f"Запрос к Shikimori: {url}")
            
            anime_response = requests.get(url, headers=headers)
            anime_data = anime_response.json()
            if not anime_data:
                logger.debug("Ошибка: пустой список аниме")
                return None, "Ошибка загрузки данных", ""

            random_anime = anime_data[0]
            image_url = f"https://shikimori.one{random_anime['image']['original']}"
            anime_title = random_anime['russian']
            anime_url = f"https://shikimori.one{random_anime['url']}"

            if is_missing_image(image_url):
                logger.debug(f"Попытка {attempt+1}: найдено отсутствующее изображение, повтор запроса...")
                continue  
            
            logger.debug(f"Выбрано аниме: ID={random_anime['id']}, Название={anime_title}, Картинка={image_url}")
            
            with open(VIDEO_TITLES_FILE, "r", encoding="utf-8") as file:
                video_titles = file.readlines()
            
            random_title = random.choice(video_titles).strip()
            logger.debug(f"Выбранный заголовок: {random_title}")
            
            response = requests.get(image_url, headers=headers)
            img_data = Image.open(BytesIO(response.content))
            img_data = img_data.resize((300, 450), Image.LANCZOS)
            img_filename = f"anime_{random.randint(1000, 9999)}.jpg"
            img_data.save(img_filename)

            caption = f"{escape_markdown(random_title)}\n||[{escape_markdown(anime_title)}]({anime_url})||"
            return img_filename, caption, random_anime['id']

        logger.debug("Превышено количество попыток загрузки нормального изображения")
        return None, "Ошибка загрузки данных", ""

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None, "Ошибка загрузки данных", ""

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привет! Выберите действие:", reply_markup=keyboard)

@dp.message(Command("anime"))
@dp.message(F.text.lower() == "аниме")
async def anime_button_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Без имени"
    user_tag = f"@{message.from_user.username}" if message.from_user.username else "Нет username"

    add_user(user_id, username, user_tag)

    img_path, caption, anime_id = await fetch_data()

    if img_path:
        sent_message = await message.answer_photo(photo=FSInputFile(img_path), caption=caption, parse_mode="MarkdownV2")
        os.remove(img_path)
        add_stat(user_id, anime_id, caption.split("\n")[0].replace("\\", ""), sent_message.message_id, message.chat.id)
    else:
        await message.answer("Не удалось загрузить данные.")

@dp.message(Command("history"))
async def history_command(message: Message):
    user_id = message.from_user.id
    stats = get_user_stats(user_id)

    if not stats:
        await message.answer("У вас пока нет истории запросов.")
        return

    history_text = "📜 *История ваших запросов:*\n\n"
    for record in stats[:10]:
        date, anime_id, title = record[1], record[3], record[4]
        history_text += f"📅 {date} | 🎬 {title} (ID: {anime_id})\n"

    await message.answer(history_text, parse_mode="Markdown")


@dp.message(Command("stats"))
async def stats_command(message: Message):
    # user_id = message.from_user.id
    
    # if not has_permission(user_id, "stats"):
    #     await message.answer("⛔ У вас нет прав для использования этой команды.")
    #     return

    stats = get_all_user_stats()
    if not stats:
        await message.answer("❌ Пока нет данных о запросах.")
        return

    sorted_stats = sorted(stats, key=lambda x: x[1], reverse=True)
    stats_text = "📊 *Статистика запросов:*\n\n"
    for user_tag, count in sorted_stats:
        stats_text += f"{user_tag} - {count}\n"
    
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message(Command("get_permissions"))
async def get_permissions_command(message: Message):
    user_id = message.from_user.id
    code = str(random.randint(100000, 999999))
    pending_codes[user_id] = code
    logger.info(f"Код подтверждения для {user_id}: {code}")
    await message.answer("🔑 Код подтверждения отправлен в консоль. Отправьте его боту, чтобы получить права.")

@dp.message()
async def confirm_permission(message: Message):
    user_id = message.from_user.id
    
    if user_id not in pending_codes:
        return  # Игнорируем сообщение, если код не запрашивался этим пользователем
    
    if message.text == pending_codes[user_id]:
        add_user_permission(user_id, "stats")
        del pending_codes[user_id]
        await message.answer("✅ Доступ к команде /stats получен!")
    else:
        await message.answer("❌ Неверный код подтверждения.")

async def main():
    init_db()
    logger.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
