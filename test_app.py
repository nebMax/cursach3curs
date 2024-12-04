import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert "Ласкаво просимо" in response.data.decode('utf-8')


def test_login(client):
    response = client.post('/login', data={'username': 'test', 'password': 'test'})
    assert response.status_code == 200 or response.status_code == 302  # Redirect or success

def test_register(client):
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 302  # Redirect after registration
