"""All routers, in the order they are registered."""

from fastapi import APIRouter

from app.api.routes import health, pay, sync, transactions

ROUTERS: list[APIRouter] = [health.router, sync.router, transactions.router, pay.router]
