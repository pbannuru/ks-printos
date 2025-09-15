from fastapi import APIRouter, FastAPI, Depends, Query, Request
from pydantic import BaseModel, field_validator
from typing import Optional, Union, List
from uuid import uuid4
from app.config import app_config
from app.internal.utils.chat_api_utils import api_access_token, get_text_embedding, update_markdown_links
from app.services.chat_api_service import fetch_result
from app.sql_app.dbenums.core_enums import DomainEnum, LanguageEnum, PersonaEnum, SourceEnum
from pydantic import BaseModel
from app.middlewares.authentication import JWTBearerTenantApiSwaggerAuthenticated
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from app.internal.utils.exception_examples import response_example_search
from app.internal.utils.api_rate_limiter import limiter

router = APIRouter(
    prefix="/Chat_API",
    tags=["chat_AI_suggestions"],
)

app_configs = app_config.AppConfig.get_all_configs()
limit_string = app_configs["chat_api_limit"] + "/minute"

class SearchRequest(BaseModel):
    search_query: str
    domain: DomainEnum
    device: Optional[str] = ""  # Optional with default empty string
    persona: PersonaEnum
    size: int = 5  # Default value
    source: List[SourceEnum] # Can be None (default) or a specific index
    language: LanguageEnum  # Default value

    @field_validator("search_query")
    def validate_search_query(cls, value):
        """Ensure search query contains only alphabets, numbers, and date formats (YYYY-MM-DD or MM/DD/YYYY)."""
        pattern = r"^[a-zA-Z0-9\s\-/(),_. :?!]+$"  # Allows letters, numbers, spaces, hyphens, slashes, and colons
        
        if len(value) > 400:
            raise ValueError("Search query must not exceed 400 characters.")
        
        if not re.match(pattern, value):
            raise ValueError("Search query can only contain alphabets, numbers, spaces, and date formats (YYYY-MM-DD or MM/DD/YYYY).")
        
        value_clean = value.strip().rstrip(".!?,;:")
        query_emb = get_text_embedding(value_clean)
        query_vec = np.array(query_emb).reshape(1, -1)

        emb_df= pd.read_pickle(app_configs['query_embidding_path'])
        threat_vecs = np.vstack(emb_df["embeddings"].values)
        similarity_scores = cosine_similarity(query_vec, threat_vecs)[0]
        max_similarity = np.max(similarity_scores)

        if max_similarity > 0.80:   #checks if score is >=0.80 then rejects the query
            raise ValueError("Search query is out of my scope. Please ask a valid query.")

        return value
    
@router.put(
    "",
    summary="Chat API for getting the data for entered filters and matching query in body of request",
    responses=response_example_search
)
@limiter.limit(limit_string)
async def search_route(request: Request , searchRequest: SearchRequest,token_payload=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
                       profile: bool = Query(False, description="Enable profiling (default: False)") ):

# async def search_route(request: SearchRequest):
    index_configs = app_config.AppConfig.get_sectionwise_configs("index_values")
    # source_list = [source_item.value for source_item in searchRequest.source]
    # indices = [index_configs[source_name] for source_name in set(source_list)]

    # print(f"=======Extracted params are query -> {searchRequest.search_query}, domain -> {}")
    # Fetch results using async function
    result = await fetch_result(
        search_query=searchRequest.search_query,
        domain=searchRequest.domain,
        device=searchRequest.device,
        persona=searchRequest.persona,
        size=searchRequest.size,
        source=searchRequest.source, #[s.value for s in searchRequest.source],  # Passing list if no source is provided
        language=searchRequest.language,
    )
    print(f"============Source is {searchRequest.source}================")
    token_payload = api_access_token()
    post_process_res = update_markdown_links(result["content"],token_payload)
    result["content"]=post_process_res

    return result
