from fastapi import APIRouter

from app.api.v1 import (
    admin,
    bookmarks,
    health,
    ingest,
    notifications,
    opportunities,
    profile,
    recommendations,
    search,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(opportunities.router)
api_router.include_router(bookmarks.router)
api_router.include_router(recommendations.router)
api_router.include_router(ingest.router)
api_router.include_router(notifications.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)

# Additional routers (calendar, dashboard) are registered here as they're
# implemented in later milestones.
