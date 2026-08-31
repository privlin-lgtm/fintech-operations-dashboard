from fastapi import APIRouter

from app.api.v1.endpoints import alerts, auth, cases, customers, reports, transactions

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(transactions.router)
api_router.include_router(cases.router)
api_router.include_router(alerts.router)
api_router.include_router(reports.router)
api_router.include_router(reports.schedule_router)
