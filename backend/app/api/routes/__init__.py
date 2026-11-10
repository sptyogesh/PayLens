"""All routers, in the order they are registered."""

from fastapi import APIRouter

from app.api.routes import health

ROUTERS: list[APIRouter] = [health.router]
