from datetime import datetime
from pydantic import BaseModel

from app.sql_app.dbenums.core_enums import kzPersonaEnum
from app.sql_app.dbmodels.isearchui_search_feedback import ImpressionEnum, PersonaEnum


class CreateFeedbackDto(BaseModel):
    impression: ImpressionEnum

    search_text: str
    search_device: list[str]
    # search_persona: kzPersonaEnum
    kz_search_persona: kzPersonaEnum
    feedback_text: str
    feedback_by: str

    on_document_id: str
    on_document_title: str
    on_document_description: str

    on_result_position: int


class EditFeedbackImpressionDto(BaseModel):
    impression: ImpressionEnum

    class Config:
        orm_mode = True


class EditFeedbackTextDto(BaseModel):
    feedback_text: str

    class Config:
        orm_mode = True
