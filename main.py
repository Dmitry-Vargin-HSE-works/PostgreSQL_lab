from conf import user, password
from mypg import PostgreSQL
import datetime

if __name__ == '__main__':
    db = PostgreSQL(user, password, "library")
    db.insert_into("my_user", {
        'full_name': 'Stas',
        'birth_date': datetime.date.today(),
        'phone_number': "+79996663322",
    })
    print("\n".join(map(str, db.select_from("my_user"))))
    db.close()
