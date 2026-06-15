from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)

# Additional routers (opportunities, search, bookmarks, profile, recommendations,
# notifications, calendar, dashboard, admin) are registered here as they're
# implemented in later milestones.
