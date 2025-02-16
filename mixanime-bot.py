import asyncio
import random
import requests
import os
import json
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
        
        for attempt in range(MAX_RETRIES):  # Ограничение на число попыток
            random_page = random.randint(1, 5900)
            url = API_URL.format(page=random_page)
            if DEBUG_MODE:
                print(f"[DEBUG] Запрос к Shikimori: {url}")
            
            anime_response = requests.get(url, headers=headers)
            anime_data = anime_response.json()
            if not anime_data:
                if DEBUG_MODE:
                    print("[DEBUG] Ошибка: пустой список аниме")
                return None, "Ошибка загрузки данных"

            random_anime = anime_data[0]
            image_url = f"https://shikimori.one{random_anime['image']['original']}"
            anime_title = random_anime['russian']
            anime_url = f"https://shikimori.one{random_anime['url']}"

            if is_missing_image(image_url):
                if DEBUG_MODE:
                    print(f"[DEBUG] Попытка {attempt+1}: найдено отсутствующее изображение, повтор запроса...")
                continue  # Повторяем запрос
            
            if DEBUG_MODE:
                print(f"[DEBUG] Выбрано аниме: ID={random_anime['id']}, Название={random_anime['russian']}, Картинка={image_url}")

            # Читаем список заголовков
            with open(VIDEO_TITLES_FILE, "r", encoding="utf-8") as file:
                video_titles = file.readlines()
            
            if DEBUG_MODE:
                print(f"[DEBUG] Загруженные заголовки ({len(video_titles)} шт.)")

            random_title = random.choice(video_titles).strip()
            if DEBUG_MODE:
                print(f"[DEBUG] Выбранный заголовок: {random_title}")

            # Загружаем изображение
            response = requests.get(image_url, headers=headers)
            img_data = Image.open(BytesIO(response.content))
            img_data = img_data.resize((300, 450), Image.LANCZOS)
            img_filename = f"anime_{random.randint(1000, 9999)}.jpg"
            img_data.save(img_filename)

            cleared_anime_title = escape_markdown(anime_title)
            cleared_random_title = escape_markdown(random_title)

            caption = f"{cleared_random_title}\n||[{cleared_anime_title}]({anime_url})||"
            return img_filename, caption

        if DEBUG_MODE:
            print("[DEBUG] Превышено количество попыток загрузки нормального изображения")
        return None, "Ошибка загрузки данных"

    except Exception as e:
        if DEBUG_MODE:
            print("[DEBUG] Ошибка:", e)
        return None, "Ошибка загрузки данных"

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привет! Выберите действие:", reply_markup=keyboard)

@dp.message(Command("anime"))
@dp.message(F.text.lower() == "аниме")
async def anime_button_handler(message: Message):
    img_path, caption = await fetch_data()
    if img_path:
        await message.answer_photo(photo=FSInputFile(img_path), caption=caption, parse_mode="MarkdownV2")
        os.remove(img_path)  # Удаляем временный файл после отправки
    else:
        await message.answer("Не удалось загрузить данные.")

async def main():
    if DEBUG_MODE:
        print("[DEBUG] Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
