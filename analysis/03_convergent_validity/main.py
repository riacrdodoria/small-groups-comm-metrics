from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from scipy.stats import pearsonr as scipy_pearsonr
except Exception:  # pragma: no cover - fallback when scipy is unavailable
    scipy_pearsonr = None

try:
    from numba import njit
except Exception:  # pragma: no cover - fallback when numba is unavailable
    njit = None


# ── PARAMETERS ────────────────────────────────────────────────
GORMAN_DIR = Path("data/raw/gorman")
CONV_DIR = Path("data/processed/convergent_validity")
FIGURES_DIR = Path("figures/03_convergent_validity")
README_PATH = Path("analysis/03_convergent_validity/README.md")

ENTROPY_WINDOW = 61
PCT_DET_WINDOW = 301
RMSE_WINDOW = 30
RMSE_DELTA_N = 20
RMSE_EPSILON = 3.0
MIN_DIAG_LENGTH = 2
MIN_RMSE_NEIGHBORS = 3
SCATTER_SAMPLE_FRAC = 0.10
RNG_SEED = 42
# ──────────────────────────────────────────────────────────────

sns.set_theme(style="whitegrid", context="talk")
RNG = np.random.default_rng(RNG_SEED)


def fisher_pvalue(r: float, n: int) -> float:
    if n < 4 or np.isnan(r):
        return float("nan")
    if abs(r) >= 1.0:
        return 0.0
    z = 0.5 * math.log((1 + r) / (1 - r)) * math.sqrt(max(n - 3, 1))
    return math.erfc(abs(z) / math.sqrt(2.0))


def fisher_ci(r: float, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    if n < 4 or np.isnan(r):
        return float("nan"), float("nan")
    if abs(r) >= 1.0:
        bound = 1.0 if r > 0 else -1.0
        return bound, bound
    z = np.arctanh(r)
    se = 1.0 / math.sqrt(n - 3)
    z_crit = 1.959963984540054
    lower = math.tanh(z - z_crit * se)
    upper = math.tanh(z + z_crit * se)
    return float(lower), float(upper)


def compute_pearson(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, int]:
    mask = np.isfinite(x) & np.isfinite(y)
    n = int(mask.sum())
    if n < 3:
        return float("nan"), float("nan"), n
    x_valid = x[mask]
    y_valid = y[mask]
    if np.std(x_valid) == 0 or np.std(y_valid) == 0:
        return float("nan"), float("nan"), n
    if scipy_pearsonr is not None:
        r, p = scipy_pearsonr(x_valid, y_valid)
        return float(r), float(p), n
    r = float(np.corrcoef(x_valid, y_valid)[0, 1])
    p = fisher_pvalue(r, n)
    return r, p, n


if njit is not None:
    @njit(cache=True)
    def pct_det_for_window(symbols: np.ndarray) -> float:
        n = int(symbols.size)
        if n < 2:
            return 0.0
        recurrent_points = 0
        diagonal_points = 0
        for offset in range(1, n):
            run_length = 0
            for i in range(n - offset):
                if symbols[i] == symbols[i + offset]:
                    recurrent_points += 1
                    run_length += 1
                else:
                    if run_length >= MIN_DIAG_LENGTH:
                        diagonal_points += run_length
                    run_length = 0
            if run_length >= MIN_DIAG_LENGTH:
                diagonal_points += run_length
        if recurrent_points == 0:
            return 0.0
        return 100.0 * diagonal_points / recurrent_points
else:
    def pct_det_for_window(symbols: np.ndarray) -> float:
        n = int(symbols.size)
        if n < 2:
            return 0.0
        recurrent_points = 0
        diagonal_points = 0
        for offset in range(1, n):
            matches = symbols[:-offset] == symbols[offset:]
            recurrent_points += int(matches.sum())
            if matches.any():
                padded = np.concatenate(([0], matches.astype(np.int8), [0]))
                diff = np.diff(padded)
                starts = np.where(diff == 1)[0]
                ends = np.where(diff == -1)[0]
                lengths = ends - starts
                if lengths.size:
                    diagonal_points += int(lengths[lengths >= MIN_DIAG_LENGTH].sum())
        if recurrent_points == 0:
            return 0.0
        return float(100.0 * diagonal_points / recurrent_points)


def shannon_entropy_from_counts(counts: np.ndarray) -> float:
    total = counts.sum()
    if total <= 0:
        return 0.0
    probs = counts[counts > 0] / total
    return float(-(probs * np.log2(probs)).sum())


def compute_entropy_series(speakers: np.ndarray) -> np.ndarray:
    n = len(speakers)
    unique_speakers = np.unique(speakers)
    speaker_to_idx = {speaker: idx for idx, speaker in enumerate(unique_speakers)}
    mapped = np.array([speaker_to_idx[s] for s in speakers], dtype=np.int64)
    counts = np.zeros(len(unique_speakers), dtype=np.int64)
    result = np.zeros(n, dtype=float)

    half_window = ENTROPY_WINDOW // 2
    left = 0
    right = -1

    for t in range(n):
        new_left = max(0, t - half_window)
        new_right = min(n - 1, t + half_window)

        while left < new_left:
            counts[mapped[left]] -= 1
            left += 1
        while left > new_left:
            left -= 1
            counts[mapped[left]] += 1
        while right < new_right:
            right += 1
            counts[mapped[right]] += 1
        while right > new_right:
            counts[mapped[right]] -= 1
            right -= 1

        result[t] = shannon_entropy_from_counts(counts)

    return result


if njit is not None:
    @njit(cache=True)
    def _compute_pct_det_series_numba(speakers: np.ndarray) -> np.ndarray:
        n = len(speakers)
        result = np.zeros(n, dtype=np.float64)
        half_window = PCT_DET_WINDOW // 2
        for t in range(n):
            start = 0 if t < half_window else t - half_window
            end = n if (t + half_window + 1) > n else (t + half_window + 1)
            result[t] = pct_det_for_window(speakers[start:end])
        return result

    @njit(cache=True)
    def _compute_rmse_series_numba(pct_det: np.ndarray) -> np.ndarray:
        n = len(pct_det)
        rmse = np.empty(n, dtype=np.float64)
        rmse[:] = np.nan
        horizon = RMSE_DELTA_N
        for t in range(n):
            value_t = pct_det[t]
            if not np.isfinite(value_t):
                continue
            if t + horizon >= n:
                continue
            valid_obs = True
            for h in range(1, horizon + 1):
                if not np.isfinite(pct_det[t + h]):
                    valid_obs = False
                    break
            if not valid_obs:
                continue

            start = 0 if t < RMSE_WINDOW else t - RMSE_WINDOW
            neighbor_count = 0
            squared_error_sum = 0.0
            for h in range(1, horizon + 1):
                pred_sum = 0.0
                pred_count = 0
                for s in range(start, t):
                    if s + horizon >= n:
                        continue
                    if not np.isfinite(pct_det[s]):
                        continue
                    if abs(pct_det[s] - value_t) > RMSE_EPSILON:
                        continue
                    valid_path = True
                    for hh in range(1, horizon + 1):
                        if not np.isfinite(pct_det[s + hh]):
                            valid_path = False
                            break
                    if not valid_path:
                        continue
                    if h == 1:
                        neighbor_count += 1
                    pred_sum += pct_det[s + h]
                    pred_count += 1
                if pred_count < MIN_RMSE_NEIGHBORS:
                    neighbor_count = 0
                    break
                mean_prediction = pred_sum / pred_count
                diff = mean_prediction - pct_det[t + h]
                squared_error_sum += diff * diff
            if neighbor_count >= MIN_RMSE_NEIGHBORS:
                rmse[t] = math.sqrt(squared_error_sum / horizon)
        return rmse

    def compute_pct_det_series(speakers: np.ndarray) -> np.ndarray:
        return _compute_pct_det_series_numba(speakers)

    def compute_rmse_series(pct_det: np.ndarray) -> np.ndarray:
        return _compute_rmse_series_numba(pct_det)
else:
    def compute_pct_det_series(speakers: np.ndarray) -> np.ndarray:
        n = len(speakers)
        result = np.zeros(n, dtype=float)
        half_window = PCT_DET_WINDOW // 2
        for t in range(n):
            start = max(0, t - half_window)
            end = min(n, t + half_window + 1)
            result[t] = pct_det_for_window(speakers[start:end])
        return result

    def compute_rmse_series(pct_det: np.ndarray) -> np.ndarray:
        n = len(pct_det)
        rmse = np.full(n, np.nan, dtype=float)
        horizon = RMSE_DELTA_N
        for t in range(n):
            if not np.isfinite(pct_det[t]):
                continue
            if t + horizon >= n:
                continue
            obs = pct_det[t + 1:t + horizon + 1]
            if not np.all(np.isfinite(obs)):
                continue

            start = max(0, t - RMSE_WINDOW)
            candidate_idx = np.arange(start, t)
            if candidate_idx.size == 0:
                continue
            candidate_idx = candidate_idx[candidate_idx + horizon < n]
            if candidate_idx.size == 0:
                continue
            neighbor_mask = np.isfinite(pct_det[candidate_idx]) & (
                np.abs(pct_det[candidate_idx] - pct_det[t]) <= RMSE_EPSILON
            )
            neighbors = candidate_idx[neighbor_mask]
            if neighbors.size < MIN_RMSE_NEIGHBORS:
                continue
            trajectories = np.vstack([pct_det[s + 1:s + horizon + 1] for s in neighbors])
            if trajectories.shape[0] < MIN_RMSE_NEIGHBORS:
                continue
            mean_prediction = np.nanmean(trajectories, axis=0)
            if not np.all(np.isfinite(mean_prediction)):
                continue
            rmse[t] = float(np.sqrt(np.mean((mean_prediction - obs) ** 2)))
        return rmse


def compute_metrics(series_df: pd.DataFrame) -> pd.DataFrame:
    speakers = series_df["speaker_id"].to_numpy(dtype=np.int64)
    metrics_df = series_df[["second", "speaker_id"]].copy()
    metrics_df["entropy"] = compute_entropy_series(speakers)
    metrics_df["pct_det"] = compute_pct_det_series(speakers)
    metrics_df["rmse"] = compute_rmse_series(metrics_df["pct_det"].to_numpy(dtype=float))
    return metrics_df


def normalize_columns(columns: Iterable[object]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for column in columns:
        name = str(column).strip()
        normalized = " ".join(name.lower().replace("_", " ").split())
        mapping[normalized] = name
    return mapping


def pick_speaker_column(df: pd.DataFrame) -> Tuple[str | None, bool]:
    normalized = normalize_columns(df.columns)
    preferred = [
        "speaker id",
        "speaker",
        "speakernum",
        "spkr codes",
        "spkr code",
        "speaker code",
        "speaker codes",
        "unnamed: 4",
    ]
    for key in preferred:
        if key in normalized:
            return normalized[key], True

    candidates: List[Tuple[str, float, float]] = []
    for column in df.columns:
        series = pd.to_numeric(df[column], errors="coerce")
        valid = series.dropna()
        if valid.empty:
            continue
        integer_like = np.isclose(valid, np.round(valid)).mean()
        non_negative = (valid >= 0).mean()
        if integer_like >= 0.95 and non_negative >= 0.95 and valid.nunique() >= 2:
            candidates.append((str(column), float(valid.nunique()), float(valid.max())))
    if candidates:
        candidates.sort(key=lambda item: (item[1], -item[2]))
        return candidates[0][0], False

    return None, False


def coerce_speaker_ids(raw_series: pd.Series) -> pd.Series:
    speaker_labels = raw_series.astype(str).str.strip()
    speaker_labels = speaker_labels.replace({"": np.nan, "nan": np.nan, "None": np.nan})
    silence_tokens = {"0", "0.0", "silence", "silent", "pause", "no speaker", "none"}
    is_silence = speaker_labels.str.lower().isin(silence_tokens)

    numeric_speakers = pd.to_numeric(speaker_labels, errors="coerce")
    numeric_valid = numeric_speakers.dropna()
    if not numeric_valid.empty and numeric_speakers.notna().mean() >= 0.8:
        return numeric_speakers.fillna(0).round().astype(int)

    active_labels = pd.unique(speaker_labels[~speaker_labels.isna() & ~is_silence])
    label_map = {label: idx + 1 for idx, label in enumerate(active_labels)}
    return speaker_labels.map(label_map).fillna(0).astype(int)


def is_supported_series_schema(second_col: str | None, speaker_col: str | None, speaker_col_is_explicit: bool) -> bool:
    if speaker_col is None:
        return False
    if second_col is not None:
        return True
    return speaker_col_is_explicit


def infer_domain_from_dataframe(df: pd.DataFrame) -> str:
    text = " ".join(str(value) for value in df.columns)
    sample_values = df.head(50).astype(str).fillna("").to_numpy().ravel()
    text = f"{text} {' '.join(sample_values)}".lower()
    submarine_tokens = {
        "captain",
        "navigator",
        "officer on deck",
        "fathometer",
        "quartermaster",
        "periscope",
        "radar",
        "helm",
        "contact coordinator",
    }
    if any(token in text for token in submarine_tokens):
        return "submarine"
    return "surgical"


def infer_context(file_path: Path, df: pd.DataFrame) -> str:
    stem = file_path.stem
    prefix = stem[0].upper()
    if prefix == "E":
        return "submarine_experienced"
    if prefix == "T":
        return "submarine_less_experienced"
    if prefix == "J":
        return "surgical_student"
    domain = infer_domain_from_dataframe(df)
    return f"{domain}_unknown"


def load_standard_series(file_path: Path) -> Tuple[pd.DataFrame, Dict[str, object]]:
    workbook = pd.ExcelFile(file_path)
    first_sheet = workbook.sheet_names[0]
    raw_df = pd.read_excel(file_path, sheet_name=first_sheet)

    normalized = normalize_columns(raw_df.columns)
    second_col = None
    for candidate in ["second", "epoch", "team epoch"]:
        if candidate in normalized:
            second_col = normalized[candidate]
            break

    speaker_col, speaker_col_is_explicit = pick_speaker_column(raw_df)
    if not is_supported_series_schema(second_col, speaker_col, speaker_col_is_explicit):
        raise ValueError(
            f"Unsupported workbook schema for speaker time series in {file_path.name}: "
            f"missing usable second/speaker columns on sheet '{first_sheet}'."
        )

    if second_col is None:
        series_df = raw_df[[speaker_col]].copy()
        series_df.insert(0, "second", np.arange(1, len(series_df) + 1))
        series_df.columns = ["second", "speaker_id"]
    else:
        series_df = raw_df[[second_col, speaker_col]].copy()
        series_df.columns = ["second", "speaker_id"]

    series_df["second"] = pd.to_numeric(series_df["second"], errors="coerce")
    series_df = series_df.dropna(subset=["second"]).copy()
    series_df["second"] = series_df["second"].round().astype(int)

    series_df["speaker_id"] = coerce_speaker_ids(series_df["speaker_id"])
    series_df = series_df.sort_values("second").drop_duplicates(subset=["second"], keep="last")

    full_seconds = np.arange(int(series_df["second"].min()), int(series_df["second"].max()) + 1)
    series_df = series_df.set_index("second").reindex(full_seconds)
    series_df.index.name = "second"
    series_df["speaker_id"] = series_df["speaker_id"].fillna(0).astype(int)
    series_df = series_df.reset_index()

    context = infer_context(file_path, raw_df)
    domain = "submarine" if context.startswith("submarine") else "surgical"
    silence_pct = float((series_df["speaker_id"] == 0).mean() * 100.0)
    metadata = {
        "source_file": file_path.name,
        "sheet_name": first_sheet,
        "team_id": file_path.stem,
        "context": context,
        "domain": domain,
        "n_seconds": int(len(series_df)),
        "silence_pct": silence_pct,
        "speaker_id_column": speaker_col,
    }
    return series_df, metadata


def make_lsh_equivalent(standard_df: pd.DataFrame) -> pd.DataFrame:
    lsh_df = standard_df.copy()
    replaced = lsh_df["speaker_id"].replace(0, np.nan)
    replaced = replaced.ffill().bfill().fillna(0)
    lsh_df["speaker_id"] = replaced.astype(int)
    return lsh_df


def make_long_metrics(metrics_df: pd.DataFrame, metadata: Dict[str, object], method: str) -> pd.DataFrame:
    out = metrics_df.copy()
    out.insert(0, "method", method)
    out.insert(0, "domain", metadata["domain"])
    out.insert(0, "context", metadata["context"])
    out.insert(0, "team_id", metadata["team_id"])
    out.insert(0, "source_file", metadata["source_file"])
    return out


def summarize_team_correlations(
    metadata: Dict[str, object],
    metrics_standard: pd.DataFrame,
    metrics_lsh: pd.DataFrame,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for metric in ["entropy", "pct_det", "rmse"]:
        r, p_value, n = compute_pearson(
            metrics_standard[metric].to_numpy(dtype=float),
            metrics_lsh[metric].to_numpy(dtype=float),
        )
        ci_lower, ci_upper = fisher_ci(r, n)
        rows.append(
            {
                "context": metadata["context"],
                "domain": metadata["domain"],
                "team_id": metadata["team_id"],
                "metric": metric,
                "r": r,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "p_value": p_value,
                "n_seconds": n,
                "silence_pct": metadata["silence_pct"],
                "source_file": metadata["source_file"],
            }
        )
    return rows


def pooled_domain_summary(
    metrics_standard_all: pd.DataFrame,
    metrics_lsh_all: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for domain in ["surgical", "submarine"]:
        standard_domain = metrics_standard_all[metrics_standard_all["domain"] == domain].copy()
        lsh_domain = metrics_lsh_all[metrics_lsh_all["domain"] == domain].copy()
        if standard_domain.empty or lsh_domain.empty:
            continue
        team_count = int(standard_domain["team_id"].nunique())
        silence_mean = float(standard_domain.groupby("team_id")["speaker_id"].apply(lambda s: (s == 0).mean() * 100.0).mean())
        for metric in ["entropy", "pct_det", "rmse"]:
            merged = standard_domain[["team_id", "second", metric]].merge(
                lsh_domain[["team_id", "second", metric]],
                on=["team_id", "second"],
                suffixes=("_standard", "_lsh"),
                how="inner",
            )
            r, p_value, n = compute_pearson(
                merged[f"{metric}_standard"].to_numpy(dtype=float),
                merged[f"{metric}_lsh"].to_numpy(dtype=float),
            )
            ci_lower, ci_upper = fisher_ci(r, n)
            rows.append(
                {
                    "domain": domain,
                    "metric": metric,
                    "r": r,
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper,
                    "p_value": p_value,
                    "n_seconds": n,
                    "team_count": team_count,
                    "mean_silence_pct": silence_mean,
                }
            )
    return pd.DataFrame(rows)


def sampled_scatter(
    metrics_standard_all: pd.DataFrame,
    metrics_lsh_all: pd.DataFrame,
    domain: str,
    metric: str,
    output_path: Path,
) -> None:
    merged = metrics_standard_all[
        metrics_standard_all["domain"] == domain
    ][["team_id", "second", metric]].merge(
        metrics_lsh_all[metrics_lsh_all["domain"] == domain][["team_id", "second", metric]],
        on=["team_id", "second"],
        suffixes=("_standard", "_lsh"),
        how="inner",
    )
    merged = merged.dropna()
    if merged.empty:
        return

    r, _, n = compute_pearson(
        merged[f"{metric}_standard"].to_numpy(dtype=float),
        merged[f"{metric}_lsh"].to_numpy(dtype=float),
    )
    sample_n = max(1, int(math.ceil(len(merged) * SCATTER_SAMPLE_FRAC)))
    if sample_n < len(merged):
        sample_idx = RNG.choice(len(merged), size=sample_n, replace=False)
        plot_df = merged.iloc[np.sort(sample_idx)].copy()
    else:
        plot_df = merged.copy()

    label_map = {"entropy": "Entropy", "pct_det": "%DET"}
    fig, ax = plt.subplots(figsize=(9, 8), constrained_layout=True)
    sns.regplot(
        data=plot_df,
        x=f"{metric}_standard",
        y=f"{metric}_lsh",
        scatter_kws={"alpha": 0.3, "s": 18, "color": "#1f77b4"},
        line_kws={"color": "#d62728", "lw": 2},
        ci=None,
        ax=ax,
    )
    ax.set_title(f"{label_map[metric]}: standard vs. LSH-equivalent ({domain})")
    ax.set_xlabel(f"Standard-method {label_map[metric]}")
    ax.set_ylabel(f"LSH-equivalent {label_map[metric]}")
    ax.text(
        0.03,
        0.97,
        f"Pearson r = {r:.3f}\nPaired seconds = {n:,}\nPlotted sample = {len(plot_df):,} (10%)",
        transform=ax.transAxes,
        ha="left",
        va="top",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "alpha": 0.9},
    )
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def silence_distribution_figure(results_df: pd.DataFrame, output_path: Path) -> None:
    silence_df = (
        results_df[["domain", "context", "team_id", "silence_pct"]]
        .drop_duplicates()
        .sort_values(["domain", "silence_pct", "team_id"], ascending=[True, False, True])
    )
    if silence_df.empty:
        return

    fig, ax = plt.subplots(figsize=(14, 8), constrained_layout=True)
    sns.barplot(
        data=silence_df,
        x="team_id",
        y="silence_pct",
        hue="context",
        dodge=False,
        palette="tab10",
        ax=ax,
    )
    ax.set_title("Silence percentage in the standard Gorman series by team")
    ax.set_xlabel("Team ID")
    ax.set_ylabel("Silence percentage (%)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="Context", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def update_readme(domain_summary_df: pd.DataFrame) -> None:
    summary_map = {
        (row["domain"], row["metric"]): row
        for _, row in domain_summary_df.iterrows()
    }

    def get(domain: str, metric: str, field: str) -> float:
        row = summary_map.get((domain, metric))
        if row is None:
            return float("nan")
        return float(row[field])

    def get_team_count(domain: str) -> int:
        rows = domain_summary_df[domain_summary_df["domain"] == domain]
        if rows.empty:
            return 0
        return int(rows["team_count"].iloc[0])

    def get_silence(domain: str) -> float:
        rows = domain_summary_df[domain_summary_df["domain"] == domain]
        if rows.empty:
            return float("nan")
        return float(rows["mean_silence_pct"].iloc[0])

    readme_text = f"""# 03_convergent_validity

This directory contains the code and documentation for the **convergent validity** stage of the reproducible analysis pipeline.

## Step 3 — Convergent Validity

Input:  `data/raw/gorman/*` (Gorman standard-method 1 Hz series in Excel format)
Output: `data/processed/convergent_validity/`

### Method note

LSH-equivalent series are created by forward-filling silence codes (`speaker_id = 0`) with the most recent active speaker. If a series starts with silence, the initial gap is backward-filled from the first active speaker. This isolates the single methodological difference between the LSH approach and the standard Gorman coding method while preserving the original second-by-second timeline.

### Results

Surgical teams (experienced + student, N={get_team_count('surgical')} teams):  
  Entropy: r = {get('surgical', 'entropy', 'r'):.3f} (95% CI [{get('surgical', 'entropy', 'ci_lower'):.3f}, {get('surgical', 'entropy', 'ci_upper'):.3f}]), p = {get('surgical', 'entropy', 'p_value'):.3g}  
  %DET:    r = {get('surgical', 'pct_det', 'r'):.3f} (95% CI [{get('surgical', 'pct_det', 'ci_lower'):.3f}, {get('surgical', 'pct_det', 'ci_upper'):.3f}]), p = {get('surgical', 'pct_det', 'p_value'):.3g}  
  RMSE:    r = {get('surgical', 'rmse', 'r'):.3f} (95% CI [{get('surgical', 'rmse', 'ci_lower'):.3f}, {get('surgical', 'rmse', 'ci_upper'):.3f}]), p = {get('surgical', 'rmse', 'p_value'):.3g}  
  Mean silence: {get_silence('surgical'):.2f}%

Submarine crews (experienced + less experienced, N={get_team_count('submarine')} crews):  
  Entropy: r = {get('submarine', 'entropy', 'r'):.3f} (95% CI [{get('submarine', 'entropy', 'ci_lower'):.3f}, {get('submarine', 'entropy', 'ci_upper'):.3f}]), p = {get('submarine', 'entropy', 'p_value'):.3g}  
  %DET:    r = {get('submarine', 'pct_det', 'r'):.3f} (95% CI [{get('submarine', 'pct_det', 'ci_lower'):.3f}, {get('submarine', 'pct_det', 'ci_upper'):.3f}]), p = {get('submarine', 'pct_det', 'p_value'):.3g}  
  RMSE:    r = {get('submarine', 'rmse', 'r'):.3f} (95% CI [{get('submarine', 'rmse', 'ci_lower'):.3f}, {get('submarine', 'rmse', 'ci_upper'):.3f}]), p = {get('submarine', 'rmse', 'p_value'):.3g}  
  Mean silence: {get_silence('submarine'):.2f}%

### Target values (from prior exploratory analyses)

- Surgical Entropy: r ≈ .867
- Submarine Entropy: r ≈ .932

### Files

- `main.py` loads the available Gorman Excel files, extracts the standard 1 Hz speaker series, creates the LSH-equivalent forward-filled version, computes Entropy, %DET, and RMSE for both versions, and exports the comparison outputs.
- `data/processed/convergent_validity/convergent_validity_results.csv` stores per-team metric correlations between the standard and LSH-equivalent series.
- `data/processed/convergent_validity/metrics_standard_all.csv` stores pooled second-level metrics for the standard-method series.
- `data/processed/convergent_validity/metrics_lsh_all.csv` stores pooled second-level metrics for the LSH-equivalent series.
- `data/processed/convergent_validity/domain_summary.csv` stores pooled domain-level correlations used in this README.
- `figures/03_convergent_validity/` stores the requested scatter plots and silence distribution figure.
"""
    README_PATH.write_text(readme_text)


def main() -> None:
    CONV_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    file_paths = sorted([path for path in GORMAN_DIR.iterdir() if path.suffix.lower() in {".xls", ".xlsx"}])
    if not file_paths:
        raise FileNotFoundError(f"No Excel files found in {GORMAN_DIR}")

    standard_frames: List[pd.DataFrame] = []
    lsh_frames: List[pd.DataFrame] = []
    result_rows: List[Dict[str, object]] = []
    extraction_rows: List[Dict[str, object]] = []

    for file_path in file_paths:
        try:
            standard_series, metadata = load_standard_series(file_path)
        except ValueError as exc:
            print(f"Skipping {file_path.name}: {exc}")
            extraction_rows.append(
                {
                    "source_file": file_path.name,
                    "sheet_name": None,
                    "team_id": file_path.stem,
                    "context": "unsupported_schema",
                    "domain": "unknown",
                    "n_seconds": 0,
                    "silence_pct": np.nan,
                    "speaker_id_column": None,
                    "status": "skipped",
                    "notes": str(exc),
                }
            )
            continue

        lsh_series = make_lsh_equivalent(standard_series)

        metrics_standard = compute_metrics(standard_series)
        metrics_lsh = compute_metrics(lsh_series)

        standard_frames.append(make_long_metrics(metrics_standard, metadata, method="standard"))
        lsh_frames.append(make_long_metrics(metrics_lsh, metadata, method="lsh_equivalent"))
        result_rows.extend(summarize_team_correlations(metadata, metrics_standard, metrics_lsh))
        extraction_rows.append({**metadata, "status": "processed", "notes": ""})

    metrics_standard_all = pd.concat(standard_frames, ignore_index=True)
    metrics_lsh_all = pd.concat(lsh_frames, ignore_index=True)
    results_df = pd.DataFrame(result_rows).sort_values(["domain", "team_id", "metric"])
    extraction_df = pd.DataFrame(extraction_rows).sort_values(["domain", "team_id"])
    domain_summary_df = pooled_domain_summary(metrics_standard_all, metrics_lsh_all).sort_values(["domain", "metric"])

    metrics_standard_all.to_csv(CONV_DIR / "metrics_standard_all.csv", index=False)
    metrics_lsh_all.to_csv(CONV_DIR / "metrics_lsh_all.csv", index=False)
    results_df.to_csv(CONV_DIR / "convergent_validity_results.csv", index=False)
    extraction_df.to_csv(CONV_DIR / "gorman_series_inventory.csv", index=False)
    domain_summary_df.to_csv(CONV_DIR / "domain_summary.csv", index=False)

    sampled_scatter(metrics_standard_all, metrics_lsh_all, domain="surgical", metric="entropy", output_path=FIGURES_DIR / "scatter_entropy_surgical.png")
    sampled_scatter(metrics_standard_all, metrics_lsh_all, domain="submarine", metric="entropy", output_path=FIGURES_DIR / "scatter_entropy_submarine.png")
    sampled_scatter(metrics_standard_all, metrics_lsh_all, domain="surgical", metric="pct_det", output_path=FIGURES_DIR / "scatter_pct_det_surgical.png")
    sampled_scatter(metrics_standard_all, metrics_lsh_all, domain="submarine", metric="pct_det", output_path=FIGURES_DIR / "scatter_pct_det_submarine.png")
    silence_distribution_figure(results_df, FIGURES_DIR / "silence_distribution.png")

    update_readme(domain_summary_df)


if __name__ == "__main__":
    main()
