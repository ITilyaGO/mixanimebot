import sqlite3

DB_PATH = "bot_data.db"

def init_db():
    """Создает таблицы, если их нет"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        user_tag TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER NOT NULL,
        anime_id TEXT NOT NULL,
        title TEXT NOT NULL,
        likes_count INTEGER DEFAULT 0,
        message_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS permissions (
        user_id INTEGER NOT NULL,
        command TEXT NOT NULL,
        PRIMARY KEY (user_id, command),
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    conn.close()

def add_user(user_id, username, user_tag):
    """Добавляет нового пользователя или обновляет существующего"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO users (user_id, username, user_tag) 
    VALUES (?, ?, ?) 
    ON CONFLICT(user_id) DO UPDATE SET username = excluded.username, user_tag = excluded.user_tag;
    """, (user_id, username, user_tag))

    conn.commit()
    conn.close()

def add_stat(user_id, anime_id, title, message_id, chat_id):
    """Добавляет запись о запросе аниме"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO stats (user_id, anime_id, title, message_id, chat_id) 
    VALUES (?, ?, ?, ?, ?);
    """, (user_id, anime_id, title, message_id, chat_id))

    conn.commit()
    conn.close()

def get_user_stats(user_id):
    """Получает все запросы пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM stats WHERE user_id = ? ORDER BY date DESC;", (user_id,))
    stats = cursor.fetchall()

    conn.close()
    return stats

def get_all_user_stats():
    """Получает количество запросов по всем пользователям"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT users.user_tag, COUNT(stats.user_id) 
    FROM stats 
    JOIN users ON stats.user_id = users.user_id 
    GROUP BY stats.user_id 
    ORDER BY COUNT(stats.user_id) DESC;
    """)
    stats = cursor.fetchall()
    
    conn.close()
    return stats

def add_user_permission(user_id, command):
    """Добавляет право пользователю на выполнение команды"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO permissions (user_id, command) VALUES (?, ?);
    """, (user_id, command))

    conn.commit()
    conn.close()

def get_user_permission(user_id, command):
    """Проверяет, есть ли у пользователя право на выполнение команды"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM permissions WHERE user_id = ? AND command = ?;", (user_id, command))
    result = cursor.fetchone()

    conn.close()
    return result is not None
