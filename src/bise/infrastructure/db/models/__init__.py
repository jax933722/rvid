"""ORM models package.

Importing this package registers every model on ``Base.metadata`` so that
``create_all`` and Alembic autogenerate see the full schema regardless of
import order.
"""

from bise.infrastructure.db.models.company import CompanyModel, DomainModel
from bise.infrastructure.db.models.crawl import CrawledPageModel, CrawlJobModel
from bise.infrastructure.db.models.seo import SeoProfileModel
from bise.infrastructure.db.models.technology import (
    CompanyTechnologyModel,
    TechnologyCategoryModel,
    TechnologyModel,
)

__all__ = [
    "CompanyModel",
    "CompanyTechnologyModel",
    "CrawlJobModel",
    "CrawledPageModel",
    "DomainModel",
    "SeoProfileModel",
    "TechnologyCategoryModel",
    "TechnologyModel",
]
