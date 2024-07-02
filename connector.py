import mysql.connector
from mysql.connector import errorcode

import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    user = os.getenv('DB_USER'),
    password = os.getenv('DB_PASSWORD'),
    host = os.getenv('DB_URL'),
)

cursor = conn.cursor()

DB_NAME="restaurant"

# Create the database
try:
    cursor.execute(f"CREATE DATABASE {DB_NAME}")
    print(f"Database {DB_NAME} created successfully.")
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_DB_CREATE_EXISTS:
        print(f"Database {DB_NAME} already exists.")
    else:
        print(f"Failed to create database: {err}")
finally:
    cursor.close()
    conn.close()