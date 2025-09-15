import json
from typing import List
from app.internal.utils.timer import Timer
from app.internal.utils.opensearch_utils import *
from app.services.opensearch_service_upgraded_api import OpenSearchService
from app.dto.core_search_response_model import *
from app.sql_app.dbenums.core_enums import (
    PersonaEnum,
    DomainEnum,
    SourceEnum,
    LanguageEnum,
)

def remove_catalog_number_duplicates(search_data):
    filtered_records = []

    for record in search_data:
        cat_num = getattr(record, "catalog_number", "") or ""
        title = getattr(record, "title", "") or ""

        if cat_num:
            found_in_other_title = False
            for other in search_data:
                if other == record:
                    continue
                other_title = getattr(other, "title", "") or ""
                if cat_num in other_title:
                    found_in_other_title = True
                    break

            if found_in_other_title and (cat_num not in title):
                continue
        
        filtered_records.append(record)

    return filtered_records
class CoreSearchService:

    def __init__(self, db=None):
        self.db = db

    async def search(
        self,
        query: str,
        domain: DomainEnum,
        device: str,
        persona: PersonaEnum,
        size: int,
        source: List[SourceEnum],
        language: LanguageEnum,
    ):

        timer = Timer().start_timer()
        hybrid_response, reranker_response = OpenSearchService.get_search_response(
            query, domain, device, persona, size, source, language
        )

        # response = OpenSearchService.get_search_response(
        #     query, domain, device, persona, size, source, language
        # )
        timer.end_timer()

        # search_start_time_str = timer.strftime("%Y-%m-%d %H:%M:%S")
        OpenSearchService.log_search_response(
            query,
            domain,
            device,
            persona,
            source,
            language,
            timer.start_time_string,
            timer.elapsed_time_ms,
        )
        acronym_dict=OpenSearchUtilsData.acronym_dict

        def is_index_page(text):
            
            # Pattern to detect a repeated special character sequence.
            repeated_special_pattern = re.compile(r'([\W_])(?:\s*\1){5,}')
            
            # Count occurrences of such repeated sequences.
            occurrences = repeated_special_pattern.findall(text)
            repeated_found = len(occurrences) >= 4  # True if 3 or more occurrences are found.

            # Pattern for detecting lines that end with a dotted sequence followed by a page number.
            page_number_pattern = re.compile(r'.*(\. ?){5,}\s*\d+\s*$')
            
            # index-related keywords.
            toc_keywords = {"table of contents", "index", "contents"}
            # Check if any of the keywords appear in the text (case-insensitive).
            keyword_found = any(keyword in text.lower() for keyword in toc_keywords)
            
            
            lines = text.splitlines()
            if not lines:
                return False

            page_pattern_count = sum(1 for line in lines if page_number_pattern.match(line))
            
            total_lines = len(lines)
            dotted_ratio = page_pattern_count / total_lines if total_lines > 0 else 0
            
            if (repeated_found and keyword_found) or (page_pattern_count > 4) or (dotted_ratio > 0.5 and repeated_found):
                return True

            return False

        search_data_list = []
        document_page_keys = set()

        if reranker_response is not None and not reranker_response.empty:

            meta_df = pd.json_normalize(reranker_response["metadata"])

            # Remove "metadata." prefix if needed
            meta_df = meta_df.rename(columns=lambda x: x.replace("metadata.", ""))

            # Join with the other columns (e.g. text)
            final_df = pd.concat([reranker_response.drop(columns=["metadata"]), meta_df], axis=1)
            final_df = final_df.fillna("")
            final_df.rename(columns={'text':'full_text'},inplace=True)
            # filter out index pages
            final_df = final_df[~final_df["full_text"].apply(is_index_page)]

            columns_to_extract = ["documentID","title","catalog_number","description","contentType","contentUpdateDate","language","renderLink",
            "relevant_text","products","page_number","full_text","docLanguageLocaleMap","kz_persona","namedAsset",
            "uuid","thumbnail_url","assetGroup","source","score"]

            cols = [col for col in final_df.columns if col in columns_to_extract]
            rerank_df = final_df[cols]
            rerank_df['relevant_text'] = final_df['full_text'].apply(lambda text: OpenSearchUtils.extract_relevant_text_with_acronyms(
                    query, text, acronym_dict, limit=3))

            response_source = rerank_df.to_dict(orient='records')
            for record in response_source:
                documentID = record['documentID']
                page_number = record['page_number']
                unique_key = f"{documentID}_{page_number}"
                
                if unique_key in document_page_keys:
                    continue
                document_page_keys.add(unique_key)
                search_data_list.append(SearchResponseData(**record))
            
        # --- Step 2: Handle hybrid hits (excluding duplicates) ---
        if hybrid_response:
            # print("hybrid;;;;;;;;;;;;;;;;;;;;;;;;",hybrid_response['took'])
            for search_hits in hybrid_response["hits"]["hits"]:

                response_source = search_hits["_source"]
                full_text = response_source.get("text", "")
                if is_index_page(full_text):
                    continue

                document_id = response_source["metadata"]["documentID"]
                page_number = response_source["metadata"]["page_number"]
                unique_key = f"{document_id}_{page_number}"

                if unique_key in document_page_keys:
                    continue
                document_page_keys.add(unique_key)

                relevant_text = OpenSearchUtils.extract_relevant_text_with_acronyms(
                    query, full_text, acronym_dict, limit=3
                )

                response_source['response_type'] = 'hybrid_response'
                response_source["score"] = search_hits["_score"]
                response_source["documentID"] = document_id
                response_source["title"] = response_source["metadata"]["title"]
                response_source["catalog_number"] = response_source["metadata"].get("catalog_number", "")  # default to empty string if key missing
                response_source["description"] = response_source["metadata"]["description"]
                response_source["contentType"] = response_source["metadata"]["contentType"]
                response_source["contentUpdateDate"] = response_source["metadata"]["contentUpdateDate"]
                response_source["language"] = response_source["metadata"]["language"]
                response_source["renderLink"] = response_source["metadata"].get('renderLink','')
                response_source["relevant_text"] = relevant_text
                response_source["products"] = response_source["metadata"]["products"]
                response_source["page_number"] = response_source["metadata"]["page_number"]
                response_source['full_text'] = full_text
                response_source['docLanguageLocaleMap'] = response_source['metadata'].get('docLanguageLocaleMap',{})
                response_source['kz_persona'] = response_source['metadata'].get('kz_persona','')
                response_source['namedAsset'] = response_source['metadata'].get('namedAsset','')
                response_source['uuid'] = response_source['metadata'].get('uuid','')
                response_source['thumbnail_url'] = response_source['metadata'].get('thumbnail_url','')
                response_source['assetGroup'] = response_source['metadata'].get('assetGroup','')
                response_source['source'] = response_source['metadata'].get('source','')
                search_data_list.append(SearchResponseData(**response_source))



        search_data_list=remove_catalog_number_duplicates(search_data_list)

       
        swapped = True
        while swapped:
            swapped = False
            for i in range(len(search_data_list)):
                for j in range(i + 1, len(search_data_list)):
                    a = search_data_list[i]
                    b = search_data_list[j]

                    if a.title.strip().lower() != b.title.strip().lower():
                        continue

                    score_diff = abs(a.score - b.score)
                    if score_diff >= 1:
                        continue

                    if a.contentUpdateDate < b.contentUpdateDate:
                        # swapping the  scores 
                        a.score, b.score = b.score, a.score
                        # swapping the object in the list
                        search_data_list[i], search_data_list[j] = b, a

                        swapped = True
                        #Print statements for testing
                        # print(
                        #     f"Swapped positions {i}--->{j} "
                        #     f"{a.documentID} ({a.score}, date={a.contentUpdateDate}) ----> {b.documentID} ({b.score}, date={b.contentUpdateDate}) "
                        # )

        # if hybrid_response or reranker_response:
        #     print('entered in to duplicate fixing ')
        # Deduplicate based on documentID and keep record with max score
        # best_records = {}
        # for item in search_data_list:
        #     doc_id = item.documentID
        #     current_score = item.score
        #     if doc_id not in best_records or current_score > best_records[doc_id].score:
        #         best_records[doc_id] = item
        # search_data_list = list(best_records.values())
        # --- Step 3: Create metadata & final response ---
        metadata_obj = SearchResponseMetadata(
            limit=size,
            size=len(search_data_list),
            query=query,
            device=device,
            persona=persona,
            domain=domain,
            source=source,
            language=language,
        )
    
        final_response = SearchResponse(metadata=metadata_obj, data=search_data_list)
        return final_response



