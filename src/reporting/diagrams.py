"""Generates the report infographics: architecture, workflow, pipelines and schema.

Figures are written to outputs/report/assets/ for embedding in the technical report.
These depict project structure and previously verified counts; no results are computed here.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent.parent / "outputs" / "report" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#1F3A5F"
BLUE = "#2E6DA4"
TEAL = "#2E8B8B"
ORANGE = "#D97A34"
GREEN = "#3F8F5B"
PURPLE = "#6B4E9B"
RED = "#B03A3A"; GREY = "#6B7280"
LIGHT = "#F5F7FA"


def box(ax, x, y, w, h, title, sub=None, color=BLUE, fc=None, ts=11, ss=8.5):
    fc = fc or LIGHT
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=1.8, edgecolor=color, facecolor=fc, zorder=2))
    if sub:
        # Title sits near the top; the subtitle block is centred in the remaining space so
        # multi-line subtitles never collide with the title.
        ax.text(x + w / 2, y + h - 0.33, title, ha="center", va="center", fontsize=ts,
                fontweight="bold", color=NAVY, zorder=3)
        ax.text(x + w / 2, y + (h - 0.55) / 2 + 0.03, sub, ha="center", va="center",
                fontsize=ss, color=GREY, zorder=3, linespacing=1.45)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=ts,
                fontweight="bold", color=NAVY, zorder=3)


def arrow(ax, p1, p2, color=GREY, style="-|>", lw=1.8, rad=0.0):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=15,
                                 linewidth=lw, color=color,
                                 connectionstyle=f"arc3,rad={rad}", zorder=1))


def canvas(w, h, title, subtitle=None):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 10); ax.set_ylim(0, h / w * 10)
    ax.axis("off")
    top = h / w * 10
    ax.text(5, top - 0.32, title, ha="center", fontsize=14, fontweight="bold", color=NAVY)
    if subtitle:
        ax.text(5, top - 0.68, subtitle, ha="center", fontsize=9.5, color=GREY)
    return fig, ax, top


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- 1. Architecture
def architecture():
    fig, ax, top = canvas(11, 5.6, "System Architecture",
                          "Layered batch pipeline: ingestion - processing - storage - analytics")
    y = top - 2.5
    box(ax, 0.15, y, 1.9, 1.25, "Data Sources", "BODS archives\nGTFS + SIRI-VM", ORANGE, "#FDF1E7")
    box(ax, 2.35, y, 1.9, 1.25, "Ingestion", "PySpark\nsrc/ingestion", BLUE)
    box(ax, 4.55, y, 1.9, 1.25, "Processing", "Delay reconstruction\nsrc/processing", TEAL)
    box(ax, 6.75, y, 1.9, 1.25, "Silver Store", "Parquet, partitioned\nby service day", PURPLE, "#F0EBF7")

    for x in (2.05, 4.25, 6.45):
        arrow(ax, (x, y + 0.62), (x + 0.30, y + 0.62))

    # consumers
    cy = y - 1.85
    box(ax, 1.6, cy, 2.0, 1.05, "Relational DB", "SQLite star schema\nparameterised access", GREEN, "#EAF4EE")
    box(ax, 4.0, cy, 2.0, 1.05, "Machine Learning", "MLlib: 3 models\n+ baseline", BLUE)
    box(ax, 6.4, cy, 2.0, 1.05, "Analytics", "EDA figures +\ndomain metrics", TEAL)

    # Distribution "bus": drop from the silver store, span horizontally, then drop into each consumer.
    bus_y = cy + 1.42
    ax.plot([7.70, 7.70], [y, bus_y], color=GREY, lw=1.8, zorder=1)
    ax.plot([2.60, 7.70], [bus_y, bus_y], color=GREY, lw=1.8, zorder=1)
    for cx in (2.60, 5.00, 7.40):
        arrow(ax, (cx, bus_y), (cx, cy + 1.05))

    box(ax, 8.95, y, 0.95, 1.25, "Outputs", "reports\nfigures", GREY, "#EFF1F4", ts=9.5, ss=8)
    arrow(ax, (8.65, y + 0.62), (8.95, y + 0.62))
    save(fig, "fig_architecture.png")


# ---------------------------------------------------------------- 2. Workflow with counts
def workflow():
    fig, ax, top = canvas(11, 4.4, "End-to-End Data Workflow",
                          "Record counts observed at each stage (two service days)")
    y = top - 2.4
    stages = [
        ("Raw archives", "~15.5 GB\n5,641 XML snapshots", ORANGE, "#FDF1E7"),
        ("Bronze", "GTFS + SIRI-VM\nlanded", BLUE, LIGHT),
        ("Silver (GM)", "10.52M positions\n2.59M stop-events", TEAL, LIGHT),
        ("Delay events", "164,343 raw\nmatched", PURPLE, "#F0EBF7"),
        ("Cleaned target", "150,955 events\nML-ready", GREEN, "#EAF4EE"),
    ]
    w = 1.82
    for i, (t, s, c, fc) in enumerate(stages):
        x = 0.15 + i * 1.98
        box(ax, x, y, w, 1.3, t, s, c, fc, ts=10.5, ss=8)
        if i:
            arrow(ax, (x - 0.16, y + 0.65), (x, y + 0.65))
    ax.text(5, y - 0.55, "Filters applied: Greater Manchester bounding box | service-date scope | "
                         "journey-consistency cleaning",
            ha="center", fontsize=8.5, color=GREY, style="italic")
    save(fig, "fig_workflow.png")


# ---------------------------------------------------------------- 3. Delay reconstruction
def delay_method():
    fig, ax, top = canvas(11, 5.4, "Delay Reconstruction Method",
                          "The AVL feed carries no delay field, so delay is derived in three stages")
    y = top - 2.75
    box(ax, 0.2, y, 2.9, 1.7, "1. Resolve services",
        "GTFS calendar day-of-week\n+ calendar_dates exceptions\n-> trips running that date", BLUE)
    box(ax, 3.55, y, 2.9, 1.7, "2. Pin journey to trip",
        "Match scheduled ORIGIN\ndeparture (operator + line)\n-> robust to lateness", TEAL)
    box(ax, 6.9, y, 2.9, 1.7, "3. Snap to stop",
        "Nearest on-trip stop\n(haversine <= 120 m)\n-> delay = actual - scheduled", PURPLE, "#F0EBF7")
    arrow(ax, (3.1, y + 0.85), (3.55, y + 0.85))
    arrow(ax, (6.45, y + 0.85), (6.9, y + 0.85))

    box(ax, 1.6, y - 1.85, 6.8, 1.25, "4. Consistency cleaning",
        "Drop journeys whose per-stop delay SD > 6 min - physically impossible for one bus,\n"
        "i.e. matching failures. 164,343 -> 150,955 events; >20-min tail cut from 28% to 6%.",
        GREEN, "#EAF4EE", ts=11, ss=8.5)
    arrow(ax, (5.0, y), (5.0, y - 0.60))
    save(fig, "fig_delay_method.png")


# ---------------------------------------------------------------- 4. ML pipeline
def ml_pipeline():
    fig, ax, top = canvas(11, 4.8, "Machine Learning Pipeline (PySpark MLlib)",
                          "Feature stages are fitted inside cross-validation to avoid leakage")
    y = top - 2.35
    st = [("StringIndexer", "operator, line", BLUE), ("OneHotEncoder", "categorical -> vector", BLUE),
          ("VectorAssembler", "+ direction, stop_seq,\nsched_hour, lat/lon", TEAL),
          ("Estimator", "LR / RF / GBT", PURPLE)]
    w = 2.2
    for i, (t, s, c) in enumerate(st):
        x = 0.2 + i * 2.45
        box(ax, x, y, w, 1.2, t, s, c, "#F0EBF7" if c == PURPLE else LIGHT, ts=10, ss=8)
        if i:
            arrow(ax, (x - 0.25, y + 0.6), (x, y + 0.6))

    box(ax, 0.2, y - 1.7, 5.0, 1.1, "CrossValidator (3-fold, seed 42)",
        "ParamGrid tuning - identical split for every model", ORANGE, "#FDF1E7", ts=10.5, ss=8.5)
    box(ax, 5.6, y - 1.7, 4.2, 1.1, "Excluded (leakage guard)",
        "ping_sec | dist_m | delay_min\nasserted absent by pytest", "#B03A3A", "#FBEDED", ts=10.5, ss=8.5)
    arrow(ax, (2.6, y), (2.6, y - 0.60))
    save(fig, "fig_ml_pipeline.png")


# ---------------------------------------------------------------- 5. Spark optimisation
def spark_pipeline():
    fig, ax, top = canvas(11, 4.6, "Spark Processing & Optimisation",
                          "Techniques applied and the evidence captured for each")
    y = top - 2.35
    items = [
        ("Partitioning", "8 partitions configured\n(>= 4 required)", BLUE),
        ("Repartition", "8 -> 16 on join key\nverified at runtime", TEAL),
        ("Broadcast join", "small lookup broadcast\nBroadcastHashJoin in plan", GREEN),
        ("Caching", "cache() / unpersist()\nInMemoryRelation in plan", PURPLE),
    ]
    w = 2.2
    for i, (t, s, c) in enumerate(items):
        x = 0.2 + i * 2.45
        box(ax, x, y, w, 1.25, t, s, c, "#F0EBF7" if c == PURPLE else LIGHT, ts=10.5, ss=8)

    box(ax, 0.2, y - 1.75, 9.65, 1.15, "Lazy evaluation & DAG evidence",
        ".explain(True) physical plan captured + Spark UI partition utilisation screenshot.\n"
        "Driver memory raised to 4 GB and shuffle partitions to 64 after an OutOfMemoryError on the join.",
        ORANGE, "#FDF1E7", ts=11, ss=8.5)
    for i in range(4):
        arrow(ax, (1.3 + i * 2.45, y), (1.3 + i * 2.45, y - 0.60))
    save(fig, "fig_spark_pipeline.png")


# ---------------------------------------------------------------- 6. ER diagram
def er_diagram():
    fig, ax, top = canvas(10, 5.2, "Database Schema (Star Design)",
                          "Foreign keys enforced with PRAGMA foreign_keys = ON - 0 violations")

    def table(x, y, w, name, fields, color, rows):
        h = 0.44 + 0.24 + len(fields) * 0.235
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                                    linewidth=1.8, edgecolor=color, facecolor="white", zorder=2))
        ax.add_patch(FancyBboxPatch((x, y + h - 0.44), w, 0.44,
                                    boxstyle="round,pad=0.02,rounding_size=0.05",
                                    linewidth=0, facecolor=color, zorder=3))
        ax.text(x + w / 2, y + h - 0.22, name, ha="center", va="center", fontsize=10.5,
                fontweight="bold", color="white", zorder=4)
        for i, f in enumerate(fields):
            ax.text(x + 0.14, y + h - 0.72 - i * 0.235, f, ha="left", va="center",
                    fontsize=8.4, color=NAVY, zorder=4)
        ax.text(x + w / 2, y - 0.22, rows, ha="center", fontsize=8.6,
                color=color, fontweight="bold", zorder=4)
        return h

    fy = top - 4.05
    fact_fields = ["PK  event_id", "     service_date", "FK  operator", "     line",
                   "     direction_id", "     trip_id", "FK  stop_id", "     stop_sequence",
                   "     sched_sec", "     ping_sec", "     delay_min"]
    fh = table(3.3, fy, 3.5, "fact_delay_event", fact_fields, BLUE, "150,955 rows")
    dh = table(0.2, fy + 1.55, 2.6, "dim_operator",
               ["PK  operator", "     operator_name"], GREEN, "18 rows")
    table(7.3, fy + 1.55, 2.6, "dim_stop",
          ["PK  stop_id", "     stop_name", "     stop_lat / stop_lon"], ORANGE, "7,765 rows")

    ly = fy + 1.55 + dh / 2
    arrow(ax, (2.8, ly), (3.3, ly), color=GREEN)
    arrow(ax, (7.3, ly), (6.8, ly), color=ORANGE)
    ax.text(3.05, ly + 0.20, "1..N", ha="center", fontsize=8, color=GREY)
    ax.text(7.05, ly + 0.20, "1..N", ha="center", fontsize=8, color=GREY)
    save(fig, "fig_er_diagram.png")


# ---------------------------------------------------------------- 7. Cleaning funnel
def cleaning_funnel():
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    stages = ["Raw matched\nevents", "After delay\nrange filter", "After journey\nconsistency filter"]
    vals = [164343, 164343, 150955]
    colors = [ORANGE, TEAL, GREEN]
    bars = ax.barh(range(3), vals, color=colors, height=0.55)
    ax.set_yticks(range(3)); ax.set_yticklabels(stages, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("Delay events", fontsize=10)
    ax.set_title("Data Cleaning Funnel — Delay Event Table", fontsize=13,
                 fontweight="bold", color=NAVY, pad=14)
    for b, v in zip(bars, vals):
        ax.text(v + 2500, b.get_y() + b.get_height() / 2, f"{v:,}", va="center",
                fontsize=10, fontweight="bold", color=NAVY)
    ax.text(0.99, -0.18, "~49% of matched journeys removed as physically inconsistent (matching failures)",
            transform=ax.transAxes, ha="right", fontsize=8.5, color=GREY, style="italic")
    ax.set_xlim(0, 190000)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_cleaning_funnel.png")


# ------------------------------------------------------- 1. Key results (Exec Summary)
def key_results():
    fig, ax, top = canvas(11, 3.9, "Key Results at a Glance",
                          "All values from verified pipeline runs over two service days")
    stats = [("10.52M", "vehicle position\nrecords processed", BLUE, LIGHT),
             ("150,955", "verified delay\nobservations", TEAL, LIGHT),
             ("7.19 min", "best model RMSE\n(GBT, R² 0.644)", GREEN, "#EAF4EE"),
             ("26.2%", "Service Reliability\n(target 85%)", ORANGE, "#FDF1E7"),
             ("0.22", "Travel Time Variability\n(target 0.15)", RED, "#FBEDED")]
    w = 1.82
    y = top - 2.35
    for i, (big, lab, c, fc) in enumerate(stats):
        x = 0.15 + i * 1.98
        ax.add_patch(FancyBboxPatch((x, y), w, 1.5, boxstyle="round,pad=0.02,rounding_size=0.06",
                                    linewidth=1.8, edgecolor=c, facecolor=fc, zorder=2))
        ax.text(x + w / 2, y + 1.06, big, ha="center", va="center", fontsize=16,
                fontweight="bold", color=c, zorder=3)
        ax.text(x + w / 2, y + 0.48, lab, ha="center", va="center", fontsize=8.3,
                color=GREY, zorder=3, linespacing=1.45)
    save(fig, "fig_key_results.png")


# ------------------------------------------------------- 2. Journey identification (Lit review)
def journey_mismatch():
    fig, ax, top = canvas(11, 4.3, "The Journey-Identification Problem",
                          "The two feeds describe the same bus with incompatible identifiers")
    y = top - 2.35
    box(ax, 0.3, y, 3.5, 1.45, "GTFS timetable",
        "identifies a journey by\ntrip_id (opaque hash)\ne.g. VJ00b3f14...", BLUE)
    box(ax, 6.2, y, 3.5, 1.45, "SIRI-VM positions",
        "identifies a journey by\noperator + line +\ndated journey reference", TEAL)
    ax.add_patch(FancyBboxPatch((4.15, y + 0.35), 1.7, 0.75,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=1.8, edgecolor=RED, facecolor="#FBEDED", zorder=2))
    ax.text(5.0, y + 0.72, "no shared key", ha="center", va="center", fontsize=10,
            fontweight="bold", color=RED, zorder=3)
    arrow(ax, (3.8, y + 0.72), (4.15, y + 0.72), color=RED)
    arrow(ax, (6.2, y + 0.72), (5.85, y + 0.72), color=RED)
    box(ax, 1.6, y - 1.55, 6.8, 1.15, "Resolution adopted",
        "Anchor on the scheduled ORIGIN DEPARTURE time, shared by both feeds and\n"
        "unaffected by how late the vehicle is actually running.", GREEN, "#EAF4EE", ss=8.5)
    arrow(ax, (5.0, y + 0.35), (5.0, y - 0.40), color=GREEN)
    save(fig, "fig_journey_mismatch.png")


# ------------------------------------------------------- 3. Memory vs distributed (Reflection)
def tradeoff():
    fig, ax, top = canvas(11, 4.4, "Memory versus Distributed Trade-off",
                          "Observed on this project, not argued in the abstract")
    y = top - 2.4
    box(ax, 0.3, y, 4.4, 1.5, "Single-machine (pandas)",
        "~7 GB compressed XML per day\nexceeds comfortable memory\n-> not viable at this scale",
        RED, "#FBEDED")
    box(ax, 5.3, y, 4.4, 1.5, "Distributed (PySpark)",
        "file-per-snapshot parallelises\nnaturally across partitions\n-> viable, and used here",
        GREEN, "#EAF4EE")
    box(ax, 0.3, y - 1.7, 9.4, 1.25, "But distribution is not free",
        "The spatial-temporal join still failed with heap exhaustion under default settings, because too\n"
        "few shuffle partitions forced each task to materialise too much at once. A hard memory limit\n"
        "becomes a tuning problem: capability is gained, but so is operational complexity.",
        ORANGE, "#FDF1E7", ts=11, ss=8.4)
    arrow(ax, (2.5, y), (2.5, y - 0.45), color=GREY)
    arrow(ax, (7.5, y), (7.5, y - 0.45), color=GREY)
    save(fig, "fig_tradeoff.png")


# ------------------------------------------------------- 4. Outcomes (Conclusion)
def outcomes():
    fig, ax, top = canvas(11, 4.1, "Learning Outcomes Evidenced",
                          "Each outcome mapped to concrete, verifiable project evidence")
    items = [("B1", "Big-O analysis;\nOOM fix measured", BLUE),
             ("B2", "modular PySpark\n+ SQL layer", TEAL),
             ("B4", "10.5M records;\nMLlib comparison", GREEN),
             ("B6", "Git, pytest,\nsecurity, ethics", PURPLE),
             ("B7", "report + critical\nreflection", ORANGE),
             ("B8", "derived a target\nabsent from source", RED)]
    w = 1.5
    y = top - 2.3
    for i, (code, txt, c) in enumerate(items):
        x = 0.2 + i * 1.63
        ax.add_patch(FancyBboxPatch((x, y), w, 1.45, boxstyle="round,pad=0.02,rounding_size=0.06",
                                    linewidth=1.8, edgecolor=c, facecolor=LIGHT, zorder=2))
        ax.text(x + w / 2, y + 1.06, code, ha="center", va="center", fontsize=14,
                fontweight="bold", color=c, zorder=3)
        ax.text(x + w / 2, y + 0.45, txt, ha="center", va="center", fontsize=7.9,
                color=GREY, zorder=3, linespacing=1.4)
    save(fig, "fig_outcomes.png")




def build_all():
    """Regenerates every report infographic. Returns the filenames written."""
    architecture(); workflow(); delay_method(); ml_pipeline()
    spark_pipeline(); er_diagram(); cleaning_funnel()
    key_results(); journey_mismatch(); tradeoff(); outcomes()
    return sorted(p.name for p in OUT.glob("*.png"))


if __name__ == "__main__":
    print("\n".join(build_all()))
