from typing import List, Optional
from pydantic import BaseModel
from app.sql_app.dbenums.core_enums import (
    PersonaEnum,
    DomainEnum,
    SourceEnum,
    LanguageEnum,
    kzPersonaEnum,
)


class ResponseMetadata(BaseModel):
    size: int
    limit: int
    query: str
    device: Optional[List[str]] = None
    persona: kzPersonaEnum
    domain: DomainEnum
    source: list[SourceEnum]
    language: LanguageEnum


class AutoSuggestResponse(BaseModel):
    metadata: ResponseMetadata
    data: List[str] = []
