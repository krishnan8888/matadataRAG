import unittest

from app.retrieval.context_builder import build_context
from app.retrieval.types import RetrievalResult


class AnswerContextTests(unittest.TestCase):
    def test_deduplicate_removes_repeated_evidence(self):
        results = [
            RetrievalResult(
                document_id="contract",
                content="Project: Apex-249 | Rate: $166.00",
                source="table_store",
                score=0.9,
            ),
            RetrievalResult(
                document_id="contract",
                content="  project: APEX-249   | Rate: $166.00  ",
                source="vector_db",
                score=0.8,
            ),
        ]

        context = build_context(
            results,
            include_debug_metadata=False,
            deduplicate=True,
        )

        self.assertEqual(context.count("["), 1)
        self.assertIn("$166.00", context)

    def test_default_context_keeps_all_results(self):
        results = [
            RetrievalResult("one", "same", "table_store"),
            RetrievalResult("two", "same", "vector_db"),
        ]

        context = build_context(results)

        self.assertEqual(context.count("["), 2)


if __name__ == "__main__":
    unittest.main()
