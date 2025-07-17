import asyncio
import os
from dotenv import load_dotenv

from aiogram.types import InputFile, FSInputFile, BotCommand
from aiogram import Bot, Dispatcher
from aiogram.methods import SetMyCommands

from routers import router

# Загрузка переменных
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_KEY')

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

async def main():

	commands = [
		BotCommand(command="start", description="Запустить бота"),
		BotCommand(command="weather", description="Узнать погоду"),
		BotCommand(command="voice", description="Узнать погоду и озвучить"),
		BotCommand(command="help", description="Помощь и справка")
	]

	await bot.set_my_description("Учебный бот для домашнего задания TG")
	await bot.set_my_short_description("Учебный бот Zerocoder")
	await bot(SetMyCommands(commands=commands))

	dp.include_router(router)
	await dp.start_polling(bot)
	await bot.session.close()


if __name__ == '__main__':
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		print('Exit')