"""FastAPI dependency providers.

These pull the fully-wired :class:`Container` from application state and hand
use cases to routers, so routers never construct their own dependencies.
"""

from __future__ import annotations

from typing import Annotated

from config.containers import Container
from fastapi import Depends, Request

from bise.application.use_cases.companies.create_company import CreateCompany
from bise.application.use_cases.companies.get_company import GetCompany
from bise.application.use_cases.companies.list_companies import ListCompanies
from bise.application.use_cases.crawling.get_crawl_job import GetCrawlJob
from bise.application.use_cases.crawling.list_crawl_jobs import ListCrawlJobs
from bise.application.use_cases.crawling.request_crawl import RequestCrawl
from bise.application.use_cases.discovery.discover_businesses import DiscoverBusinesses
from bise.application.use_cases.enrichment.detect_marketing import DetectMarketing
from bise.application.use_cases.enrichment.detect_technologies import DetectTechnologies
from bise.application.use_cases.enrichment.enqueue_enrichment import EnqueueEnrichment
from bise.application.use_cases.enrichment.get_company_seo import GetCompanySeo
from bise.application.use_cases.enrichment.get_queue_summary import GetQueueSummary
from bise.application.use_cases.enrichment.list_company_marketing import ListCompanyMarketing
from bise.application.use_cases.enrichment.list_company_technologies import ListCompanyTechnologies
from bise.application.use_cases.enrichment.list_technologies import ListTechnologies
from bise.application.use_cases.enrichment.run_seo_scan import RunSeoScan
from bise.application.use_cases.search.rebuild_search_document import RebuildSearchDocument
from bise.application.use_cases.search.search_companies import SearchCompanies
from bise.application.use_cases.workspace.lists import (
    AddCompanyToList,
    CreateCompanyList,
    DeleteCompanyList,
    ListCompanyLists,
    ListListMembers,
    RemoveCompanyFromList,
)
from bise.application.use_cases.workspace.saved_searches import (
    DeleteSavedSearch,
    ListSavedSearches,
    SaveSearch,
)
from bise.application.use_cases.workspace.tags import (
    AddCompanyTag,
    ListCompanyTags,
    RemoveCompanyTag,
)


def get_container(request: Request) -> Container:
    """Return the process-wide container stored on app state."""
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_create_company(container: ContainerDep) -> CreateCompany:
    return container.create_company()


def get_get_company(container: ContainerDep) -> GetCompany:
    return container.get_company()


def get_list_companies(container: ContainerDep) -> ListCompanies:
    return container.list_companies()


def get_request_crawl(container: ContainerDep) -> RequestCrawl:
    return container.request_crawl()


def get_list_crawl_jobs(container: ContainerDep) -> ListCrawlJobs:
    return container.list_crawl_jobs()


def get_get_crawl_job(container: ContainerDep) -> GetCrawlJob:
    return container.get_crawl_job()


def get_detect_technologies(container: ContainerDep) -> DetectTechnologies:
    return container.detect_technologies()


def get_list_company_technologies(container: ContainerDep) -> ListCompanyTechnologies:
    return container.list_company_technologies()


def get_list_technologies(container: ContainerDep) -> ListTechnologies:
    return container.list_technologies()


def get_detect_marketing(container: ContainerDep) -> DetectMarketing:
    return container.detect_marketing()


def get_list_company_marketing(container: ContainerDep) -> ListCompanyMarketing:
    return container.list_company_marketing()


def get_discover_businesses(container: ContainerDep) -> DiscoverBusinesses:
    return container.discover_businesses()


def get_run_seo_scan(container: ContainerDep) -> RunSeoScan:
    return container.run_seo_scan()


def get_get_company_seo(container: ContainerDep) -> GetCompanySeo:
    return container.get_company_seo()


def get_search_companies(container: ContainerDep) -> SearchCompanies:
    return container.search_companies()


def get_rebuild_search_document(container: ContainerDep) -> RebuildSearchDocument:
    return container.rebuild_search_document()


def get_save_search(container: ContainerDep) -> SaveSearch:
    return container.save_search()


def get_list_saved_searches(container: ContainerDep) -> ListSavedSearches:
    return container.list_saved_searches()


def get_delete_saved_search(container: ContainerDep) -> DeleteSavedSearch:
    return container.delete_saved_search()


def get_create_company_list(container: ContainerDep) -> CreateCompanyList:
    return container.create_company_list()


def get_list_company_lists(container: ContainerDep) -> ListCompanyLists:
    return container.list_company_lists()


def get_delete_company_list(container: ContainerDep) -> DeleteCompanyList:
    return container.delete_company_list()


def get_add_company_to_list(container: ContainerDep) -> AddCompanyToList:
    return container.add_company_to_list()


def get_remove_company_from_list(container: ContainerDep) -> RemoveCompanyFromList:
    return container.remove_company_from_list()


def get_list_list_members(container: ContainerDep) -> ListListMembers:
    return container.list_list_members()


def get_add_company_tag(container: ContainerDep) -> AddCompanyTag:
    return container.add_company_tag()


def get_remove_company_tag(container: ContainerDep) -> RemoveCompanyTag:
    return container.remove_company_tag()


def get_list_company_tags(container: ContainerDep) -> ListCompanyTags:
    return container.list_company_tags()


def get_enqueue_enrichment(container: ContainerDep) -> EnqueueEnrichment:
    return container.enqueue_enrichment()


def get_queue_summary(container: ContainerDep) -> GetQueueSummary:
    return container.get_queue_summary()
