"""
FinGuard - Banking Fraud Detection & Transaction Intelligence System
Module: exploratory_analysis.py
Purpose: Conducts comprehensive exploratory data analysis (EDA), computes financial
         exposure metrics, and generates publication-grade visualizations.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

# Visual design constants adhering to FinGuard design specification
PALETTE = {
    "navy_dark": "#0A192F",
    "navy_card": "#172A45",
    "slate_text": "#8892B0",
    "light_text": "#CCD6F6",
    "coral_alert": "#FF4D4D",
    "teal_secure": "#00E5FF",
    "amber_caution": "#FFAA00",
    "grid_color": "#233554",
}

def set_finguard_plot_style() -> None:
    """Configures professional dark-navy theme for financial intelligence dashboards."""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor": PALETTE["navy_dark"],
        "axes.facecolor": PALETTE["navy_card"],
        "axes.edgecolor": PALETTE["grid_color"],
        "axes.labelcolor": PALETTE["light_text"],
        "xtick.color": PALETTE["slate_text"],
        "ytick.color": PALETTE["slate_text"],
        "text.color": PALETTE["light_text"],
        "grid.color": PALETTE["grid_color"],
        "grid.linestyle": "--",
        "grid.alpha": 0.5,
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "figure.titlesize": 14,
        "figure.titleweight": "bold",
    })


def _safe_save_figure(out_path: Path, dpi: int = 300) -> Path:
    """Saves figure safely, resolving Windows/OneDrive file locks and reparse points."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        try:
            out_path.unlink()
        except OSError:
            pass
    try:
        plt.savefig(str(out_path), dpi=dpi, bbox_inches="tight")
    except OSError:
        import time
        time.sleep(0.5)
        if out_path.exists():
            try:
                out_path.unlink()
            except OSError:
                pass
        plt.savefig(str(out_path), dpi=dpi, bbox_inches="tight")
    plt.close()
    return out_path


def load_clean_data(filepath: str | Path) -> pd.DataFrame:
    """Loads cleaned, preprocessed transactions."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned dataset not found at: {path.resolve()}")
    df = pd.read_csv(path)
    return df


def compute_eda_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Computes comprehensive statistical metrics across legitimate and fraud classes."""
    legit_mask = df["Class"] == 0
    fraud_mask = df["Class"] == 1

    total_count = len(df)
    legit_count = int(legit_mask.sum())
    fraud_count = int(fraud_mask.sum())
    fraud_rate = (fraud_count / total_count) * 100.0

    total_amount = float(df["Amount"].sum())
    legit_amount = float(df.loc[legit_mask, "Amount"].sum())
    fraud_amount = float(df.loc[fraud_mask, "Amount"].sum())
    fraud_exposure_pct = (fraud_amount / total_amount) * 100.0

    legit_amt_series = df.loc[legit_mask, "Amount"]
    fraud_amt_series = df.loc[fraud_mask, "Amount"]

    return {
        "volume": {
            "total_transactions": total_count,
            "legitimate_count": legit_count,
            "fraud_count": fraud_count,
            "fraud_percentage": fraud_rate,
            "imbalance_ratio": f"1:{int(round(legit_count / fraud_count))}",
        },
        "financial_exposure": {
            "total_turnover_eur": total_amount,
            "legitimate_volume_eur": legit_amount,
            "fraud_exposure_eur": fraud_amount,
            "fraud_exposure_percentage": fraud_exposure_pct,
        },
        "amount_metrics": {
            "legit_mean": float(legit_amt_series.mean()),
            "legit_median": float(legit_amt_series.median()),
            "legit_std": float(legit_amt_series.std()),
            "legit_min": float(legit_amt_series.min()),
            "legit_max": float(legit_amt_series.max()),
            "fraud_mean": float(fraud_amt_series.mean()),
            "fraud_median": float(fraud_amt_series.median()),
            "fraud_std": float(fraud_amt_series.std()),
            "fraud_min": float(fraud_amt_series.min()),
            "fraud_max": float(fraud_amt_series.max()),
        },
    }


def plot_class_distribution(df: pd.DataFrame, output_dir: Path) -> Path:
    """Generates dual-axis log-scale volume and share distribution chart."""
    set_finguard_plot_style()
    stats = compute_eda_summary_stats(df)
    vol = stats["volume"]
    exp = stats["financial_exposure"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), facecolor=PALETTE["navy_dark"])

    # Subplot 1: Transaction Volume Comparison (Log-scale bar chart)
    categories = ["Legitimate (Class 0)", "Fraudulent (Class 1)"]
    counts = [vol["legitimate_count"], vol["fraud_count"]]
    colors = [PALETTE["teal_secure"], PALETTE["coral_alert"]]

    bars = ax1.bar(categories, counts, color=colors, width=0.45, edgecolor="none")
    ax1.set_yscale("log")
    ax1.set_ylabel("Transaction Count (Log Scale)", color=PALETTE["light_text"])
    ax1.set_title("Transaction Volume & Extreme Class Imbalance")
    ax1.grid(True, axis="y", alpha=0.3)

    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height * 1.3,
            f"{count:,}\n({(count / vol['total_transactions']) * 100:.3f}%)",
            ha="center",
            va="bottom",
            color=PALETTE["light_text"],
            fontsize=10,
            fontweight="bold",
        )

    # Subplot 2: Financial Exposure Volume (€)
    amounts = [exp["legitimate_volume_eur"], exp["fraud_exposure_eur"]]
    bars2 = ax2.bar(categories, amounts, color=colors, width=0.45, edgecolor="none")
    ax2.set_yscale("log")
    ax2.set_ylabel("Total Turnover in EUR (Log Scale)", color=PALETTE["light_text"])
    ax2.set_title("Total Financial Exposure Comparison")
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"€{y:,.0f}"))
    ax2.grid(True, axis="y", alpha=0.3)

    for bar, amt in zip(bars2, amounts):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height * 1.3,
            f"€{amt:,.2f}\n({(amt / exp['total_turnover_eur']) * 100:.3f}%)",
            ha="center",
            va="bottom",
            color=PALETTE["light_text"],
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    out_path = output_dir / "class_distribution.png"
    return _safe_save_figure(out_path)


def plot_amount_distribution(df: pd.DataFrame, output_dir: Path) -> Path:
    """Generates comparative density and boxplots for transaction amounts."""
    set_finguard_plot_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), facecolor=PALETTE["navy_dark"])

    legit_amt = df[df["Class"] == 0]["Amount"]
    fraud_amt = df[df["Class"] == 1]["Amount"]

    # Subplot 1: Boxplot with logarithmic scale
    data_to_plot = [legit_amt, fraud_amt]
    box = ax1.boxplot(
        data_to_plot,
        tick_labels=["Legitimate", "Fraudulent"],
        patch_artist=True,
        showmeans=True,
        meanline=True,
        medianprops={"color": "#FFFFFF", "linewidth": 2},
        meanprops={"color": PALETTE["amber_caution"], "linewidth": 2, "linestyle": "--"},
        flierprops={"marker": ".", "color": PALETTE["slate_text"], "alpha": 0.3},
    )
    box["boxes"][0].set_facecolor(PALETTE["teal_secure"])
    box["boxes"][1].set_facecolor(PALETTE["coral_alert"])

    ax1.set_yscale("log")
    ax1.set_ylabel("Amount in EUR (Log Scale)", color=PALETTE["light_text"])
    ax1.set_title("Monetary Amount Distribution by Class (Boxplot)")
    ax1.grid(True, axis="y", alpha=0.3)

    # Subplot 2: Density / Histogram (clipped at 99th percentile for visual clarity)
    p99 = float(df["Amount"].quantile(0.99))
    legit_subset = legit_amt[legit_amt <= p99]
    sample_legit_kde = legit_subset.sample(n=min(30000, len(legit_subset)), random_state=42)
    fraud_subset = fraud_amt[fraud_amt <= p99]

    sns.kdeplot(
        sample_legit_kde,
        ax=ax2,
        color=PALETTE["teal_secure"],
        label=f"Legitimate (Mean: €{legit_amt.mean():.2f})",
        fill=True,
        alpha=0.3,
        linewidth=2,
    )
    sns.kdeplot(
        fraud_subset,
        ax=ax2,
        color=PALETTE["coral_alert"],
        label=f"Fraudulent (Mean: €{fraud_amt.mean():.2f})",
        fill=True,
        alpha=0.4,
        linewidth=2,
    )
    ax2.set_xlim(0, p99)
    ax2.set_xlabel("Transaction Amount in EUR (up to 99th percentile: €{:.0f})".format(p99))
    ax2.set_ylabel("Kernel Density")
    ax2.set_title("Transaction Amount Probability Density (KDE)")
    ax2.legend(loc="upper right", facecolor=PALETTE["navy_card"], edgecolor=PALETTE["grid_color"])
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = output_dir / "amount_distribution_by_class.png"
    return _safe_save_figure(out_path)


def plot_temporal_patterns(df: pd.DataFrame, output_dir: Path) -> Path:
    """Analyzes fraud occurrence patterns across hours and 48-hour timeline."""
    set_finguard_plot_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), facecolor=PALETTE["navy_dark"])

    # Subplot 1: Hourly Transaction Volume & Fraud Rate %
    hourly_stats = df.groupby("Hour").agg(
        total_txn=("Class", "count"),
        fraud_txn=("Class", "sum"),
    ).reset_index()
    hourly_stats["fraud_rate_pct"] = (hourly_stats["fraud_txn"] / hourly_stats["total_txn"]) * 100.0

    ax1.bar(
        hourly_stats["Hour"],
        hourly_stats["total_txn"],
        color=PALETTE["teal_secure"],
        alpha=0.35,
        width=0.6,
        label="Total Volume",
    )
    ax1.set_ylabel("Total Transactions", color=PALETTE["teal_secure"])
    ax1.set_xticks(range(24))
    ax1.grid(True, alpha=0.2)

    # Secondary twin axis for fraud rate
    ax1_twin = ax1.twinx()
    ax1_twin.plot(
        hourly_stats["Hour"],
        hourly_stats["fraud_rate_pct"],
        color=PALETTE["coral_alert"],
        marker="o",
        linewidth=2.5,
        markersize=6,
        label="Fraud Rate (%)",
    )
    ax1_twin.set_ylabel("Fraud Rate (%)", color=PALETTE["coral_alert"])
    ax1_twin.grid(False)
    ax1.set_title("Hourly Transaction Volume vs Fraud Incidence Rate (00:00 - 23:00)")

    # Subplot 2: Timeline across full 48 hours (binned into 1-hour windows)
    df_timeline = df.copy()
    df_timeline["Elapsed_Hour"] = (df_timeline["Time"] // 3600).astype(int)
    timeline_stats = df_timeline.groupby("Elapsed_Hour").agg(
        fraud_count=("Class", "sum"),
        fraud_exposure=("Amount", lambda x: x[df_timeline.loc[x.index, "Class"] == 1].sum()),
    ).reset_index()

    ax2.plot(
        timeline_stats["Elapsed_Hour"],
        timeline_stats["fraud_count"],
        color=PALETTE["amber_caution"],
        marker="s",
        linewidth=2,
        markersize=5,
        label="Fraud Events per Hour",
    )
    ax2.set_xlabel("Elapsed Hours from First Transaction (0 to 48 Hours)")
    ax2.set_ylabel("Fraud Events per Hour", color=PALETTE["amber_caution"])
    ax2.set_title("48-Hour Continuous Fraud Velocity Timeline")
    ax2.axvline(24, color=PALETTE["slate_text"], linestyle=":", label="Day 1 / Day 2 Boundary")
    ax2.legend(loc="upper right", facecolor=PALETTE["navy_card"], edgecolor=PALETTE["grid_color"])
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = output_dir / "hourly_fraud_pattern.png"
    return _safe_save_figure(out_path)


def plot_correlation_matrix(df: pd.DataFrame, output_dir: Path) -> Tuple[Path, pd.Series]:
    """Generates correlation ranking of all PCA features against target Class."""
    set_finguard_plot_style()
    v_cols = [f"V{i}" for i in range(1, 29)] + ["Amount", "Hour", "Class"]
    corr = df[v_cols].corr()
    class_corr = corr["Class"].drop("Class").sort_values()

    fig, ax = plt.subplots(figsize=(14, 7), facecolor=PALETTE["navy_dark"])

    colors = [PALETTE["coral_alert"] if x > 0 else PALETTE["teal_secure"] for x in class_corr.values]
    bars = ax.barh(class_corr.index, class_corr.values, color=colors, height=0.6)

    ax.axvline(0, color=PALETTE["slate_text"], linestyle="-", linewidth=1)
    ax.set_xlabel("Pearson Correlation Coefficient with Target (Class = 1)")
    ax.set_title("Feature Leverage Ranking: Linear Correlation with Fraud Class")
    ax.grid(True, axis="x", alpha=0.3)

    for bar, val in zip(bars, class_corr.values):
        ax.text(
            val + (0.008 if val >= 0 else -0.022),
            bar.get_y() + bar.get_height() / 2.0,
            f"{val:+.3f}",
            va="center",
            fontsize=8,
            color=PALETTE["light_text"],
            fontweight="bold",
        )

    plt.tight_layout()
    out_path = output_dir / "correlation_heatmap.png"
    _safe_save_figure(out_path)
    return out_path, class_corr


def plot_top_feature_boxplots(df: pd.DataFrame, output_dir: Path, top_corr: pd.Series) -> Path:
    """Generates comparative boxplots for top 4 positively and negatively correlated features."""
    set_finguard_plot_style()
    # Top 2 negative and Top 2 positive
    top_negative = list(top_corr.head(2).index)
    top_positive = list(top_corr.tail(2).index)
    selected_features = top_negative + top_positive

    fig, axes = plt.subplots(2, 2, figsize=(13, 9), facecolor=PALETTE["navy_dark"])
    axes = axes.flatten()

    for idx, feat in enumerate(selected_features):
        ax = axes[idx]
        legit_vals = df[df["Class"] == 0][feat]
        fraud_vals = df[df["Class"] == 1][feat]

        box = ax.boxplot(
            [legit_vals, fraud_vals],
            tick_labels=["Legitimate", "Fraudulent"],
            patch_artist=True,
            showmeans=True,
            meanline=True,
            medianprops={"color": "#FFFFFF", "linewidth": 2},
            meanprops={"color": PALETTE["amber_caution"], "linewidth": 2, "linestyle": "--"},
            flierprops={"marker": ".", "color": PALETTE["slate_text"], "alpha": 0.2},
        )
        box["boxes"][0].set_facecolor(PALETTE["teal_secure"])
        box["boxes"][1].set_facecolor(PALETTE["coral_alert"])

        corr_val = top_corr[feat]
        ax.set_title(f"{feat} Distribution (Corr with Fraud: {corr_val:+.3f})")
        ax.set_ylabel(f"{feat} Value")
        ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    out_path = output_dir / "top_features_distribution.png"
    return _safe_save_figure(out_path)


def plot_amount_vs_time_scatter(df: pd.DataFrame, output_dir: Path) -> Path:
    """Visualizes Amount vs Time with layered fraud markers."""
    set_finguard_plot_style()
    fig, ax = plt.subplots(figsize=(14, 6), facecolor=PALETTE["navy_dark"])

    legit = df[df["Class"] == 0]
    fraud = df[df["Class"] == 1]

    # Sample legitimate for performance while plotting all fraud instances
    sample_legit = legit.sample(n=min(25000, len(legit)), random_state=42)

    ax.scatter(
        sample_legit["Time"] / 3600.0,
        sample_legit["Amount"],
        c=PALETTE["teal_secure"],
        alpha=0.15,
        s=12,
        label=f"Legitimate Transactions (Sample: {len(sample_legit):,})",
        edgecolors="none",
    )
    ax.scatter(
        fraud["Time"] / 3600.0,
        fraud["Amount"],
        c=PALETTE["coral_alert"],
        alpha=0.9,
        s=45,
        label=f"Fraudulent Transactions (All: {len(fraud):,})",
        edgecolors="#FFFFFF",
        linewidths=0.5,
    )

    ax.set_yscale("log")
    ax.set_xlabel("Elapsed Time in Hours (0 to 48 Hours)")
    ax.set_ylabel("Transaction Amount in EUR (Log Scale)")
    ax.set_title("Temporal Transaction Exposure Scatter: Amount vs Time")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"€{y:,.0f}"))
    ax.legend(loc="upper right", facecolor=PALETTE["navy_card"], edgecolor=PALETTE["grid_color"])
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = output_dir / "amount_vs_fraud_scatter.png"
    return _safe_save_figure(out_path)


def run_full_eda(data_path: str | Path, figures_dir: str | Path) -> Dict[str, Any]:
    """Orchestrates end-to-end exploratory analysis and saves all visual figures."""
    df = load_clean_data(data_path)
    fig_dir = Path(figures_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("[FinGuard EDA] Computing statistical summaries...", flush=True)
    stats = compute_eda_summary_stats(df)

    print("[FinGuard EDA] Plotting class distribution...", flush=True)
    f1 = plot_class_distribution(df, fig_dir)

    print("[FinGuard EDA] Plotting amount distributions and KDE...", flush=True)
    f2 = plot_amount_distribution(df, fig_dir)

    print("[FinGuard EDA] Plotting temporal velocity and hourly trends...", flush=True)
    f3 = plot_temporal_patterns(df, fig_dir)

    print("[FinGuard EDA] Plotting correlation matrix...", flush=True)
    f4, top_corr = plot_correlation_matrix(df, fig_dir)

    print("[FinGuard EDA] Plotting top feature contrasts...", flush=True)
    f5 = plot_top_feature_boxplots(df, fig_dir, top_corr)

    print("[FinGuard EDA] Plotting Amount vs Time scatter...", flush=True)
    f6 = plot_amount_vs_time_scatter(df, fig_dir)

    figures = [str(f.resolve()) for f in [f1, f2, f3, f4, f5, f6]]
    return {
        "stats": stats,
        "figures": figures,
        "top_negative_features": list(top_corr.head(5).index),
        "top_positive_features": list(top_corr.tail(5).index),
    }


if __name__ == "__main__":
    clean_path = Path("FinGuard/data/processed/clean_creditcard.csv")
    fig_path = Path("FinGuard/reports/figures")

    if not clean_path.exists():
        print(f"Error: Processed data file {clean_path} does not exist. Run data_cleaning.py first.")
        sys.exit(1)

    results = run_full_eda(clean_path, fig_path)
    print("\n=== FinGuard EDA Summary Results ===")
    vol = results["stats"]["volume"]
    exp = results["stats"]["financial_exposure"]
    amt = results["stats"]["amount_metrics"]
    print(f"Total Transactions: {vol['total_transactions']:,}")
    print(f"Legitimate: {vol['legitimate_count']:,} | Fraudulent: {vol['fraud_count']:,}")
    print(f"Fraud Rate: {vol['fraud_percentage']:.4f}% ({vol['imbalance_ratio']})")
    print(f"Total Turnover: €{exp['total_turnover_eur']:,.2f}")
    print(f"Fraud Exposure: €{exp['fraud_exposure_eur']:,.2f} ({exp['fraud_exposure_percentage']:.4f}%)")
    print(f"Average Amount: Legit = €{amt['legit_mean']:.2f} | Fraud = €{amt['fraud_mean']:.2f}")
    print(f"Top Inversely Correlated Features: {results['top_negative_features']}")
    print(f"Top Directly Correlated Features: {results['top_positive_features']}")
    print(f"Figures generated: {len(results['figures'])} charts saved to {fig_path.resolve()}")
