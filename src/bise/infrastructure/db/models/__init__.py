"""ORM models package.

Importing this package registers every model on ``Base.metadata`` so that
``create_all`` and Alembic autogenerate see the full schema regardless of
import order.
"""

from bise.infrastructure.db.models.auth import ApiKeyModel, WorkspaceModel
from bise.infrastructure.db.models.company import CompanyModel, DomainModel
from bise.infrastructure.db.models.crawl import CrawledPageModel, CrawlJobModel
from bise.infrastructure.db.models.enrichment import EnrichmentJobModel
from bise.infrastructure.db.models.marketing import MarketingSignalModel
from bise.infrastructure.db.models.search import SearchDocumentModel
from bise.infrastructure.db.models.seo import SeoProfileModel
from bise.infrastructure.db.models.technology import (
    CompanyTechnologyModel,
    TechnologyCategoryModel,
    TechnologyModel,
)
from bise.infrastructure.db.models.workspace import (
    CompanyListItemModel,
    CompanyListModel,
    CompanyTagModel,
    SavedSearchModel,
)

__all__ = [
    "ApiKeyModel",
    "CompanyListItemModel",
    "CompanyListModel",
    "CompanyModel",
    "CompanyTagModel",
    "CompanyTechnologyModel",
    "CrawlJobModel",
    "CrawledPageModel",
    "DomainModel",
    "EnrichmentJobModel",
    "MarketingSignalModel",
    "SavedSearchModel",
    "SearchDocumentModel",
    "SeoProfileModel",
    "TechnologyCategoryModel",
    "TechnologyModel",
    "WorkspaceModel",
]
