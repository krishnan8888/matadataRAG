from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from app.settings import ANSWER_MODEL, OLLAMA_BASE_URL

ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """
You are the final answer stage of a retrieval-augmented generation system.

Answer the user's question using ONLY the retrieved context below.

Rules:
- Do not invent facts that are not present in the context.
- If the context is insufficient, say exactly what information is missing.
- Prefer a direct, concise answer.
- When useful, mention the source document name in parentheses.
- Do not mention internal retrieval scores, chunk IDs, or implementation details.

User question:
{query}

Retrieved context:
{context}

Answer:
"""
)


def generate_answer(query: str, context: str) -> str:
    if not context.strip():
        return (
            "I could not find relevant context in the ingested documents "
            "to answer this question."
        )

    llm = ChatOllama(
        model=ANSWER_MODEL,
        temperature=0,
        base_url=OLLAMA_BASE_URL,
    )
    chain = ANSWER_PROMPT | llm
    response = chain.invoke({
        "query": query,
        "context": context
    })

    return str(response.content).strip()
