import mysql.connector
from mysql.connector import errorcode

import os
from dotenv import load_dotenv

from enum import Enum
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, create_engine, Field

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
    
    
# Define your database schema
class OrderStatus(str, Enum):
    in_kitchen = "in_kitchen"
    prepared = "prepared"
    served = "served"
    cancelled = "cancelled"

class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"

class PaymentMethod(str, Enum):
    cash = "cash"
    credit_card = "credit_card"
    debit_card = "debit_card"
    online = "online"

class Customer(SQLModel, table=True):
    customer_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class Menu(SQLModel, table=True):
    menu_item_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None

class Order(SQLModel, table=True):
    order_id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int
    order_type: str
    table_number: Optional[int] = None
    order_status: OrderStatus
    order_date: datetime = Field(default_factory=datetime.now)
    total_amount: float

class OrderItem(SQLModel, table=True):
    order_item_id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int
    menu_item_id: int
    quantity: int
    price: float

class Table(SQLModel, table=True):
    table_id: Optional[int] = Field(default=None, primary_key=True)
    table_number: int
    seating_capacity: int
    status: str

class Bill(SQLModel, table=True):
    bill_id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int
    bill_amount: float
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    billing_date: datetime = Field(default_factory=datetime.now)

# Database connection URL
DATABASE_URL = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_URL')}/{DB_NAME}"

# Create the MySQL database engine
engine = create_engine(DATABASE_URL)

# Create the database tables
SQLModel.metadata.create_all(engine)