import uuid
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class Job(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    title: str = Field(...)
    sourceType: str = Field(...)
    platform: str = Field(...)
    criterias: dict[str,str] = Field(...)
    url: str = Field(...)
    applyUrl: str = Field(...)
    slug: str = Field(...)
    motherCompany: str = Field(...)
    company: str = Field(...)
    country: str = Field(...)
    district: Optional[str]
    city: str = Field(...)
    zipCode: Optional[str]
    skills: Optional[list[str]]
    description: str = Field(...)
    scrapStatus: str = Field(...)
    status: Optional[str]
    applicationDate: Optional[str]
    timeoutDate: Optional[str]
    createdAt: str = Field(...)
    createdOn: str = Field(...)
    lastUpdated: Optional[str]
    tags: Optional[list[str]]
    qualificationsRequired: Optional[list[str]]
    qualificationsPreferred: Optional[list[str]]
    structuredData: Optional[dict[str,str]]
    #website_alive: Optional[bool]

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "title": "Chef de projet fonctionnel - H/F",
                "sourceType": "jobBoard",
                "platform": "fr.indeed.com",
                "criterias": {
                    "query": "python",
                    "location":"Lyon"
                },
                "url": "https://fr.indeed.com/viewjob?jk=f04ef871ad28c9ea",
                "applyUrl": "https://www.talentsit.fr/emplois/56760-lead-developer-kotlin-hf/",
                "slug": "viewjob?jk=f04ef871ad28c9ea",
                "motherCompany": "Seyos",
                "company": "Seyos",
                "country": "France",
                "district": None,
                "city": "La Courneuve",
                "zipCode": "93",
                "skills": None,
                "description": """# Description de l'entreprise :
Seyos est un cabinet de recrutement spécialisé dans les métiers de l'IT. Nous intervenons au niveau national et proposons aux candidats des opportunités professionnelles au sein d'éditeurs de logiciels, DSI d'entreprises (clients finaux), startups, acteurs E-commerce. En 9 années d'existence, plus de 1 300 professionnels de l'IT et du Digital ont déjà été recrutés par l'intermédiaire de Seyos au sein de 400 entreprises.

# Description du poste :
Leader français du recyclage depuis 1985, notre client est aujourd'hui le troisième acteur français du traitement des déchets. Composée de 13 000 collaborateurs, présents sur 300 sites en France et à l'international, la société est impliquée sur l'ensemble de la chaîne de valeur de la gestion des déchets auprès de 70 000 clients privés.""",
                "scrapStatus": "new",
                "status": None,
                "applicationDate": None,
                "timeoutDate": None,
                "createdAt": "2024-06-01T23:41:34",
                "createdOn": "2024-06-01",
                "tags": ["kotlin"],
                "qualificationsRequired": ["kotlin", "Compose"],
                "qualificationsPreferred": ["javascript"],
                "structuredData":{
                    "recruiter": "Paul Atkinson",
                    "coverLetterData": {
                        "adjectivesList": "$list-de nature curieuse,réfléchis,créatif,force de proposition,aimant partager",
                        "companyBlock": "block"
                    },
                    "company":{
                        "values": "LoremIpsum",
                        "engagements": "LoremIpsum",
                        "company": "LoremIpsum"
                    },
                    "department": "LoremIpsum",
                    "missions": "LoremIpsum",
                    "stack": "LoremIpsum",
                    "profile": "LoremIpsum",
                    "experience": "LoremIpsum",
                    "bonus": "LoremIpsum",
                    "hiringProcess": "LoremIpsum",
                    "personalNotes": "LoremIpsum"
                }
            }
        }

class JobUpdate(BaseModel):
    title: Optional[str]
    #sourceType: str = Field(...)
    #platform: str = Field(...)
    #criterias: dict[str,str] = Field(...)
    #url: str = Field(...)
    applyUrl: Optional[str]
    #slug: str = Field(...)
    motherCompany: Optional[str]
    company: Optional[str]
    country: Optional[str]
    district: Optional[str]
    city: Optional[str]
    zipCode: Optional[str]
    skills: Optional[list[str]]
    description: Optional[str]
    scrapStatus: Optional[str]
    status: Optional[str]
    applicationDate: Optional[str]
    timeoutDate: Optional[str]
    #createdAt: str = Field(...)
    #createdOn: str = Field(...)
    lastUpdated: str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    tags: Optional[list[str]]
    qualificationsRequired: Optional[list[str]]
    qualificationsPreferred: Optional[list[str]]
    structuredData: Optional[dict[str,str]]
    #website_alive: Optional[bool]

    class Config:
        schema_extra = {
            "example": {
                "title": "Chef de projet fonctionnel - H/F",
                "sourceType": "jobBoard",
                "platform": "fr.indeed.com",
                "criterias": {
                    "query": "python",
                    "location":"Lyon"
                },
                "url": "https://fr.indeed.com/viewjob?jk=f04ef871ad28c9ea",
                "applyUrl": "https://www.talentsit.fr/emplois/56760-lead-developer-kotlin-hf/",
                "slug": "viewjob?jk=f04ef871ad28c9ea",
                "motherCompany": "Seyos",
                "company": "Seyos",
                "country": "France",
                "district": None,
                "city": "La Courneuve",
                "zipCode": "93",
                "skills": None,
                "description": """# Description de l'entreprise :
Seyos est un cabinet de recrutement spécialisé dans les métiers de l'IT. Nous intervenons au niveau national et proposons aux candidats des opportunités professionnelles au sein d'éditeurs de logiciels, DSI d'entreprises (clients finaux), startups, acteurs E-commerce. En 9 années d'existence, plus de 1 300 professionnels de l'IT et du Digital ont déjà été recrutés par l'intermédiaire de Seyos au sein de 400 entreprises.

# Description du poste :
Leader français du recyclage depuis 1985, notre client est aujourd'hui le troisième acteur français du traitement des déchets. Composée de 13 000 collaborateurs, présents sur 300 sites en France et à l'international, la société est impliquée sur l'ensemble de la chaîne de valeur de la gestion des déchets auprès de 70 000 clients privés.""",
                "scrapStatus": "new",
                "status": None,
                "applicationDate": None,
                "timeoutDate": None,
                "createdAt": "2024-06-01T23:41:34",
                "createdOn": "2024-06-01",
                "lastUpdated": "2024-06-01T23:41:34",
                "tags": ["kotlin"],
                "qualificationsRequired": ["kotlin", "Compose"],
                "qualificationsPreferred": ["javascript"],
                "structuredData":{
                    "recruiter": "Paul Atkinson",
                    "coverLetterData": {
                        "adjectivesList": "$list-de nature curieuse,réfléchis,créatif,force de proposition,aimant partager",
                        "companyBlock": "block"
                    },
                    "company":{
                        "values": "LoremIpsum",
                        "engagements": "LoremIpsum",
                        "company": "LoremIpsum"
                    },
                    "department": "LoremIpsum",
                    "missions": "LoremIpsum",
                    "stack": "LoremIpsum",
                    "profile": "LoremIpsum",
                    "experience": "LoremIpsum",
                    "bonus": "LoremIpsum",
                    "hiringProcess": "LoremIpsum",
                    "personalNotes": "LoremIpsum"
                }
            }
        }