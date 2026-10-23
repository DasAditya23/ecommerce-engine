# Secure E-Commerce Order Engine

A transactional backend API built with Python, FastAPI, and SQLAlchemy. Features JWT authentication, race-condition-safe checkout logic, and complex SQL reporting.

## Features
- **JWT Authentication:** Register and log in to receive a Bearer token.
- **Transactional Checkout:** Uses SQLAlchemy row-level locks (`with_for_update`) to prevent race conditions when multiple users buy the last item in stock.
- **ACID Rollbacks:** If any item in an order is out of stock, the entire transaction is rolled back, ensuring inventory consistency.
- **SQL Reporting:** Endpoint that uses complex JOINs and GROUP BY to calculate top-selling products by revenue.
- **Dockerized:** Includes a Dockerfile and docker-compose.yml for deployment.

## Tech Stack
Python, FastAPI, SQLAlchemy, SQLite (PostgreSQL-ready), JWT (python-jose), bcrypt, Pydantic, Docker.

## Run Locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## API Documentation
Once running, navigate to http://127.0.0.1:8000/docs to test endpoints via Swagger UI.

## How to test
1. POST /register to create a user.
2. POST /token to log in and receive an access token.
3. Click Authorize in Swagger and paste the token.
4. POST /checkout to make a purchase.
5. GET /reports/top-products to view aggregated revenue data.
