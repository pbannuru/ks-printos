from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, text, Boolean
from app.sql_app.database import Base
from sqlalchemy.sql import func

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)  # Identifier for the prompt
    description = Column(Text, nullable=True)  # Optional description of what this prompt is for
    content = Column(Text, nullable=False)  # The actual prompt text
    is_active = Column(Boolean, default=True, nullable=False)  # For toggling without deleting

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


