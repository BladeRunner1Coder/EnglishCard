import streamlit as st
import psycopg2
from dotenv import load_dotenv
import os
import random
import db_scripts as db
import st_scripts as sts

st.set_page_config(page_title="EnglishCard - Изучение английского", page_icon="📚", layout="wide")
st.title("📚 Привет, давайте попрактикуемся в английском языке!")
if "logged_in" not in st.session_state or st.session_state.logged_in == False:
    st.markdown("""
        ### У вас есть возможность использовать тренажёр, как конструктор, 
        ### и собирать свою собственную базу для обучения. 
        ### Для этого слева нажмите кнопку "Войти", введите ваше имя и воспользуйтесь инструментами: 
        ### Добавить слово ➕, Удалить слово 🗑️, Статистика 📚
        ### Ну что, начнём? ⬇️
        """)
st.divider()
load_dotenv()
con = db.get_db_connection()
db.init_database(con, db.words)
sts.render_sidebar(con)
if st.session_state.user_id:
    tab1, tab2, tab3, tab4 = st.tabs(["📖 Изучение", "➕ Добавить слово", "🗑️ Удалить слово", "📊 Статистика"])
    with tab1:
        sts.render_study_tab(con)

st.divider()
if st.button("Схема базы данных"):
    st.image("postgres - english_card - public.png")
    # ... остальные вкладки
# else:
#     st.title("📚 Привет, давай попрактикуемся в английском языке!")
#     st.markdown("""
#     ### У тебя есть возможность использовать тренажёр, как конструктор,
#     ### и собирать свою собственную базу для обучения. Для этого нажми кнопку "Войти", введи своё имя и
#     ### воспрользуйся инструментами: добавить слово ➕, удалить слово 🗑️, статистика 📚
#     ### Ну что, начнём ⬇️
#     """)
    # Приветственное сообщение
    # pass