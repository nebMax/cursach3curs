import mysql.connector
from config.db_config import db_config

def get_db_connection():
    """
    Підключення до бази даних через конфігурацію з db_config.
    """
    return mysql.connector.connect(**db_config)

import logging

logging.basicConfig(level=logging.INFO)  # Налаштування логування

def execute_query(query, params=None, fetch=False):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
        connection.commit()
        return cursor  # Повертаємо курсор для доступу до lastrowid
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()






