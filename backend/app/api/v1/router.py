from fastapi import APIRouter

from app.api.v1 import bookmarks, health, opportunities, profile, recommendations

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(opportunities.router)
api_router.include_router(bookmarks.router)
api_router.include_router(recommendations.router)

# Additional routers (search, notifications, calendar, dashboard, admin) are
# registered here as they're implemented in later milestones.
