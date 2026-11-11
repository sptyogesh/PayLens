"""All routers, in the order they are registered."""

from fastapi import APIRouter

from app.api.routes import chat, dashboard, fira, health, pay, report, sync, transactions

ROUTERS: list[APIRouter] = [
    health.router,
    sync.router,
    transactions.router,
    dashboard.router,
    pay.router,
    chat.router,
    fira.router,
    report.router,
]
