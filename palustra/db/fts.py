"""SQLite FTS5 trigram fuzzy search index management and query execution."""

import re
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

FTS_TABLE_NAME = "taxa_fts"

CREATE_FTS_TABLE_SQL = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE_NAME} USING fts5(
    clean_scientific_name,
    common_name,
    symbol,
    content='taxa',
    content_rowid='id',
    tokenize='trigram'
);
"""

CREATE_TRIGGERS_SQL = f"""
CREATE TRIGGER IF NOT EXISTS taxa_ai AFTER INSERT ON taxa BEGIN
    INSERT INTO {FTS_TABLE_NAME}(rowid, clean_scientific_name, common_name, symbol)
    VALUES (new.id, new.clean_scientific_name, new.common_name, new.symbol);
END;

CREATE TRIGGER IF NOT EXISTS taxa_ad AFTER DELETE ON taxa BEGIN
    INSERT INTO {FTS_TABLE_NAME}({FTS_TABLE_NAME}, rowid, clean_scientific_name, common_name, symbol)
    VALUES ('delete', old.id, old.clean_scientific_name, old.common_name, old.symbol);
END;

CREATE TRIGGER IF NOT EXISTS taxa_au AFTER UPDATE ON taxa BEGIN
    INSERT INTO {FTS_TABLE_NAME}({FTS_TABLE_NAME}, rowid, clean_scientific_name, common_name, symbol)
    VALUES ('delete', old.id, old.clean_scientific_name, old.common_name, old.symbol);
    INSERT INTO {FTS_TABLE_NAME}(rowid, clean_scientific_name, common_name, symbol)
    VALUES (new.id, new.clean_scientific_name, new.common_name, new.symbol);
END;
"""

REBUILD_FTS_SQL = f"INSERT INTO {FTS_TABLE_NAME}({FTS_TABLE_NAME}) VALUES('rebuild');"

def init_fts5(conn) -> None:
    """Initialize SQLite FTS5 trigram virtual table and synchronization triggers."""
    conn.execute(text(CREATE_FTS_TABLE_SQL))
    for statement in CREATE_TRIGGERS_SQL.strip().split(";\n\n"):
        stmt = statement.strip()
        if stmt:
            conn.execute(text(stmt))

def rebuild_fts5(conn) -> None:
    """Explicitly rebuild the FTS5 index from the underlying taxa table."""
    conn.execute(text(REBUILD_FTS_SQL))

def sanitize_fts5_query(raw_query: str) -> str:
    """Sanitize user query for SQLite FTS5 syntax."""
    # Strip any special FTS5 operators to prevent syntax errors
    cleaned = re.sub(r'["*^():{}]', ' ', raw_query)
    # Collapse multiple spaces
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    if not tokens:
        return ""
    # In trigram tokenization, quote multi-word tokens for exact phrase/substring sequence
    return " ".join(f'"{token}"' for token in tokens)

def search_taxa(
    session: Session,
    query_str: str,
    limit: int = 20,
    offset: int = 0,
    region: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute trigram fuzzy search or short-query fallback against SQLite FTS5."""
    query_clean = query_str.strip()
    if not query_clean:
        return {"total": 0, "results": []}

    # If query has 3 or more characters, use FTS5 trigram MATCH
    if len(query_clean) >= 3:
        fts_query = sanitize_fts5_query(query_clean)
        if not fts_query:
            return {"total": 0, "results": []}

        region_filter = ""
        params: Dict[str, Any] = {
            "fts_query": fts_query,
            "limit": limit,
            "offset": offset,
        }

        if region == "EMP":
            region_filter = "AND t.nwpl_indicator_emp IS NOT NULL"
        elif region == "AGCP":
            region_filter = "AND t.nwpl_indicator_agcp IS NOT NULL"

        count_sql = text(f"""
            SELECT COUNT(*)
            FROM {FTS_TABLE_NAME} f
            JOIN taxa t ON f.rowid = t.id
            WHERE {FTS_TABLE_NAME} MATCH :fts_query
            {region_filter}
        """)
        total_count = session.execute(count_sql, {"fts_query": fts_query}).scalar() or 0

        # BM25 ranking: lower score means more relevant in SQLite FTS5
        search_sql = text(f"""
            SELECT 
                t.symbol,
                t.clean_scientific_name,
                t.common_name,
                t.family,
                t.nwpl_indicator_emp,
                t.nwpl_indicator_agcp,
                bm25({FTS_TABLE_NAME}) AS score
            FROM {FTS_TABLE_NAME} f
            JOIN taxa t ON f.rowid = t.id
            WHERE {FTS_TABLE_NAME} MATCH :fts_query
            {region_filter}
            ORDER BY score ASC, t.clean_scientific_name ASC
            LIMIT :limit OFFSET :offset
        """)
        rows = session.execute(search_sql, params).mappings().all()

        results = []
        for r in rows:
            results.append({
                "symbol": r["symbol"],
                "clean_scientific_name": r["clean_scientific_name"],
                "common_name": r["common_name"],
                "family": r["family"],
                "nwpl_indicator_emp": r["nwpl_indicator_emp"],
                "nwpl_indicator_agcp": r["nwpl_indicator_agcp"],
                "bm25_score": float(r["score"]),
                "matched_field": "fts5_trigram",
            })

        return {"total": total_count, "results": results}

    else:
        # Fallback for queries shorter than 3 characters (e.g. 1-2 char USDA symbols or genus starts)
        like_pattern = f"{query_clean}%"
        region_filter = ""
        params = {
            "like_pat": like_pattern,
            "limit": limit,
            "offset": offset,
        }

        if region == "EMP":
            region_filter = "AND t.nwpl_indicator_emp IS NOT NULL"
        elif region == "AGCP":
            region_filter = "AND t.nwpl_indicator_agcp IS NOT NULL"

        count_sql = text(f"""
            SELECT COUNT(*)
            FROM taxa t
            WHERE (t.symbol LIKE :like_pat OR t.clean_scientific_name LIKE :like_pat)
            {region_filter}
        """)
        total_count = session.execute(count_sql, {"like_pat": like_pattern}).scalar() or 0

        search_sql = text(f"""
            SELECT 
                t.symbol,
                t.clean_scientific_name,
                t.common_name,
                t.family,
                t.nwpl_indicator_emp,
                t.nwpl_indicator_agcp,
                0.0 AS score
            FROM taxa t
            WHERE (t.symbol LIKE :like_pat OR t.clean_scientific_name LIKE :like_pat)
            {region_filter}
            ORDER BY t.clean_scientific_name ASC
            LIMIT :limit OFFSET :offset
        """)
        rows = session.execute(search_sql, params).mappings().all()

        results = []
        for r in rows:
            results.append({
                "symbol": r["symbol"],
                "clean_scientific_name": r["clean_scientific_name"],
                "common_name": r["common_name"],
                "family": r["family"],
                "nwpl_indicator_emp": r["nwpl_indicator_emp"],
                "nwpl_indicator_agcp": r["nwpl_indicator_agcp"],
                "bm25_score": 0.0,
                "matched_field": "prefix_like",
            })

        return {"total": total_count, "results": results}
