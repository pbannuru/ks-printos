from collections import defaultdict
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Body
from typing import Annotated, List, Optional, Dict,Any
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, field_validator
from app.dto.core_search_response_model import SearchResponse
from app.internal.utils.chat_api_utils import bulkrenderlink
from app.internal.utils.opensearch_utils import OpenSearchUtilsData
from app.middlewares.authentication import JWTBearerTenantApiSwaggerAuthenticated
from app.services.chat_search import chat_fetch_result
from app.services.core_search_service_upgraded import CoreSearchService
from app.config import app_config
from app.services.extras_kaas_service import RenderLinkService
from app.services.opensearch_service_upgraded_api import OpenSearchService
from app.sql_app.dbenums.core_enums import PersonaEnum, DomainEnum, SourceEnum, LanguageEnum, kzPersonaEnum
from app.internal.utils.api_rate_limiter import limiter
from app.internal.utils.exception_examples import response_example_search_with_ai_suggestion
from fastapi.responses import StreamingResponse
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import asyncio, re
import json, regex



router = APIRouter(
    prefix="/stream_chat",
    tags=["search_chat_streaming"],
)

app_configs = app_config.AppConfig.get_all_configs()
limiter_str = app_configs["chat_search_limit"] + "/minute"

async def event_stream_chat_response(query, domain, device, persona, size, source, language,include_suggestion: bool):
    # Step 1: Call OpenSearch
    search_result = await CoreSearchService(None).search(query, domain, device, persona, size, source, language)
    search_results = search_result.model_dump()
    metadata = search_results['metadata']
    data = search_results['data']

    grouped_data = defaultdict(lambda: {
        "page_number": [],
        "full_text": "",
        "relevant_text": None,
        "score": None,
        "title": None,
        "description": None,
        "contentType": None,
        "contentUpdateDate": None,
        "parentDoc": None,
        "language": None,
        "renderLink": None,
        "products": None,
        'docLanguageLocaleMap': None,
        'kz_persona': None,
        'namedAsset':None,
        'uuid': None,
        'thumbnail_url': None,
        'source': None,
    })

    for i in data:
        docid = i["documentID"]

        # Append page_number to list
        grouped_data[docid]["page_number"].append(i["page_number"])

        # Concatenate full_text as string
        grouped_data[docid]["full_text"] += i.get("full_text", "")

        # Set only the first value (non-None) for other fields
        for field in [
            "relevant_text", "score", "title", "description", "contentType",
            "contentUpdateDate", "parentDoc", "language", "renderLink", "products",'docLanguageLocaleMap',
            'kz_persona','namedAsset','uuid','thumbnail_url','source',
        ]:
            if grouped_data[docid][field] is None:
                grouped_data[docid][field] = i.get(field)

    # Now convert grouped_data to list of dicts
    merged_data = [
        {
            "documentID": docid,
            "score": values["score"],
            "title": values["title"],
            "description": values["description"],
            "contentType": values["contentType"],
            "contentUpdateDate": values["contentUpdateDate"],
            "parentDoc": values["parentDoc"],
            "language": values["language"],
            "renderLink": values["renderLink"],
            "page_number": values["page_number"],
            "products": values["products"],
            "relevant_text": values["relevant_text"],
            "full_text": values["full_text"],
            'docLanguageLocaleMap': values['docLanguageLocaleMap'],
            'kz_persona': values['kz_persona'],
            'namedAsset': values['namedAsset'],
            'uuid': values['uuid'],
            'thumbnail_url': values['thumbnail_url'],
            'source': values['source']
        }
        for docid, values in grouped_data.items()
    ]
    # print('printing merged data----------------')
    # print(merged_data)
    yield json.dumps(jsonable_encoder({'search': {'metadata': metadata, 'data': merged_data}})) + "\n\n"

    await asyncio.sleep(0.1)

    if include_suggestion:

        pattern = r"^[\p{L}\p{N}\s\-/(),_. ;:?!]+$" # Allows Letters from any language/script (Unicode letters) via \p{L}, numbers, spaces, hyphens, slashes, and colons
        
        if len(query) > 400:
            raise ValueError("Search query must not exceed 400 characters.")
        
        if not regex.match(pattern, query):
            raise ValueError("Search query can only contain alphabets, numbers, spaces, and date formats (YYYY-MM-DD or MM/DD/YYYY).")
        value_clean = query.strip().rstrip(".!?,;:")
        query_emb = OpenSearchService.get_text_embedding(value_clean)
        query_vec = np.array(query_emb).reshape(1, -1)

        emb_df= pd.read_pickle(app_configs['query_embidding_path'])
        threat_vecs = np.vstack(emb_df["embeddings"].values)
        similarity_scores = cosine_similarity(query_vec, threat_vecs)[0]
        max_similarity = np.max(similarity_scores)
        word_count = len(value_clean.split())
        # set threshold
        if word_count <= 2:
            threshold = 0.84
        else:
            threshold = 0.80
        print("similarity score",max_similarity)
        if max_similarity > threshold:   #checks if score is >=0.80 then rejects the query
            raise ValueError("Search query is out of my scope. Please ask a valid query.")

        # data = [r for r in search_results['data'] if r.get("response_type") == "reranker_response"]
        data= data[:10]
        renderlinks_input = defaultdict(list)
        for r in data:
            documentID = r['documentID']
            language = r['language'].value

            if documentID.startswith("ish_") or documentID.startswith("pdf_") or documentID.startswith("c0"):
                renderlinks_input[language].append(documentID)
                # bulkrenderlink()
        for key, value in renderlinks_input.items():
            links = await bulkrenderlink(value,key)
            # print('bulk render link response---------',links)

            for r in data:
                documentID = r['documentID']
                if documentID in links.keys():
                    r['renderLink']=links[documentID]
        # for r in data:
        #     documentID = r['documentID']
            # print(documentID,"-------------",r['renderLink'])
        suggestion = await chat_fetch_result(
            query, domain, device, persona, size, source, language, data
        )
        # print("printing suggestions -----------------")
        # print(suggestion)
        yield json.dumps(jsonable_encoder({'ai_suggestion': suggestion})) + "\n\n"

class SearchRequestBody(BaseModel):
    query: str
    device: Optional[List[str]] = None  # default None if not provided

@router.post(
    "",
    summary="Stream Search + AI Suggestion",
    responses=response_example_search_with_ai_suggestion,
)
@limiter.limit(limiter_str)
async def stream_chat(
    request: Request,
    domain: Annotated[DomainEnum, Query(description="Data domain to be searched")],
    language: Annotated[LanguageEnum, Query(description="Document language to search for")] = LanguageEnum.English,
    # device: Annotated[str | None, Query(max_length=128, description="Device for which the query refers to")] = None,
    persona: Annotated[kzPersonaEnum, Query(description="Role of the user")] =kzPersonaEnum.PressOperatorLevel3,
    size: Annotated[int, Query(description="Maximum number of results to return.", gt=0, le=50)] = 20,
    source: Annotated[List[SourceEnum], Query(description="Source to search from. All option searches all sources in the list.")] = [SourceEnum.All],
    include_suggestion: Annotated[bool, Query(description="Include AI suggestion step", example=True)] = True,
    include_stream: Annotated[bool, Query(description="Include streaming", example=True)] = True,
    body: SearchRequestBody = Body(..., description="Body containing the search query"),
    profile: bool = Query(False, description="Enable profiling (default: False)"),
    token_payload=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
    ):
    query = body.query
    device = body.device

    # if not query:
    #     default_result = await fetch_default_results(domain, device, persona, size, source, language)
    #     return {
    #         "search": default_result,   # keep same structure as normal
    #         "ai_suggestion": None       # no suggestion when no query
    #     }
    
    if include_stream:
        return StreamingResponse(
            event_stream_chat_response(query, domain, device, persona, size, source, language, include_suggestion),
            media_type="text/event-stream",
        )
    else:
        search_result = await CoreSearchService(None).search(query, domain, device, persona, size, source, language)
        search_results = search_result.model_dump()
        data = search_results['data']

        grouped_data = defaultdict(lambda: {
            "page_number": [],
            "full_text": "",
            "relevant_text": None,
            "score": None,
            "title": None,
            "description": None,
            "contentType": None,
            "contentUpdateDate": None,
            "parentDoc": None,
            "language": None,
            "renderLink": None,
            "products": None,
            'docLanguageLocaleMap': None,
            'kz_persona': None,
            'namedAsset':None,
            'uuid': None,
            'thumbnail_url': None,
            'source':None,
        })


        for i in data:
            docid = i["documentID"]

            # Append page_number to list
            grouped_data[docid]["page_number"].append(i["page_number"])

            # Concatenate full_text as string
            grouped_data[docid]["full_text"] += i.get("full_text", "")

            # Set only the first value (non-None) for other fields
            for field in [
                "relevant_text", "score", "title", "description", "contentType",
                "contentUpdateDate", "parentDoc", "language", "renderLink", "products",'docLanguageLocaleMap',
                'kz_persona','namedAsset','uuid','thumbnail_url','source',
            ]:
                if grouped_data[docid][field] is None:
                    grouped_data[docid][field] = i.get(field)

        # Now convert grouped_data to list of dicts
        merged_data = [
            {
                "documentID": docid,
                "score": values["score"],
                "title": values["title"],
                "description": values["description"],
                "contentType": values["contentType"],
                "contentUpdateDate": values["contentUpdateDate"],
                "parentDoc": values["parentDoc"],
                "language": values["language"],
                "renderLink": values["renderLink"],
                "page_number": values["page_number"],
                "products": values["products"],
                "relevant_text": values["relevant_text"],
                "full_text": values["full_text"],
                'docLanguageLocaleMap': values['docLanguageLocaleMap'],
                'kz_persona': values['kz_persona'],
                'namedAsset': values['namedAsset'],
                'uuid': values['uuid'],
                'thumbnail_url': values['thumbnail_url'],
                'source': values['source']
            }
            for docid, values in grouped_data.items()
        ]

        if include_suggestion:
            pattern = r"^[\p{L}\p{N}\s\-/(),_. ;:?!]+$" # Allows Letters from any language/script (Unicode letters) via \p{L}, numbers, spaces, hyphens, slashes, and colons
        
            if len(query) > 400:
                raise ValueError("Search query must not exceed 400 characters.")
            
            if not regex.match(pattern, query):
                raise ValueError("Search query can only contain alphabets, numbers, spaces, and date formats (YYYY-MM-DD or MM/DD/YYYY).")
            value_clean = query.strip().rstrip(".!?,;:")
            query_emb = OpenSearchService.get_text_embedding(value_clean)
            query_vec = np.array(query_emb).reshape(1, -1)

            emb_df= pd.read_pickle(app_configs['query_embidding_path'])
            threat_vecs = np.vstack(emb_df["embeddings"].values)
            similarity_scores = cosine_similarity(query_vec, threat_vecs)[0]
            max_similarity = np.max(similarity_scores)

            word_count = len(value_clean.split())
            # set threshold
            if word_count <= 2:
                threshold = 0.84
            else:
                threshold = 0.80
            print("similarity score",max_similarity)
            if max_similarity > threshold:   #checks if score is >=0.80 then rejects the query
                raise ValueError("Search query is out of my scope. Please ask a valid query.")
            # data = [r for r in search_results['data'] if r.get("response_type") == "reranker_response"]
            data = data[:10]
            renderlinks_input = defaultdict(list)
            for r in data:
                documentID = r['documentID']
                language = r['language'].value

                if documentID.startswith("ish_") or documentID.startswith("pdf_") or documentID.startswith("c0"):
                    renderlinks_input[language].append(documentID)
                    
                    # bulkrenderlink()
            for key, value in renderlinks_input.items():
                links = await bulkrenderlink(value,key)
                # print('bulk render link response---------',links)
                for r in data:
                    documentID = r['documentID']
                    if documentID in links.keys():
                        r['renderLink']=links[documentID]

            suggestion = await chat_fetch_result(query, domain, device, persona, size, source, language, data)
        else:
            suggestion = None

        return {
            "search": {
                "metadata": search_results['metadata'],
                "data": merged_data
            },
            "ai_suggestion": suggestion,
        }
    
    