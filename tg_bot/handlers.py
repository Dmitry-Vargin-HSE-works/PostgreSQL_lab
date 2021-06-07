from aiogram import types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import dp, db, bot
import tg_bot.keyboards as keyboards


@dp.message_handler(commands=['start', 'databases'])
async def start_menu(mes: types.Message):
    keyboard = keyboards.get_keyboard_for_start_menu()
    await mes.answer(
        ('Hello! There you can control a library database and any other you created!\n'
         if mes.text == '/start' else '') +
        'To connect and start work, choose any below.', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data == 'start_menu')
async def menu(call_back: types.CallbackQuery):
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text='To connect and start work, choose any below.'
    )
    await bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=mes_id,
        reply_markup=keyboards.get_keyboard_for_start_menu())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('connect_to:'))
async def reconnect_to(call_back: types.CallbackQuery):
    db_name = call_back.data[call_back.data.find(':') + 1:]

    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    if db_name in db.get_databases():
        if db.db_name != db_name:
            db.reconnect(db_name)
        tables = db.get_tables()
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=mes_id,
            text=f"You have chosen \"{db_name}\" database."
        )
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=mes_id,
            reply_markup=keyboards.get_keyboard_for_current_database()
        )
    else:
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=mes_id,
            reply_markup=keyboards.get_keyboard_for_start_menu()
        )
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=mes_id,
            text="The database was removed recently!\nChoose any other."
        )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('choose_table:'))
async def choose_table(call_back: types.CallbackQuery):
    table_name = call_back.data[call_back.data.find(':') + 1:]

    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    if table_name in db.get_tables():
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=mes_id,
            text="Choose what you want to do with it."
        )
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=mes_id,
            reply_markup=keyboards.get_keyboard_for_current_table(table_name)
        )
    else:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=mes_id,
            text="The table was removed recently!\nChoose any other."
        )
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=mes_id,
            reply_markup=keyboards.get_keyboard_for_current_database()
        )


@dp.callback_query_handler(lambda c: c.data and c.data == 'delete_database')
async def delete_database(call_back: types.CallbackQuery):
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Yes', callback_data='delete_database_true'),
        InlineKeyboardButton('No', callback_data='connect_to:'+db.db_name)
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text=f"Are you sure you want to delete {db.db_name}?"
    )
    await bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=mes_id,
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data and c.data == 'delete_database_true')
async def delete_database_true(call_back: types.CallbackQuery):
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    await bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=mes_id,
        reply_markup=None
    )
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text=f'{db.db_name} has successfully removed.'
    )
    db.reconnect()
