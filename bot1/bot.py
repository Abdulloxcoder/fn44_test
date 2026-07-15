from aiogram import Dispatcher, Bot, types, F
from aiogram.filters import CommandStart, Command
from database import connection, jadval_yaratish, malumot
import asyncio
from load import BOT_TOKEN


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def hello(message: types.Message):
    ismi=message.from_user.full_name
    telegram_id=message.from_user.id
    malumot(ismi,telegram_id)
    await message.reply(f"Salom {message.from_user.full_name} sizning malumotlaringiz saqlandi!")




async def main():
    jadval_yaratish()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())