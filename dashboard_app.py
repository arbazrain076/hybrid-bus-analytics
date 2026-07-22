"""Streamlit dashboard for the bus reliability platform.

An optional presentation layer over results the pipeline has already produced. It performs no
computation of its own: every figure is read from the relational store or from outputs/, so the
dashboard cannot disagree with the report.

Run with:  streamlit run dashboard_app.py
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dashboard import data_access as da  # noqa: E402

st.set_page_config(page_title="Bus Reliability Platform", page_icon="🚌", layout="wide")

ON_TIME_TARGET = 85.0


@st.cache_data(show_spinner=False)
def _headline():
    return da.headline_metrics()


@st.cache_data(show_spinner=False)
def _operators():
    return da.operator_summary()


@st.cache_data(show_spinner=False)
def _lines(operator: str):
    return da.line_summary(operator)


@st.cache_data(show_spinner=False)
def _hours(operator: str | None):
    return da.delay_by_hour(operator)


@st.cache_data(show_spinner=False)
def _stops(operator: str):
    return da.worst_stops(operator)


def overview() -> None:
    st.subheader("Network overview")
    m = _headline()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Delay observations", f"{int(m['events']):,}")
    c2.metric("Mean delay", f"{m['mean_delay']:.2f} min")
    c3.metric("Service Reliability", f"{m['on_time_pct']:.1f}%",
              delta=f"{m['on_time_pct'] - ON_TIME_TARGET:.1f} vs target", delta_color="inverse")
    c4.metric("Operators / lines", f"{int(m['operators'])} / {int(m['lines'])}")

    st.caption(
        f"Service Reliability is the share of arrivals within ±{da.ON_TIME_TOL_MIN:.0f} minutes of "
        f"timetable. The brief's target is {ON_TIME_TARGET:.0f}%."
    )

    left, right = st.columns(2)
    with left:
        fig = da.figure("delay_distribution.png")
        if fig:
            st.image(str(fig), caption="Distribution of observed delay")
    with right:
        fig = da.figure("delay_by_hour.png")
        if fig:
            st.image(str(fig), caption="Mean delay by scheduled hour")


def operators_view() -> None:
    st.subheader("Operator compliance")
    ops = _operators()
    st.dataframe(
        ops.rename(columns={"operator": "Code", "operator_name": "Operator", "events": "Events",
                            "mean_delay": "Mean delay (min)", "on_time_pct": "On-time %"}),
        use_container_width=True, hide_index=True,
    )
    st.caption("Operators with at least 500 observed arrivals. No operator meets the 85% target.")

    chosen = st.selectbox("Inspect an operator", ops["operator"].tolist())
    if not chosen:
        return

    lines = _lines(chosen)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Least reliable lines**")
        st.dataframe(lines.head(12), use_container_width=True, hide_index=True)
    with c2:
        hours = _hours(chosen)
        if not hours.empty:
            st.markdown("**Delay by scheduled hour**")
            st.line_chart(hours.set_index("sched_hour")["mean_delay"])

    st.markdown("**Stops with the highest mean delay**")
    st.dataframe(_stops(chosen), use_container_width=True, hide_index=True)


def models_view() -> None:
    st.subheader("Model comparison")
    models = da.model_comparison()
    if models is None:
        st.info("Run scripts/run_ml.py to generate the model comparison.")
        return

    st.dataframe(models, use_container_width=True, hide_index=True)
    st.caption(
        "Evaluated on the held-out test day under a time-based split (seed 42). Model Efficiency is the "
        "reciprocal of RMSE per training second, so higher is better."
    )
    c1, c2 = st.columns(2)
    for col, name, cap in [
        (c1, "metrics_error_by_model.png", "Prediction error by model"),
        (c2, "metrics_accuracy_vs_cost.png", "Accuracy against training cost"),
    ]:
        fig = da.figure(name)
        if fig:
            col.image(str(fig), caption=cap)


def main() -> None:
    st.title("🚌 Hybrid Bus Reliability Platform")
    st.caption("Greater Manchester · reconstructed from open BODS timetable and vehicle-position data")

    if not da.database_available():
        st.error(
            "No database found. Build the pipeline first:\n\n"
            "```\npython scripts/run_pipeline.py\n```"
        )
        return

    overview_tab, operator_tab, model_tab = st.tabs(["Overview", "Operators", "Models"])
    with overview_tab:
        overview()
    with operator_tab:
        operators_view()
    with model_tab:
        models_view()


if __name__ == "__main__":
    main()
