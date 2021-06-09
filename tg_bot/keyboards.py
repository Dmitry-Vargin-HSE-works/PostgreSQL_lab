from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from loader import db


def get_keyboard_for_start_menu():
    button_list = [InlineKeyboardButton(x, callback_data=f'connect_to:{x}') for x in db.get_databases()]
    keyboard = InlineKeyboardMarkup().add(*button_list)
    keyboard = keyboard.add(
        InlineKeyboardButton(
            'Create DB',
            callback_data='create_db'
        )
    )
    return keyboard


def get_keyboard_for_current_database():
    tables = db.get_tables()
    kb = InlineKeyboardMarkup().add(*[
        InlineKeyboardButton(
            table,
            callback_data=f"choose_table:{table}")
        for table in tables
    ]).add(
        InlineKeyboardButton(
            "Create table",
            callback_data='create_table'
        )).add(
        InlineKeyboardButton(
            "Delete this database",
            callback_data="delete_database"
        )).add(
        InlineKeyboardButton(
            '<< Back to DataBases',
            callback_data=f'start_menu'))
    return kb


def get_keyboard_for_current_table(table_name: str):
    kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                'Select head',
                callback_data=f'select_head:{table_name}'
        )).add(
            InlineKeyboardButton(
                'Select all(csv file)',
                callback_data=f'select_from:{table_name}'),
            InlineKeyboardButton(
                'Select by id',
                callback_data=f'select_by_id:{table_name}'),
        ).add(
            InlineKeyboardButton(
                'Insert a few query',
                callback_data=f'insert_into:{table_name}'),
            InlineKeyboardButton(
                'Insert from csv',
                callback_data=f'insert_from_csv:{table_name}'),
        ).add(
            InlineKeyboardButton(
                'Update data',
                callback_data=f'update_into:{table_name}'),
        ).add(
            InlineKeyboardButton(
                'Delete by attribute',
                callback_data=f'delete_by_attr:{table_name}'),  # TODO
            InlineKeyboardButton(
                'Delete table',
                callback_data=f'delete_table:{table_name}'),
        ).add(
            InlineKeyboardButton(
                '<<Back to tables',
                callback_data=f'connect_to:{db.db_name}'),
        )
    return kb


def get_keyboard_for_done_act(table_name: str):
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            '<<Back to table',
            callback_data=f'choose_table:{table_name}'),
    ).add(
        InlineKeyboardButton(
            '<<Back to database',
            callback_data=f'connect_to:{db.db_name}'),
    ).add(
        InlineKeyboardButton(
            '<<Back to start',
            callback_data=f'start_menu'),
    )
    return kb


def get_keyboard_for_cancel_form():
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            'Cancel',
            callback_data='start_menu',
        )
    )
    return kb
