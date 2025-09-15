# Define the graph with just one LLM step
import requests
from app.config import app_config
from app.internal.utils.chat_api_utils import api_access_token
# from app.services.core_search_AI_suggestion_service import core_search_tool
from app.internal.utils.opensearch_utils import OpenSearchUtilsData
from app.sql_app.dbenums.core_enums import *
import ast, re
from datetime import datetime
from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.managed import IsLastStep
from langgraph.prebuilt import ToolNode, InjectedState
from opensearchpy import OpenSearch
from uuid import uuid4
from app.config.env import environment
from openai import AzureOpenAI


app_configs = app_config.AppConfig.get_all_configs()

AZURE_OPENAI_API_KEY = "68201d536a9c4a8c94758292020a33d3"
AZURE_OPENAI_API_VERSION = "2023-05-15"
AZURE_OPENAI_ENDPOINT = (
    "https://davinci-dev-openai-api.corp.hpicloud.net/knowledgechatbot"
)
AZURE_OPENAI_DEPLOYMENT_ID = "gpt-4o-mini"  # Change this for other models


shared_llm_config = dict(
    openai_api_key=AZURE_OPENAI_API_KEY,
    openai_api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    default_headers={
        "Authorization": f"Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IktleSIsInBpLmF0bSI6IjEifQ.eyJzY29wZSI6W10sImF1dGhvcml6YXRpb25fZGV0YWlscyI6W10sImNsaWVudF9pZCI6ImZDVnlUTFVjMUM0eUp3bmZEU0ZkYzBZTXFsenhDcnI3IiwiaXNzIjoiaHR0cHM6Ly9sb2dpbi1pdGcuZXh0ZXJuYWwuaHAuY29tIiwianRpIjoiSjVLdElNUHZaaEd1cXBLMkwzWVBBYSIsImV4cCI6MTc0ODg4NjczNH0.O8dwEc4WPhvnujySAvRq9ITNyYl-tB1cL2dRtnyNDuz3vmZpbyC6CeIdYX0hmIpE6SJAClvCEyEYdJs0ng98lDV4j1x0ybGfMDKZDhbtTmRwmWSHTM025akpAy4OQifZHPsbrdYIxsNVQbKvPtFuJKRewapFzGcl3R9KdIzjMArN72nr6Up7ivGaJpB_BUAl7xU6at-tNIM8yQwurQim16Iygq9izgXv8uhZKXYNy5VjocqYBY7qApvsxxQO6ORJsXbY6WiiFji3ACvQ0iH5ZJveXF87EmzK81Wa_yviC3BqRlY_Tkfb8VD5FiGPLtABxps4BQfTdCIFxkBoEFiVng"
    },  # Authorization:
    # default_headers={"Authorization": f"Bearer {OpenSearchUtils.access_token()}"},
    # http_client=http_client1,
    # http_client = #httpx.Client(verify=ctx),
    streaming=True,
    temperature=0,
)


def create_llm_object():
    token = api_access_token()
    llm = AzureChatOpenAI(
        api_key="68201d536a9c4a8c94758292020a33d3",
        api_version="2023-05-15",
        azure_endpoint="https://davinci-dev-openai-api.corp.hpicloud.net/knowledgechatbot",
        deployment_name="gpt-4o-mini",
        default_headers={"Authorization": f"Bearer {token}"},
        temperature=0.1,
        seed=42,
        # http_client = httpx.Client(verify=ctx)
    )
    # print("llm object created with token----", token)
    return llm


def get_llm_by_model(model_name: str):
    if model_name == "gpt-4o-mini":
        return create_llm_object()
    return models[model_name]


# llm = create_llm_object()
models = {
    "gpt-4o-mini": create_llm_object(),
    "llama-3.1-70b": AzureChatOpenAI(
        deployment_name="llama-3.1-70b", **shared_llm_config
    ),
}


# def build_instruction(domain: str) -> str:
#     return f"""
#         <|begin_of_text|><|start_header_id|>system<|end_header_id|> 
#         1.You are an assistant that answers questions based only on the provided documents.
#         2.Please do not refuse answers unless the question is totally irrelevant, If its totally irrelevant jsut say ** I could not find context with respect to query**.
#         3.you are an expert extraction algorithm specializing in technical documentation for **HP {domain} press**,designed to assist service engineers and support agents in answering technical questions. Your goal is to identify and extract relevant information from technical manuals, product guides, and troubleshooting documentation to provide clear and accurate answers to user queries. 
#         4.Focus on understanding complex technical concepts and providing concise and actionable information that helps resolve issues effectively. 
#         5.If users query is outside of Domain respond with **Sorry, I can only answer questions limited to HP {domain} Industrial presses**.
#         6.If you do not know the value of an attribute asked to extract,just say that you do not know, do not try to make up an answer.
#         7.While Answering check for Domain, You need to respond for the domain which user interested.
#         8. For every paragraph you write, if a source is referenced, use the exact link provided in the data and format it strictly as a Markdown hyperlink:
#             **[Document Title](<exact-link-from-data>)**. 
#             - Always preserve the full URL exactly as provided (including tokens like ?Expires=..., &Signature=..., &Key-Pair-Id=...).
#             - Do not alter, shorten, or replace the link in any way.
#         9.** Answer Style **: 
#         Keep responses concise, neutral, and technical. 
#         Where applicable, provide step-by-step procedures derived from the given context.
#         10. At the end of your commentary: 
#         Create a sources list of book names, paragraph Number, author name, and a link source and page Number to be cited. 
#         For example, if the source is **https://docs.aws.amazon.com/pdfs/amazonglacier/latest/dev/glacier-dg.pdf** and page=340, 
#         then generate the markdown link as **[Source](https://docs.aws.amazon.com/pdfs/amazonglacier/latest/dev/glacier-dg.pdf) and page=340**.
#         11. Do not include any generic support messages like **If you need further assistance, feel free to ask!** or similar statements. Only return technical content relevant to the query.
#             <|eot_id|><|start_header_id|>user<|end_header_id|>
#         ## Personality
#         - Friendly, calm and approachable expert customer service assistant.
#         ## Tone
#         - Warm, concise, confident, never fawning.
#         ## Variety
#         - Do not repeat the same sentence twice.
#         - Vary your responses so it doesn't sound robotic.
#             """



class AgentState(MessagesState):
    safety: LlamaGuardOutput
    is_last_step: IsLastStep
    question: str
    generation: str
    web_search: str
    documents: List[Document]
    domain: DomainEnum
    device: str
    persona: PersonaEnum
    size: int
    source: list[SourceEnum]
    language: LanguageEnum
    citations: List[dict]
    rows: int
    documents: List[dict]


def wrap_model(model: BaseChatModel, instruct: str):
    # model = model.bind_tools(tools)
    preprocessor = RunnableLambda(
        lambda state: [SystemMessage(content=instruct)] + state["messages"],
        name="StateModifier",
    )
    return preprocessor | model




async def acall_model_Final(state: AgentState, config: RunnableConfig):
    # print(state)

    messages = state.get("messages", [])
    if not isinstance(messages, list) or not messages:
        raise ValueError("Invalid or missing 'messages' in state.")

    documents = state.get("documents")
    query = state.get("question") or ""

    if not documents or not documents:
        return {
            "messages": [
                AIMessage(
                    id="no-documents",
                    content="Sorry, no relevant documents were found for your query. Please try rephrasing it.",
                )
            ],
            "question": query,
            "citations": [],
        }

    # Flatten and concatenate document contents to add as system context
    # doc_texts = "\n\n".join(
    #     doc.get("relevant_text", "") for doc in documents.get("data", []) if "relevant_text" in doc
    # )
    doc_texts = "\n\n".join(
    f"### {doc.get('title', 'Untitled')}\n"
    f"**Document ID:** {doc.get('documentID', '')}\n"
    f"**Description:** {doc.get('description', '')}\n"
    f"**Products:** {', '.join(doc.get('products', []))}\n"
    f"**Content:**\n{doc.get('full_text', '')}\n"
    f"[Click to open document]({doc.get('renderLink', '')})"
    for doc in documents
    )
    domain = state.get('domain').value

    instructions_dynamic = OpenSearchUtilsData.prompt

    instructions_dynamic = instructions_dynamic.replace('HP domain press',f"HP {domain} Press OR Digital Press OR Press series")

    enriched_messages = [
        SystemMessage(content=f"Context documents:\n{doc_texts}"),
    ] + messages

    llm = get_llm_by_model(config["configurable"].get("model", "gpt-4o-mini"))
    model_runnable = wrap_model(llm, instructions_dynamic)

    try:
        state["messages"] = enriched_messages
        response = await model_runnable.ainvoke(state, config)
        print("Model response received.")
    except Exception as e:
        print("Error during ainvoke:", e)
        raise

    # Extract documents for citations
    # citations = documents.get("data", [])
    print("printing chat suggestions content----------------------")

    content = response.content
    # print(content)
    final_response = {
        "messages": content,
        # "question": query,
        # "citations": citations, 
    }
    # print(final_response)
    return final_response

agent = StateGraph(AgentState)

# Add only the final processing node
agent.add_node("output", acall_model_Final)

# Set it as the entry point
agent.set_entry_point("output")

# Compile the graph
research_assistant = agent.compile()




async def chat_fetch_result(
    search_query: str,
    domain: str,
    device: str,
    persona: str,
    size: int,
    source: List[str],
    language: str,
    search_results_json,
):
    # print(source)

    inputs = {
    "messages": [
        HumanMessage(content=search_query),
    ],
    "question": search_query,
    "domain": domain,
    "device": device,
    "persona": persona,
    "size": size,
    "source": source,
    "language": language,
    "documents": search_results_json,  # ✅ use this instead of ToolMessage
    "is_last_step": True,
        }
    result = await research_assistant.ainvoke(
        inputs,
        config=RunnableConfig(configurable={"thread_id": uuid4()}),
    )
    print("printing result : -------------------------------------")
    human_messages = [
        message for message in result["messages"] if isinstance(message, HumanMessage)
    ]
    content = "\n\n".join([msg.content for msg in human_messages[1:]])
    print("content:--------------")
    print("--------------------------------------")
    question = result['question']
    documents = result['documents']

    response = {
        "content": content,
        "question": question,
        "citations": documents,
    }
    return response

