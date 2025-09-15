from sqlalchemy.orm import Session
from app.sql_app.dbmodels.prompts import Prompt
from cachetools import TTLCache
from typing import Optional

class PromptService:
    # Cache: store up to 50 prompts, refresh every 300 seconds (5 minutes)
    _cache = TTLCache(maxsize=50, ttl=300)

    def __init__(self, db: Session):
        self.db = db
        self.__model = Prompt

    def get_prompt_by_name(self, name: str) -> Optional[Prompt]:
        """Fetch a prompt by its name (cached)."""
        if name in self._cache:
            return self._cache[name]

        prompt = (
            self.db.query(self.__model)
            .filter(self.__model.name == name, self.__model.is_active == True)
            .first()
        )
        if prompt:
            self._cache[name] = prompt
        return prompt

    def get_all_prompts(self):
        """Fetch all active prompts (no caching for list)."""
        return (
            self.db.query(self.__model)
            .filter(self.__model.is_active == True)
            .all()
        )

    def create_prompt(self, name: str, content: str, description: str = None):
        """Create a new prompt."""
        prompt = self.__model(
            name=name,
            content=content,
            description=description
        )
        self.db.add(prompt)
        self.db.commit()
        self.db.refresh(prompt)
        self._cache[name] = prompt  # ✅ Update cache immediately
        return prompt

    def update_prompt(self, name: str, new_content: str):
        """Update the content of an existing prompt by name."""
        prompt = self.get_prompt_by_name(name)
        if prompt:
            prompt.content = new_content
            self.db.commit()
            self.db.refresh(prompt)
            self._cache[name] = prompt  # ✅ Refresh cache
        return prompt

    def deactivate_prompt(self, name: str):
        """Mark a prompt as inactive."""
        prompt = self.get_prompt_by_name(name)
        if prompt:
            prompt.is_active = False
            self.db.commit()
            if name in self._cache:
                del self._cache[name]  # ✅ Remove from cache
        return prompt
