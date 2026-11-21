CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW());

CREATE TABLE IF NOT EXISTS common_words(id SERIAL PRIMARY KEY,
                        russian_word VARCHAR(50) NOT NULL,
                        english_word VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        UNIQUE(russian_word, english_word));

CREATE TABLE IF NOT EXISTS user_words(id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        russian_word VARCHAR(50) NOT NULL,
                        english_word VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, russian_word, english_word));

CREATE TABLE IF NOT EXISTS learning_stats(id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        word_id INTEGER NOT NULL,
                        word_type VARCHAR(50) NOT NULL,
                        correct_answers INTEGER NOT NULL DEFAULT 0,
                        total_attempts INTEGER NOT NULL DEFAULT 0,
                        last_reviewed TIMESTAMP NOT NULL DEFAULT NOW(),
                        CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, word_id, word_type));