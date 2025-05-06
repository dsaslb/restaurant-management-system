from flask_sqlalchemy import SQLAlchemy
from extensions import db
from .employee import User, Employee, Contract, Attendance
from .inventory import InventoryItem, Ingredient, OrderItem, StockItem, StockTransaction, StockUsageAlert
from .notification import Notification, AlertLog
from .schedule import Schedule, ScheduleHistory

__all__ = [
    'db',
    'User',
    'Employee',
    'Contract',
    'Attendance',
    'InventoryItem',
    'Ingredient',
    'OrderItem',
    'StockItem',
    'StockTransaction',
    'StockUsageAlert',
    'Notification',
    'AlertLog',
    'Schedule',
    'ScheduleHistory'
]

# models 패키지 초기화
from models.employee import Employee, Contract, Attendance
from models.schedule import ScheduleHistory
