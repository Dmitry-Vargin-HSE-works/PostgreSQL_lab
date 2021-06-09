from aiogram.dispatcher.filters.state import State, StatesGroup


class CreateDBState(StatesGroup):
    S1 = State()


class CreateTableState(StatesGroup):
    name = State()
    rows = State()


class SelectDataState(StatesGroup):
    id_ = State()


class InsertDataState(StatesGroup):
    values = State()
    csv = State()


class UpdateDataState(StatesGroup):
    where = State()
    replacement = State()


class DeleteDataState(StatesGroup):
    where = State()