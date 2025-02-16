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

# Создаём логгер
logger = logging.getLogger()
logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

# Создаём обработчик для вывода в файл
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# Создаём обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# Очищаем старые обработчики (если есть) и добавляем новые
if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Сбор статистики
STATS_FILE = "stats.json"
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Создание клавиатуры
keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Аниме")]],
    resize_keyboard=True
)

def escape_markdown(text: str) -> str:
    special_chars = r"[_*`~\[\](){}#+.!-]"
    return re.sub(f"({special_chars})", r"\\\1", text)

def is_missing_image(image_url):
    return "/assets/globals/missing_original.jpg" in image_url

async def fetch_data():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        for attempt in range(MAX_RETRIES):
            random_page = random.randint(1, 5900)
            url = API_URL.format(page=random_page)
            logger.debug(f"Запрос к Shikimori: {url}")
            
            anime_response = requests.get(url, headers=headers)
            anime_data = anime_response.json()
            if not anime_data:
                logger.debug("Ошибка: пустой список аниме")
                return None, "Ошибка загрузки данных"

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
            return img_filename, caption

        logger.debug("Превышено количество попыток загрузки нормального изображения")
        return None, "Ошибка загрузки данных"

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None, "Ошибка загрузки данных"

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привет! Выберите действие:", reply_markup=keyboard)

@dp.message(Command("anime"))
@dp.message(F.text.lower() == "аниме")
async def anime_button_handler(message: Message):
    user_id = str(message.from_user.id)
    
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        stats = json.load(f)
    
    stats[user_id] = stats.get(user_id, 0) + 1
    
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)
    
    logger.info(f"Пользователь {user_id} запросил аниме ({stats[user_id]} раз)")
    
    img_path, caption = await fetch_data()
    if img_path:
        await message.answer_photo(photo=FSInputFile(img_path), caption=caption, parse_mode="MarkdownV2")
        os.remove(img_path)
    else:
        await message.answer("Не удалось загрузить данные.")

async def main():
    logger.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
