import streamlit as st
import psycopg2
from dotenv import load_dotenv
import os
import random
import db_scripts as db

def render_sidebar(conn):
    with st.sidebar:
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
        if "show_login" not in st.session_state:
            st.session_state.show_login = False
        if "username" not in st.session_state:
            st.session_state.username = ""
        if "user_id" not in st.session_state:
            st.session_state.user_id = None
        if st.session_state.logged_in:
            st.write("Профиль")
            st.success(f"Вы вошли как: **{st.session_state.username}**")
            if st.button("Выйти"):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.user_id = None
                st.rerun()
        else:
            if st.button("Войти"):
                st.session_state.show_login = True
            if st.session_state.show_login:
                with st.form("login_form"):
                    name = st.text_input("Введите ваше имя:")
                    submitted = st.form_submit_button("Подтвердить")
                    if submitted:
                        try:
                            user_id = db.login_user(conn, name)
                            if user_id is not None:
                                st.session_state.logged_in = True
                                st.session_state.show_login = False
                                st.session_state.username = name.strip()
                                st.session_state.user_id = user_id
                                st.rerun()
                            else:
                                st.error("Введите корректное имя")
                        except Exception as e:
                            st.error(f"Ошибка базы данных: {e}")

def render_study_tab(conn):
    st.write("Изучаем слова")
    words = db.get_user_words(conn, user_id=st.session_state.user_id)
    r_word, c_word, c_words = db.generate_options(conn, words)
    st.write(f'Слово "{r_word}"')
    st.write("Как будет по-английски?")
    st.write("Выберите перевод:")
    """
    TODO: Реализовать вкладку изучения слов
    - Отображение текущего слова на русском
    - 4 кнопки с вариантами перевода
    - Обработка правильных/неправильных ответов
    - Кнопка следующего слова
    """
    pass
