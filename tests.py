from fastapi.testclient import TestClient
from todo import app, Base, engine, SessionLocal, User, Task, Category

# Создаём тестовый клиент
client = TestClient(app)

# Уникальный email для каждого запуска тестов
import time
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "secret123"


def test_register():
    """Тест 1: Регистрация нового пользователя."""
    response = client.post("/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200
    assert response.json()["email"] == TEST_EMAIL
    print("✅ test_register прошёл")


def test_login():
    """Тест 2: Вход и получение токена."""
    response = client.post("/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    print("✅ test_login прошёл")


def test_login_wrong_password():
    """Тест 3: Неверный пароль — должен вернуть 401."""
    response = client.post("/login", json={
        "email": TEST_EMAIL,
        "password": "wrong_password"
    })
    assert response.status_code == 401
    print("✅ test_login_wrong_password прошёл")


def test_create_task():
    """Тест 4: Создание задачи с авторизацией."""
    # Логинимся
    login_response = client.post("/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    token = login_response.json()["access_token"]
    
    # Создаём задачу
    response = client.post(
        "/tasks",
        json={"title": "Тестовая задача", "description": "Проверка"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Тестовая задача"
    print("✅ test_create_task прошёл")


def test_task_without_auth():
    """Тест 5: Без токена — 401 (не авторизован)."""
    response = client.get("/tasks")
    assert response.status_code == 401
    print("✅ test_task_without_auth прошёл")


def test_create_category():
    """Тест 6: Создание категории."""
    login_response = client.post("/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/categories",
        json={"name": "Тестовая категория"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Тестовая категория"
    print("✅ test_create_category прошёл")