from fastapi import APIRouter

from app.api.v1 import health, opportunities, profile

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(opportunities.router)

# Additional routers (search, bookmarks, recommendations, notifications,
# calendar, dashboard, admin) are registered here as they're implemented in
# later milestones.
