import json
import re
import time
from opensearchpy import OpenSearch
import pandas as pd
import requests
from app.config import app_config
import logging
from app.config.env import environment
from app.internal.utils.chat_api_utils import get_api_access_token
from app.sql_app.dbenums.core_enums import (
    PersonaEnum,
    DomainEnum,
    SourceEnum,
    LanguageEnum,
    kzPersonaEnum,
)
from app.internal.utils.opensearch_utils import OpenSearchUtils, OpenSearchUtilsData

app_configs = app_config.AppConfig.get_all_configs()
index_configs = app_config.AppConfig.get_sectionwise_configs(
    "upgraded_search_index_values"
)


class OpenSearchService:

    timeout_seconds = app_configs["timeout_seconds"]
    client = OpenSearch(
        hosts=[
            {
                "host": app_configs["host"],
                "port": app_configs["port"],
            }
        ],
        http_auth=(
            app_configs["opensearch_auth_user"],
            environment.AUTH_OPENSEARCH_PASSWORD,
        ),
        use_ssl=eval(app_configs["use_ssl"]),
        verify_certs=eval(app_configs["verify_certs"]),
        ssl_assert_hostname=eval(app_configs["ssl_assert_hostname"]),
        ssl_show_warn=eval(app_configs["ssl_show_warn"]),
        timeout=int(timeout_seconds),
        # 🔑 Connection Pool / Timeout tuning
        # max_retries=3,           # retry failed requests
        # retry_on_timeout=True,   # retry if request times out
        # http_compress=True,      # enable compression
        # maxsize=50,              # max connections in pool per node
    )

    ################ FILTERS FOR HYBRID QUERY ################
    @staticmethod
    def generate_device_filter_for_hybrid_query(
        device: list[str] | None,
        user_search_query: str,
        domain: DomainEnum,
        query_without_product_keyword: str,
    ):
        """
        Get device_filter for the query based on
        if the search query has any matching products
        from product_mapping.csv file
        """
        product_mapping = OpenSearchUtils.get_product_mapping(domain)
        modified_search_query = OpenSearchUtils.remove_unpaired_doublequotes_from_query(
            user_search_query
        )
        query_without_product_keyword_and_unpaired_quotes = (
            OpenSearchUtils.remove_unpaired_doublequotes_from_query(
                query_without_product_keyword
            )
        )
        if device is None:
            for key, device_list in product_mapping.items():
                if f" {key} " in f" {modified_search_query} ":
                    device_list = [str(d).lower() for d in device_list]
                    return [
                        {
                            "bool": {
                                "should": [
                                    {
                                        "bool": {
                                            "must_not": [
                                                {
                                                    "exists": {
                                                        "field": "metadata.products"
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "terms": {
                                            "metadata.products.keyword": device_list
                                        }
                                    },
                                ]
                            }
                        }
                    ], query_without_product_keyword_and_unpaired_quotes
            return (
                [],
                query_without_product_keyword_and_unpaired_quotes,
            )  # Return an empty list if no match is found

        return [
            {
                "bool": {
                    "should": [
                        {
                            "bool": {
                                "must_not": [{"exists": {"field": "metadata.products"}}]
                            }
                        },
                        {"terms": {"metadata.products.keyword": device}},
                    ]
                }
            }
        ], query_without_product_keyword_and_unpaired_quotes

    @staticmethod
    def generate_persona_filter_for_query(persona: PersonaEnum):
        if persona == PersonaEnum.Engineer:
            return []
        else:
            return [{"match": {"metadata.persona": persona.value}}]
        
    @staticmethod
    def generate_kz_persona_filter_for_query(persona: kzPersonaEnum):
        if persona == kzPersonaEnum.HPCE:
            return []
        return [{"term": {"metadata.kz_persona.keyword": persona.value}}]

    @staticmethod
    def generate_exact_match_query_filter(user_search_query: str):
        """
        Get `query_filter` If the `user search query`
        has pair(s) of double quote(s) to get the exact match results.
        """
        # If search query has no double quotes, No 'query_filter' is been used.
        if '"' not in user_search_query:
            return []
        modified_search_query = OpenSearchUtils.remove_unpaired_doublequotes_from_query(
            user_search_query
        )
        query_filter = [
            {
                "query_string": {
                    "query": modified_search_query,
                    "fields": ["text"],
                }
            }
        ]
        return query_filter

    @staticmethod
    def generate_language_filter(language: LanguageEnum):
        return [{"term": {"metadata.language.keyword": language.value}}]

    # @staticmethod
    # def access_token():
    #     url = "https://login-itg.external.hp.com/as/token.oauth2"

    #     headers = {
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         "Cookie": "HPIUIDITG=0LDlPLBnLGAYz4Lmwrgfck",
    #     }

    #     data = {
    #         "grant_type": "client_credentials",
    #         "client_id": "fCVyTLUc1C4yJwnfDSFdc0YMqlzxCrr7",
    #         "client_secret": "gzjWw1GBah37dxueZM7CtytExqaNLNP4KNCXzQTDA5sDBx4gfKpNPMFY1jo7cE2v",
    #     }

    #     response = requests.post(url, headers=headers, data=data, verify = False)

    #     if response.status_code == 200:
    #         return response.json().get("access_token")
    #     else:
    #         print(f"Failed to get token: {response.status_code}")
    #         print(response.text)
    #         return None

    @staticmethod
    def get_text_embedding(input_text):
        try:
            token = get_api_access_token()
            url = (
                "https://davinci-dev-openai-api.corp.hpicloud.net/"
                "knowledgechatbot/openai/deployments/text-embedding-ada-002/"
                "embeddings?api-version=2023-05-15"
            )

            payload = json.dumps(
                {"input": input_text, "model": "text-embedding-ada-002"}
            )

            headers = {
                "api-key": "68201d536a9c4a8c94758292020a33d3",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }

            response = requests.post(url, headers=headers, data=payload, verify = False)
            response.raise_for_status()  # raises error for HTTP status codes like 4xx or 5xx

            data = response.json()
            return data["data"][0]["embedding"]

        except Exception as e:
            print(f"❌ Error during embedding generation: {e}")
            return None

    ################ OPENSEARCH HYBRID QUERY ################
    @staticmethod
    def get_search_query(
        user_search_query: str,
        domain: DomainEnum,
        device: list[str],
        persona: PersonaEnum,
        size: int,
        language: LanguageEnum,
        query_without_product_keyword: str,
    ):

        persona_filter = OpenSearchService.generate_kz_persona_filter_for_query(persona)
        query_filter = OpenSearchService.generate_exact_match_query_filter(
            query_without_product_keyword
        )
        device_filter, query_without_product_keywords = (
            OpenSearchService.generate_device_filter_for_hybrid_query(
                device, user_search_query, domain, query_without_product_keyword
            )
        )
        language_filter = OpenSearchService.generate_language_filter(language)
        print("test_print_query", query_without_product_keywords)

        open_search_query = {
            "size": size,
            "_source": {"excludes": ["vector_field"]},
            "query": {
                "hybrid": {
                    "queries": [
                        {
                            "bool": {
                                "should": [
                                    {
                                        "function_score": {
                                            "query": {
                                                "multi_match": {
                                                    "query": query_without_product_keywords,
                                                    "minimum_should_match": "66%",
                                                    "type": "most_fields",
                                                    "fuzziness": "auto",
                                                    "fields": [
                                                        "metadata.title^7",
                                                        "text",
                                                    ],
                                                    "boost": 7,
                                                }
                                            },
                                            "functions": [
                                                {
                                                    "gauss": {
                                                        "metadata.contentUpdateDate": {
                                                            "origin": "now",
                                                            "scale": "2190d",
                                                            "decay": 0.9,
                                                        }
                                                    },
                                                    "weight": 2,
                                                }
                                            ],
                                            "score_mode": "multiply",
                                        }
                                    },
                                    {
                                        "function_score": {
                                            "query": {
                                                "multi_match": {
                                                    "query": query_without_product_keywords,
                                                    "minimum_should_match": "66%",
                                                    "type": "most_fields",
                                                    "fields": [
                                                        "metadata.title^2",
                                                        "text^3",
                                                    ],
                                                    "analyzer": "word_join_analyzer",
                                                    "boost": 9,
                                                }
                                            },
                                            "functions": [
                                                {
                                                    "gauss": {
                                                        "metadata.contentUpdateDate": {
                                                            "origin": "now",
                                                            "scale": "2190d",
                                                            "decay": 0.9,
                                                        }
                                                    },
                                                    "weight": 2,
                                                }
                                            ],
                                            "score_mode": "multiply",
                                        }
                                    },
                                    {
                                        "function_score": {
                                            "query": {
                                                "multi_match": {
                                                    "query": query_without_product_keywords,
                                                    "type": "phrase",
                                                    "fields": [
                                                        ".metadata.title^2",
                                                        "text",
                                                    ],
                                                    "boost": 4,
                                                    "analyzer": "acronym_synonym_analyzer",
                                                }
                                            },
                                            "functions": [
                                                {
                                                    "gauss": {
                                                        "metadata.contentUpdateDate": {
                                                            "origin": "now",
                                                            "scale": "2190d",
                                                            "decay": 0.9,
                                                        }
                                                    },
                                                    "weight": 2,
                                                }
                                            ],
                                            "score_mode": "multiply",
                                        }
                                    },
                                    {
                                        "function_score": {
                                            "query": {
                                                "multi_match": {
                                                    "query": query_without_product_keywords,
                                                    "type": "bool_prefix",
                                                    "minimum_should_match": "66%",
                                                    "fields": ["text^3"],
                                                    "boost": 6,
                                                }
                                            },
                                            "functions": [
                                                {
                                                    "gauss": {
                                                        "metadata.contentUpdateDate": {
                                                            "origin": "now",
                                                            "scale": "2190d",
                                                            "decay": 0.9,
                                                        }
                                                    },
                                                    "weight": 2,
                                                }
                                            ],
                                            "score_mode": "multiply",
                                        }
                                    },
                                ],
                                "filter": [
                                    *persona_filter,
                                    *language_filter,
                                    *device_filter,
                                    *query_filter,
                                    {"match": {"metadata.Domain": domain.value}},
                                    {"exists": {"field": "metadata.Doc_Status"}},
                                    {
                                        "term": {
                                            "metadata.Doc_Status.keyword": "published"
                                        }
                                    },
                                ],
                            }
                        },
                        {
                            "knn": {
                                "vector_field": {
                                    "vector": OpenSearchService.get_text_embedding(
                                        query_without_product_keywords
                                    ),
                                    "k": 100,
                                    "filter": {
                                        "bool": {
                                            "must": [],
                                            "filter": [
                                                *persona_filter,
                                                *language_filter,
                                                *device_filter,
                                                *query_filter,
                                                {
                                                    "match": {
                                                        "metadata.Domain": domain.value
                                                    }
                                                },
                                                {
                                                    "exists": {
                                                        "field": "metadata.Doc_Status"
                                                    }
                                                },
                                                {
                                                    "term": {
                                                        "metadata.Doc_Status.keyword": "published"
                                                    }
                                                },
                                            ],
                                        }
                                    },
                                }
                            }
                        },
                    ]
                }
            },
            "ext": {
                "rerank": {
                    "query_context": {"query_text": query_without_product_keywords}
                }
            },
        }
        # print(open_search_query)
        return open_search_query

    ################ OPENSEARCH TEMPLATE QUERY ################
    @staticmethod
    def get_search_template_query(
        query_without_stop_words: str,
        domain: DomainEnum,
        device: list[str],
        persona: kzPersonaEnum,
        size: int,
        language: LanguageEnum,
        query_without_product_keyword: str,
    ):
        """
        Fucntion to prepare template based opensearch query to support catalogID/ErrorCode
        search. Below are the scenarios handled:
        - Any search query having two or less words in it, uses `opensearch_template_query`.
        - Opensearch query expects `persona` to be added only when It's `operator`.
        - `exact_match` flag has to be set If there are any paired double quotes in search query.
        - User search query has to be trimmed If It contains any product keywords; and
          matched devices from product mapping dictionary have to be passed to `products` field in query.
          ex: `CA593-00000 12000` will be split into `query`: CA593-00000, `products`: ['HP Indigo 12000 Digital Press', 'HP Indigo 12000HD Digital Press']
        """
        opensearch_template_query = {
            "id": app_configs["upgraded_search_template"],
            "params": {
                "limit": True,
                "size": size,
                "domain": domain.value,
                "language": language.value,
            },
        }

        # Update the template query dictionary based on the scenarios mentioned in docstring.
        if persona != kzPersonaEnum.HPCE:
            opensearch_template_query["params"]["persona"] = persona.value

        doublequote_modified_search_query = (
            OpenSearchUtils.remove_unpaired_doublequotes_from_query(
                query_without_stop_words
            )
        )
        if '"' in doublequote_modified_search_query:
            opensearch_template_query["params"]["exact_match"] = True

        products, search_query_without_product_key = (
            OpenSearchUtils.get_devices_from_query(
                device,
                doublequote_modified_search_query,
                domain,
                query_without_product_keyword,
            )
        )

        opensearch_template_query["params"]["query"] = search_query_without_product_key
        if len(products) >= 1:
            opensearch_template_query["params"]["hasProducts"] = True
            opensearch_template_query["params"]["products"] = products
            opensearch_template_query['params']['product_query'] = OpenSearchUtils.add_device_to_template(products[0])
        if len(search_query_without_product_key.split()) >= 2:
            two_words = True
        else:
            two_words = False
            if OpenSearchUtils.check_catalog_pattern(search_query_without_product_key):
                # print('pattern response ',OpenSearchUtils.check_catalog_pattern(search_query_without_product_key))
                opensearch_template_query["params"]["catalog"] = True
        opensearch_template_query["params"]["two_words"] = two_words
        # print('template for keyword------',opensearch_template_query)
        return opensearch_template_query

    @staticmethod
    def get_search_response(
        user_search_query: str,
        domain: DomainEnum,
        device: list[str],
        persona: kzPersonaEnum,
        size: int,
        source: list[SourceEnum],
        language: LanguageEnum,
    ):
        """
        Returns the response to opensearch query
        """

        source_list = [source_item.value for source_item in source]
        indices = [index_configs[source_name] for source_name in set(source_list)]
        # If there are any stop words in `user_search_query` - Remove.
        user_search_query_lower = user_search_query.lower()
        query_without_stop_words = OpenSearchUtils.remove_stop_words(
            user_search_query_lower
        )
        query_without_unpaired_quotes = (
            OpenSearchUtils.remove_unpaired_doublequotes_from_query(
                query_without_stop_words
            )
        )
        # query_without_product_keyword = OpenSearchUtils.remove_product_keyword_from_search_query(query_without_unpaired_quotes, domain)
        query_without_product_keyword = query_without_unpaired_quotes


        if len(query_without_product_keyword.split()) <= 2:
            
            print('cheking query::::::::::::::::::',query_without_stop_words)
            request_body = OpenSearchService.get_search_template_query(
                query_without_stop_words,
                domain,
                device,
                persona,
                size,
                language,
                query_without_product_keyword,
            )

            search_template_response = OpenSearchService.client.search_template(
                body=request_body, index=indices
            )
            return search_template_response,None
        else:
            search_request_body = OpenSearchService.get_search_query(
                query_without_stop_words,
                domain,
                device,
                persona,
                size,
                language,
                query_without_product_keyword,
            )
            hybrid_search_response = OpenSearchService.client.search(
                index=indices,
                params={"search_pipeline": app_configs["upgraded_search_pipeline"]},
                body=search_request_body,
                request_timeout=30,
            )
            # testdf = pd.DataFrame(hybrid_search_response["hits"]["hits"])
            # testdf.to_csv('testdf.csv')
            # print('records---',hybrid_search_response)
            hybrid_data = []
            for search_hits in hybrid_search_response["hits"]["hits"]:
                
                hybrid_data.append(search_hits["_source"])
                # print('hybrid_response--------------',search_hits)

            rerank_df = pd.DataFrame(hybrid_data)
            # print(hybrid_df['metadata'].apply(lambda x: (x.get('documentID'),x.get('title'),x.get('page_number'))).to_list())
            pairs = [(query_without_stop_words, text) for text in rerank_df["text"]]
            scores = OpenSearchUtilsData.model.predict(pairs)

            rerank_df["score"] = scores

            # 3. Sort by this column
            rerank_df = rerank_df.sort_values(by="score", ascending=False).reset_index(drop=True)

            return None, rerank_df

    @staticmethod
    def execute_custom_search(
        opensearch_query: str,
        source: list[SourceEnum],
    ):
        """
        Returns the response to opensearch query
        """
        request_body = opensearch_query
        source_list = [source_item.value for source_item in source]
        indices = [index_configs[source_name] for source_name in set(source_list)]
        return OpenSearchService.client.search(
            index=indices,
            params={"search_pipeline": app_configs["upgraded_search_pipeline"]},
            body=request_body,
        )

    ################ Auto suggest ################

    def get_auto_suggest_query(
        auto_suggest_term: str,
        device: list[str],
        persona: kzPersonaEnum,
        size: int,
        domain: DomainEnum,
        language: LanguageEnum,
    ):
        auto_suggest_query = {
            "id": app_configs["ph2_autosuggest_template"],
            "params": {
                "search_word": auto_suggest_term,
                "limit": size,
                "products": device,
                "domain": domain.value,
                "language": language.value,
            },
        }
        # If person is engineer we don't send any value. This will get results for all personas.
        # Only for `Operator`, we specify value to filter only `Operator` documents.
        if persona != PersonaEnum.Engineer:
            auto_suggest_query["params"].update({"persona": persona.value})
        return auto_suggest_query

    def get_auto_suggest_response(
        user_search_query: str,
        device: list[str],
        persona: kzPersonaEnum,
        size: int,
        domain: DomainEnum,
        source: list[SourceEnum],
        language: LanguageEnum,
    ):
        """
        Returns the response to opensearch auto suggest query
        """
        request_query = OpenSearchService.get_auto_suggest_query(
            user_search_query, device, persona, size, domain, language
        )
        source_list = [source_item.value for source_item in source]
        indices = [index_configs[source_name] for source_name in set(source_list)]

        return OpenSearchService.client.search_template(
            body=request_query, index=indices
        )

    ################ Logs response details to index ################
    @staticmethod
    def log_search_response(
        user_search_query: str,
        domain: DomainEnum,
        device: list[str],
        persona: kzPersonaEnum,
        source: list[SourceEnum],
        language: LanguageEnum,
        start_time: str,
        timetaken: float,
    ):
        """
        Logs the response to opensearch with given details
        """
        # Combining query parameters with timestamp
        data_to_log_index = {
            "query": user_search_query,
            "domain": domain.value,
            "device": device,
            "persona": persona.value,
            "source": [source_item.value for source_item in source],
            "language": language.value,
            "timestamp": start_time,
            "timetaken": timetaken,
        }

        # Indexing data into 'kcss-v7' index
        logging_response = OpenSearchService.client.index(
            index=app_configs["log_index"], body=data_to_log_index
        )
        if environment.DEBUG_MODE:
            print("logging_response:", logging_response)
        return logging_response