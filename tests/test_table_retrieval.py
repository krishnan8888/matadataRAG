import unittest
import sys
from types import ModuleType
from unittest.mock import patch
from unittest.mock import Mock

import numpy as np

from app.retrieval.matching import cosine_scores, hybrid_scores
from app.retrieval.table_retriever import retrieve
from app.retrieval.types import RetrievalRequest
from app.table_rows import build_table_row_records


class TableRowTests(unittest.TestCase):
    def test_build_records_keeps_project_context_and_headers(self):
        payload = {
            "document_id": "contracts",
            "tables": [{
                "table_id": "rates",
                "project_id": "Apex-249",
                "document_section": "SOW #1",
                "section_title": "Rates",
                "rows": [
                    ["Role", "Rate"],
                    ["Cloud Architect", "$166.00"],
                ],
            }],
        }

        records = build_table_row_records(payload)

        self.assertEqual(len(records), 1)
        self.assertIn("Project: Apex-249", records[0]["content"])
        self.assertIn("Role: Cloud Architect", records[0]["content"])
        self.assertIn("Rate: $166.00", records[0]["content"])

    def test_cosine_scores_handles_zero_vectors(self):
        scores = cosine_scores([1.0, 0.0], [[1.0, 0.0], [0.0, 0.0]])

        self.assertEqual(scores, [1.0, 0.0])

    def test_hybrid_scoring_prefers_matching_project_identifier(self):
        texts = [
            "Project: Apex-249 | Role: Cloud Architect | Rate: $166.00",
            "Project: Zenith-777 | Role: Cloud Architect | Rate: $180.00",
        ]
        scores = hybrid_scores(
            "Cloud Architect rate for Apex-249",
            texts,
            precomputed_semantic_scores=[0.7, 0.9],
        )

        self.assertGreater(scores[0], scores[1])


class PersistedRetrievalTests(unittest.TestCase):
    @patch("app.ingest.vectordb.get_table_rows")
    @patch("app.retrieval.table_retriever.TABLE_DIR")
    def test_retrieval_embeds_only_query(
        self,
        table_dir,
        get_table_rows,
    ):
        table_dir.__truediv__.return_value.exists.return_value = True
        get_table_rows.return_value = {
            "ids": ["row-1", "row-2"],
            "documents": [
                "Project: Apex-249 | Role: Cloud Architect | Rate: $166.00",
                "Project: Other-100 | Role: Cloud Architect | Rate: $180.00",
            ],
            "metadatas": [
                {"table_id": "rates", "row_index": 1, "project_id": "Apex-249"},
                {"table_id": "rates", "row_index": 2, "project_id": "Other-100"},
            ],
            "embeddings": np.asarray([[1.0, 0.0], [0.8, 0.2]]),
        }
        generate_embeddings = Mock(
            return_value=np.asarray([[1.0, 0.0]])
        )
        fake_embedder = ModuleType("app.ingest.embedder")
        fake_embedder.generate_embeddings = generate_embeddings

        with patch.dict(sys.modules, {"app.ingest.embedder": fake_embedder}):
            results = retrieve(
                RetrievalRequest(
                    query="Cloud Architect rate for Apex-249",
                    top_k=2,
                ),
                {"document_id": "contracts"},
            )

        generate_embeddings.assert_called_once_with([
            "Cloud Architect rate for Apex-249"
        ])
        self.assertEqual(results[0].metadata["project_id"], "Apex-249")


if __name__ == "__main__":
    unittest.main()
