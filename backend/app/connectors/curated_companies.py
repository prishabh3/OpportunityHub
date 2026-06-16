"""Curated, high-value company-hosted hackathons. These flagship programs have
no machine-readable API, so they're maintained as a static (but real) list and
ingested through the same pipeline (idempotent upsert)."""

from typing import Any

from app.connectors.base import BaseConnector, NormalizedOpportunity, SourceMeta

_COMPANY_HACKATHONS: list[dict[str, Any]] = [
    {
        "external_id": "google-solution-challenge",
        "title": "Google Developer Student Clubs Solution Challenge",
        "organizer": "Google",
        "description": "Build a solution to one of the UN's 17 Sustainable Development Goals using Google technologies. Google's flagship student hackathon.",
        "apply_url": "https://developers.google.com/community/gdsc-solution-challenge",
        "tags": ["AI", "Google Cloud", "Social Good", "Student"],
        "remote_type": "remote",
    },
    {
        "external_id": "microsoft-imagine-cup",
        "title": "Microsoft Imagine Cup",
        "organizer": "Microsoft",
        "description": "Microsoft's global student technology competition — build a startup-style project on Azure and pitch for mentorship, Azure credits, and cash prizes.",
        "apply_url": "https://imaginecup.microsoft.com/",
        "tags": ["Azure", "AI", "Startup", "Student"],
        "remote_type": "remote",
    },
    {
        "external_id": "aws-gameday",
        "title": "AWS GameDay Challenges",
        "organizer": "Amazon Web Services",
        "description": "Gamified, hands-on team challenges that test your ability to build and operate real systems on AWS under pressure.",
        "apply_url": "https://aws.amazon.com/gameday/",
        "tags": ["AWS", "Cloud", "DevOps"],
        "remote_type": "hybrid",
    },
    {
        "external_id": "amazon-alexa-challenge",
        "title": "Amazon Alexa Skills Challenges",
        "organizer": "Amazon",
        "description": "Design and build voice experiences as Alexa skills and compete for prizes and Amazon developer recognition.",
        "apply_url": "https://developer.amazon.com/alexa",
        "tags": ["Voice", "Alexa", "AI"],
        "remote_type": "remote",
    },
    {
        "external_id": "nvidia-gtc-hackathon",
        "title": "NVIDIA GTC Hackathons",
        "organizer": "NVIDIA",
        "description": "Accelerated-computing and AI hackathons run around NVIDIA GTC, with access to GPUs, CUDA, and NVIDIA AI tooling.",
        "apply_url": "https://www.nvidia.com/gtc/",
        "tags": ["AI", "GPU", "CUDA", "Deep Learning"],
        "remote_type": "hybrid",
    },
    {
        "external_id": "ibm-call-for-code",
        "title": "IBM Call for Code Global Challenge",
        "organizer": "IBM",
        "description": "Build solutions that fight climate change and humanitarian issues using open source and IBM Cloud. One of the largest tech-for-good hackathons.",
        "apply_url": "https://callforcode.org/",
        "tags": ["Open Source", "Social Good", "IBM Cloud", "AI"],
        "remote_type": "remote",
    },
    {
        "external_id": "mongodb-genai-hackathon",
        "title": "MongoDB GenAI Hackathons",
        "organizer": "MongoDB",
        "description": "Build generative-AI applications backed by MongoDB Atlas Vector Search.",
        "apply_url": "https://www.mongodb.com/community/forums/c/events/",
        "tags": ["Generative AI", "MongoDB", "Vector Search"],
        "remote_type": "remote",
    },
    {
        "external_id": "databricks-genai-hackathon",
        "title": "Databricks Generative AI Hackathons",
        "organizer": "Databricks",
        "description": "Build data and AI applications on the Databricks Lakehouse and Mosaic AI platform.",
        "apply_url": "https://www.databricks.com/events",
        "tags": ["Data", "Generative AI", "Databricks", "ML"],
        "remote_type": "hybrid",
    },
    {
        "external_id": "cloudflare-hackathons",
        "title": "Cloudflare Developer Hackathons",
        "organizer": "Cloudflare",
        "description": "Build on Cloudflare Workers, Pages, and the edge developer platform.",
        "apply_url": "https://developers.cloudflare.com/",
        "tags": ["Edge", "Serverless", "Workers"],
        "remote_type": "remote",
    },
    {
        "external_id": "intel-ai-hackathons",
        "title": "Intel AI Hackathons",
        "organizer": "Intel",
        "description": "Optimize and build AI workloads using Intel's developer tools, oneAPI, and AI hardware.",
        "apply_url": "https://www.intel.com/content/www/us/en/developer/topic-technology/artificial-intelligence/overview.html",
        "tags": ["AI", "oneAPI", "Performance"],
        "remote_type": "hybrid",
    },
    {
        "external_id": "adobe-express-hackathon",
        "title": "Adobe Express Add-ons Hackathons",
        "organizer": "Adobe",
        "description": "Build add-ons and creative tooling on the Adobe Express developer platform.",
        "apply_url": "https://developer.adobe.com/express/",
        "tags": ["Creative", "Add-ons", "Adobe Express"],
        "remote_type": "remote",
    },
    {
        "external_id": "openai-hackathons",
        "title": "OpenAI-Sponsored AI Hackathons",
        "organizer": "OpenAI",
        "description": "OpenAI regularly sponsors AI hackathons with API credits and prizes for building with GPT and the OpenAI platform.",
        "apply_url": "https://openai.com/news/",
        "tags": ["AI", "LLM", "OpenAI API"],
        "remote_type": "remote",
    },
]


class CuratedCompaniesConnector(BaseConnector):
    meta = SourceMeta(
        key="company-hackathons",
        display_name="Company Hackathons",
        base_url="https://opportunityhub.dev",
        opportunity_types=["hackathon"],
    )

    async def fetch(self) -> list[NormalizedOpportunity]:
        return [
            NormalizedOpportunity(
                external_id=h["external_id"],
                type="hackathon",
                status="active",
                title=h["title"],
                organizer=h["organizer"],
                description=h["description"],
                country="Global",
                remote_type=h.get("remote_type", "remote"),
                difficulty="intermediate",
                apply_url=h["apply_url"],
                source_url=h["apply_url"],
                tags=h["tags"],
            )
            for h in _COMPANY_HACKATHONS
        ]
