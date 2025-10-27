# Импорт необходимых модулей Flask и расширений
from flask import Flask, render_template, redirect, request, jsonify
from flask_cors import CORS
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# Конфигурация Flask приложения
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'  # Путь к базе данных SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключение отслеживания изменений для производительности
app.config['JWT_SECRET_KEY'] = "secret-key-here"  # Секретный ключ для JWT токенов
CORS(app)  # Включение CORS для всех маршрутов (разрешает запросы с фронтенда)
port = int(os.environ.get("PORT", 10000))
# Инициализация расширений Flask
bcrypt = Bcrypt(app)  # Для безопасного хеширования паролей пользователей
jwt = JWTManager(app)  # Для управления JWT токенами аутентификации

# Инициализация базы данных SQLAlchemy
db = SQLAlchemy(app)

# Модель базы данных для пользователей системы
class User(db.Model):
    # Основные поля пользователя для аутентификации и профиля
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор пользователя
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email пользователя (уникальный)
    password_hash = db.Column(db.String(128), nullable=False)  # Хеш пароля для безопасности
    first_name = db.Column(db.String(50))  # Имя пользователя
    last_name = db.Column(db.String(50))  # Фамилия пользователя
    phone = db.Column(db.String(20))  # Номер телефона
    is_admin = db.Column(db.Boolean, default=False)  # Флаг администратора системы
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата регистрации пользователя

    # Связи с другими моделями базы данных
    orders = db.relationship('Order', backref='user', lazy=True)  # Связь с заказами пользователя
    basket_items = db.relationship('BasketItem', backref='user', lazy=True)  # Связь с элементами корзины

    # Метод для преобразования объекта пользователя в словарь (без чувствительных данных)
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Модель заказа пользователя
class Order(db.Model):
    # Основные поля заказа для обработки покупок
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор заказа
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ID пользователя, сделавшего заказ
    total_amount = db.Column(db.Float, nullable=False)  # Общая сумма заказа в рублях
    status = db.Column(db.String(20), default='pending')  # Статус заказа (pending, confirmed, shipped, delivered)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата и время создания заказа

    # Связь с элементами заказа (товары в заказе)
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

# Модель элемента заказа (конкретный товар в заказе)
class OrderItem(db.Model):
    # Поля для описания конкретного товара в заказе
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор элемента заказа
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)  # ID заказа, к которому относится элемент
    sneaker_id = db.Column(db.Integer, db.ForeignKey('sneaker.id'), nullable=False)  # ID товара (кроссовок)
    size = db.Column(db.Float, nullable=False)  # Размер выбранного товара
    quantity = db.Column(db.Integer, nullable=False)  # Количество единиц товара
    price = db.Column(db.Float, nullable=False)  # Цена за единицу товара на момент заказа

# Модель корзины для хранения товаров пользователя
class BasketItem(db.Model):
    # Поля для элементов корзины пользователя
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор элемента корзины
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ID пользователя, которому принадлежит корзина
    sneaker_id = db.Column(db.Integer, db.ForeignKey('sneaker.id'), nullable=False)  # ID товара в корзине
    size = db.Column(db.Float, nullable=False)  # Размер выбранного товара
    quantity = db.Column(db.Integer, nullable=False, default=1)  # Количество товара в корзине
    added_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата добавления товара в корзину

    # Метод для преобразования объекта корзины в словарь
    def to_dict(self):
        sneaker = Sneaker.query.get(self.sneaker_id)
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sneaker_id': self.sneaker_id,
            'size': self.size,
            'quantity': self.quantity,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'product': sneaker.to_dict() if sneaker else None
        }

# Модель кроссовок (товаров в каталоге)
class Sneaker(db.Model):
    # Основные поля товара для каталога кроссовок
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор товара
    brand = db.Column(db.String(50), nullable=False)  # Бренд производителя (Nike, Adidas, etc.)
    model = db.Column(db.String(100), nullable=False)  # Название модели (Air Force 1, Gazelle, etc.)
    size = db.Column(db.Float, nullable=False)  # Размер обуви (европейский)
    color_name = db.Column(db.String(50), nullable=False)  # Название цвета (Black/Red, White, etc.)
    color_code = db.Column(db.String(7))  # HEX код цвета для отображения

    # Ценовая информация товара
    price = db.Column(db.Float, nullable=False)  # Цена товара в рублях

    # Подробное описание и характеристики товара
    description = db.Column(db.Text)  # Детальное описание товара
    category = db.Column(db.String(50))  # Категория товара (Running, Basketball, Casual, etc.)
    gender = db.Column(db.String(20))  # Пол (Men, Women, Kids)

    # Статус доступности товара
    in_stock = db.Column(db.Boolean, default=True)  # Флаг наличия товара на складе
    condition = db.Column(db.String(20), default='New')  # Состояние товара (New, Used, etc.)

    # Медиа и дополнительные данные товара
    image_url = db.Column(db.String(200))  # URL изображения товара
    release_year = db.Column(db.Integer)  # Год выпуска модели
    sku = db.Column(db.String(50))  # Артикул товара (Stock Keeping Unit)
    
    # Метод для преобразования объекта в словарь (для API)
    def to_dict(self):
        return {
            'id': self.id,
            'brand': self.brand,
            'model': self.model,
            'size': self.size,
            'color_name': self.color_name,
            'color_code': self.color_code,
            'price': self.price,
            'description': self.description,
            'category': self.category,
            'gender': self.gender,
            'in_stock': self.in_stock,
            'condition': self.condition,
            'image_url': self.image_url,
            'release_year': self.release_year,
            'sku': self.sku
        }

# API маршруты для аутентификации пользователей

@app.route('/auth/register', methods=['POST'])
def register():
    """Регистрация нового пользователя в системе"""
    data = request.get_json()

    # Валидация обязательных полей для регистрации
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email и пароль обязательны'}), 400

    # Проверка на существование пользователя с таким email
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 400

    # Создание нового пользователя с хешированием пароля
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        email=data['email'],
        password_hash=hashed_password,
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        phone=data.get('phone')
    )

    # Сохранение пользователя в базе данных
    db.session.add(new_user)
    db.session.commit()

    # Генерация JWT токена для автоматического входа после регистрации
    access_token = create_access_token(identity=new_user.id)

    return jsonify({
        'message': 'Пользователь успешно зарегистрирован',
        'access_token': access_token,
        'user': new_user.to_dict()
    }), 201

@app.route('/auth/login', methods=['POST'])
def login():
    """Аутентификация пользователя и вход в систему"""
    data = request.get_json()

    # Проверка наличия обязательных полей
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email и пароль обязательны'}), 400

    # Поиск пользователя в базе данных по email
    user = User.query.filter_by(email=data['email']).first()

    # Проверка существования пользователя и корректности пароля
    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Неверный email или пароль'}), 401

    # Генерация JWT токена для сессии пользователя
    access_token = create_access_token(identity=user.id)

    return jsonify({
        'message': 'Вход выполнен успешно',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@app.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Получение данных профиля текущего аутентифицированного пользователя"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    return jsonify(user.to_dict()), 200

@app.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Обновление данных профиля текущего пользователя"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()

    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404

    # Обновление разрешенных полей профиля
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone' in data:
        user.phone = data['phone']

    # Сохранение изменений в базе данных
    db.session.commit()

    return jsonify({
        'message': 'Профиль обновлен',
        'user': user.to_dict()
    }), 200

# API маршруты для работы с каталогом товаров

@app.route('/catalog', methods=['GET'])
def get_products():
    """Получить список всех товаров из каталога кроссовок"""
    items = Sneaker.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/catalog/<int:item_id>', methods=['GET'])
def get_product(item_id):
    """Получить детальную информацию о конкретном товаре по его ID"""
    item = Sneaker.query.get(item_id)
    if item:
        return jsonify(item.to_dict())
    return jsonify({'error': 'Товар не найден'}), 404

# API маршруты для работы с корзиной пользователя

@app.route('/basket', methods=['GET'])
@jwt_required()
def get_basket():
    """Получить содержимое корзины текущего пользователя"""
    user_id = get_jwt_identity()
    basket_items = BasketItem.query.filter_by(user_id=user_id).all()
    return jsonify([item.to_dict() for item in basket_items])

@app.route('/basket', methods=['POST'])
@jwt_required()
def add_to_basket():
    """Добавить товар в корзину пользователя"""
    user_id = get_jwt_identity()
    data = request.get_json()

    # Проверка обязательных полей
    if not data.get('sneaker_id') or not data.get('size'):
        return jsonify({'error': 'ID товара и размер обязательны'}), 400

    # Проверка существования товара
    sneaker = Sneaker.query.get(data['sneaker_id'])
    if not sneaker:
        return jsonify({'error': 'Товар не найден'}), 404

    # Поиск существующего товара в корзине
    existing_item = BasketItem.query.filter_by(
        user_id=user_id,
        sneaker_id=data['sneaker_id'],
        size=data['size']
    ).first()

    if existing_item:
        # Увеличение количества существующего товара
        existing_item.quantity += data.get('quantity', 1)
    else:
        # Создание нового элемента корзины
        new_item = BasketItem(
            user_id=user_id,
            sneaker_id=data['sneaker_id'],
            size=data['size'],
            quantity=data.get('quantity', 1)
        )
        db.session.add(new_item)

    db.session.commit()
    return jsonify({'message': 'Товар добавлен в корзину'}), 201

@app.route('/basket/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_basket_item(item_id):
    """Обновить количество товара в корзине"""
    user_id = get_jwt_identity()
    data = request.get_json()

    item = BasketItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({'error': 'Элемент корзины не найден'}), 404

    if 'quantity' in data:
        if data['quantity'] <= 0:
            # Удаление товара из корзины при количестве <= 0
            db.session.delete(item)
        else:
            item.quantity = data['quantity']

    db.session.commit()
    return jsonify({'message': 'Корзина обновлена'}), 200

@app.route('/basket/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_basket(item_id):
    """Удалить товар из корзины"""
    user_id = get_jwt_identity()

    item = BasketItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({'error': 'Элемент корзины не найден'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Товар удален из корзины'}), 200

@app.route('/basket', methods=['DELETE'])
@jwt_required()
def clear_basket():
    """Очистить всю корзину пользователя"""
    user_id = get_jwt_identity()

    BasketItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({'message': 'Корзина очищена'}), 200

# Запуск Flask приложения и инициализация базы данных
if __name__ == '__main__':
    with app.app_context():
        # Создание всех таблиц базы данных на основе моделей
        db.create_all()

        # Создание учетной записи администратора при первом запуске
        if not User.query.filter_by(email='admin@admin.com').first():
            print("👤 Создание учетной записи администратора...")
            admin_password = bcrypt.generate_password_hash('admin').decode('utf-8')
            admin_user = User(
                email='admin@admin.com',
                password_hash=admin_password,
                first_name='Администратор',
                last_name='Системы',
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Администратор создан: admin@admin.com / admin")

        # Заполнение каталога начальными товарами при первом запуске
        if Sneaker.query.count() == 0:
            print("📦 Заполнение базы данных товарами...")

            # Список товаров для начального заполнения каталога
            sneakers = [
                # Мужские кроссовки
                Sneaker(
                    brand="Nike",
                    model="Air Jordan 1 Retro High",
                    size=42.0,
                    color_name="Black/Red",
                    price=18999,
                    description="Культовая баскетбольная модель 1985 года. Высокое качество материалов.",
                    category="Basketball",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1600269452121-4f2416e55c28?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Adidas",
                    model="Yeezy Boost 350 V2",
                    size=43.5,
                    color_name="Zebra",
                    price=25999,
                    description="Лимитированная модель от Kanye West. Технология Boost для максимального комфорта.",
                    category="Lifestyle",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1560769624-6b03633ba29e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2022
                ),
                Sneaker(
                    brand="Nike",
                    model="Dunk Low Retro",
                    size=41.0,
                    color_name="Panda",
                    price=12999,
                    description="Классические кроссовки для скейтбординга. Универсальный черно-белый дизайн.",
                    category="Skateboarding",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="New Balance",
                    model="550",
                    size=44.0,
                    color_name="White/Green",
                    price=14999,
                    description="Ретро-баскетбольные кроссовки. Премиальная кожа и замша.",
                    category="Lifestyle",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2022
                ),
                Sneaker(
                    brand="Nike",
                    model="Air Force 1 Low",
                    size=42.5,
                    color_name="Triple White",
                    price=10999,
                    description="Легендарные кроссовки 1982 года. Чистый белый цвет на каждый день.",
                    category="Casual",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Nike",
                    model="Air Max 97",
                    size=44.5,
                    color_name="Silver Bullet",
                    price=16999,
                    description="Футуристичный дизайн вдохновлен японскими скоростными поездами.",
                    category="Running",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1605348532760-6753d2c43329?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2022
                ),
                Sneaker(
                    brand="Nike",
                    model="Blazer Mid '77",
                    size=42.0,
                    color_name="Vintage White",
                    price=11999,
                    description="Винтажный баскетбольный стиль. Универсальная модель.",
                    category="Casual",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1560769624-6b03633ba29e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Reebok",
                    model="Classic Leather",
                    size=43.0,
                    color_name="White",
                    price=7999,
                    description="Легендарные кроссовки 1983 года. Мягкая кожа и комфорт.",
                    category="Lifestyle",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),

                # Женские кроссовки
                Sneaker(
                    brand="Nike",
                    model="Air Force 1 '07",
                    size=38.0,
                    color_name="White/Pink",
                    price=9999,
                    description="Иконические кроссовки в нежном розовом цвете. Идеально для повседневного образа.",
                    category="Casual",
                    gender="Women",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1549298916-b41d501d3772?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Adidas",
                    model="Stan Smith",
                    size=37.5,
                    color_name="White/Green",
                    price=8999,
                    description="Классические теннисные кроссовки. Минималистичный дизайн и комфорт.",
                    category="Casual",
                    gender="Women",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Nike",
                    model="React Element 55",
                    size=39.0,
                    color_name="Light Cream",
                    price=11999,
                    description="Стильные кроссовки с амортизацией React. Элегантный бежевый цвет.",
                    category="Lifestyle",
                    gender="Women",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1560769624-6b03633ba29e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Puma",
                    model="RS-X³ Puzzle",
                    size=38.5,
                    color_name="Pink/White",
                    price=13999,
                    description="Яркие кроссовки в стиле 90-х. Комфорт и индивидуальность.",
                    category="Lifestyle",
                    gender="Women",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Adidas",
                    model="Superstar",
                    size=37.0,
                    color_name="Black/White",
                    price=10999,
                    description="Легендарные кроссовки с тремя полосками. Классика уличной моды.",
                    category="Casual",
                    gender="Women",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Nike",
                    model="Cortez",
                    size=38.0,
                    color_name="White/Purple",
                    price=9999,
                    description="Ретро-бегущие кроссовки. Комфорт и стиль в одном.",
                    category="Running",
                    gender="Women",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),

                # Детские кроссовки
                Sneaker(
                    brand="Nike",
                    model="Air Max 90",
                    size=32.0,
                    color_name="Black/White",
                    price=7999,
                    description="Классические кроссовки с воздушной подушкой. Для активных детей.",
                    category="Casual",
                    gender="Kids",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1605348532760-6753d2c43329?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Adidas",
                    model="Gazelle Kids",
                    size=31.0,
                    color_name="Blue/White",
                    price=6999,
                    description="Маленькая копия классики. Качественные материалы для детей.",
                    category="Casual",
                    gender="Kids",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Puma",
                    model="Suede Classic Kids",
                    size=30.5,
                    color_name="Red/White",
                    price=5999,
                    description="Яркие кроссовки для маленьких модников. Комфорт и стиль.",
                    category="Casual",
                    gender="Kids",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1560769624-6b03633ba29e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Nike",
                    model="Force 1 Low Kids",
                    size=29.0,
                    color_name="White/Blue",
                    price=6999,
                    description="Детская версия легенды. Качественные материалы и комфорт.",
                    category="Casual",
                    gender="Kids",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Adidas",
                    model="Superstar Kids",
                    size=28.0,
                    color_name="White/Black",
                    price=6499,
                    description="Маленькие звездочки уличной моды. Для самых маленьких.",
                    category="Casual",
                    gender="Kids",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),

                # Дополнительные мужские
                Sneaker(
                    brand="Adidas",
                    model="Ultraboost 22",
                    size=43.0,
                    color_name="Black",
                    price=18999,
                    description="Профессиональные беговые кроссовки с технологией Boost.",
                    category="Running",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Nike",
                    model="Pegasus 39",
                    size=42.0,
                    color_name="Black/White",
                    price=12999,
                    description="Универсальные беговые кроссовки для тренировок.",
                    category="Running",
                    gender="Men",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),

                # Дополнительные женские
                Sneaker(
                    brand="Nike",
                    model="Zoom Pegasus Turbo",
                    size=38.5,
                    color_name="Pink/Black",
                    price=14999,
                    description="Быстрые беговые кроссовки для женщин. Максимальная амортизация.",
                    category="Running",
                    gender="Women",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1560769624-6b03633ba29e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                ),
                Sneaker(
                    brand="Adidas",
                    model="NMD_R1",
                    size=37.5,
                    color_name="White/Pink",
                    price=15999,
                    description="Современные кроссовки с технологией Boost. Урбанистический стиль.",
                    category="Lifestyle",
                    gender="Women",
                    in_stock=True,
                    condition="New",
                    image_url="https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80",
                    release_year=2023
                )
            ]

            # Массовое добавление товаров в базу данных
            db.session.add_all(sneakers)
            db.session.commit()
            print("✅ 25 кроссовок добавлены в базу данных!")

    # Запуск Flask сервера в режиме разработки с автоматической перезагрузкой
    print("🚀 Запуск сервера на http://127.0.0.1:5000")
    app.run(debug=True)
