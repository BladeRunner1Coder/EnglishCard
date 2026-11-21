import streamlit as st
import psycopg2
from dotenv import load_dotenv
import os
import random

st.set_page_config(page_title="EnglishCard - Изучение английского", page_icon="📚", layout="wide")
words = [("стол", "table"), ("кресло", "chair"), ("нож", "knife"), ("вилка", "fork"), ("ложка", "spoon"),
         ("комната", "room"), ("стекло", "glass"), ("дерево", "tree"), ("вода", "water"), ("солнце", "sun"),]
load_dotenv()

@st.cache_resource
def get_db_connection():
    conn = psycopg2.connect(host=os.getenv("DB_HOST", "localhost"),
                            database=os.getenv("DB_NAME", "your_db_name"),
                            user=os.getenv("DB_USER", "postgres"),
                            password=os.getenv("DB_PASSWORD", "postgres"),
                            port=os.getenv("DB_PORT", "5431"))
    return conn

@st.cache_resource
def init_database(_conn, word_list):
    try:
        with _conn.cursor() as cur:
            cur.execute('''CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW());''')
            cur.execute('''CREATE TABLE IF NOT EXISTS common_words(id SERIAL PRIMARY KEY,
                        russian_word VARCHAR(50) NOT NULL,
                        english_word VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        UNIQUE(russian_word, english_word));''')
            cur.execute('''CREATE TABLE IF NOT EXISTS user_words(id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        russian_word VARCHAR(50) NOT NULL,
                        english_word VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, russian_word, english_word));''')
            cur.execute('''CREATE TABLE IF NOT EXISTS learning_stats(id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        word_id INTEGER NOT NULL,
                        word_type VARCHAR(50) NOT NULL,
                        correct_answers INTEGER NOT NULL DEFAULT 0,
                        total_attempts INTEGER NOT NULL DEFAULT 0,
                        last_reviewed TIMESTAMP NOT NULL DEFAULT NOW(),
                        CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, word_id, word_type));''')
            if word_list:
                cur.executemany('''INSERT INTO common_words(russian_word, english_word) VALUES(%s, %s)
                                    ON CONFLICT (russian_word, english_word) DO NOTHING;''', word_list)
        _conn.commit()
    except Exception:
        _conn.rollback()
        raise

def login_user(conn, username):
    clean_username = username.strip()
    if not clean_username:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT id FROM users WHERE username = %s;''', (clean_username,))
            row = cur.fetchone()
            if row is not None:
                conn.commit()
                return row[0]
            else:
                cur.execute('''INSERT INTO users(username) VALUES(%s) RETURNING id;''', (clean_username,))
                user_id = cur.fetchone()[0]
                conn.commit()
                return user_id
    except Exception:
        conn.rollback()
        raise

def get_user_words(conn, user_id):
    word_list = []
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT id, russian_word, english_word FROM common_words;''')
            common_words = cur.fetchall()
            for c_w in common_words:
                row = {'id': c_w[0], 'russian_word': c_w[1], 'english_word': c_w[2], 'word_type': 'common'}
                word_list.append(row)
            cur.execute('''SELECT id, russian_word, english_word FROM user_words WHERE user_id = %s;''', (user_id,))
            user_words = cur.fetchall()
            if user_words is not None:
                for u_w in user_words:
                    row = {'id': u_w[0], 'russian_word': u_w[1], 'english_word': u_w[2], 'word_type': 'user'}
                    word_list.append(row)
        conn.commit()
        return word_list
    except Exception:
        conn.rollback()
        raise

def add_personal_word(conn, user_id, russian_word, english_word):
    clean_rus = russian_word.strip()
    clean_eng = english_word.strip()
    if not clean_rus or not clean_eng:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT russian_word, english_word FROM common_words 
            WHERE russian_word = %s AND english_word = %s;''', (clean_rus, clean_eng))
            if cur.fetchone() is not None:
                conn.commit()
                return False
            cur.execute('''SELECT russian_word, english_word FROM user_words WHERE user_id = %s 
            AND russian_word = %s AND english_word = %s;''', (user_id, clean_rus, clean_eng))
            if cur.fetchone() is not None:
                conn.commit()
                return False
            else:
                cur.execute('''INSERT INTO user_words(user_id, russian_word, english_word) 
                VALUES(%s, %s, %s);''', (user_id, clean_rus, clean_eng))
                conn.commit()
                return True
    except Exception:
        conn.rollback()
        raise

def delete_personal_word(conn, user_id, word_id):
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT user_id, id FROM user_words 
                        WHERE user_id = %s AND id = %s;''', (user_id, word_id))
            if cur.fetchone() is not None:
                cur.execute('''DELETE FROM user_words WHERE user_id = %s AND id = %s;''', (user_id, word_id))
                cur.execute('''DELETE FROM learning_stats WHERE user_id = %s AND word_id = %s 
                            AND word_type = 'user';''', (user_id, word_id))
                conn.commit()
                return True
            else:
                conn.commit()
                return False
    except Exception:
        conn.rollback()
        raise

def update_stats(conn, user_id, word_id, word_type, is_correct):
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT user_id, word_id, word_type, correct_answers, total_attempts 
            FROM learning_stats WHERE user_id = %s AND word_id = %s AND word_type = %s;''',
                        (user_id, word_id, word_type))
            row = cur.fetchone()
            if row is None:
                cur.execute('''INSERT INTO learning_stats(user_id, word_id, word_type, correct_answers, 
                total_attempts) VALUES(%s, %s, %s, %s, %s);''', (user_id, word_id, word_type, 1 if is_correct == True else 0, 1))
                conn.commit()
            else:
                cor_answers = row[3]
                t_attempts = row[4] + 1
                cur.execute('''UPDATE learning_stats SET correct_answers = %s, total_attempts = %s, 
                last_reviewed = NOW() WHERE user_id = %s AND word_id = %s AND word_type = %s;''',
                (cor_answers + 1 if is_correct == True else cor_answers, t_attempts, user_id, word_id, word_type))
                conn.commit()
    except Exception:
        conn.rollback()
        raise

def get_statistics(conn, user_id):
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT COUNT(*), SUM(correct_answers), SUM(total_attempts), MAX(last_reviewed) 
                        FROM learning_stats WHERE user_id = %s;''', (user_id, ))
            row = cur.fetchone()
            conn.commit()
            if not row or row[0] == 0:
                return {'id': user_id, 'learned_words': 0, 'correct_answers': 0, 'total_attempts': 0, 'last_reviewed': None}
            else:
                return {'id': user_id, 'learned_words': row[0], 'correct_answers': row[1], 'total_attempts': row[2], 'last_reviewed': row[3]}
    except Exception:
        conn.rollback()
        raise

def generate_options(conn, user_id, russian_word):
    all_words = get_user_words(conn, user_id)
    correct_word = ""
    for word in all_words:
        if russian_word == word['russian_word']:
            correct_word = word['english_word']
    c_words = [correct_word]
    na_words = list({word['english_word'] for word in all_words if word['english_word'] != correct_word})
    n_words = random.sample(range(len(na_words)), 3)
    for n_word in n_words:
        c_words.append(na_words[n_word])
    random.shuffle(c_words)
    return c_words

# con = get_db_connection()
# init_database(con, words)
# login_user(con, "Sergei")
# con.close()
