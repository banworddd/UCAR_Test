from flask import Flask, request, jsonify, Response
import json
import sqlite3
from datetime import datetime, timezone
import os

app = Flask(__name__)
DB_NAME = 'reviews.db'

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()

# Функция анализа тональности для записи отзыва в БД (для эндпоинта POST /reviews
def analyze_sentiment(text: str) -> str:
    text = text.lower()
    positives = ['хорош', 'люблю', 'отличн', 'нравит', 'супер']
    negatives = ['плохо', 'ненавиж', 'ужасн', 'отстой', 'проблем']

    if any(word in text for word in positives):
        return 'positive'
    elif any(word in text for word in negatives):
        return 'negative'
    else:
        return 'neutral'

# Эндпоинт POST /reviews
@app.route('/reviews', methods=['POST'])
def add_review():
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'Missing "text" field'}), 400

    text = data['text']
    sentiment = analyze_sentiment(text)
    created_at = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reviews (text, sentiment, created_at)
        VALUES (?, ?, ?)
    ''', (text, sentiment, created_at))
    conn.commit()
    review_id = cursor.lastrowid
    conn.close()

    result = {
        "id": review_id,
        "text": text,
        "sentiment": sentiment,
        "created_at": created_at
    }

    return Response(
        json.dumps(result, ensure_ascii=False),
        content_type='application/json'
    )

# Запуск приложения
if __name__ == '__main__':
    init_db()
    app.run(debug=True)