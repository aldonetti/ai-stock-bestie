"""SQLite database manager for the investment analysis tool."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import pandas as pd

import config as cfg


def _get_db_path() -> Path:
    """Return absolute path to the DB file, creating parent dirs as needed."""
    # Resolve relative to repo root (one level up from src/)
    root = Path(__file__).parent.parent
    db_path = root / cfg.INVESTMENT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@contextmanager
def _connect() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for DB connections with row_factory set."""
    conn = sqlite3.connect(str(_get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they do not exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS watchlist (
                ticker      TEXT PRIMARY KEY,
                name        TEXT,
                sector      TEXT,
                added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS price_history (
                ticker      TEXT    NOT NULL,
                date        DATE    NOT NULL,
                open        REAL,
                high        REAL,
                low         REAL,
                close       REAL,
                volume      INTEGER,
                adj_close   REAL,
                PRIMARY KEY (ticker, date)
            );

            CREATE TABLE IF NOT EXISTS analysis_cache (
                ticker          TEXT        NOT NULL,
                period          TEXT        NOT NULL,
                calculated_at   TIMESTAMP   NOT NULL,
                indicators      TEXT        NOT NULL,
                PRIMARY KEY (ticker, period)
            );

            CREATE TABLE IF NOT EXISTS llm_cache (
                ticker          TEXT        NOT NULL,
                period          TEXT        NOT NULL,
                provider        TEXT        NOT NULL,
                created_at      TIMESTAMP   NOT NULL,
                recommendation  TEXT        NOT NULL,
                PRIMARY KEY (ticker, period, provider)
            );
        """)


# ---------------------------------------------------------------------------
# Watchlist helpers
# ---------------------------------------------------------------------------

def get_watchlist() -> List[str]:
    """Return all tickers in the watchlist."""
    with _connect() as conn:
        rows = conn.execute("SELECT ticker FROM watchlist ORDER BY added_at").fetchall()
    return [r["ticker"] for r in rows]


def add_to_watchlist(ticker: str, name: Optional[str] = None, sector: Optional[str] = None) -> None:
    """Add a ticker to the watchlist (no-op if already present)."""
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (ticker, name, sector) VALUES (?, ?, ?)",
            (ticker.upper(), name, sector),
        )


def remove_from_watchlist(ticker: str) -> None:
    """Remove a ticker from the watchlist."""
    with _connect() as conn:
        conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))


# ---------------------------------------------------------------------------
# Price history helpers
# ---------------------------------------------------------------------------

def upsert_price_history(ticker: str, df: pd.DataFrame) -> None:
    """
    Insert or replace OHLCV rows for a ticker.

    Args:
        ticker: Stock ticker symbol
        df: DataFrame with columns [Open, High, Low, Close, Volume] and DatetimeIndex
    """
    if df is None or df.empty:
        return
    ticker = ticker.upper()
    rows: List[tuple] = []
    for idx, row in df.iterrows():
        date_str = str(idx.date()) if hasattr(idx, "date") else str(idx)[:10]
        adj_close = float(row.get("Adj Close", row.get("Close", 0))) if hasattr(row, "get") else None
        rows.append((
            ticker,
            date_str,
            float(row["Open"]) if pd.notna(row["Open"]) else None,
            float(row["High"]) if pd.notna(row["High"]) else None,
            float(row["Low"]) if pd.notna(row["Low"]) else None,
            float(row["Close"]) if pd.notna(row["Close"]) else None,
            int(row["Volume"]) if pd.notna(row["Volume"]) else None,
            float(adj_close) if adj_close is not None and pd.notna(adj_close) else None,
        ))
    with _connect() as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO price_history
               (ticker, date, open, high, low, close, volume, adj_close)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )


def get_price_history(ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve stored OHLCV rows for a ticker.

    Args:
        ticker: Stock ticker symbol
        start_date: ISO date string (YYYY-MM-DD), inclusive
        end_date: ISO date string (YYYY-MM-DD), inclusive

    Returns:
        DataFrame with DatetimeIndex and OHLCV columns, or empty DataFrame
    """
    query = "SELECT date, open, high, low, close, volume, adj_close FROM price_history WHERE ticker = ?"
    params: List[Any] = [ticker.upper()]
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(
        rows,
        columns=["date", "Open", "High", "Low", "Close", "Volume", "Adj Close"],
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df.index.name = None
    return df


def get_stored_date_range(ticker: str) -> tuple:
    """Return (min_date, max_date) strings for stored data, or (None, None)."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT MIN(date), MAX(date) FROM price_history WHERE ticker = ?",
            (ticker.upper(),),
        ).fetchone()
    if row and row[0]:
        return row[0], row[1]
    return None, None


# ---------------------------------------------------------------------------
# Analysis cache helpers
# ---------------------------------------------------------------------------

def set_analysis_cache(ticker: str, period: str, indicators: Dict) -> None:
    """Persist computed indicators dict for a ticker/period."""
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO analysis_cache (ticker, period, calculated_at, indicators)
               VALUES (?, ?, ?, ?)""",
            (ticker.upper(), period, now, json.dumps(indicators)),
        )


def get_analysis_cache(ticker: str, period: str) -> Optional[Dict]:
    """Retrieve cached indicators dict, or None if not stored."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT indicators FROM analysis_cache WHERE ticker = ? AND period = ?",
            (ticker.upper(), period),
        ).fetchone()
    if row:
        return json.loads(row["indicators"])
    return None


# ---------------------------------------------------------------------------
# LLM cache helpers
# ---------------------------------------------------------------------------

def set_llm_cache(ticker: str, period: str, provider: str, recommendation: str) -> None:
    """Store an LLM recommendation."""
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO llm_cache (ticker, period, provider, created_at, recommendation)
               VALUES (?, ?, ?, ?, ?)""",
            (ticker.upper(), period, provider, now, recommendation),
        )


def get_llm_cache(ticker: str, period: str, provider: str, max_age_hours: int = cfg.LLM_INVESTMENT_CACHE_HOURS) -> Optional[str]:
    """
    Retrieve a cached LLM recommendation if it's within max_age_hours.

    Returns:
        Recommendation text or None if not found / too old
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT recommendation, created_at FROM llm_cache WHERE ticker = ? AND period = ? AND provider = ?",
            (ticker.upper(), period, provider),
        ).fetchone()
    if not row:
        return None
    created_at = datetime.fromisoformat(row["created_at"])
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
    if age_hours > max_age_hours:
        return None
    return row["recommendation"]


def clear_llm_cache(ticker: str, period: str, provider: str) -> None:
    """Delete a specific LLM cache entry to force refresh."""
    with _connect() as conn:
        conn.execute(
            "DELETE FROM llm_cache WHERE ticker = ? AND period = ? AND provider = ?",
            (ticker.upper(), period, provider),
        )
