from test.test_main import client
from main import app
from fastapi import status
from router.auth import get_current_user
from database import SessionLocal
from tables import Transactions
from datetime import date

def override_get_current_user():
    return {
        'id' : 1,
        'username' : 'testuser'
    }

def test_todo():
    db = SessionLocal()
    # remove old test data if its exist
    db.query(Transactions).filter(Transactions.id == 0).delete()

    Transaction = Transactions(
        id = 0,
        title = 'Testing',
        amount = 9999,
        type = 'income',
        category = 'Test',
        date = date.today(),
        owner_id = 1
    )
    db.add(Transaction)
    db.commit()

app.dependency_overrides[get_current_user] = override_get_current_user

def test_get_transaction():
    response = client.get('/transactions')
    assert response.status_code == status.HTTP_200_OK

def test_specific_transaction():
    response = client.get('/transactions/0')
    assert response.status_code == status.HTTP_200_OK

def test_create_transaction():
    db = SessionLocal()
    db.query(Transactions).filter(Transactions.id == 0).delete()
    db.commit()

    request_data = {
        'id' : 0,
        'title' : 'Testing',
        'amount' : 9999,
        'type' : 'income',
        'category' : 'Test',
        'date' : str(date.today()),
        'owner_id' : 1
    }
    response = client.post('/transactions',json = request_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {'message':'Transaction created successfully'}

def test_update_transaction():
    request_data = {
        'title' : 'Testing',
    }
    response = client.put('/transactions/0',json = request_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message':'Transacation updated Successfully'}

def test_delete_transaction():
    response = client.delete('/transactions/0')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'message':'Transaction deleted successfully'}
