from app.config import app_config
from app.internal.utils.chat_api_utils import api_access_token, getKaasLink
from app.internal.utils.opensearch_utils import OpenSearchUtils
from app.services.core_search_service_upgraded import CoreSearchService
from langgraph.prebuilt import InjectedState
from langchain_core.documents import Document
from langchain_core.tools import tool
from typing import Literal, List, Annotated

app_configs = app_config.AppConfig.get_all_configs()

@tool
async def core_search_tool(query, state: Annotated[dict, InjectedState]):
    """this will communicate with search api and get response based on the query and filters given by user"""
    # print("State received by core_search:", state)  # Log the state for debugging
    print("============Entered core_search service method================")
    user_search_query = state.get("question", "")
    domain = state.get("domain", "")
    device = state.get("device") or None
    print(f"=========Device is {device}========")
    persona = state.get("persona", "")
    size = state.get("size", 20)
    source = state.get("source", [])
    language = state.get("language", "en")


    print('params send to tool-------------')
    print(domain,device,persona,size,source,language)

    response = await CoreSearchService(None).search(
        query, domain, device, persona, size, source, language
    )
    result=response.model_dump()

    # client.search
    print("Docs in retrice_mmr")
    # count=result.get('metadata', {}).get('size', 0)
    # print("count--------------:",count)
    open_docs=[]
    count=result.get('metadata', {}).get('size', 0)
    kaas_render_link =app_configs['extras_kaas_render_url']
    token = api_access_token()
    print("search_result---------------------------",result)

    for r in result['data']:
        documentID = r['documentID']
        print('documentID and its link ------------',documentID)
        if documentID.startswith("pdf_") or documentID.startswith("c0") or documentID.startswith('ish'):
            r['renderLink'] = getKaasLink(kaas_render_link + documentID,token)
            print(r['renderLink'])
    for r in result['data']:
        metadata = {k: v for k, v in r.items() if k != "relevant_text"}
        print('metadata',metadata)
        open_docs.append(
            Document(
                page_content=r["relevant_text"],
                metadata=metadata
            )
        )
    state["rows"]=count

    return open_docs
