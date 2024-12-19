import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ContentType, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

# CONFIGURATION
BOT_TOKEN = "8164341939:AAH4BXM2uv0BZJ4fVmzxq87-0OJbjBqw6E8"
ADMIN_IDS = [5183767407]  # Подставьте сюда ID ваших админов

# DATABASE SETUP
conn = sqlite3.connect("shop.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price INTEGER,
    description TEXT
)
""")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    certificate TEXT,
    price INTEGER,
    purchase_date TEXT
)
""")
conn.commit()

# INITIALIZATION
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# STATES
class PurchaseState(StatesGroup):
    waiting_for_certificate = State()
    waiting_for_payment_proof = State()
    waiting_for_payment = State()
    payment_verified = State()

class AdminState(StatesGroup):
    editing_price = State()
    editing_description = State()
    adding_product_name = State()
    adding_product_price = State()
    adding_product_description = State()

# KEYBOARDS
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎁 Выбрать сертификат")],
        [KeyboardButton(text="📞 Поддержка")],
        [KeyboardButton(text="📝 Отзывы")],
        [KeyboardButton(text="⚙ Админ панель")]  # Кнопка для администраторов
    ], resize_keyboard=True
)

certificate_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Обычный сертификат - 600 рублей")],
        [KeyboardButton(text="Парный сертификат - 800 рублей")],
        [KeyboardButton(text="Мгновенный сертификат - 1300 рублей")],
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True
)

pay_button = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 ОПЛАТИТЬ")],
        [KeyboardButton(text="◀ Назад")]
    ], resize_keyboard=True
)

admin_panel_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✏️ Редактировать цены")],
        [KeyboardButton(text="📝 Редактировать описание")],
        [KeyboardButton(text="➕ Добавить новый товар")],
        [KeyboardButton(text="❌ Удалить товар")],
        [KeyboardButton(text="📤 Сделать рассылку")],
        [KeyboardButton(text="👥 Выдать доступ в админ панель")],
        [KeyboardButton(text="◀ Назад")]
    ], resize_keyboard=True
)

# HANDLERS

# Команда /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Добро пожаловать в наш магазин! Выберите нужный пункт:",
        reply_markup=main_menu
    )

# Обработка кнопки "Выбрать сертификат"
@dp.message(lambda message: message.text == "🎁 Выбрать сертификат")
async def choose_certificate(message: types.Message):
    await message.answer("Выберите сертификат:", reply_markup=certificate_menu)

# Обработка выбора сертификата
@dp.message(lambda message: message.text == "Обычный сертификат - 600 рублей")
async def normal_certificate(message: types.Message):
    await message.answer("Вы выбрали Обычный сертификат за 600 рублей. Для оплаты нажмите '💳 ОПЛАТИТЬ'.", reply_markup=pay_button)

@dp.message(lambda message: message.text == "Парный сертификат - 800 рублей")
async def pair_certificate(message: types.Message):
    await message.answer("Вы выбрали Парный сертификат за 800 рублей. Для оплаты нажмите '💳 ОПЛАТИТЬ'.", reply_markup=pay_button)

@dp.message(lambda message: message.text == "Мгновенный сертификат - 1300 рублей")
async def instant_certificate(message: types.Message):
    await message.answer("Вы выбрали Мгновенный сертификат за 1300 рублей. Для оплаты нажмите '💳 ОПЛАТИТЬ'.", reply_markup=pay_button)

@dp.message(lambda message: message.text == "❌ Отмена")
async def cancel(message: types.Message):
    await message.answer("Вы отменили выбор сертификата.", reply_markup=main_menu)

# Обработка кнопки "Поддержка"
@dp.message(lambda message: message.text == "📞 Поддержка")
async def support(message: types.Message):
    await message.answer("Для поддержки напишите нам на почту: support@example.com.")

# Обработка кнопки "Отзывы"
@dp.message(lambda message: message.text == "📝 Отзывы")
async def reviews(message: types.Message):
    await message.answer("Оставьте отзыв на нашем сайте: www.example.com/reviews")

# Админ панель
@dp.message(lambda message: message.text == "⚙ Админ панель" and message.from_user.id in ADMIN_IDS)
async def admin_panel(message: types.Message):
    await message.answer(
        "Добро пожаловать в Админ панель. Выберите действие:",
        reply_markup=admin_panel_menu
    )

# Редактировать цены
@dp.message(lambda message: message.text == "✏️ Редактировать цены" and message.from_user.id in ADMIN_IDS)
async def edit_prices(message: types.Message):
    cursor.execute("SELECT name FROM products")
    products = cursor.fetchall()
    product_names = [product[0] for product in products]

    if not product_names:
        await message.answer("Нет доступных товаров для редактирования.")
        return

    await message.answer("Выберите товар для редактирования цены:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=product_name)] for product_name in product_names] + [[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

    await AdminState.editing_price.set()

# Обработка выбора товара для редактирования цены
@dp.message(State(AdminState.editing_price))
async def choose_product_for_price_edit(message: types.Message, state: FSMContext):
    product_name = message.text.strip()

    cursor.execute("SELECT id, price FROM products WHERE name = ?", (product_name,))
    product = cursor.fetchone()

    if not product:
        await message.answer("Этот товар не найден. Попробуйте снова.")
        return

    await state.update_data(product_id=product[0], old_price=product[1])

    await message.answer(f"Вы выбрали товар: {product_name}. Введите новую цену:")
    await AdminState.editing_price.set()

# Обработка новой цены
@dp.message(State(AdminState.editing_price))
async def update_price(message: types.Message, state: FSMContext):
    try:
        new_price = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите корректную цену.")
        return

    data = await state.get_data()
    product_id = data["product_id"]

    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
    conn.commit()

    await message.answer(f"Цена товара успешно обновлена на {new_price} рублей.")
    await admin_panel(message)

# Редактировать описание
@dp.message(lambda message: message.text == "📝 Редактировать описание" and message.from_user.id in ADMIN_IDS)
async def edit_description(message: types.Message):
    cursor.execute("SELECT name FROM products")
    products = cursor.fetchall()
    product_names = [product[0] for product in products]

    if not product_names:
        await message.answer("Нет доступных товаров для редактирования.")
        return

    await message.answer("Выберите товар для редактирования описания:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=product_name)] for product_name in product_names] + [[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

    await AdminState.editing_description.set()

# Обработка выбора товара для редактирования описания
@dp.message(State(AdminState.editing_description))
async def choose_product_for_description_edit(message: types.Message, state: FSMContext):
    product_name = message.text.strip()

    cursor.execute("SELECT id, description FROM products WHERE name = ?", (product_name,))
    product = cursor.fetchone()

    if not product:
        await message.answer("Этот товар не найден. Попробуйте снова.")
        return

    await state.update_data(product_id=product[0], old_description=product[1])

    await message.answer(f"Вы выбрали товар: {product_name}. Введите новое описание:")
    await AdminState.editing_description.set()

# Обработка нового описания
@dp.message(State(AdminState.editing_description))
async def update_description(message: types.Message, state: FSMContext):
    new_description = message.text.strip()

    data = await state.get_data()
    product_id = data["product_id"]

    cursor.execute("UPDATE products SET description = ? WHERE id = ?", (new_description, product_id))
    conn.commit()

    await message.answer(f"Описание товара успешно обновлено.")
    await admin_panel(message)

# Добавление товара
@dp.message(lambda message: message.text == "➕ Добавить новый товар" and message.from_user.id in ADMIN_IDS)
async def add_product(message: types.Message):
    await message.answer("Введите название товара:")
    await AdminState.adding_product_name.set()

# Добавление названия товара
@dp.message(State(AdminState.adding_product_name))
async def add_product_name(message: types.Message, state: FSMContext):
    product_name = message.text.strip()
    await state.update_data(product_name=product_name)

    await message.answer(f"Введите цену для товара '{product_name}':")
    await AdminState.adding_product_price.set()

# Добавление цены
@dp.message(State(AdminState.adding_product_price))
async def add_product_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text.strip())
    except ValueError:
        await message.answer("Пожалуйста, введите корректную цену.")
        return

    data = await state.get_data()
    product_name = data["product_name"]

    await state.update_data(price=price)

    await message.answer(f"Введите описание для товара '{product_name}':")
    await AdminState.adding_product_description.set()

# Добавление описания
@dp.message(State(AdminState.adding_product_description))
async def add_product_description(message: types.Message, state: FSMContext):
    description = message.text.strip()

    data = await state.get_data()
    product_name = data["product_name"]
    price = data["price"]

    cursor.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)", 
                   (product_name, price, description))
    conn.commit()

    await message.answer(f"Товар '{product_name}' успешно добавлен.")
    await admin_panel(message)

# Run bot
if __name__ == "__main__":
    asyncio.run(dp.start_polling())
