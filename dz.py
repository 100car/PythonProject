# підключення до бази даних в postgresql через sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, MetaData, text
from sqlalchemy.orm import sessionmaker

import json

# Завантаження конфігурації з файлу config.json
with open('credential.json') as file:
    data = json.load(file)
    login = data['login']
    password = data['password']

DATABASE_URL = f'postgresql+psycopg2://{login}:{password}@localhost:5432/academy'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()
metadata.reflect(bind=engine)

tables = metadata.tables # словник з таблицями бази даних

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
            print(f"{str(data) if data is not None else '':<15}", end='\t')
        print()

# створювати звіти:

# вивести інформацію про всі навчальні групи
def report_all_groups():
    show_table('groups')

def report_all_groups_with_faculty():
    query_text = """
        SELECT G.id, G.name, F.name AS faculty_name
        FROM groups G
        LEFT JOIN faculties F ON G.id = F.id
        ORDER BY G.id
    """

    query = session.execute(text(query_text))
    results = query.all()

    # Заголовки
    column_names = ['id', 'name', 'faculty_name']
    print('\t'.join(f"{col:<15}" for col in column_names))
    print('-' * (len(column_names) * 16))

    # Дані
    for row in results:
        print('\t'.join(f"{str(data) if data is not None else '':<15}" for data in row))


# ▷ вивести інформацію про конкретного teacher
def report_teacher(teacher_id):
    query_text = f"""
        SELECT *
        FROM TEACHERS
        WHERE id = {teacher_id}
    """

    # Перетворюємо на SQLAlchemy text
    query = session.execute(text(query_text))
    results = query.all()

    # Друкуємо таблицю
    table = tables['teachers']
    column_names = table.columns.keys()

    # Заголовок
    print('\t'.join(f"{col:<15}" for col in column_names))
    print('-' * (len(column_names) * 16))

    # Дані
    for row in results:
        print('\t'.join(f"{str(data) if data is not None else '':<15}" for data in row))


# ▷ вивести назви груп, що належать до конкретного факультету,
def report_groups_by_faculty(faculty_id):
    query_text = f"""
        SELECT G.name
        FROM GROUPS G
        JOIN FACULTIES F ON G.id = F.id
        WHERE F.id = {faculty_id}
    """

    query = session.execute(text(query_text))
    results = query.all()

    print(f"Групи факультету з id={faculty_id}:")
    for row in results:
        print(f"- {row[0]}")

# ▷ вивести назви предметів, які викладає конкретний викладач
def report_subjects_by_teacher(teacher_id):
    query_text = f"""
        SELECT S.name
        FROM SUBJECTS S
        JOIN LECTURES L ON S.id = L.id
        WHERE L.teacherid = {teacher_id}
    """

    query = session.execute(text(query_text))
    results = query.all()

    print(f"Предмети викладача з id={teacher_id}:")
    for row in results:
        print(f"- {row[0]}")

report_all_groups()
print()
report_all_groups_with_faculty()
print()
report_teacher(2)
print()
report_groups_by_faculty(3)
print()
report_subjects_by_teacher(4)