from fastapi import APIRouter

from app.api.v1 import health, profile

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(profile.router)

# Additional routers (opportunities, search, bookmarks, recommendations,
# notifications, calendar, dashboard, admin) are registered here as they're
# implemented in later milestones.
