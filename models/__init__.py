from .user import User
from .employee import Employee, WorkEvaluation, TerminationDocument, Payroll
from .supplier import Supplier
from .order import Order, OrderItem
from .contract import Contract, ContractTemplate, ContractRenewalLog, SignatureLog
from .notification import Notification, AlertLog, NotificationSetting, NotificationLog

from .inventory import (
    ProductCategory,
    InventoryStatus,
    InventoryItem,
    InventoryBatch,
    Ingredient,
    StockItem,
    StockTransaction,
    StockUsageAlert,
    Inventory,
    Disposal
)

from .schedule import Schedule, ScheduleHistory
from .attendance import Attendance

from extensions import db

__all__ = [
    'User',
    'Employee',
    'Supplier',
    'Order',
    'OrderItem',
    'ProductCategory',
    'InventoryStatus',
    'InventoryItem',
    'InventoryBatch',
    'Ingredient',
    'StockItem',
    'StockTransaction',
    'StockUsageAlert',
    'Inventory',
    'Disposal',
    'Schedule',
    'ScheduleHistory',
    'Notification',
    'AlertLog',
    'Attendance',
    'Contract',
    'ContractTemplate',
    'ContractRenewalLog',
    'SignatureLog',
    'WorkEvaluation',
    'TerminationDocument',
    'NotificationSetting',
    'NotificationLog',
    'Payroll',
]

# models 패키지 초기화
# from models.employee import Employee, Contract, Attendance
# from models.schedule import ScheduleHistory
