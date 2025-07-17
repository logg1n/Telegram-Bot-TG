from dotenv import load_dotenv
import os
from pathlib import Path

from datetime import datetime

import aiohttp
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile

from gtts import gTTS
from googletrans import Translator


load_dotenv()
router: Router = Router()
translator = Translator()

WEATHER_KEY = os.getenv('WEATHER_KEY')

@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Command Start")


@router.message(Command('help'))
async def help_command(message: Message):
    commands = await get_commands()
    await message.answer(f'Доступные команды: {", ".join(commands)}')


@router.message(F.text.startswith('/weather'))
async def text_weather(message: Message):
    msg = message.text.strip().split()

    # Проверяем правильность формата
    if len(msg) != 2:
        await message.answer("⚠️ Используйте: /weather <город>")
        return
    city = msg[-1]  # Объединяем все части после /weather
    weather = await get_weather(city)
    await message.answer(weather)


# @router.message(F.text.startswith('/weatherv'))
@router.message(F.text.startswith('/voice'))
async def voice_weather(message: Message):
    msg = message.text.strip().split()

    if len(msg) != 2:
        await message.answer("⚠️ Используйте: /voice <город>")
        return

    city = msg[-1]
    weather = await get_weather(city)

    # Озвучка текста
    tts = gTTS(text=weather, lang='ru')
    audio_path = f"temp/weather_{message.from_user.id}.mp3"
    tts.save(audio_path)

    # Отправка аудиофайла
    audio = FSInputFile(audio_path)
    await message.answer_voice(audio)

    # Удаление файла после отправки (опционально)
    os.remove(audio_path)

@router.message(F.text)
async def translate_text(message: Message):
    msg = message.text
    lang = translator.detect(msg[:50])
    if lang.confidence:
        await message.answer("⚠️ Трудно распознать текст")

    await message.answer(translator.translate(msg, 'en').text)

@router.message(F.photo | F.document.mime_type.startswith("image/"))
async def save_any_image(message: Message):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    user_dir = Path(f"temp/img/user_{message.from_user.id}")
    user_dir.mkdir(parents=True, exist_ok=True)

    # Выбираем источник: фото или документ
    if message.photo:
        prefix = "photo"
        file = message.photo[-1]
        ext = "jpg"
        file_id = file.file_unique_id
    else:
        prefix = "image"
        file = message.document
        ext = file.file_name.split('.')[-1]
        file_id = file.file_unique_id

    file_name = f"{prefix}_{file_id}_{timestamp}.{ext}"
    save_path = user_dir / file_name

    await message.bot.download(file.file_id, destination=save_path)
    size_kb = os.path.getsize(save_path) / 1024

    await message.reply(
        f"🖼 Изображение сохранено:\n"
        f"• Имя: {file_name}\n"
        f"• Размер: {size_kb:.2f} KB\n"
        f"• Путь: {save_path}"
    )


async def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric&lang=ru"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                # Формируем ответ
                weather_description = data['weather'][0]['description']
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                humidity = data['main']['humidity']
                wind_speed = data['wind']['speed']

                reply = (
                    f"🌦 Погода в {city}:\n"
                    f"• Состояние: {weather_description.capitalize()}\n"
                    f"• Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                    f"• Влажность: {humidity}%\n"
                    f"• Ветер: {wind_speed} м/с"
                )

                return reply
            else:
                error_data = await response.json()
                return f"❌ Ошибка: {error_data.get('message', 'Неизвестная ошибка')}"


async def get_commands():
    return [
        '\n/start - Начало работы',
        '\n/help - Список команд',
        '\n/weather <город> - Погода текстом',
        '\n/weatherv <город> - Погода голосом'
    ]