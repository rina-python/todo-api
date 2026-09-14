# TODO API

Мой первый бэкенд-проект на FastAPI.

## Что умеет

- ✅ Создавать задачи (POST /tasks)
- ✅ Показывать все задачи (GET /tasks)
- ✅ Обновлять задачи (PUT /tasks/{id})
- ✅ Удалять задачи (DELETE /tasks/{id})

## Технологии

- Python 3.12
- FastAPI
- SQLite + SQLAlchemy
- HTML + JavaScript

## Как запустить

1. Установить зависимости:
pip install fastapi uvicorn sqlalchemy pydantic

text
2. Запустить сервер:
python -m uvicorn todo:app --reload

text
3. Открыть в браузере:
http://127.0.0.1:8000/docs
