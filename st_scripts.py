import streamlit as st
import psycopg2
from dotenv import load_dotenv
import os
import random
import db_scripts as db
import re
from datetime import datetime

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
    try:
        words = db.get_user_words(conn, st.session_state.user_id)
    except Exception as e:
        st.error(f"Ошибка базы данных: {e}")
        return
    if "options" not in st.session_state:
        st.session_state.options = db.generate_options(words)
        st.session_state.answer_status = None
    id_word, r_word, c_word, type_word, c_words = st.session_state.options
    st.write(f'Слово "{r_word}"')
    st.write("Как будет по-английски?")
    st.write("Выберите перевод:")
    is_solved = st.session_state.answer_status is True
    with st.container(horizontal=True, horizontal_alignment="left"):
        for i, option in enumerate(c_words):
            if st.button(option, key=f"option_{i}", disabled=is_solved):
                is_correct = (option == c_word)
                st.session_state.answer_status = is_correct
                try:
                    db.update_stats(conn, st.session_state.user_id, id_word, type_word, is_correct)
                except Exception as e:
                    st.error(f"Не удалось сохранить статистику: {e}")
                if st.session_state.answer_status:
                    st.rerun()
    if st.session_state.answer_status is True:
        st.success("Правильный ответ!")
    elif st.session_state.answer_status is False:
        st.error("Неправильный ответ! Попробуйте ещё раз!")
    if st.button("Следующее слово"):
        st.session_state.options = db.generate_options(words)
        st.session_state.answer_status = None
        st.rerun()

def render_add_word_tab(conn):
    if st.session_state.pop("clear_add_form", False):
        st.session_state.add_r_word = ""
        st.session_state.add_e_word = ""
    with st.form("add_word_form", clear_on_submit=False):
        r_word = st.text_input("Введите русское слово:", key="add_r_word")
        e_word = st.text_input("Введите английское слово:", key="add_e_word")
        submitted = st.form_submit_button("Добавить в базу данных")
    if submitted:
        r_clean = r_word.strip().lower()
        e_clean = e_word.strip().lower()
        if not r_clean or not e_clean:
            st.warning("Пожалуйста, заполните оба поля.")
            return
        if not re.fullmatch(r"[А-Яа-яЁё\s-]+", r_clean):
            st.warning("Русское слово должно содержать только кириллицу.")
            return
        if not re.fullmatch(r"[A-Za-z\s'-]+", e_clean):
            st.warning("Английское слово должно содержать только латиницу.")
            return
        try:
            added = db.add_personal_word(conn, st.session_state.user_id, r_clean, e_clean)
        except Exception as e:
            st.error(f"Не удалось добавить в базу данных: {e}")
            return
        if added:
            st.session_state.clear_add_form = True
            st.session_state.add_success_msg = "Успешно добавлено в базу данных!"
            st.session_state.pop("options", None)
            st.rerun()
        else:
            st.warning("Такое слово уже есть в базе данных!")
    if "add_success_msg" in st.session_state:
        st.success(st.session_state.pop("add_success_msg"))
        try:
            word_number_list = db.get_user_words(conn, st.session_state.user_id)
            st.write(f"Вы изучаете {len(word_number_list)} слов")
        except Exception as e:
            st.error(f"Не удалось прочитать количество слов из базы данных: {e}")

def pluralize_words(n: int) -> str:
    if 11 <= (n % 100) <= 19:
        return f"{n} слов"
    last_digit = n % 10
    if last_digit == 1:
        return f"{n} слово"
    if 2 <= last_digit <= 4:
        return f"{n} слова"
    return f"{n} слов"

def render_delete_word_tab(conn):
    if "delete_success_msg" in st.session_state:
        st.success(st.session_state.pop("delete_success_msg"))
    try:
        user_words = db.get_user_words(conn, st.session_state.user_id)
    except Exception as e:
        st.error(f"Не удалось взять слова из базы данных: {e}")
        return
    personal_words = []
    for word in user_words:
        if word["word_type"] == "user":
            personal_words.append(word["russian_word"])
    if personal_words:
        selected_word = st.selectbox("Выберите слово:", personal_words)
        st.write(f'Вы выбрали слово "{selected_word}"')
        if st.button("Удалить слово из базы данных"):
            word_id = None
            for word in user_words:
                if word["russian_word"] == selected_word:
                    word_id = word["id"]
                    break
            try:
                gone = db.delete_personal_word(conn, st.session_state.user_id, word_id)
            except Exception as e:
                st.error(f"Не удалось удалить слово из базы данных: {e}")
                return
            if gone:
                st.session_state.delete_success_msg = "Слово удалено успешно!"
                st.session_state.pop("answer_status", None)
                st.session_state.pop("options", None)
                st.rerun()
            else:
                st.warning("Не удалось удалить слово!")
    else:
        st.warning("У вас нет персональных слов!")

def render_statistics_tab(conn):
    try:
        user_stats = db.get_statistics(conn, st.session_state.user_id)
    except Exception as e:
        st.error(f"Не удалось загрузить статистику: {e}")
        return
    if user_stats['total_attempts'] == 0:
        percent = "Попыток ещё не было!"
    else:
        percent = round(100 * user_stats['correct_answers'] / user_stats['total_attempts'], 2)
    st.write(f"Количество изученных слов: {user_stats['learned_words']}")
    st.write(f"Количество попыток: {user_stats['total_attempts']}")
    st.write(f"Количество правильных ответов: {user_stats['correct_answers']}")
    st.write(f"Процент правильных ответов: {percent}")
    if user_stats['last_reviewed'] is None:
        st.write("Время самой недавней попытки: Попыток ещё не было!")
    else:
        formatted_time = user_stats['last_reviewed'].strftime("%H:%M:%S %d.%m.%Y")
        st.write(f"Время самой недавней попытки: {formatted_time}")

def render_schema():
    if "show_pic" not in st.session_state:
        st.session_state.show_pic = False
    button_label = "Скрыть схему базы данных" if st.session_state.show_pic else "Показать схему базы данных"
    if st.button(button_label):
        st.session_state.show_pic = not st.session_state.show_pic
        st.rerun()
    if st.session_state.show_pic:
        st.image("postgres - english_card - public.png")