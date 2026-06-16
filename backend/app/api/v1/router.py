from fastapi import APIRouter

from app.api.v1 import (
    bookmarks,
    health,
    ingest,
    notifications,
    opportunities,
    profile,
    recommendations,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(opportunities.router)
api_router.include_router(bookmarks.router)
api_router.include_router(recommendations.router)
api_router.include_router(ingest.router)
api_router.include_router(notifications.router)

# Additional routers (search, calendar, dashboard, admin) are registered here
# as they're implemented in later milestones.
