import re
import time
from typing import List, Tuple, Set

import psycopg2
from aiogram import types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext

from loader import dp, db, bot
import tg_bot.keyboards as keyboards
from .handler_for_headers import *
from .states import *


@dp.message_handler(commands=['start', 'databases'], state='*')
async def start_menu(mes: types.Message, state: FSMContext):
    if state:
        await state.reset_state()
    db.reconnect(db_name='postgres')
    keyboard = keyboards.get_keyboard_for_start_menu()
    await mes.answer(
        ('Hello! There you can control a library database and any other you created!\n'
         if mes.text == '/start' else '') +
        'To connect and start work, choose any below.', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data == 'start_menu', state='*')
async def menu(call_back: types.CallbackQuery, state: FSMContext):
    if state:
        await state.reset_state()
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id
    db.reconnect('postgres')
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
            text=f"Choose what you want to do with \"{table_name}\"."
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


@dp.callback_query_handler(lambda c: c.data == 'delete_database')
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
        text=f"Are you sure you want to delete {db.db_name}?",
        reply_markup=kb,
    )


@dp.callback_query_handler(lambda c: c.data == 'delete_database_true')
async def delete_database_true(call_back: types.CallbackQuery):
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id
    db_name = db.db_name
    db.reconnect(db_name='postgres')
    try:
        db.delete_database(db_name)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=mes_id,
            text=f'{db_name} has successfully removed.'
        )
    except (Exception, psycopg2.Error) as ex:
        print(ex)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=mes_id,
            text=f'Something was wrong.\nMay be somebody is connected to this now.\nTry again later.'
        )


@dp.callback_query_handler(lambda c: c.data == 'create_db', state=None)
async def create_db(call_back: types.CallbackQuery):
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    await CreateDBState.S1.set()
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text='OK. Send me a database name'
             '(You can user only Latin alphabet and "_".'
             'Also name size must be from 4 to 25)',
        reply_markup=keyboards.get_keyboard_for_cancel_form()
    )


@dp.message_handler(state=CreateDBState.S1)
async def name_for_db(mes: types.Message, state: FSMContext):
    chat_id = mes.chat.id
    mes_id = mes.message_id
    if len(re.findall(r'^[a-zA-Z_]{4,25}$', mes.text)) == 0:
        await mes.answer(
            'The name is not valid. Try again',
            reply_markup=keyboards.get_keyboard_for_cancel_form())
    elif mes.text in db.get_databases():
        await mes.answer(
            'A database with this name already exist. Choose another one.',
            reply_markup=keyboards.get_keyboard_for_cancel_form())
    else:
        await state.reset_state()
        db.create_database(mes.text)
        await mes.answer(
            f'DataBase "{mes.text}" has created successfully!',
            reply_markup=keyboards.get_keyboard_for_start_menu()
        )


@dp.callback_query_handler(lambda c: c.data == 'create_table')
async def create_table(call_back: types.CallbackQuery):
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    await CreateTableState.name.set()
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text='OK. Send me a table name'
             '(You can user only Latin alphabet and "_".'
             'Also name size must be from 4 to 25)',
        reply_markup=keyboards.get_keyboard_for_cancel_form()
    )


@dp.message_handler(state=CreateTableState.name)
async def name_for_table(mes: types.Message, state: FSMContext):
    chat_id = mes.chat.id
    mes_id = mes.message_id
    if len(re.findall(r'^[a-zA-Z_]{4,25}$', mes.text)) == 0:
        await mes.answer(
            'The name is not valid. Try again',
            reply_markup=keyboards.get_keyboard_for_cancel_form())
    elif mes.text in db.get_tables():
        await mes.answer(
            'A table with this name already exist. Choose another one.',
            reply_markup=keyboards.get_keyboard_for_cancel_form())
    else:
        await state.update_data(name=mes.text)
        await state.set_state(CreateTableState.rows)
        await mes.answer(
            f'Good!\nNow send me a list of rows.\nExample:\n\n' + db.rows_example,
            reply_markup=keyboards.get_keyboard_for_cancel_form()
        )


@dp.message_handler(state=CreateTableState.rows)
async def rows_for_table(mes: types.Message, state: FSMContext):
    chat_id = mes.chat.id
    mes_id = mes.message_id
    rows: List[str] = mes.text.split('\n')
    try:
        data = await state.get_data()
        db.create_table(data.get('name'), rows)
    except (psycopg2.Error, Exception) as ex:
        await bot.send_message(
            chat_id=chat_id,
            text='A table is incorrect.\nSee example:\n\n' + db.rows_example,
            reply_markup=keyboards.get_keyboard_for_cancel_form())
    else:
        await mes.answer(
            f'{data["name"]} has created!',
            reply_markup=keyboards.get_keyboard_for_current_database()
        )
        await state.reset_state()
