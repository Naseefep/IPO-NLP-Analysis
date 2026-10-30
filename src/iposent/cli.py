import argparse
import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
import platform
import pandas as pd
from .data import validate_ipos, price_features, filter_news
from .sentiment import LoughranMcDonald, FinBERT, aggregate
from .analysis import estimate, holdout, TARGETS


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    out = Path(args.output)
    # Prevent stale files from a previous run being mistaken for current results.
    if out.exists() and any(out.iterdir()):
        raise ValueError("Output directory must be new or empty; choose a fresh run name")
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
                "status": "started", "mode": "SYNTHETIC_DEMO" if args.demo else "research",
                "lookback_calendar_days": args.lookback_days, "text_field": "headline", "model": args.model,
                "inputs": {str(p): digest(p) for p in [args.ipos, args.prices, args.news]}, "packages": {}}
    for pkg in ["pandas", "numpy", "statsmodels", "scipy", "transformers", "torch"]:
        try:
            manifest["packages"][pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            pass
    try:
        ipos = validate_ipos(pd.read_csv(args.ipos))
        panel = price_features(ipos, pd.read_csv(args.prices))
        valid, audit = filter_news(ipos, pd.read_csv(args.news), args.lookback_days)
        audit.to_csv(out / "news_audit.csv", index=False)
        panel.to_csv(out / "price_audit.csv", index=False)
        manifest["counts"] = {"ipos": len(ipos), "news_input": len(audit), "news_retained": len(valid),
                              "verified_prices": int(panel.price_rejection.eq("").sum())}
        manifest["news_rejections"] = audit.rejection.value_counts().to_dict()
        if valid.empty:
            raise ValueError("No eligible pre-listing news remains; inspect news_audit.csv")
        scored = valid.reset_index(drop=True)
        if args.model in ["lm", "both"]:
            if not args.lm_dictionary:
                raise ValueError("--lm-dictionary is required for LM scoring")
            scorer = LoughranMcDonald(args.lm_dictionary)
            manifest["lm_dictionary_sha256"] = scorer.sha256
            manifest["lm_dictionary_path"] = str(args.lm_dictionary)
            scored = pd.concat([scored, scorer.score(scored.text.tolist())], axis=1)
        if args.model in ["finbert", "both"]:
            scorer = FinBERT(revision=args.finbert_revision)
            manifest["finbert_revision"] = scorer.revision
            manifest["finbert_labels"] = scorer.labels
            scored = pd.concat([scored, scorer.score(scored.text.tolist())], axis=1)
        scored.to_csv(out / "article_scores.csv", index=False)
        agg = aggregate(scored)
        panel = panel.merge(agg, on="symbol", how="left", validate="one_to_one")
        panel["article_count"] = panel.article_count.fillna(0).astype(int)
        panel.to_csv(out / "analysis_panel.csv", index=False)
        coefficients, correlations, diagnostics, skipped = estimate(panel)
        for name, table in [("coefficients", coefficients), ("correlations", correlations), ("diagnostics", diagnostics)]:
            table.to_csv(out / f"{name}.csv", index=False)
        manifest["skipped_models"] = skipped
        metrics = []
        for score in [c for c in ["finbert_score", "lm_score"] if c in panel]:
            for target in TARGETS:
                metric, predictions = holdout(panel, score, target)
                metrics.append(metric)
                if not predictions.empty:
                    predictions.to_csv(out / f"holdout_{score}_{target}.csv", index=False)
        (out / "holdout_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf8")
        make_plot(panel, out, args.demo)
        manifest["status"] = "complete"
        manifest["interpretation"] = "Synthetic software demonstration; no empirical inference." if args.demo else "Associational estimates; inspect audits, confidence intervals and holdout errors."
    except Exception as exc:
        manifest.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    print(f"Completed {manifest['mode']} run: {out.resolve()}")


def make_plot(panel, out, demo):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    score = "finbert_score" if "finbert_score" in panel else "lm_score"
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, target in zip(axes, TARGETS):
        ax.scatter(panel[score], panel[target], color="#157a86", alpha=.7)
        ax.set(xlabel=score, ylabel=target)
        ax.grid(alpha=.15)
    fig.suptitle("SYNTHETIC DEMO - no research findings" if demo else "Pre-listing sentiment and listing-day outcomes")
    fig.tight_layout()
    fig.savefig(out / "sentiment_outcomes.png", dpi=160)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description="Auditable financial sentiment research")
    p.add_argument("--ipos", required=True)
    p.add_argument("--prices", required=True)
    p.add_argument("--news", required=True)
    p.add_argument("--model", choices=["finbert", "lm", "both"], default="finbert")
    p.add_argument("--lm-dictionary")
    p.add_argument("--finbert-revision")
    p.add_argument("--lookback-days", type=int, default=30)
    p.add_argument("--output", default="outputs/research")
    p.add_argument("--demo", action="store_true", help="Mark all outputs as synthetic demonstration")
    run(p.parse_args())


if __name__ == "__main__":
    main()
