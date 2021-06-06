from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from mypg import PostgreSQL

from conf import API_TOKEN, USER, PASSWORD


bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = PostgreSQL(USER, PASSWORD)
