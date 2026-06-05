from app.retrieval.types import RetrievalResult


def build_context(
    results: list[RetrievalResult],
    include_debug_metadata: bool = True
) -> str:
    context_blocks = []

    for result in results:
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
