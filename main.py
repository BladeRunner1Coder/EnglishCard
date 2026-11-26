import streamlit as st
from dotenv import load_dotenv
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
db.init_database()
sts.render_sidebar()
if st.session_state.user_id:
    tab1, tab2, tab3, tab4 = st.tabs(["📖 Изучение", "➕ Добавить слово", "🗑️ Удалить слово", "📊 Статистика"])
    with tab1:
        sts.render_study_tab()
    with tab2:
        sts.render_add_word_tab()
    with tab3:
        sts.render_delete_word_tab()
    with tab4:
        sts.render_statistics_tab()
st.divider()
sts.render_schema()
