import re,ast
from typing import List
from app.sql_app.dbenums.core_enums import DomainEnum
from app.config import app_config
import pandas as pd
from sentence_transformers import CrossEncoder
from sqlalchemy.orm import Session
from app.sql_app.database import SessionLocal
from app.services.prompt_service import PromptService

app_configs = app_config.AppConfig.get_all_configs()


class OpenSearchUtilsData:
    indigo_product_mapping = None
    pwp_product_mapping = None
    scitex_product_mapping = None
    threeD_product_mapping = None
    stop_words_pattern = ""
    acronym_dict=None
    suggestions_cache = {}
    model = CrossEncoder("app/models/marco", device="cpu")
    prompt = None


class OpenSearchUtils:

    @staticmethod
    def build_instruction() -> str:
    # instructions = OpenSearchUtils.get_prompt()
        db: Session = SessionLocal()
        prompt_service = PromptService(db)
        # Fetch a specific prompt by name
        prompt_obj = prompt_service.get_prompt_by_name("stream_chat")
        instructions = prompt_obj.content
        print('collected prompt-----------------',instructions)
        return f"""{instructions}"""
    
    ################ User search query modification methods ################
    @staticmethod
    def remove_stop_words(user_search_query: str):
        """split `user_search_query` to keep all words inside "" as single word.
        stop words should not be removed from exact match query."""

        # replaces the match with the content of the first capturing group.
        query_without_stop_words = re.sub(
            OpenSearchUtilsData.stop_words_pattern, r"\1", user_search_query
        )
        query_after_extra_space_removal = " ".join(
            query_without_stop_words.split()
        ).strip()
        # if len(query_after_extra_space_removal.split()) <=2:
        #     query_after_extra_space_removal = OpenSearchUtils.add_device_to_query(query_after_extra_space_removal,device)
        return query_after_extra_space_removal
    
    @staticmethod
    def add_device_to_template(device):
        """add device to template if products column length is not zero"""
        common_words_pattern = r'\b(?:hp|pagewide|advantage|web|pwp|Scitex|indigo|digital|press|series|-|color|mono|generic)\b'
        cleaned = re.sub(common_words_pattern, '', device, flags=re.IGNORECASE)
        # Normalize whitespace
        device_clean = re.sub(r'\s+', ' ', cleaned).strip()
        # Add device only if it's not already in query
        # if device_clean.lower() not in query_without_stop_words.lower():
        #     return f"{query_without_stop_words} for {device_clean}"
        return device_clean
    
    @staticmethod
    def remove_product_keyword_from_search_query(user_search_query: str, domain: DomainEnum):
        product_mapping = OpenSearchUtils.get_product_mapping(domain)
        clean_user_search_query = user_search_query.replace('"', '').strip()
        for key, device_list in product_mapping.items():
            if f" {key} " in f" {user_search_query.lower()} ":
                if len(clean_user_search_query.split()) == len(key.split()):
                        return ''
                else:
                    query_without_product_key = user_search_query.replace(
                            key, "", 1
                        ).strip()
                    return query_without_product_key
        return user_search_query

    @staticmethod
    def get_devices_from_query(
        device: list[str] | None, user_search_query: str, domain: DomainEnum, query_without_product_keyword: str
    ):
        """
        If `user_search_query` has two words and one/both of them is product keyword,
        split it and use the first product keyword to fetch device names from `product_mapping`.
        """
        product_mapping = OpenSearchUtils.get_product_mapping(domain)
        if device is None:
            for key, device_list in product_mapping.items():
                device_list = [d for d in device_list]
                if f" {key} " in f" {user_search_query} ":
                    # handles when `user_search_query' is exactly matching product key
                    # ex: user_search_query = "WS6000" or "Mono T400"
                    if len(user_search_query.split()) == len(key.split()):
                        return [], ''
                    # two words in `user_search_query`, First product keyword matched is used to get product list
                    # Next word is passed as `query` to template search.
                    # ex: "WS6000 1OK" --> `WS6000` for product list, `10K` for `query`
                    else:
                        query_without_product_key = user_search_query.replace(
                            key, "", 1
                        ).strip()
                        return device_list, query_without_product_keyword
            return [], query_without_product_keyword
        
        return device, query_without_product_keyword

    @staticmethod
    def remove_unpaired_doublequotes_from_query(value: str):
        """
        Remove - if there is an odd number of double quotes in `user_search_query`.
        """
        double_quote_count = value.count('"')
        if double_quote_count % 2 != 0:
            last_quote_index = value.rfind('"')
            modified_modified_value = (
                value[:last_quote_index] + value[last_quote_index + 1 :]
            )
        else:
            modified_modified_value = value
        return modified_modified_value

    @staticmethod
    def get_acronym_dict():
        path=app_configs['acronym_file']
        df=pd.read_csv(path)
        df['value'] = df['value'].apply(ast.literal_eval)
        acronym_dict = dict(zip(df['key'],df['value']))
        return acronym_dict
    ################  PRODUCT DICTIONARY ################
    @staticmethod
    def get_mapping_dict(mapping_csv):
        df = pd.read_csv(r"{}".format(mapping_csv))
        # Create dictionary<product: [matchstrings] from csv file dataframe
        df["Product"] = df["Product"].apply(
            lambda x: [item.strip() for item in x.split(",")]
        )
        df["MatchString"] = df["MatchString"].apply(lambda x: x.lower())
        return df.set_index("MatchString")["Product"].to_dict()

    @staticmethod
    def get_product_mapping(domain: DomainEnum):
        if domain == DomainEnum.Indigo:
            return OpenSearchUtilsData.indigo_product_mapping
        elif domain == DomainEnum.Scitex:
            return OpenSearchUtilsData.scitex_product_mapping
        elif domain == DomainEnum.ThreeD:
            return OpenSearchUtilsData.threeD_product_mapping
        else:
            return OpenSearchUtilsData.pwp_product_mapping

    @staticmethod
    def get_stop_word_pattern():
        # To avoid matching and removal of overlapping stop words <`a`, `an`, `and`>
        joined_stop_words = "|".join(OpenSearchUtils.stop_words)
        # regex to group double quotes words in one and stop words in another.
        return rf'("[^"]*")|(\b(?:{joined_stop_words})\b)'
    
    @staticmethod
    def extract_relevant_text_with_acronyms(query, text, acronym_dict, limit=3):
        # Split the text into sentences
        sentences = re.split(r'(?<=\.\s)', text)

        # Determine query terms based on acronym_dict and double quotes
        quoted_phrases = re.findall(r'["\'](.*?)["\']', query)
        query_terms = sum(
        [[term] + acronym_dict.get(term.upper(), []) for term in query.split()], []
        )
        
        #Find sentences containing any query terms and count matches
        relevant_sentences = []
        for sentence in sentences: 
            match_count = 0

            #Perform exact match for quoted terms
            for phrase in quoted_phrases:
                if re.search(r'\b' + re.escape(phrase) + r'\b', sentence, re.IGNORECASE):
                    match_count += 5

            match_count += 5 if query.lower() in sentence.lower() else 0

            match_count  += sum(
                (0.5 if term in OpenSearchUtils.stop_words else 1)
                for term in query_terms
                if re.search(re.escape(term), sentence, re.IGNORECASE))
            if match_count > 0:
                relevant_sentences.append((sentence, match_count))
        
        
        #Sorting sentences by number of matches
        relevant_sentences.sort(key=lambda x: x[1], reverse=True)
        
        #Limit the number of sentences
        top_sentences = [sentence for sentence, _ in relevant_sentences[:limit]]
        return " ".join(top_sentences)
    
    @staticmethod
    def check_catalog_pattern(text: str) -> bool:
        patterns = {
            "C[0-9]{8}": re.compile(r"C[0-9]{8}",re.IGNORECASE),
            "(CA|CX|TS|CT|CU)[a-zA-Z0-9]{3}-[0-9]{5}": re.compile(r"(CA|CX|TS|CT|CU)[a-zA-Z0-9]{3}-[0-9]{5}",re.IGNORECASE),
            "P[0-9]{2}-[0-9]{4}": re.compile(r"P[0-9]{2}-[0-9]{4}",re.IGNORECASE),
            "PPC-[0-9]{6}": re.compile(r"PPC-[0-9]{6}",re.IGNORECASE),
            "(ITN|T|Q)[0-9]{4}(-[0-9]{5})?": re.compile(r"(ITN|T|Q)[0-9]{4}(-[0-9]{5})?",re.IGNORECASE),
            "(XRS|TN|CN|XR|MNU)-[0-9]{4}": re.compile(r"(XRS|TN|CN|XR|MNU)-[0-9]{4}",re.IGNORECASE),
            r"\d{4,6}-\d{3,5}": re.compile(r"\d{4,6}-\d{3,5}",re.IGNORECASE)
        }
        return any(regex.search(text) for regex in patterns.values())
    
    @staticmethod
    def init():
        # reads app/assets/*.csv to prepare product_mapping dict
        OpenSearchUtilsData.indigo_product_mapping = OpenSearchUtils.get_mapping_dict(
            app_configs["indigo_file"]
        )

        OpenSearchUtilsData.pwp_product_mapping = OpenSearchUtils.get_mapping_dict(
            app_configs["pwp_file"]
        )

        OpenSearchUtilsData.scitex_product_mapping = OpenSearchUtils.get_mapping_dict(
            app_configs["scitex_file"]
        )
        OpenSearchUtilsData.threeD_product_mapping = OpenSearchUtils.get_mapping_dict(
            app_configs["threed_file"]
        )

        OpenSearchUtilsData.acronym_dict=OpenSearchUtils.get_acronym_dict()
        OpenSearchUtilsData.stop_words_pattern = OpenSearchUtils.get_stop_word_pattern()
        OpenSearchUtilsData.prompt = OpenSearchUtils.build_instruction()

        # List of stop words to remove from `user_search_query` for core search API.

    stop_words = [
        "and",
        "an",
        "a",
        "are",
        "was",
        "as",
        "that",
        "at",
        "be",
        "but",
        "by",
        "for",
        "if",
        "into",
        "is",
        "it",
        "no",
        "not",
        "of",
        "on",
        "or",
        "such",
        "their",
        "there",
        "these",
        "they",
        "then",
        "the",
        "this",
        "to",
        "will",
        "with",
    ]
