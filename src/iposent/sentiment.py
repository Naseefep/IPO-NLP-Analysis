"""Finance-specific lexicon and contextual scoring, kept at article level."""
import hashlib
import re
from pathlib import Path
import numpy as np
import pandas as pd


class LoughranMcDonald:
    def __init__(self, path):
        path = Path(path)
        self.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        table = pd.read_csv(path)
        table.columns = table.columns.str.strip().str.lower()
        if not {"word", "positive", "negative"}.issubset(table.columns):
            raise ValueError("Use the official LM master CSV with Word, Positive, Negative columns")
        self.positive = set(table.loc[pd.to_numeric(table.positive, errors="coerce").gt(0), "word"].str.upper())
        self.negative = set(table.loc[pd.to_numeric(table.negative, errors="coerce").gt(0), "word"].str.upper())
        self.uncertainty = set(table.loc[pd.to_numeric(table.uncertainty, errors="coerce").gt(0), "word"].str.upper()) if "uncertainty" in table else set()

    def score(self, texts):
        result = []
        for text in texts:
            tokens = re.findall(r"[A-Za-z]+", text.upper())
            p = sum(t in self.positive for t in tokens)
            n = sum(t in self.negative for t in tokens)
            u = sum(t in self.uncertainty for t in tokens)
            result.append({"lm_score": (p-n)/len(tokens) if tokens else np.nan,
                           "lm_positive": p, "lm_negative": n, "lm_tokens": len(tokens),
                           "lm_coverage": (p+n)/len(tokens) if tokens else np.nan,
                           "lm_uncertainty": u/len(tokens) if tokens else np.nan})
        return pd.DataFrame(result)


class FinBERT:
    MODEL = "ProsusAI/finbert"
    # Immutable repository revision; recorded again with each run.
    REVISION = "0bc2ac10dda6929bcb1f77ccc43c7ec5c424f031"

    def __init__(self, revision=None, batch_size=16):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        self.torch = torch
        self.revision = revision or self.REVISION
        self.batch_size = batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL, revision=self.revision)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL, revision=self.revision, use_safetensors=True)
        self.model.eval()
        self.labels = {str(v).lower(): int(k) for k, v in self.model.config.id2label.items()}
        if set(self.labels) != {"positive", "negative", "neutral"}:
            raise ValueError(f"Unexpected model label mapping: {self.labels}")

    def score(self, texts):
        chunks, owners = [], []
        capacity = min(512, self.model.config.max_position_embeddings) - self.tokenizer.num_special_tokens_to_add(pair=False)
        for i, text in enumerate(texts):
            ids = self.tokenizer.encode(text, add_special_tokens=False)
            for j in range(0, len(ids), capacity):
                chunks.append(self.tokenizer.prepare_for_model(ids[j:j+capacity], add_special_tokens=True, return_attention_mask=True))
                owners.append(i)
        accum = {i: [] for i in range(len(texts))}
        for start in range(0, len(chunks), self.batch_size):
            batch = self.tokenizer.pad(chunks[start:start+self.batch_size], padding=True, return_tensors="pt")
            with self.torch.inference_mode():
                probs = self.model(**batch).logits.softmax(-1).cpu().numpy()
            for owner, prob in zip(owners[start:start+self.batch_size], probs):
                accum[owner].append(prob)
        rows = []
        for i in range(len(texts)):
            p = np.mean(accum[i], axis=0) if accum[i] else np.full(3, np.nan)
            values = {f"finbert_p_{name}": float(p[index]) for name, index in self.labels.items()}
            values["finbert_score"] = values["finbert_p_positive"] - values["finbert_p_negative"]
            values["finbert_chunks"] = len(accum[i])
            rows.append(values)
        return pd.DataFrame(rows)


def aggregate(scored):
    columns = [c for c in ["finbert_score", "lm_score", "lm_coverage", "lm_uncertainty"] if c in scored]
    if scored.empty:
        return pd.DataFrame(columns=["symbol", "article_count", *columns])
    means = scored.groupby("symbol")[columns].mean()
    means["article_count"] = scored.groupby("symbol").size()
    return means.reset_index()
