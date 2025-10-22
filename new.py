# підключення
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

import json

from sqlalchemy.testing.suite.test_reflection import metadata

with open('credential.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    login = data['login']
    password = data['password']

DATABASE_URL = f'postgresql+psycopg2://{login}:{password}@localhost/hospital'

# створення двигуна бази даних
engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)

session = Session()

metadata = MetaData()
metadata.reflect(bind=engine)

tables = metadata.tables
# for table_name, table in tables.items():
#     print(f"Table: {table_name}")
#     for column in table.columns:
#         print(f"  Column: {column.name}, Type: {column.type}")
#     print()

# doctors = tables['doctors']
# query_text = """
# SELECT * FROM doctors
# WHERE SALARY > 92000;
# """

# переведення рядка в об'єкт SQLAlchemy TextClause
# query_text = text(query_text)
# print(query_text)

# виконання запиту
# query = session.execute(query_text)
#
# results = query.all()
#
# doctors = tables['doctors']
# column_name = doctors.columns.keys()
# print(column_name)
#
# for row in results:
#     print(row)

# Завдання 1
# Для бази даних «Лікарня», яку ви розробляли в рамках
# курсу «Теорія Баз Даних», створіть додаток для взаємодії з
# базою даних, який дозволяє:
# ■ Показати всб ю таблицю.
# ■ Вивести назви всіх таблиць у базі даних.
def show_table_names():
    print("Таблицi:")
    for table_name in tables:
        print('*', table_name)

# ■ Показати всю таблицю
def show_table(table_name):
    query_text = f"""
        SELECT *
        FROM {table_name.upper()}
    """

    query_text = text(query_text)
    query = session.execute(query_text)
    results = query.all()

    table = tables[table_name]
    column_names = table.columns.keys()

    for column in column_names:
        print(f"{column:<15}", end='\t')
    print()

    for row in results:
        for data in row:
            print(f"{data:<15}", end='\t')
        print()


# show_table_names()





# ■ Вставляти рядки в таблиці бази даних.
# ■ Оновлення рядків у таблицях бази даних. При спробі
# оновлення усіх рядків в одній таблиці надайте запит на
# підтвердження користувачеві. Оновлювати усі рядки
# можна лише після підтвердження користувачем.
# ■ Видалення рядків з таблиць баз даних. При спробі видалити
# усі рядки в одній таблиці потрібно видавати користувачу
# запит на підтвердження. Видаляти усі рядки, можна тільки
# після підтвердження користувачем.



# Завдання 2
# ля бази даних «Лікарня», яку ви розробляли в рамках
# курсу «Теорія Баз Даних», створіть додаток для взаємодії
# з базою даних, який дозволяє створювати звіти:
# * doctors
# * doctorsspecializations
# * specializations
# ▷ Вивести прізвища лікарів та їх спеціалізації;
def report_doctors_specializations():
    query_text = """
    SELECT d.surname, STRING_AGG(s.name, ', ') AS specialization
    FROM doctors d
    JOIN doctorsspecializations ds ON ds.doctor_id = d.id
    JOIN specializations s ON s.id = ds.specialization_id
    GROUP  BY d.surname
    order  by d.surname; 
    """

    query_text = text(query_text)
    query = session.execute(query_text)
    results = query.all()

    print(f"{'Прізвище':<20}\t{'Спеціалізація':<30}")
    for row in results:
        print(f"{row.surname:<20}\t{row.specialization:<30}")

# report_doctors_specializations()
# show_table('doctors')
# show_table('specializations')

def report_doctor_specializations(doctor_surname):
    query_text = f"""
    SELECT STRING_AGG(s.name, ', ') AS specialization
    FROM doctors d
    JOIN doctorsspecializations ds ON ds.doctor_id = d.id
    JOIN specializations s ON s.id = ds.specialization_id
    WHERE d.surname = '{doctor_surname}';
    """

    query_text = text(query_text)
    query = session.execute(query_text)
    results = query.all()

    print(f"Спеціалізації лікаря {doctor_surname}: {results[0].specialization}")




# report_doctor_specializations("Беляева")

# ▷ Вивести прізвища та зарплати (сума ставки та надбавки) лікарів, які перебувають у відпустці;
def report_doctors_on_vacation():
    query_text = """
    SELECT d.surname, (d.salary + d.premium) AS total_salary, v.startdate, v.enddate
    FROM doctors d
    JOIN vacations v ON v.doctor_id = d.id
    WHERE CURRENT_DATE BETWEEN v.startdate AND v.enddate;
    """

    query_text = text(query_text)
    query = session.execute(query_text)
    results = query.all()

    print(f"{'Прізвище':<20}\t{'Зарплата':<15}\t{'Відпустка:':<15}")
    for row in results:
        print(f"{row.surname:<20}\t{row.total_salary:<15}\t{row.startdate} - {row.enddate}")

# show_table_names()
# show_table("vacations")
report_doctors_on_vacation()


# ▷ Вивести назви палат, які знаходяться у певному відділенні;
# ▷ Вивести усі пожертвування за вказаний місяць у
# вигляді: відділення, спонсор, сума пожертвування, дата
# пожертвування;
# ▷ Вивести назви відділень без повторень, які спонсору-
# ються певною компанією






