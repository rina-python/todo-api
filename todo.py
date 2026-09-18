from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from auth import hash_password, verify_password, create_access_token, decode_token

# --- База данных ---
engine = create_engine('sqlite:///todo.db', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Модель: Пользователь ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

# --- Модель: Задача ---
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    done = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))  # ← кто владелец

Base.metadata.create_all(bind=engine)

# --- Схемы валидации ---
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TaskCreate(BaseModel):
    title: str
    description: str = ""

class TaskUpdate(BaseModel):
    title: str = None
    description: str = None
    done: bool = None

# --- Приложение ---
app = FastAPI(title="TODO API with Auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Безопасность ---
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверяет токен и возвращает пользователя."""
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Неверный токен")
    
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Токен без email")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        return user
    finally:
        db.close()

# --- Эндпоинты: Регистрация и вход ---

@app.post("/register")
def register(user_data: UserCreate):
    db = SessionLocal()
    try:
        # Проверяем, нет ли уже такого email
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email уже занят")
        
        # Создаём пользователя с хешированным паролем
        new_user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"id": new_user.id, "email": new_user.email}
    finally:
        db.close()

@app.post("/login")
def login(user_data: UserLogin):
    db = SessionLocal()
    try:
        # Ищем пользователя по email
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user or not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        
        # Создаём токен
        token = create_access_token({"sub": user.email})
        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()

# --- Эндпоинты: Задачи (только для авторизованных) ---

@app.get("/")
def root():
    return {"message": "Добро пожаловать в TODO API!"}

@app.get("/tasks")
def get_tasks(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        tasks = db.query(Task).filter(Task.owner_id == current_user.id).all()
        return {"tasks": [{"id": t.id, "title": t.title, "description": t.description, "done": t.done} for t in tasks]}
    finally:
        db.close()

@app.post("/tasks")
def create_task(task: TaskCreate, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        new_task = Task(
            title=task.title,
            description=task.description,
            owner_id=current_user.id  # ← привязываем к пользователю
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return {"id": new_task.id, "title": new_task.title, "done": new_task.done}
    finally:
        db.close()

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        db_task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
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

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        db_task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        db.delete(db_task)
        db.commit()
        return {"message": f"Задача {task_id} удалена"}
    finally:
        db.close()