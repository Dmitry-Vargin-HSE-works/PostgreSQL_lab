import os
import csv
from typing import List, Tuple
import psycopg2
import psycopg2.extensions as type_code
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class PostgreSQL:

    rows_example = "name str -not_null\nage int\nbirth_date date\ndescription text\nbook_id int -fk table_name\n"

    def __init__(self, username: str, password: str, db_name="postgres"):
        self.types = {
            'str': 'character varying',
            'int': 'integer',
            'date': 'date',
            'text': 'text',
            '-fk': '-fk',
        }
        self.db_name = db_name
        self.user = username
        self.password = password
        try:
            self.conn = psycopg2.connect(
                user=username,
                password=password,
                host="127.0.0.1",
                port="5432",
                database=self.db_name,
            )
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            print(f"{username} has connected successfully to \"{self.db_name}\" database!")
            if self.db_name == "postgres":
                print(f"Reconnect to another database to start work.")
        except (Exception, psycopg2.Error) as ex:
            self.close()
            print(ex)

    def reconnect(self, db_name='postgres'):
        self.close()
        self.__init__(self.user, self.password, db_name)

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()

    def get_databases(self) -> List:
        self.cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        res = list(sum(self.cursor.fetchall(), tuple()))
        res.remove("postgres")
        return res

    def get_tables(self) -> List:
        self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        return list(sum(self.cursor.fetchall(), tuple()))

    def get_attributes(self, table_name: str, with_type=False):
        try:
            self.cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
            return {x.name: int(x.type_code) for x in self.cursor.description} \
                if with_type else [x.name for x in self.cursor.description]
        except (Exception, psycopg2.Error) as ex:
            print(ex)
            return []

    # 1
    def create_database(self, db_name):
        self.cursor.execute(
            f"""
            CREATE DATABASE {db_name} WITH 
                OWNER = {self.user}
                ENCODING = 'UTF8'
                CONNECTION LIMIT = -1;
            """
        )

    def create_table(self, table_name, lines: list):
        """
        Create a table within list of lines with attributes.
        For example:
            name str -not_null
            age int
            birth_date date
            description text
            book_id -fk table_name
        WARN: ID will be created automatically!
        """
        line = ''
        res = f"CREATE TABLE {table_name} ("
        res += f"id serial NOT NULL, "
        fk_text = ""
        for line in lines:
            tmp: list = line.split()
            tmp_res = f"{tmp[0]} {self.types[tmp[1]]}"
            if "-not_null" in tmp:
                tmp_res += " NOT NULL"
            if "-fk" in tmp:
                fk_param: str = tmp[tmp.index("-fk") + 1]
                if fk_param.startswith("-"):
                    raise Exception("fk cannot apply to another key")
                fk_text += f'CONSTRAINT {tmp[0]} FOREIGN KEY ({tmp[0]}) REFERENCES "{fk_param}" (id)'
            res += tmp_res + ", "
        res += "PRIMARY KEY (id)"
        if fk_text:
            res += ", " + fk_text
        res += ");"
        self.cursor.execute(res)

    # 2
    def delete_database(self, db_name: str):
        if db_name == self.db_name:
            return
        self.cursor.execute(f"DROP DATABASE {db_name};")

    # 3 / 6
    def select_from(self, table_name, **kwargs):
        attributes = kwargs.get('attributes', '*')
        if attributes != '*':
            attributes = ", ".join(attributes)
        try:
            self.cursor.execute(
                f"SELECT {attributes} FROM {table_name};")
        except (Exception, psycopg2.Error) as ex:
            print(ex)
        res = self.cursor.fetchall()
        return res[:kwargs.get('limit', len(res))]

    def select_by_id(self, table_name, id_):
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE id={id_}")
        return self.cursor.fetchall()[0]

    def select_from_as_csv(self, table_name: str):
        """:return a abs path to csv file"""
        file_num = max(
            list(map(
                lambda x: int(x[4:]),
                filter(
                    lambda x: x.startswith('file') and x[4:].isdigit(),
                    os.listdir('data')
                )
            )) + [-1]
        )+1
        file_name = f'file{file_num}.csv'
        f = open(f'data/{file_name}', 'w')
        csv_writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(self.get_attributes(table_name))
        try:
            self.cursor.execute(f'SELECT * FROM {table_name};')
            csv_writer.writerows(self.cursor.fetchall())
        except (Exception, psycopg2.Error) as ex:
            print(ex)
        finally:
            f.close()
            return os.path.abspath('data/' + file_name)

    # 5
    def insert_row(self, table_name, row):
        columns = self.get_attributes(table_name)
        columns.remove('id')

        command = f"INSERT INTO {table_name} {', '.join(columns)} VALUES ({','.join(['%s'] * len(row))});"
        self.cursor.execute(command, tuple(row))

    def insert_rows(self, table_name: str, rows: Tuple[Tuple]):
        if len(rows):
            columns = self.get_attributes(table_name)
            columns.remove('id')
            rows = tuple(map(tuple, rows))

            command = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES "
            command += ', '.join(["(" + ", ".join(["%s"] * len(rows[0])) + ")"] * len(rows))
            self.cursor.execute(command + ';', sum(rows, tuple()))

    def insert_rows_csv(self, table_name: str, path) -> int:
        """:return a number of inserted rows"""
        with open(path, 'r') as f:
            csv_reader = csv.reader(f, delimiter=';', quotechar='"')
            columns = self.get_attributes(table_name)
            columns.remove('id')
            i = 0
            for row in csv_reader:
                if i != 0 and len(row):
                    command = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({','.join(['%s'] * len(row))});"
                    self.cursor.execute(command + ';', tuple(row))
                i += 1
        return i

    def update_where(self, table_name: str, replacement: dict, where: dict):
        if 'id' in replacement.keys():
            replacement.pop('id')
        replacement_str = ", ".join([f"{k} = %s" for k in replacement.keys()])
        command = f'UPDATE {table_name} SET {replacement_str}'
        params = tuple(replacement.values())
        if where != {}:
            where_str = ", ".join([f"{k} = %s" for k in where.keys()])
            command += ' WHERE ' + where_str
            params = params + tuple(where.values())
        self.cursor.execute(command+';', params)

    # 4 / 8 / 9
    def delete_row_by_atr(self, table_name: str, where: dict):
        replacement_str = ", ".join([f"{k} = %s" for k in where.keys()])
        command = f'DELETE FROM {table_name} WHERE {replacement_str};'
        params = tuple(where.values())
        self.cursor.execute(command, params)

    def delete_all_by(self, table_name: str, **kwargs):
        keys = set(self.get_attributes(table_name)) & set(kwargs.keys())
        command = f"DELETE FROM {table_name} WHERE " + ", ".join([f"{k}={kwargs[k]}" for k in keys])
        self.cursor.execute(command+';')

    def clean_table(self, table_name):
        if type(table_name) == str:
            self.cursor.execute(f"DELETE FROM {table_name};")
        else:
            for t in table_name:
                self.cursor.execute(f"DELETE FROM {t};")

    def delete_table(self, table_name):
        if type(table_name) == str:
            self.cursor.execute(f"DROP TABLE {table_name};")
        else:
            for t in table_name:
                self.cursor.execute(f"DROP TABLE {t};")
