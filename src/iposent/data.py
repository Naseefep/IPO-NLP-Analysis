"""Validate prices and enforce a conservative information cutoff."""
import html
import re
import unicodedata
import numpy as np
import pandas as pd


def require(df, columns):
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")


def clean_text(value):
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def normalise_headline(value):
    return re.sub(r"[^\w]+", " ", unicodedata.normalize("NFKC", clean_text(value)).casefold()).strip()


def validate_ipos(df):
    require(df, ["symbol", "company", "listing_date", "issue_price"])
    df = df.copy()
    if df[["symbol", "company", "listing_date"]].isna().any().any():
        raise ValueError("IPO identifiers and dates cannot be missing")
    df["symbol"] = df.symbol.astype(str).str.strip().str.upper()
    if df.symbol.eq("").any() or df.symbol.duplicated().any():
        raise ValueError("Each IPO must have a unique, nonempty symbol")
    dates = pd.to_datetime(df.listing_date, format="%Y-%m-%d", errors="raise")
    df["listing_date"] = dates.dt.normalize()
    df["issue_price"] = pd.to_numeric(df.issue_price, errors="raise")
    if not (np.isfinite(df.issue_price) & df.issue_price.gt(0)).all():
        raise ValueError("Issue prices must be finite and positive")
    return df


def price_features(ipos, prices):
    require(prices, ["symbol", "observed_date", "open", "high", "low", "close", "quote_basis", "verified", "source_url"])
    p = prices.copy()
    p["symbol"] = p.symbol.astype(str).str.strip().str.upper()
    if p.symbol.duplicated().any():
        raise ValueError("Duplicate price symbols")
    df = ipos.merge(p, on="symbol", how="left", validate="one_to_one", indicator=True)
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["observed_date"] = pd.to_datetime(df.observed_date, errors="coerce").dt.normalize()
    df["price_rejection"] = ""
    def reject(mask, reason):
        df.loc[mask & df.price_rejection.eq(""), "price_rejection"] = reason
    reject(df._merge.ne("both"), "missing_price")
    reject(df.observed_date.ne(df.listing_date), "wrong_or_missing_date")
    reject(~df.verified.astype(str).str.lower().isin(["true", "1"]), "unverified_price")
    reject(df.quote_basis.ne("listing_day_nominal"), "unverified_quote_basis")
    reject(df.source_url.fillna("").str.strip().eq(""), "missing_price_source")
    numeric = df[["open", "high", "low", "close"]]
    reject(~(np.isfinite(numeric).all(axis=1) & numeric.gt(0).all(axis=1)), "invalid_ohlc")
    reject((df.high < df[["open", "close", "low"]].max(axis=1)) | (df.low > df[["open", "close", "high"]].min(axis=1)), "inconsistent_ohlc")
    valid = df.price_rejection.eq("")
    df["listing_return_pct"] = np.where(valid, 100 * (df.close / df.issue_price - 1), np.nan)
    df["intraday_return_pct"] = np.where(valid, 100 * (df.close / df.open - 1), np.nan)
    df["parkinson_daily"] = np.where(valid, np.log(df.high / df.low) / np.sqrt(4 * np.log(2)), np.nan)
    df["range_pct"] = np.where(valid, 100 * (df.high - df.low) / df.open, np.nan)
    return df.drop(columns="_merge")


def filter_news(ipos, news, lookback_days=30):
    """Window: [listing midnight IST minus N calendar days, listing midnight IST).

    Naive timestamps are interpreted as local Indian timestamps. Date-only articles
    on listing day are excluded. Keep an audit row for every rejected article.
    Exact URL or normalised-headline matches are deduplicated within each IPO.
    """
    if lookback_days < 1:
        raise ValueError("lookback_days must be positive")
    require(news, ["symbol", "headline", "published_at", "source", "url", "relevance_verified"])
    n = news.copy().reset_index(drop=True)
    n["input_row"] = n.index
    n["symbol"] = n.symbol.fillna("").astype(str).str.strip().str.upper()
    n = n.merge(ipos[["symbol", "listing_date"]], on="symbol", how="left", validate="many_to_one")
    def timestamp(value):
        try:
            t = pd.Timestamp(value)
            if pd.isna(t):
                return pd.NaT
            return t.tz_localize("Asia/Kolkata") if t.tzinfo is None else t.tz_convert("Asia/Kolkata")
        except (ValueError, TypeError):
            return pd.NaT
    n["published_local"] = pd.to_datetime(n.published_at.map(timestamp), utc=True).dt.tz_convert("Asia/Kolkata")
    cutoff = n.listing_date.dt.tz_localize("Asia/Kolkata")
    n["headline"] = n.headline.map(clean_text)
    n["rejection"] = ""
    def reject(mask, reason):
        n.loc[mask & n.rejection.eq(""), "rejection"] = reason
    reject(n.listing_date.isna(), "unknown_symbol")
    reject(n.published_local.isna(), "invalid_timestamp")
    reject(n.published_local >= cutoff, "at_or_after_cutoff")
    reject(n.published_local < cutoff - pd.Timedelta(days=lookback_days), "before_window")
    reject(~n.relevance_verified.astype(str).str.lower().isin(["true", "1"]), "relevance_not_verified")
    reject(n.headline.eq(""), "empty_headline")
    reject(n.url.fillna("").str.strip().eq("") | n.source.fillna("").str.strip().eq(""), "missing_provenance")
    n = n.sort_values(["published_local", "input_row"], na_position="last")
    seen_titles, seen_urls = set(), set()
    for i, row in n[n.rejection.eq("")].iterrows():
        title_key = (row.symbol, normalise_headline(row.headline))
        url_key = (row.symbol, str(row.url).strip())
        if title_key in seen_titles or url_key in seen_urls:
            n.loc[i, "rejection"] = "duplicate"
        else:
            seen_titles.add(title_key)
            seen_urls.add(url_key)
    # Headlines are primary: snippets often repeat the headline or contain search boilerplate.
    n["text"] = n.apply(lambda row: row.headline[:-len(" - " + str(row.source))].strip()
                        if row.headline.endswith(" - " + str(row.source)) else row.headline, axis=1)
    return n[n.rejection.eq("")].copy(), n.sort_values("input_row")
