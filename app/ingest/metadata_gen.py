import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from app.settings import METADATA_MODEL, OLLAMA_BASE_URL


VALID_EMBEDDING_MODES = {
    "none",
    "summary_only",
    "full_text_chunks",
    "table_summaries",
    "hybrid_text_and_table",
    "code_chunks",
}

VALID_RETRIEVAL_MODES = {
    "metadata_filter",
    "semantic_search",
    "keyword_search",
    "table_lookup",
    "dataframe_query",
    "structured_field_lookup",
    "code_symbol_search",
    "full_document_injection",
}

VALID_STORAGE_TARGETS = {
    "metadata_store",
    "vector_db",
    "table_store",
    "dataframe_store",
    "structured_json_store",
    "keyword_index",
    "raw_file_store",
}

VALID_TABLE_HANDLING = {
    "none",
    "extract_tables_separately",
    "preserve_as_dataframe",
    "extract_fields_and_items",
    "preserve_log_events",
}

DEFAULT_METADATA = {
    "document_type": "unknown",
    "document_purpose": "",
    "summary": "",
    "topics": [],
    "important_keywords": [],
    "contains_tables": False,
    "is_structured_data": False,
    "content_structure": "unknown",
    "embedding_mode": "full_text_chunks",
    "retrieval_modes": [
        "metadata_filter",
        "semantic_search"
    ],
    "storage_targets": [
        "metadata_store",
        "vector_db"
    ],
    "chunking_strategy": "semantic_sections",
    "table_handling": "none",
    "language": "unknown",
    "estimated_information_density": "medium",
    "possible_user_queries": []
}


llm = ChatOllama(
    model=METADATA_MODEL,
    temperature=0,
    base_url=OLLAMA_BASE_URL,
)


prompt = ChatPromptTemplate.from_template(
    """
You are an intelligent document analysis and routing system for an advanced agentic RAG pipeline.

Your job is to analyze uploaded files and generate a retrieval profile that will later be used for:

1. document relevance filtering
2. semantic retrieval routing
3. chunking decisions
4. embedding decisions
5. storage decisions
6. downstream agent/tool selection

The generated metadata will determine:
- whether the file should be embedded
- how the file should be embedded
- where processed outputs should be stored
- which retrieval methods should process the file

You must classify the document carefully.

IMPORTANT:

Embedding retrieval is useful mainly for:
- long-form semantic text
- research papers
- documentation
- contracts
- reports
- rulebooks
- articles
- notes
- manuals

Embedding retrieval is usually NOT useful for:
- spreadsheets
- structured tabular data
- invoices
- order databases
- CSV exports
- transaction logs
- highly numeric tables
- records with strict row/column structure

For structured/tabular documents, retrieval systems should usually:
- preserve tables or rows as structured data
- use table lookup or dataframe querying
- avoid normal prose chunk embeddings unless table summaries are useful

Do not assume one universal retrieval strategy. Different files should get different retrieval profiles.

Analyze the following document.

Return ONLY valid JSON.

Document:
{document}

JSON format:
{{
    "document_type": "",
    "document_purpose": "",
    "summary": "",
    "topics": [],
    "important_keywords": [],
    "contains_tables": false,
    "is_structured_data": false,
    "content_structure": "",
    "embedding_mode": "",
    "retrieval_modes": [],
    "storage_targets": [],
    "chunking_strategy": "",
    "table_handling": "",
    "language": "",
    "estimated_information_density": "",
    "possible_user_queries": []
}}

Field requirements:

document_type:
- classify the document category

document_purpose:
- explain what the document is used for

summary:
- concise semantic summary

topics:
- major semantic subjects

important_keywords:
- retrieval-critical keywords

contains_tables:
- true if tables exist

is_structured_data:
- true for spreadsheets, records, transaction tables, structured datasets

content_structure:
Choose a concise label such as:
- long_form_text
- text_with_tables
- spreadsheet
- semi_structured_form
- log_or_timeseries
- code
- mixed

embedding_mode:
Choose ONE:
- none
- summary_only
- full_text_chunks
- table_summaries
- hybrid_text_and_table
- code_chunks

retrieval_modes:
Choose one or more:
- metadata_filter
- semantic_search
- keyword_search
- table_lookup
- dataframe_query
- structured_field_lookup
- code_symbol_search
- full_document_injection

storage_targets:
Choose one or more:
- metadata_store
- vector_db
- table_store
- dataframe_store
- structured_json_store
- keyword_index
- raw_file_store

Rules:
- Pure long-form text: embedding_mode full_text_chunks; retrieval_modes metadata_filter and semantic_search; storage_targets metadata_store and vector_db.
- Text with tables: embedding_mode hybrid_text_and_table; retrieval_modes metadata_filter, semantic_search, and table_lookup; storage_targets metadata_store, vector_db, and table_store.
- Pure spreadsheets/CSV/Excel: embedding_mode none or summary_only; retrieval_modes metadata_filter and dataframe_query; storage_targets metadata_store and dataframe_store.
- Semi-structured documents such as invoices, receipts, purchase orders, resumes, forms, and certificates: embedding_mode summary_only; retrieval_modes metadata_filter and structured_field_lookup; storage_targets metadata_store and structured_json_store.
- Logs and time-series text: embedding_mode none or summary_only; retrieval_modes metadata_filter and keyword_search; storage_targets metadata_store, keyword_index, and structured_json_store.
- Code files: embedding_mode code_chunks; retrieval_modes metadata_filter, semantic_search, and code_symbol_search; storage_targets metadata_store, vector_db, and keyword_index.

chunking_strategy:
Choose ONE:
- semantic_sections
- semantic_sections_with_tables
- fixed_chunks
- row_based
- page_based
- no_chunking
- event_based
- time_based
- function_class_based

table_handling:
Choose ONE:
- none
- extract_tables_separately
- preserve_as_dataframe
- extract_fields_and_items
- preserve_log_events

estimated_information_density:
Choose ONE:
- low
- medium
- high

possible_user_queries:
- likely questions users may ask about this document

Return ONLY valid JSON.
"""
)


def parse_metadata_response(content: str) -> dict:
    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start:end + 1])

        raise


def ensure_list(value):
    if isinstance(value, list):
        return value

    if value in (None, ""):
        return []

    return [value]


def normalize_metadata(metadata: dict) -> dict:
    normalized = DEFAULT_METADATA.copy()
    normalized.update(metadata)

    normalized["topics"] = ensure_list(normalized.get("topics"))
    normalized["important_keywords"] = ensure_list(
        normalized.get("important_keywords")
    )
    normalized["possible_user_queries"] = ensure_list(
        normalized.get("possible_user_queries")
    )

    embedding_mode = normalized.get("embedding_mode")
    if embedding_mode not in VALID_EMBEDDING_MODES:
        embedding_mode = DEFAULT_METADATA["embedding_mode"]
    normalized["embedding_mode"] = embedding_mode

    retrieval_modes = [
        mode
        for mode in ensure_list(normalized.get("retrieval_modes"))
        if mode in VALID_RETRIEVAL_MODES
    ]
    if "metadata_filter" not in retrieval_modes:
        retrieval_modes.insert(0, "metadata_filter")
    normalized["retrieval_modes"] = retrieval_modes

    storage_targets = [
        target
        for target in ensure_list(normalized.get("storage_targets"))
        if target in VALID_STORAGE_TARGETS
    ]
    if "metadata_store" not in storage_targets:
        storage_targets.insert(0, "metadata_store")
    normalized["storage_targets"] = storage_targets

    table_handling = normalized.get("table_handling")
    if table_handling not in VALID_TABLE_HANDLING:
        table_handling = DEFAULT_METADATA["table_handling"]

    content_structure = normalized.get("content_structure")
    if content_structure == "text_with_tables":
        table_handling = "extract_tables_separately"
    elif content_structure == "spreadsheet":
        table_handling = "preserve_as_dataframe"

    normalized["table_handling"] = table_handling

    return normalized


def generate_metadata(text: str) -> dict:

    sample = text[:6000]

    chain = prompt | llm

    response = chain.invoke({
        "document": sample
    })

    content = response.content

    try:
        metadata = parse_metadata_response(content)

    except Exception:
        metadata = DEFAULT_METADATA.copy()
        metadata["summary"] = content

    return normalize_metadata(metadata)
