from datetime import datetime
from typing import Annotated, Optional, List
from pydantic import BaseModel, StringConstraints
from app.sql_app.dbenums.core_enums import (
    DomainEnum,
    PersonaEnum,
    SourceEnum,
    LanguageEnum,
    kzPersonaEnum,
)

class SearchResponseMetadata(BaseModel):
    limit: int
    size: int
    query: str
    devices: Optional[List[str]] = None  
    persona: kzPersonaEnum
    domain: DomainEnum
    source: List[SourceEnum]
    language: LanguageEnum


class SearchResponseData(BaseModel):
    documentID: str
    score: float
    title: str
    description: str
    contentType: str
    contentUpdateDate: datetime
    score: Optional[float] = None
    parentDoc: Optional[str] = None
    page_number: int
    language: LanguageEnum
    renderLink: Optional[str] = None
    products: list[str] = []
    relevant_text: Optional[str] = None
    full_text :Optional[str] = None
    response_type: Optional[str] = None
    docLanguageLocaleMap: Optional[dict] = None
    kz_persona: Optional[str | list[str]] = None
    namedAsset: Optional[str] = None
    uuid :Optional[str] = None
    thumbnail_url:Optional[str] = None
    assetGroup: Optional[str] = None
    source: Optional[str] = None


class SearchResponse(BaseModel):
    metadata: SearchResponseMetadata
    data: list[SearchResponseData]
