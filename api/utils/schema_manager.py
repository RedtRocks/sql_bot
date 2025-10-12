class SchemaManager:
    def get_user_schema(self, username: str) -> str | None:
        # Placeholder for fetching schema text per user (could be cached)
        # In a real app, you might introspect PostgreSQL or return stored schema docs
        return None

    def analyze_columns(self, usage_rows: list[dict]):
        # Simple heuristic: columns with count >= 2 are useful
        summary: dict[str, int] = {}
        for r in usage_rows:
            col = r.get("column")
            cnt = int(r.get("count", 0))
            summary[col] = summary.get(col, 0) + cnt
        useful = [c for c, n in summary.items() if n >= 2]
        redundant = [c for c, n in summary.items() if n < 2]
        return {"useful": useful, "redundant": redundant}


