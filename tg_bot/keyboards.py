from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import db


def get_keyboard_for_start_menu():
    button_list = [InlineKeyboardButton(x, callback_data=f'connect_to:{x}') for x in db.get_databases()]
    keyboard = InlineKeyboardMarkup().add(*button_list)
    return keyboard


def get_keyboard_for_current_database():
    tables = db.get_tables()
    buttons = [
        InlineKeyboardButton(
            table,
            callback_data=f"choose_table:{table}")
        for table in tables
    ]
    delete_button = InlineKeyboardButton(
        "Delete this database",
        callback_data="delete_database"
    )
    back_button = InlineKeyboardButton(
        '<< Back to DataBases',
        callback_data=f'start_menu')
    kb = InlineKeyboardMarkup().add(*buttons).add(delete_button).add(back_button)
    return kb


def get_keyboard_for_current_table(table_name: str):
    buttons = [
        InlineKeyboardButton(
            'Select all(csv file)',
            callback_data=f'select_from:{table_name}'),
        InlineKeyboardButton(
            'Select head',
            callback_data=f'select_head:{table_name}'),
        InlineKeyboardButton(
            'Insert a few query',
            callback_data=f'insert_into:{table_name},'),
        InlineKeyboardButton(
            'Insert from csv',
            callback_data=f'insert_from_csv:{table_name}'),
        InlineKeyboardButton(
            'Delete by id',
            callback_data=f'delete_from:{table_name}'),
        InlineKeyboardButton(
            'Delete by attribute',
            callback_data=f'delete_from_atrr:{table_name}'),
        InlineKeyboardButton(
            'Clean table',
            callback_data=f'delete_all_from:{table_name}'),
        InlineKeyboardButton(
            '<<Back to tables',
            callback_data=f'connect_to:{db.db_name}'),
    ]
    return InlineKeyboardMarkup().add(*buttons)
