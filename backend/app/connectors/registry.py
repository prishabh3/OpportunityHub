from app.connectors.base import BaseConnector
from app.connectors.curated_companies import CuratedCompaniesConnector
from app.connectors.devpost import DevpostConnector
from app.connectors.unstop import UnstopConnector

CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    DevpostConnector.meta.key: DevpostConnector,
    UnstopConnector.meta.key: UnstopConnector,
    CuratedCompaniesConnector.meta.key: CuratedCompaniesConnector,
}


def build_connector(key: str) -> BaseConnector:
    return CONNECTOR_REGISTRY[key]()
