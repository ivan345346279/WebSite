import sqlite3
import os
from datetime import datetime

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'heartai.db')

def format_date(date_str):
    """Форматирование даты"""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return date_str

def show_users():
    """Показать всех пользователей"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT user_id, email, nickname, created_at FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()

    if not users:
        print("Нет пользователей в базе данных")
        conn.close()
        return

    print("\n" + "="*80)
    print("ПОЛЬЗОВАТЕЛИ")
    print("="*80)

    for user in users:
        user_id, email, nickname, created_at = user

        # Получаем количество чатов пользователя
        cursor.execute('SELECT COUNT(*) FROM chats WHERE user_id = ?', (user_id,))
        chat_count = cursor.fetchone()[0]

        # Получаем количество сообщений пользователя
        cursor.execute('''
            SELECT COUNT(*) FROM messages
            WHERE chat_id IN (SELECT chat_id FROM chats WHERE user_id = ?)
            AND role = 'user'
        ''', (user_id,))
        message_count = cursor.fetchone()[0]

        print(f"\nUser ID:      {user_id}")
        print(f"Email:        {email}")
        print(f"Nickname:     {nickname}")
        print(f"Создан:       {format_date(created_at)}")
        print(f"Чатов:        {chat_count}")
        print(f"Сообщений:    {message_count}")
        print("-" * 80)

    conn.close()
    print(f"\nВсего пользователей: {len(users)}\n")

def show_user_details(user_id):
    """Показать детальную информацию о пользователе"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT user_id, email, nickname, created_at FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        print(f"Пользователь с ID {user_id} не найден")
        conn.close()
        return

    user_id, email, nickname, created_at = user

    print("\n" + "="*80)
    print(f"ПОЛЬЗОВАТЕЛЬ: {nickname}")
    print("="*80)
    print(f"User ID:      {user_id}")
    print(f"Email:        {email}")
    print(f"Nickname:     {nickname}")
    print(f"Создан:       {format_date(created_at)}")

    # Получаем чаты пользователя
    cursor.execute('SELECT chat_id, title, created_at FROM chats WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    chats = cursor.fetchall()

    print(f"\nЧатов:        {len(chats)}")

    if chats:
        print("\nСПИСОК ЧАТОВ:")
        print("-" * 80)
        for chat in chats:
            chat_id, title, chat_created = chat

            # Получаем количество сообщений в чате
            cursor.execute('SELECT COUNT(*) FROM messages WHERE chat_id = ? AND role != "system"', (chat_id,))
            msg_count = cursor.fetchone()[0]

            print(f"\nChat ID:      {chat_id}")
            print(f"Название:     {title}")
            print(f"Создан:       {format_date(chat_created)}")
            print(f"Сообщений:    {msg_count}")

    conn.close()
    print("\n")

def show_all_chats():
    """Показать все чаты"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.chat_id, c.title, c.created_at, u.nickname, u.email
        FROM chats c
        JOIN users u ON c.user_id = u.user_id
        ORDER BY c.created_at DESC
    ''')
    chats = cursor.fetchall()

    if not chats:
        print("Нет чатов в базе данных")
        conn.close()
        return

    print("\n" + "="*80)
    print("ВСЕ ЧАТЫ")
    print("="*80)

    for chat in chats:
        chat_id, title, created_at, nickname, email = chat

        # Получаем количество сообщений
        cursor.execute('SELECT COUNT(*) FROM messages WHERE chat_id = ? AND role != "system"', (chat_id,))
        msg_count = cursor.fetchone()[0]

        print(f"\nChat ID:      {chat_id}")
        print(f"Название:     {title}")
        print(f"Пользователь: {nickname} ({email})")
        print(f"Создан:       {format_date(created_at)}")
        print(f"Сообщений:    {msg_count}")
        print("-" * 80)

    conn.close()
    print(f"\nВсего чатов: {len(chats)}\n")

def show_stats():
    """Показать статистику"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Общая статистика
    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM chats')
    chats_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM messages WHERE role = "user"')
    user_messages = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM messages WHERE role = "assistant"')
    ai_messages = cursor.fetchone()[0]

    print("\n" + "="*80)
    print("СТАТИСТИКА")
    print("="*80)
    print(f"\nПользователей:        {users_count}")
    print(f"Чатов:                {chats_count}")
    print(f"Сообщений от юзеров:  {user_messages}")
    print(f"Ответов AI:           {ai_messages}")
    print(f"Всего сообщений:      {user_messages + ai_messages}")

    if users_count > 0:
        print(f"\nСреднее чатов на юзера:     {chats_count / users_count:.1f}")
        print(f"Среднее сообщений на юзера: {user_messages / users_count:.1f}")

    conn.close()
    print("\n")

def show_announcements():
    """Показать все объявления"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT id, text, color, active, created_at FROM announcements ORDER BY id DESC')
    announcements = cursor.fetchall()

    if not announcements:
        print("\nНет объявлений в базе данных")
        conn.close()
        return

    print("\n" + "="*80)
    print("ОБЪЯВЛЕНИЯ")
    print("="*80)

    for ann in announcements:
        ann_id, text, color, active, created_at = ann
        status = "✓ Активно" if active else "✗ Неактивно"

        print(f"\nID:           {ann_id}")
        print(f"Текст:        {text}")
        print(f"Цвет:         {color}")
        print(f"Статус:       {status}")
        print(f"Создано:      {format_date(created_at)}")
        print("-" * 80)

    conn.close()
    print(f"\nВсего объявлений: {len(announcements)}\n")

def create_announcement():
    """Создать новое объявление"""
    print("\n" + "="*80)
    print("СОЗДАНИЕ ОБЪЯВЛЕНИЯ")
    print("="*80)

    text = input("\nВведи текст объявления: ").strip()
    if not text:
        print("Текст не может быть пустым")
        return

    print("\nДоступные цвета:")
    print("1. Красный (#dc2626)")
    print("2. Оранжевый (#ea580c)")
    print("3. Жёлтый (#ca8a04)")
    print("4. Зелёный (#16a34a)")
    print("5. Синий (#2563eb)")
    print("6. Фиолетовый (#9333ea)")
    print("7. Розовый (#db2777)")
    print("8. Серый (#6b7280)")

    color_choice = input("\nВыбери цвет (1-8): ").strip()

    colors = {
        '1': '#dc2626',
        '2': '#ea580c',
        '3': '#ca8a04',
        '4': '#16a34a',
        '5': '#2563eb',
        '6': '#9333ea',
        '7': '#db2777',
        '8': '#6b7280'
    }

    color = colors.get(color_choice, '#2563eb')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Деактивируем все предыдущие объявления
    cursor.execute('UPDATE announcements SET active = 0')

    # Создаём новое объявление
    cursor.execute('''
        INSERT INTO announcements (text, color, active, created_at)
        VALUES (?, ?, 1, ?)
    ''', (text, color, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    print(f"\n✓ Объявление создано и активировано!")
    print(f"Текст: {text}")
    print(f"Цвет: {color}\n")

def toggle_announcement():
    """Активировать/деактивировать объявление"""
    show_announcements()

    ann_id = input("\nВведи ID объявления для переключения: ").strip()

    if not ann_id.isdigit():
        print("Неверный ID")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT active FROM announcements WHERE id = ?', (int(ann_id),))
    result = cursor.fetchone()

    if not result:
        print("Объявление не найдено")
        conn.close()
        return

    current_active = result[0]
    new_active = 0 if current_active else 1

    # Если активируем, деактивируем все остальные
    if new_active:
        cursor.execute('UPDATE announcements SET active = 0')

    cursor.execute('UPDATE announcements SET active = ? WHERE id = ?', (new_active, int(ann_id)))
    conn.commit()
    conn.close()

    status = "активировано" if new_active else "деактивировано"
    print(f"\n✓ Объявление {status}!\n")

def delete_announcement():
    """Удалить объявление"""
    show_announcements()

    ann_id = input("\nВведи ID объявления для удаления: ").strip()

    if not ann_id.isdigit():
        print("Неверный ID")
        return

    confirm = input(f"Удалить объявление #{ann_id}? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Отменено")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM announcements WHERE id = ?', (int(ann_id),))
    conn.commit()
    conn.close()

    print(f"\n✓ Объявление удалено!\n")

def main():
    """Главное меню"""
    if not os.path.exists(DB_PATH):
        print(f"База данных не найдена: {DB_PATH}")
        return

    while True:
        print("\n" + "="*80)
        print("HEARTAI - ПРОСМОТР ДАННЫХ")
        print("="*80)
        print("\n1. Показать всех пользователей")
        print("2. Показать детали пользователя")
        print("3. Показать все чаты")
        print("4. Показать статистику")
        print("5. Показать объявления")
        print("6. Создать объявление")
        print("7. Активировать/деактивировать объявление")
        print("8. Удалить объявление")
        print("9. Выход")

        choice = input("\nВыбери опцию (1-9): ").strip()

        if choice == '1':
            show_users()
        elif choice == '2':
            user_id = input("Введи User ID: ").strip()
            show_user_details(user_id)
        elif choice == '3':
            show_all_chats()
        elif choice == '4':
            show_stats()
        elif choice == '5':
            show_announcements()
        elif choice == '6':
            create_announcement()
        elif choice == '7':
            toggle_announcement()
        elif choice == '8':
            delete_announcement()
        elif choice == '9':
            print("\nВыход...")
            break
        else:
            print("\nНеверный выбор. Попробуй снова.")

if __name__ == '__main__':
    main()
