from app.retrieval.types import RetrievalResult


def build_context(
    results: list[RetrievalResult],
    include_debug_metadata: bool = True,
    deduplicate: bool = False,
) -> str:
    context_blocks = []
    seen_content = set()

    for result in results:
        content_key = " ".join(result.content.split()).casefold()

        if deduplicate and content_key in seen_content:
            continue

        seen_content.add(content_key)
        score = ""
        metadata = ""

        if include_debug_metadata and result.score is not None:
            score = f" | score={result.score:.3f}"

        if include_debug_metadata and result.metadata:
            metadata = " | " + ", ".join(
                f"{key}={value}"
                for key, value in result.metadata.items()
                if value not in (None, "")
            )

        context_blocks.append(
            f"[{result.source} | {result.document_id}{score}{metadata}]\n"
            f"{result.content}"
        )

    return "\n\n".join(context_blocks)
