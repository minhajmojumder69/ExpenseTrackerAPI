from fastapi import FastAPI,Depends, HTTPException , Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import tables
from datetime import date
from tables import Transactions,User
from typing import Annotated, Optional ,Literal
from database import engine,SessionLocal
from fastapi.responses import JSONResponse
from router import auth
from router.auth import get_current_user

app = FastAPI()

tables.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)

class Transaction(BaseModel):
    id : int = Field(gt=0)
    title : str
    amount : float = Field(gt=0)
    type : Annotated[Literal['income', 'expense'], Field(max_length=10)]
    category : str
    date : date

class Transaction_update(BaseModel):
    id : Optional[int] = Field(default=None, gt=0)
    title : Optional[str] = Field(default=None)
    amount : Optional[float] = Field(default=None, gt=0)
    type : Optional[Literal['Income', 'Expense']] = Field(default=None)
    category : Optional[str]  = Field(default=None)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
database_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]

@app.get('/transactions')
def read_transaction(db: database_dependency,user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401,detail="Failed Authentication")
    return db.query(Transactions).filter(Transactions.owner_id == user.get('id')).all()


@app.get('/transactions/filter')
def transaction_filter(db: database_dependency,user: user_dependency, type: Optional[str] = Query(None, description= 'income or expense' ),category : Optional[str] = Query(None, description= 'Filter by category'), minimum_amount:Optional[float] = Query(None, description="Minimum transaction amount"),maximum_amount: Optional[float] = Query(None, description="Maximum transaction amount")):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    valid_types = ['income', 'expense']
    if type is not None and type.lower() not in valid_types:
        raise HTTPException(status_code=404, detail=f"Invalid type, select from {valid_types}")
    
    query = db.query(Transactions).filter(Transactions.owner_id == user.get('id'))

    if type is not None:
        query = query.filter(Transactions.type == type)
    if category is not None:
         query = query.filter(Transactions.category == category)

    if minimum_amount is not None:
        query = query.filter(Transactions.amount >= minimum_amount)

    if maximum_amount is not None:
         query = query.filter(Transactions.amount <= maximum_amount)

    return query.all()

@app.get('/transactions/{transaction_id}')
def read_specific_transactions(db: database_dependency,user: user_dependency, transaction_id: int):
    if user is None:
        raise HTTPException(status_code=401,detail='Failed Authentication')
    
    specific_transaction = db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).first()
    if specific_transaction is None:
        raise HTTPException(status_code=404,detail='Transaction not found')
    else:
        return specific_transaction

@app.post('/transactions')
def create_transactions(db: database_dependency,user:user_dependency, new_transaction : Transaction):
    if user is None:
            raise HTTPException(status_code=401,detail='Failed Authentication')
    transaction_model = Transactions(**new_transaction.model_dump(),owner_id = user.get('id'))
    db.add(transaction_model)
    db.commit()
    return JSONResponse(status_code=201,content={'message':'Transaction created successfully'})

@app.put('/transactions/{transaction_id}')
def update_transactions(db: database_dependency,user:user_dependency, transaction_id: int, update_transaction : Transaction_update):

    if user is None:
            raise HTTPException(status_code=401,detail='Failed Authentication')
    
    specific_transaction = db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).first()
    if specific_transaction is None:
        raise HTTPException(status_code=404, detail='Transaction not found')
    updated = update_transaction.model_dump(exclude_unset=True)
    for key,value in updated.items():
        setattr(specific_transaction,key,value)

    db.commit()
    return JSONResponse(status_code=200,content={'message':'Transacation updated Successfully'})

@app.delete('/transactions/{transaction_id}')
def delete_transaction(db: database_dependency,user: user_dependency, transaction_id : int):
    specific_transaction = db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).first()

    if user is None:
            raise HTTPException(status_code=401,detail='Failed Authentication')
    
    if specific_transaction is None:
            raise HTTPException(status_code=404, detail='Transaction not found')
    db.query(Transactions).filter(Transactions.id == transaction_id).delete()
    db.commit()
    return JSONResponse(status_code=200,content={'message':'Transaction deleted successfully'})

@app.get('/user')
def get_user(user: user_dependency,db : database_dependency):

    if user is None:
            raise HTTPException(status_code=401,detail="Failed Authentication")

    return db.query(User).filter(User.id == user.get('id')).first()