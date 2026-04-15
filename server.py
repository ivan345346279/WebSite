from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from openai import OpenAI
import os
from datetime import datetime
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import base64
import sqlite3
import json

# Получаем абсолютный путь к директории со скриптом
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'heartai.db')

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = secrets.token_hex(16)

# Инициализация базы данных
def init_db():
    """Создание таблиц в базе данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            nickname TEXT NOT NULL,
            avatar TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    # Таблица чатов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Таблица сообщений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
        )
    ''')

    # Таблица объявлений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            color TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# Инициализируем БД при запуске
init_db()

# Фиксированный пароль для бета-теста (не меняется при перезапуске)
BETA_PASSWORD = os.environ.get('BETA_PASSWORD', '2AE90B79')  # Можно задать через переменную окружения
BETA_END_DATE = datetime(2026, 4, 13, 21, 10, 0)  # 15 апреля 12:00 МСК = 09:00 UTC

def is_beta_active():
    """Проверка активности бета-теста"""
    return datetime.now() < BETA_END_DATE

# Настройки из ai_bot_custom.py
GROQ_API_KEYS = [
    "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",
    "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",
    "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",
]
current_api_key_index = 0

def get_groq_client():
    """Возвращает клиента с текущим API ключом"""
    return OpenAI(
        api_key=GROQ_API_KEYS[current_api_key_index],
        base_url="https://api.groq.com/openai/v1"
    )

client = get_groq_client()

# Хранилище кодов подтверждения (временное, в памяти)
verification_codes = {}  # {email: {'code': str, 'timestamp': datetime}}

# Email настройки - используем Resend API (работает на Railway)
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')  # Получи на resend.com

def send_verification_email(email, code):
    """Отправка кода подтверждения через Resend API"""
    try:
        import requests

        # Если нет API ключа - выводим код в консоль
        if not RESEND_API_KEY:
            print("\n" + "="*60)
            print(f"⚠️ RESEND_API_KEY не настроен - КОД ДЛЯ {email}:")
            print(f"🔑 КОД: {code}")
            print("="*60 + "\n")
            return True  # Возвращаем True чтобы регистрация работала

        # Отправляем через Resend API
        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'from': 'HeartAI <onboarding@resend.dev>',  # Resend тестовый адрес
                'to': [email],
                'subject': 'Код подтверждения HeartAI',
                'html': f'''
                    <h2>Привет!</h2>
                    <p>Твой код подтверждения для регистрации в HeartAI:</p>
                    <h1 style="font-size: 32px; letter-spacing: 5px;">{code}</h1>
                    <p>Код действителен 10 минут.</p>
                    <p>Если ты не регистрировался в HeartAI, просто проигнорируй это письмо.</p>
                    <p>С уважением,<br>Команда HeartAI</p>
                '''
            },
            timeout=10
        )

        if response.status_code == 200:
            print(f"✓ [{datetime.now()}] Email отправлен на {email} через Resend")
            return True
        else:
            print(f"✗ Resend API ошибка: {response.text}")
            # Выводим код в консоль как fallback
            print("\n" + "="*60)
            print(f"⚠️ EMAIL НЕ ОТПРАВЛЕН - КОД ДЛЯ {email}:")
            print(f"🔑 КОД: {code}")
            print("="*60 + "\n")
            return True  # Возвращаем True чтобы регистрация работала

    except Exception as e:
        print(f"✗ Ошибка отправки email: {e}")
        # Выводим код в консоль как fallback
        print("\n" + "="*60)
        print(f"⚠️ EMAIL НЕ ОТПРАВЛЕН - КОД ДЛЯ {email}:")
        print(f"🔑 КОД: {code}")
        print("="*60 + "\n")
        return True  # Возвращаем True чтобы регистрация работала

def get_system_prompt():
    """Возвращает system prompt"""
    return """Ты умный и полезный AI-ассистент. Отвечай КРАТКО, по делу и понятно.

ПРИНЦИПЫ:
- Максимальная краткость
- Структурированность
- Практичность
- Дружелюбие

ДЛИНА ОТВЕТА: максимум 5 строк для полного ответа"""

@app.route('/')
def index():
    """Главная страница"""
    # Проверяем, зарегистрирован ли пользователь
    if 'user_id' not in session:
        return redirect(url_for('register'))

    user_id = session['user_id']

    # Проверяем существование пользователя в БД
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return redirect(url_for('register'))

    return render_template('index.html')

@app.route('/register')
def register():
    """Страница регистрации"""
    # Проверяем бета-доступ
    if is_beta_active():
        # Проверяем есть ли бета-токен в сессии
        if 'beta_access' not in session or not session['beta_access']:
            return render_template('beta.html')

    return render_template('register.html')

@app.route('/api/auth/beta', methods=['POST'])
def check_beta():
    """Проверка бета-пароля"""
    try:
        data = request.json
        password = data.get('password', '').strip().upper()

        if password == BETA_PASSWORD:
            session['beta_access'] = True
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Неверный пароль'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/send-code', methods=['POST'])
def send_code():
    """Отправка кода подтверждения"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'error': 'Введи почту'}), 400

        # Генерируем 6-значный код
        code = str(random.randint(100000, 999999))

        # Отправляем email
        if send_verification_email(email, code):
            verification_codes[email] = {
                'code': code,
                'timestamp': datetime.now()
            }
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Ошибка отправки email'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/verify-code', methods=['POST'])
def verify_code():
    """Проверка кода подтверждения"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()

        if not email or not code:
            return jsonify({'error': 'Неверные данные'}), 400

        if email not in verification_codes:
            return jsonify({'error': 'Код не найден'}), 404

        stored_data = verification_codes[email]

        # Проверяем срок действия (10 минут)
        time_diff = (datetime.now() - stored_data['timestamp']).total_seconds()
        if time_diff > 600:
            del verification_codes[email]
            return jsonify({'error': 'Код истёк'}), 400

        # Проверяем код
        if stored_data['code'] != code:
            return jsonify({'error': 'Неверный код'}), 400

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def complete_registration():
    """Завершение регистрации"""
    try:
        email = request.form.get('email', '').strip().lower()
        code = request.form.get('code', '').strip()
        nickname = request.form.get('nickname', '').strip()

        if not email or not code or not nickname:
            return jsonify({'error': 'Заполни все поля'}), 400

        # Проверяем код ещё раз
        if email not in verification_codes or verification_codes[email]['code'] != code:
            return jsonify({'error': 'Неверный код'}), 400

        # Обработка аватара
        avatar_data = None
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file.filename:
                avatar_data = base64.b64encode(avatar_file.read()).decode('utf-8')

        # Создаём пользователя в БД
        user_id = secrets.token_hex(8)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, email, nickname, avatar, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, email, nickname, avatar_data, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # Удаляем код
        del verification_codes[email]

        # Создаём сессию
        session['user_id'] = user_id

        return jsonify({'success': True, 'user_id': user_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Отправка кода для входа"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'error': 'Введи почту'}), 400

        # Проверяем, существует ли пользователь с такой почтой в БД
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'Пользователь не найден. Зарегистрируйся.'}), 404

        # Генерируем 6-значный код
        code = str(random.randint(100000, 999999))

        # Отправляем email
        if send_verification_email(email, code):
            verification_codes[email] = {
                'code': code,
                'timestamp': datetime.now()
            }
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Ошибка отправки email'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login-verify', methods=['POST'])
def login_verify():
    """Проверка кода для входа"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()

        if not email or not code:
            return jsonify({'error': 'Неверные данные'}), 400

        if email not in verification_codes:
            return jsonify({'error': 'Код не найден'}), 404

        stored_data = verification_codes[email]

        # Проверяем срок действия (10 минут)
        time_diff = (datetime.now() - stored_data['timestamp']).total_seconds()
        if time_diff > 600:
            del verification_codes[email]
            return jsonify({'error': 'Код истёк'}), 400

        # Проверяем код
        if stored_data['code'] != code:
            return jsonify({'error': 'Неверный код'}), 400

        # Находим пользователя в БД
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        # Удаляем код
        del verification_codes[email]

        # Создаём сессию
        session['user_id'] = user[0]

        return jsonify({'success': True, 'user_id': user[0]})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Получить профиль пользователя"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Не авторизован'}), 401

        user_id = session['user_id']

        # Получаем пользователя из БД
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT nickname, email, avatar FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        return jsonify({
            'nickname': user[0],
            'email': user[1],
            'avatar': user[2]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/update', methods=['POST'])
def update_profile():
    """Обновить профиль пользователя"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Не авторизован'}), 401

        user_id = session['user_id']

        nickname = request.form.get('nickname', '').strip()

        if not nickname:
            return jsonify({'error': 'Введи ник'}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Обновляем ник
        cursor.execute('UPDATE users SET nickname = ? WHERE user_id = ?', (nickname, user_id))

        # Обновляем аватар если загружен
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file.filename:
                avatar_data = base64.b64encode(avatar_file.read()).decode('utf-8')
                cursor.execute('UPDATE users SET avatar = ? WHERE user_id = ?', (avatar_data, user_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Выход из аккаунта"""
    try:
        session.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/announcement', methods=['GET'])
def get_announcement():
    """Получить активное объявление"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT text, color FROM announcements WHERE active = 1 ORDER BY id DESC LIMIT 1')
        announcement = cursor.fetchone()
        conn.close()

        if announcement:
            return jsonify({
                'text': announcement[0],
                'color': announcement[1]
            })
        else:
            return jsonify({'text': None})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """API для отправки сообщений"""
    global current_api_key_index, client

    try:
        data = request.json
        message = data.get('message', '')
        chat_id = data.get('chat_id')

        if not message:
            return jsonify({'error': 'Пустое сообщение'}), 400

        if 'user_id' not in session:
            return jsonify({'error': 'Не авторизован'}), 401

        user_id = session['user_id']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Если chat_id не указан, создаем новый чат
        if not chat_id:
            chat_id = secrets.token_hex(8)
            cursor.execute('''
                INSERT INTO chats (chat_id, user_id, title, created_at)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, user_id, message[:30] + ('...' if len(message) > 30 else ''), datetime.now().isoformat()))

            # Добавляем system prompt
            cursor.execute('''
                INSERT INTO messages (chat_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, 'system', get_system_prompt(), datetime.now().isoformat()))

        # Добавляем сообщение пользователя в БД
        cursor.execute('''
            INSERT INTO messages (chat_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, 'user', message, datetime.now().isoformat()))
        conn.commit()

        # Получаем историю сообщений для AI
        cursor.execute('''
            SELECT role, content FROM messages
            WHERE chat_id = ?
            ORDER BY message_id ASC
        ''', (chat_id,))
        messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]

        # Ограничиваем историю (system + последние 20)
        if len(messages) > 21:
            messages = [messages[0]] + messages[-20:]

        conn.close()

        # Получаем ответ от AI
        max_retries = len(GROQ_API_KEYS)

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    max_tokens=3000,
                    temperature=0.7,
                    stream=False
                )

                ai_response = response.choices[0].message.content

                # Сохраняем ответ AI в БД
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO messages (chat_id, role, content, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, 'assistant', ai_response, datetime.now().isoformat()))
                conn.commit()
                conn.close()

                return jsonify({
                    'response': ai_response,
                    'chat_id': chat_id,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                error_str = str(e)

                # Проверяем на ошибки лимита и блокировки
                if any(code in error_str for code in ['429', '401', '403']) or 'rate limit' in error_str.lower() or 'forbidden' in error_str.lower():
                    print(f"⚠️ API ключ #{current_api_key_index + 1} недоступен: {error_str}")

                    if attempt < max_retries - 1:
                        current_api_key_index = (current_api_key_index + 1) % len(GROQ_API_KEYS)
                        client = get_groq_client()
                        print(f"🔄 Переключение на API ключ #{current_api_key_index + 1}")
                        continue
                    else:
                        return jsonify({'error': 'Ты превысил лимиты. Подожди 30 минут.'}), 429
                else:
                    return jsonify({'error': f'Ошибка: {error_str}'}), 500

        return jsonify({'error': 'Не удалось получить ответ'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chats', methods=['GET'])
def get_chats():
    """Получить список чатов"""
    try:
        if 'user_id' not in session:
            return jsonify({'chats': []})

        user_id = session['user_id']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT chat_id, title, created_at
            FROM chats
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))

        chats_list = []
        for row in cursor.fetchall():
            chats_list.append({
                'id': row[0],
                'title': row[1],
                'created': row[2]
            })

        conn.close()

        return jsonify({
            'chats': chats_list,
            'active_chat': None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Получить историю конкретного чата"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Нет сессии'}), 401

        user_id = session['user_id']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Проверяем что чат принадлежит пользователю
        cursor.execute('SELECT title FROM chats WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        chat = cursor.fetchone()

        if not chat:
            conn.close()
            return jsonify({'error': 'Чат не найден'}), 404

        # Получаем сообщения без system prompt
        cursor.execute('''
            SELECT role, content FROM messages
            WHERE chat_id = ? AND role != 'system'
            ORDER BY message_id ASC
        ''', (chat_id,))

        messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'messages': messages,
            'title': chat[0]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<chat_id>/rename', methods=['POST'])
def rename_chat(chat_id):
    """Переименовать чат"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Нет сессии'}), 401

        user_id = session['user_id']
        data = request.json
        new_title = data.get('title', '').strip()

        if not new_title:
            return jsonify({'error': 'Пустое название'}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Обновляем название чата
        cursor.execute('''
            UPDATE chats SET title = ?
            WHERE chat_id = ? AND user_id = ?
        ''', (new_title, chat_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Чат не найден'}), 404

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Удалить чат"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Нет сессии'}), 401

        user_id = session['user_id']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Удаляем сообщения чата
        cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))

        # Удаляем сам чат
        cursor.execute('DELETE FROM chats WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Создать новый чат"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Не авторизован'}), 401

        user_id = session['user_id']

        # Создаем новый чат в БД
        chat_id = secrets.token_hex(8)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chats (chat_id, user_id, title, created_at)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, user_id, 'Новый чат', datetime.now().isoformat()))

        # Добавляем system prompt
        cursor.execute('''
            INSERT INTO messages (chat_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, 'system', get_system_prompt(), datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'chat_id': chat_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

        return jsonify({'success': True, 'chat_id': chat_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mode', methods=['POST'])
def change_mode():
    """Устаревший endpoint для совместимости"""
    return jsonify({'success': True})

@app.route('/api/admin/download-db', methods=['GET'])
def download_db():
    """Скачать базу данных (только для админа)"""
    try:
        # Простая защита паролем
        auth_password = request.args.get('password')
        if auth_password != BETA_PASSWORD:
            return jsonify({'error': 'Неверный пароль'}), 401

        from flask import send_file
        return send_file(DB_PATH, as_attachment=True, download_name='heartai.db')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import sys
    import io

    # Исправление кодировки для Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("🚀 Запуск веб-сервера...")
    print("🌐 Открой в браузере: http://localhost:5000")
    print(f"⏰ {datetime.now()}")
    print(f"⚡ Модель: llama-3.3-70b-versatile")

    # Показываем бета-пароль если бета активна
    if is_beta_active():
        print("\n" + "="*60)
        print("🔒 БЕТА-ТЕСТ АКТИВЕН")
        print(f"🔑 Бета-пароль: {BETA_PASSWORD}")
        print(f"⏳ Окончание: 15 апреля 2026, 12:00 МСК")
        print("="*60 + "\n")
    else:
        print("\n✅ Бета-тест завершён. Регистрация открыта для всех.\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
