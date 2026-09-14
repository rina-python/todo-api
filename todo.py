from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware


# --- База данных ---
engine = create_engine('sqlite:///todo.db', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Модель таблицы ---
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    done = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# --- Схема для валидации данных (что присылает клиент) ---
class TaskCreate(BaseModel):
    title: str
    description: str = ""

class TaskUpdate(BaseModel):
    title: str = None
    description: str = None
    done: bool = None

# --- Приложение ---
app = FastAPI(title="TODO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Добро пожаловать в TODO API!"}

# --- 1. CREATE: Создать задачу ---
@app.post("/tasks")
def create_task(task: TaskCreate):
    db = SessionLocal()
    try:
        new_task = Task(title=task.title, description=task.description)
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return {"id": new_task.id, "title": new_task.title, "done": new_task.done}
    finally:
        db.close()

# --- 2. READ: Показать все задачи ---
@app.get("/tasks")
def get_tasks():
    db = SessionLocal()
    try:
        tasks = db.query(Task).all()
        return {"tasks": [{"id": t.id, "title": t.title, "description": t.description, "done": t.done} for t in tasks]}
    finally:
        db.close()

# --- 3. UPDATE: Обновить задачу ---
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    db = SessionLocal()
    try:
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        if task.title is not None:
            db_task.title = task.title
        if task.description is not None:
            db_task.description = task.description
        if task.done is not None:
            db_task.done = task.done
        db.commit()
        return {"id": db_task.id, "title": db_task.title, "done": db_task.done}
    finally:
        db.close()

# --- 4. DELETE: Удалить задачу ---
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db = SessionLocal()
    try:
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        db.delete(db_task)
        db.commit()
        return {"message": f"Задача {task_id} удалена"}
    finally:
        db.close()