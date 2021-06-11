import datetime
import os

import psycopg2

from aiogram import types
from aiogram.types import InputFile
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext

from tg_bot.states import *
from loader import dp, db, bot
import tg_bot.keyboards as keyboards


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('select_from:'))
async def select_from(call_back: types.CallbackQuery):
    table_name = call_back.data[call_back.data.find(':') + 1:]

    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    path = db.select_from_as_csv(table_name)
    file = InputFile(path, f"select_{table_name}.csv")
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text='Data is below'
    )
    await bot.send_document(
        chat_id=chat_id,
        document=file,
    )
    await bot.send_message(
        chat_id=chat_id,
        text='Continue work...',
        reply_markup=keyboards.get_keyboard_for_done_act(table_name),
    )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('select_head:'))
async def select_head(call_back: types.CallbackQuery):
    table_name = call_back.data[call_back.data.find(':') + 1:]

    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    data = db.select_from(table_name, limit=5)
    columns = db.get_attributes(table_name)
    res = ' | '.join(columns) + '\n' + '\n'.\
        join([' | '.
             join(map(str,
                      map(lambda s: str(s)[:30]+'...' if len(str(s)) > 30 else str(s), x)))
              for x in data])
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text='Data is below'
    )
    await bot.send_message(
        chat_id=chat_id,
        text=res,
    )
    await bot.send_message(
        chat_id=chat_id,
        text='Continue work...',
        reply_markup=keyboards.get_keyboard_for_done_act(table_name),
    )


@dp.callback_query_handler(lambda c: c.data.startswith('select_by_id:'))
async def select_by_id(call_back: types.CallbackQuery, state: FSMContext):
    table_name = call_back.data[call_back.data.find(':') + 1:]
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    await SelectDataState.id_.set()
    await state.update_data(table_name=table_name)

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text='Ok. Send me ID.',
        reply_markup=keyboards.get_keyboard_for_cancel_form()
    )


@dp.message_handler(state=SelectDataState.id_)
async def select_by_id_num(mes: types.Message, state: FSMContext):
    data = await state.get_data()
    table_name = data['table_name']
    chat_id = mes.chat.id
    mes_id = mes.message_id
    try:
        row = db.select_by_id(table_name, int(mes.text))
    except (psycopg2.Error, Exception) as ex:
        await bot.send_message(
            chat_id=chat_id,
            text='The row with this ID is not exist in the table.\nTry again.',
            reply_markup=keyboards.get_keyboard_for_cancel_form()
        )
    else:
        await state.reset_state()
        columns = db.get_attributes(table_name)
        res = ' | '.join(columns) + '\n' + ' | '.join(map(str, row))
        await bot.send_message(
            chat_id=chat_id,
            text=res,
        )
        await bot.send_message(
            chat_id=chat_id,
            text="Something else?",
            reply_markup=keyboards.get_keyboard_for_current_table(table_name)
        )


@dp.callback_query_handler(lambda c: c.data and
                                     (c.data.startswith('insert_into:') or
                                      c.data.startswith('insert_from_csv:')))
async def insert_into(call_back: types.CallbackQuery, state: FSMContext):
    table_name = call_back.data[call_back.data.find(':') + 1:]

    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id
    columns = db.get_attributes(table_name)
    columns.remove('id')

    if call_back.data.startswith('insert_into'):
        await InsertDataState.values.set()
    else:
        await InsertDataState.csv.set()
    await state.update_data(table_name=table_name)

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text='Ok, send me rows that contain the following attributes in the given sequence split within ;\n' +
             ' | '.join(columns)
        if call_back.data.startswith('insert_into') else
        'Ok, send me file with rows that contain the following attributes in the given sequence\n' +
        ';'.join(columns) + "\nand rows split within ;",
        reply_markup=keyboards.get_keyboard_for_cancel_form()
    )


@dp.message_handler(state=InsertDataState.values)
async def insert_into_values(mes: types.Message, state: FSMContext):
    chat_id = mes.chat.id
    data = await state.get_data()
    table_name = data.get('table_name')
    arr = [map(lambda s: s.strip(), x.split(';')) for x in mes.text.split('\n')]
    try:
        db.insert_rows(table_name, arr)
    except (psycopg2.Error, Exception) as ex:
        print(ex)
        await bot.send_message(
            chat_id=chat_id,
            text='Data are incorrect or some ID already exists!\nTry again or cancel it.',
            reply_markup=keyboards.get_keyboard_for_cancel_form(),
        )
    else:
        await mes.answer(
            text='Rows were added!',
            reply_markup=keyboards.get_keyboard_for_current_table(table_name),
        )
        await state.reset_state()


@dp.message_handler(state=InsertDataState.csv, content_types=['document'])
async def insert_rows_csv(mes: types.Message, state: FSMContext):
    chat_id = mes.chat.id
    data = await state.get_data()
    table_name = data.get('table_name')

    document = await bot.get_file(mes.document.file_id)
    path = f"data/from_{mes.from_user.id}"
    await bot.download_file(document.file_path, path)
    try:
        db.insert_rows_csv(table_name, path)
    except (psycopg2.Error, Exception) as ex:
        print(ex)
        await bot.send_message(
            chat_id=chat_id,
            text='Data are incorrect!\nTry again or cancel it.',
            reply_markup=keyboards.get_keyboard_for_cancel_form(),
        )
    else:
        await mes.answer(
            text='Rows were added!',
            reply_markup=keyboards.get_keyboard_for_current_table(table_name),
        )
        await state.reset_state()
    finally:
        os.remove(path)


@dp.callback_query_handler(lambda c: c.data.startswith('update_into:'))
async def update_into(call_back: types.CallbackQuery, state: FSMContext):
    table_name = call_back.data[call_back.data.find(':') + 1:]

    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id
    columns = db.get_attributes(table_name)

    await UpdateDataState.where.set()
    await state.update_data(table_name=table_name)

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text='Ok, send me attributes by which I will find the required fields. Example:\n' +
             'name John\ndata 2007\nage 39\n' +
             'if you wanna update all rows, send me "-"',
        reply_markup=keyboards.get_keyboard_for_cancel_form()
    )


@dp.message_handler(state=UpdateDataState.where)
async def update_into_where(mes: types.Message, state: FSMContext):
    chat_id = mes.chat.id
    mes_id = mes.message_id

    data = await state.get_data()
    table_name = data.get('table_name')
    columns = db.get_attributes(table_name)

    try:
        if mes == '-':
            data['where'] = {}
        else:
            arr = [x.split(' ') for x in mes.text.split('\n')]
            if any(map(lambda x: len(x) != 2, arr)):
                raise Exception('Incorrect data "def update_into_where"')
            if any(map(lambda x: x[0] not in columns, arr)):
                raise Exception('Incorrect data "def update_into_where"')
            data['where'] = {x[0]: x[1] for x in arr}
        await state.update_data(data)
        await UpdateDataState.replacement.set()
        await mes.answer(
            text='Ok. Now send me attributes and its values which will be set.'
                 '\nExample:\nname Andy\nnum_of_children 2',
            reply_markup=keyboards.get_keyboard_for_cancel_form(),
        )
    except (psycopg2.Error, Exception) as ex:
        print(ex)
        await mes.answer(
            text='Data are incorrect!\nTry again.',
            reply_markup=keyboards.get_keyboard_for_cancel_form(),
        )


@dp.message_handler(state=UpdateDataState.replacement)
async def update_into_replacement(mes: types.Message, state: FSMContext):
    chat_id = mes.chat.id
    mes_id = mes.message_id

    data = await state.get_data()
    table_name = data.get('table_name')
    columns = db.get_attributes(table_name)

    try:
        arr = [x.split(' ') for x in mes.text.split('\n')]
        replacement = {x[0]: x[1] for x in arr}
        db.update_where(table_name, replacement, data['where'])
        await state.reset_state()
        await mes.answer(
            text='Data was updated.',
            reply_markup=keyboards.get_keyboard_for_current_table(table_name),
        )
    except (psycopg2.Error, Exception) as ex:
        print(ex)
        await mes.answer(
            text='Data are incorrect!\nTry again.',
            reply_markup=keyboards.get_keyboard_for_cancel_form(),
        )


@dp.callback_query_handler(lambda c: c.data.startswith('delete_by_attr:'))
async def delete_by_attr(call_back: types.CallbackQuery, state: FSMContext):
    table_name = call_back.data[call_back.data.find(':') + 1:]
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    await DeleteDataState.where.set()
    await state.update_data(table_name=table_name)

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text='Ok. Send me attributes.\n'
             'Example:\nage 18\npet dog',
        reply_markup=keyboards.get_keyboard_for_cancel_form()
    )


@dp.message_handler(state=DeleteDataState.where)
async def delete_by_attr_where(mes: types.Message, state: FSMContext):
    data = await state.get_data()
    table_name = data['table_name']
    chat_id = mes.chat.id
    mes_id = mes.message_id
    try:
        arr = list(map(lambda x: x.split(), mes.text.split('\n')))
        where = {x[0]: x[1] for x in arr}
        db.delete_row_by_atr(table_name, where)
    except (psycopg2.Error, Exception) as ex:
        print(ex)
        await bot.send_message(
            chat_id=chat_id,
            text='The data use sent are incorrect.\nTry again.',
            reply_markup=keyboards.get_keyboard_for_cancel_form()
        )
        raise ex
    else:
        await state.reset_state()
        await bot.send_message(
            chat_id=chat_id,
            text='Data was removed. Something else',
            reply_markup=keyboards.get_keyboard_for_current_table(table_name)
        )


@dp.callback_query_handler(lambda c: c.data.startswith('delete_table:'))
async def delete_table(call_back: types.CallbackQuery):
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id

    table_name = call_back.data[call_back.data.find(':') + 1:]

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Yes', callback_data=f'delete_table_true:{table_name}'),
        InlineKeyboardButton('No', callback_data='connect_to:' + db.db_name)
    )

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=mes_id,
        text=f"Are you sure you want to delete {db.db_name}?",
        reply_markup=kb,
    )


@dp.callback_query_handler(lambda c: c.data.startswith('delete_table_true:'))
async def delete_table_true(call_back: types.CallbackQuery):
    chat_id = call_back.message.chat.id
    mes_id = call_back.message.message_id
    table_name = call_back.data[call_back.data.find(':') + 1:]
    try:
        db.delete_table(table_name)
    except (Exception, psycopg2.Error) as ex:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=mes_id,
            text=f'Something was wrong.\nTry again later.'
        )
    else:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=mes_id,
            text=f'{table_name} has successfully removed.',
            reply_markup=keyboards.get_keyboard_for_current_database()
        )
