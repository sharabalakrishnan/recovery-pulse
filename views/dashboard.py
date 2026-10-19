"""Community pulse: the organizer dashboard. Shows only group totals."""

import plotly.graph_objects as go
import streamlit as st

from pulse import scoring
from pulse.survey import STRESSOR_FLAGS, STRESSOR_LABELS
from views.common import DATA, DATA_DARK, DATA_RAMP, GREY, sample_banner, scored, setting
from views.style import page_header, section

INK, MUTED, GRID = "#1d1d1f", "#5f6470", "rgba(0,20,60,0.08)"
BASE = dict(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color=INK, family="-apple-system, BlinkMacSystemFont, Inter, Helvetica Neue, Arial, sans-serif", size=13),
            legend=dict(font=dict(color=INK, size=13)),
            margin=dict(l=70, r=30, t=30, b=70), hoverlabel=dict(bgcolor="white"))
CONFIG = {"displayModeBar": False}


def render():
    page_header("Community pulse", "Where recovery is lagging.",
                f"Anonymous check-ins after the {setting('community')} {setting('event')}, scored with belonginglab.")
    sample_banner()
    df = scored()
    if df.empty:
        st.info("No check-ins yet. Share the Check in page with residents to get started.")
        return
    s = scoring.summary(df)
    rec = scoring.recent(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Check-ins, last 4 weeks", f"{s['n_recent']:,}")
    change = s["trend_last"] - s["trend_first"]
    c2.metric("Average connection", f"{s['avg_recent']:.0f}", f"{change:+.0f} since week 1", delta_color="normal")
    c3.metric("Two or more strains", f"{s['two_plus_recent']:.0%}",
              f"{(s['two_plus_recent'] - s['two_plus_first']) * 100:+.0f} pts since week 1", delta_color="inverse")
    c4.metric(f"Asked for {s['top_need'].lower()}" if s["top_need"] else "Most requested help",
              f"{s['top_need_share']:.0%}" if s["top_need"] else "—", "top request", delta_color="off")

    # ---------------- trend
    section("Connection over time")
    st.caption("Average connection score (0–100) each week. Higher means people feel more supported and less "
               "strained. 50 is the middle of all check-ins.")
    table = scoring.neighborhood_table(rec)
    choices = table[~table["hidden"]]["neighborhood"].tolist()
    default = choices[-1] if choices else None
    pick = st.selectbox("Compare a neighborhood with the whole community", choices,
                        index=choices.index(default) if default else None) if choices else None
    st.plotly_chart(trend_chart(df, pick), use_container_width=True, theme=None, config=CONFIG)
    st.caption("The neighborhood line is a 3-week rolling average with its 90% range shaded, so small neighborhoods "
               f"reach the {scoring.MIN_GROUP}-check-in privacy minimum.")

    # ---------------- neighborhoods
    section("Neighborhoods")
    st.caption("Latest four weeks. Whiskers show the 90% range the true average likely falls in.")
    st.plotly_chart(hood_chart(table), use_container_width=True, theme=None, config=CONFIG)
    hidden = table[table["hidden"]]["neighborhood"].tolist()
    if hidden:
        st.caption(f"Hidden (fewer than {scoring.MIN_GROUP} check-ins): {', '.join(hidden)}. "
                   "Showing them could reveal individual answers.")

    # ---------------- stack + needs
    left, right = st.columns(2, gap="medium")
    with left:
        section("Strains stack up")
        st.caption("Share of recent check-ins by how many strains they report at once.")
        stack = scoring.strain_stack(rec)
        labels = [f"{i} strain" + ("" if i == 1 else "s") for i in stack.index]
        st.plotly_chart(bar_chart(labels, stack.values, [DATA_RAMP[min(i + 1, 5)] for i in range(len(stack))]),
                        use_container_width=True, theme=None, config=CONFIG)
    with right:
        section("What would help")
        st.caption("Share of recent check-ins asking for each kind of help.")
        needs = scoring.needs_ranking(rec)
        st.plotly_chart(bar_chart(needs.index.tolist(), needs.values, DATA), use_container_width=True, theme=None, config=CONFIG)

    # ---------------- strains by neighborhood
    section("Strains by neighborhood")
    shown = table[~table["hidden"]][["neighborhood", "n", "mean", *STRESSOR_FLAGS, "two_plus"]].copy()
    pct_cols = [*STRESSOR_FLAGS, "two_plus"]
    shown[pct_cols] = shown[pct_cols] * 100
    st.dataframe(
        shown, hide_index=True, use_container_width=True,
        column_config={
            "neighborhood": "Neighborhood", "n": "Check-ins",
            "mean": st.column_config.NumberColumn("Connection", format="%.0f"),
            **{f: st.column_config.ProgressColumn(STRESSOR_LABELS[f], min_value=0, max_value=100, format="%.0f%%")
               for f in STRESSOR_FLAGS},
            "two_plus": st.column_config.ProgressColumn("2+ strains", min_value=0, max_value=100, format="%.0f%%"),
        },
    )
    st.download_button("Download neighborhood totals (CSV)", shown.round(1).to_csv(index=False).encode(),
                       "recovery_pulse_neighborhoods.csv", "text/csv")
    with st.expander("How the connection score works"):
        st.markdown(f"""
Each check-in is scored with **belonginglab**. Four answers raise the score (neighbor support, sense of belonging,
trust in local help, knowing where to get information) and four strains lower it (housing, money, disrupted school
or work, stress affecting daily life). belonginglab standardizes each answer, applies its weight, adds them up and
ranks every check-in from 0 to 100, so 50 is the middle of all check-ins.

Averages come with a 90% confidence interval. Any neighborhood or week with fewer than {scoring.MIN_GROUP}
check-ins is hidden. The score describes groups, never individuals, and is not a mental health screening.
""")


def style_axes(fig):
    """Dark tick labels and titles on every axis, whatever the viewer's theme."""
    fig.update_xaxes(tickfont_color=MUTED, title_font_color=MUTED, linecolor=GRID, zerolinecolor=GRID, automargin=True)
    fig.update_yaxes(tickfont_color=INK, title_font_color=MUTED, linecolor=GRID, zerolinecolor=GRID, automargin=True)
    return fig


def trend_chart(df, pick):
    fig = go.Figure()
    all_t = scoring.weekly_trend(df)
    fig.add_trace(go.Scatter(x=all_t["week"], y=all_t["mean"], name="Whole community", mode="lines+markers",
                             line=dict(color=GREY, width=2, dash="dash"), marker=dict(size=6),
                             hovertemplate="Week %{x}: %{y:.0f}<extra>Whole community</extra>"))
    if pick:
        t = scoring.weekly_trend(df, pick, window=3)
        fig.add_trace(go.Scatter(x=list(t["week"]) + list(t["week"])[::-1], y=list(t["high"]) + list(t["low"])[::-1],
                                 fill="toself", fillcolor="rgba(108,77,170,0.15)", line=dict(width=0),
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=t["week"], y=t["mean"], name=pick, mode="lines+markers",
                                 line=dict(color=DATA_DARK, width=3), marker=dict(size=7),
                                 hovertemplate="Week %{x}: %{y:.0f}<extra>" + pick + "</extra>"))
    fig.update_layout(**{k: v for k, v in BASE.items() if k != "legend"}, height=380,
                      legend=dict(orientation="h", y=1.1, x=0, font=dict(color=INK, size=13)),
                      xaxis=dict(title="Weeks since the disaster", dtick=1, showgrid=False, tickfont=dict(size=12)),
                      yaxis=dict(range=[0, 100], gridcolor="rgba(0,20,60,0.08)", title="Connection score"))
    return style_axes(fig)


def hood_chart(table):
    shown = table[~table["hidden"]].iloc[::-1]
    colors = [DATA_RAMP[min(5, int((100 - m) // 15))] for m in shown["mean"]]
    fig = go.Figure(go.Bar(
        x=shown["mean"], y=shown["neighborhood"], orientation="h", marker_color=colors,
        error_x=dict(type="data", symmetric=False, array=shown["high"] - shown["mean"],
                     arrayminus=shown["mean"] - shown["low"], color="#1d1d1f", thickness=1.5, width=5),
        text=[f"{m:.0f}" for m in shown["mean"]], textposition="inside", insidetextanchor="start",
        textfont=dict(color="#ffffff", size=13),
        customdata=shown["n"], hovertemplate="%{y}: %{x:.0f} (n=%{customdata})<extra></extra>"))
    fig.update_layout(**BASE, height=60 + 44 * len(shown), bargap=0.4,
                      xaxis=dict(range=[0, 105], gridcolor="rgba(0,20,60,0.08)", title="Connection score"),
                      yaxis=dict(showgrid=False, tickfont=dict(size=13)))
    return style_axes(fig)


def bar_chart(labels, values, color):
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=color,
                           text=[f"{v:.0%}" for v in values], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:.0%}<extra></extra>"))
    fig.update_layout(**BASE, height=60 + 40 * len(labels), bargap=0.35,
                      xaxis=dict(visible=False, range=[0, max(values) * 1.25 if len(values) else 1]),
                      yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=13)))
    return style_axes(fig)
