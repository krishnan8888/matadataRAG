def row_to_text(row) -> str:
    if isinstance(row, dict):
        return " | ".join(
            f"{key}: {value}"
            for key, value in row.items()
        )

    if isinstance(row, list):
        return " | ".join(str(value) for value in row)

    return str(row)


def build_table_row_records(payload: dict) -> list[dict]:
    document_id = payload.get("document_id", "")
    records = []

    for table in payload.get("tables", []):
        table_id = table.get("table_id", document_id)
        project_id = table.get("project_id", "")
        document_section = table.get("document_section", "")
        section_title = table.get("section_title", "")
        rows = table.get("rows", [])
        columns = table.get("columns", [])

        if rows and isinstance(rows[0], list):
            columns = rows[0]

        for row_index, row in enumerate(rows):
            if row_index == 0 and rows and isinstance(rows[0], list):
                continue

            if columns and isinstance(row, list):
                row = {
                    str(column): row[index] if index < len(row) else ""
                    for index, column in enumerate(columns)
                }

            row_content = row_to_text(row)
            content = " | ".join(
                value
                for value in (
                    f"Project: {project_id}" if project_id else "",
                    document_section,
                    section_title,
                    row_content,
                )
                if value
            )

            records.append({
                "content": content,
                "table_id": table_id,
                "row_index": row_index,
                "project_id": project_id,
                "document_section": document_section,
                "section_title": section_title,
            })

    return records
