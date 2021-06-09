from aiogram.utils import executor
import logging

from loader import dp
import tg_bot.handlers

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp)
