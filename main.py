from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import database
import auth
from datetime import timedelta

app = FastAPI(title="E-Commerce Order Engine")

# --- Pydantic Schemas ---
class UserCreate(BaseModel):
    email: str
    password: str

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int

class OrderRequest(BaseModel):
    items: List[OrderItemRequest]

# --- Auth Endpoints ---
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(database.User).filter(database.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth.get_password_hash(user.password)
    new_user = database.User(email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Business Endpoints ---
@app.post("/checkout")
def checkout(order_req: OrderRequest, db: Session = Depends(database.get_db), current_user: database.User = Depends(auth.get_current_user)):
    total_amount = 0.0
    order_items = []
    
    try:
        for item in order_req.items:
            product = db.query(database.Product).filter(database.Product.id == item.product_id).with_for_update().first()
            
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")
            
            product.stock -= item.quantity
            item_total = product.price * item.quantity
            total_amount += item_total
            
            order_items.append(database.OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                price_at_purchase=product.price
            ))
            
        new_order = database.Order(
            user_id=current_user.id,
            total_amount=total_amount,
            items=order_items
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        return {"message": "Order successful", "order_id": new_order.id, "total": total_amount}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/top-products")
def get_top_products(db: Session = Depends(database.get_db)):
    from sqlalchemy import func
    results = db.query(
        database.Product.name,
        func.sum(database.OrderItem.quantity * database.OrderItem.price_at_purchase).label("total_revenue")
    ).join(database.OrderItem, database.Product.id == database.OrderItem.product_id)\
     .group_by(database.Product.id)\
     .order_by(func.sum(database.OrderItem.quantity * database.OrderItem.price_at_purchase).desc())\
     .limit(5).all()
    
    return [{"product": r[0], "revenue": r[1]} for r in results]
