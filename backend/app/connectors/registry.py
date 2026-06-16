from app.connectors.base import BaseConnector
from app.connectors.curated_companies import CuratedCompaniesConnector
from app.connectors.curated_early_career import CuratedEarlyCareerConnector
from app.connectors.devpost import DevpostConnector
from app.connectors.greenhouse import GreenhouseConnector
from app.connectors.unstop import UnstopConnector

CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    DevpostConnector.meta.key: DevpostConnector,
    UnstopConnector.meta.key: UnstopConnector,
    GreenhouseConnector.meta.key: GreenhouseConnector,
    CuratedCompaniesConnector.meta.key: CuratedCompaniesConnector,
    CuratedEarlyCareerConnector.meta.key: CuratedEarlyCareerConnector,
}


def build_connector(key: str) -> BaseConnector:
    return CONNECTOR_REGISTRY[key]()
