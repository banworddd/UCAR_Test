from flask import Flask, request, jsonify, Response
import json
import sqlite3
from datetime import datetime, timezone


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

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON format'}), 400

    text = data.get('text')
    if text is None:
        return jsonify({'error': 'Missing "text" field'}), 400

    if not isinstance(text, str) or not text.strip():
        return jsonify({'error': '"text" field cannot be empty'}), 400

    sentiment =  data.get('sentiment') or analyze_sentiment(text)
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

# Эндпоинт GET /reviews
# TODO Дописать фильтрацию по другим тональностям в отзыве (neutral, positive)
@app.route('/reviews', methods=['GET'])
def get_reviews():
    sentiment_filter = request.args.get('sentiment')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if sentiment_filter:
        cursor.execute('SELECT * FROM reviews WHERE sentiment = ?', (sentiment_filter,))
    else:
        cursor.execute('SELECT * FROM reviews')

    rows = cursor.fetchall()
    conn.close()

    reviews = [dict(row) for row in rows]

    return Response(
        json.dumps(reviews, ensure_ascii=False),
        content_type='application/json'
    )

# Запуск приложения
if __name__ == '__main__':
    init_db()
    app.run(debug=True)