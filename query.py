import argparse
import os


os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from app.retrieval.answer_generator import generate_answer
from app.retrieval.context_builder import build_context
from app.retrieval.router import route_query


def print_chosen_documents(documents: list[dict]) -> None:
    if not documents:
        print("Chosen docs: none")
        return

    print("Chosen docs:")

    for profile in documents:
        document_id = profile.get("document_id", "")
        score = profile.get("metadata_score", 0)
        document_type = profile.get("document_type", "")
        retrieval_modes = ", ".join(profile.get("retrieval_modes", []))

        print(
            f"- {document_id} "
            f"(metadata_score={score:.2f}, "
            f"type={document_type}, "
            f"modes={retrieval_modes})"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve context and generate a grounded answer."
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Question or search query."
    )
    parser.add_argument(
        "--top-k-docs",
        type=int,
        default=5
    )
    parser.add_argument(
        "--top-k-results",
        type=int,
        default=5
    )
    parser.add_argument(
        "--context-only",
        action="store_true",
        help="Skip LLM answer generation and only print retrieval context."
    )

    args = parser.parse_args()
    query = " ".join(args.query).strip()

    if not query:
        try:
            query = input("Query: ").strip()

        except KeyboardInterrupt:
            print()
            print("Query cancelled.")
            return

    if not query:
        print("No query provided.")
        return

    response = route_query(
        query,
        top_k_docs=args.top_k_docs,
        top_k_results=args.top_k_results
    )
    context = build_context(response["results"])
    answer_context = build_context(
        response["results"],
        include_debug_metadata=False,
        deduplicate=True,
    )
    answer = None

    if not args.context_only:
        try:
            answer = generate_answer(query, answer_context)

        except Exception as exc:
            answer = f"Answer generation failed: {exc}"

    print(f"Query: {response['query']}")
    print()
    print_chosen_documents(response["chosen_documents"])
    print()
    print("Context:")
    print(context if context else "No context retrieved.")

    if response["errors"]:
        print()
        print("Retrieval warnings:")

        for error in response["errors"]:
            print(
                f"- {error['document_id']} / "
                f"{error['retrieval_mode']}: {error['error']}"
            )

    if answer is not None:
        print()
        print("Answer:")
        print(answer)


if __name__ == "__main__":
    main()
