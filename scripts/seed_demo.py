"""Seed a demo database with enriched companies for screenshots / local demos.

Populates companies, crawled pages, technologies, SEO profiles, marketing
signals, and the search projection directly through the repositories (no live
crawling), so the UI has realistic content to render.

Usage:
    BISE_DATABASE_URL=sqlite:///./demo.db .venv/bin/python scripts/seed_demo.py
"""

from __future__ import annotations

from dataclasses import dataclass

from config.containers import Container
from config.logging import configure_logging
from bise.application.dto.company_dto import CreateCompanyCommand, NewDomainDTO
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.domain.entities.marketing_signal import MarketingSignal
from bise.domain.entities.seo_profile import SeoProfile
from bise.domain.entities.technology import CompanyTechnology
from bise.domain.value_objects.confidence import Confidence
from bise.domain.value_objects.seo_signals import SeoSignals


@dataclass
class Demo:
    name: str
    industry: str
    size: str
    host: str
    techs: list[tuple[str, str]]        # (name, category)
    seo_score: float
    pages: list[PageType]
    marketing: list[tuple[str, str]]    # (tool, category)


DEMOS = [
    Demo("Acme Dental", "Dentistry", "11-50", "acmedental.com",
         [("WordPress", "CMS"), ("Meta Pixel", "Marketing Pixel"), ("Google Analytics 4", "Analytics")],
         42.0, [PageType.CONTACT, PageType.CAREERS],
         [("Meta Pixel", "Marketing Pixel"), ("WhatsApp", "Messaging")]),
    Demo("BrightSmile Orthodontics", "Dentistry", "1-10", "brightsmile.com",
         [("WordPress", "CMS"), ("Google Tag Manager", "Tag Manager")],
         88.0, [PageType.CONTACT, PageType.BLOG],
         [("Google Tag Manager", "Tag Manager"), ("Calendly", "Appointment Booking")]),
    Demo("Coastal Plumbing", "Plumbing", "11-50", "coastalplumbing.com.au",
         [("Shopify", "E-commerce")], 71.0, [PageType.CONTACT],
         [("Mailchimp", "Lead / Newsletter Form")]),
    Demo("Nimbus Software", "Software", "51-200", "nimbus.io",
         [("React", "JavaScript Framework"), ("Next.js", "JavaScript Framework"),
          ("Google Analytics 4", "Analytics")],
         93.0, [PageType.CAREERS, PageType.BLOG],
         [("Google Analytics 4", "Analytics"), ("Intercom", "Chat / Widget")]),
    Demo("GreenLeaf Cafe", "Hospitality", "1-10", "greenleaf.cafe",
         [("WordPress", "CMS"), ("WooCommerce", "E-commerce")],
         56.0, [PageType.CONTACT],
         [("OneTrust", "Cookie / Consent")]),
    Demo("Urban Fitness", "Fitness", "11-50", "urbanfitness.co",
         [("Shopify", "E-commerce"), ("Meta Pixel", "Marketing Pixel")],
         64.0, [PageType.CONTACT, PageType.CAREERS],
         [("Meta Pixel", "Marketing Pixel"), ("TikTok Pixel", "Marketing Pixel")]),
]


def _seo_signals(host: str, score: float) -> SeoSignals:
    return SeoSignals(
        url=f"https://{host}/",
        title=f"{host} — official site",
        meta_description="Trusted local business serving the community.",
        canonical=f"https://{host}/",
        meta_robots="index,follow",
        h1_count=1,
        h2_count=3,
        has_open_graph=score > 60,
        has_structured_data=score > 70,
        has_ssl=True,
        images_total=6,
        images_missing_alt=1 if score < 70 else 0,
        internal_links=12,
        external_links=3,
        word_count=int(400 + score * 5),
    )


def seed() -> None:
    settings_container = Container()
    configure_logging(level="INFO", json_output=False)

    for demo in DEMOS:
        create = settings_container.create_company()
        dto = create.execute(
            CreateCompanyCommand(
                display_name=demo.name,
                industry=demo.industry,
                size_bucket=demo.size,
                domains=(NewDomainDTO(hostname=demo.host, is_primary=True),),
            )
        )
        company_id = dto.id
        assert company_id is not None

        with settings_container.unit_of_work() as uow:
            company = uow.companies.get(company_id)
            assert company is not None
            domain_id = company.domains[0].id
            assert domain_id is not None

            job = uow.crawl_jobs.add(CrawlJob(domain_id=domain_id, hostname=demo.host))
            for page_type in [PageType.HOME, *demo.pages]:
                path = "" if page_type is PageType.HOME else page_type.value
                uow.crawled_pages.add(
                    CrawledPage(
                        domain_id=domain_id,
                        crawl_job_id=job.id,
                        url=f"https://{demo.host}/{path}",
                        page_type=page_type,
                        http_status=200,
                        content_hash=f"{demo.host}-{page_type.value}",
                        html=f"<html><title>{demo.name}</title></html>",
                    )
                )

            links: list[CompanyTechnology] = []
            for tech_name, category in demo.techs:
                tech = uow.technologies.get_or_create(tech_name, category)
                assert tech.id is not None
                links.append(
                    CompanyTechnology(
                        company_id=company_id, technology_id=tech.id,
                        confidence=Confidence(0.9), evidence="seed", technology=tech,
                    )
                )
            uow.company_technologies.replace_for_company(company_id, links)

            uow.seo_profiles.upsert(
                SeoProfile(company_id=company_id, signals=_seo_signals(demo.host, demo.seo_score),
                           score=demo.seo_score)
            )
            uow.marketing_signals.replace_for_company(
                company_id,
                [MarketingSignal(company_id=company_id, tool_name=name, category=cat, evidence="seed")
                 for name, cat in demo.marketing],
            )
            uow.commit()

        settings_container.rebuild_search_document().execute(company_id)
        print(f"seeded: {demo.name} (#{company_id})")

    print(f"done — {len(DEMOS)} companies")


if __name__ == "__main__":
    seed()
