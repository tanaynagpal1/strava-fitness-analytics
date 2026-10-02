"""Shared building blocks for every page: colours, headers, cards, KPI cards, charts with "Show data", branding."""
import html
from pathlib import Path

import pandas as pd
import streamlit as st

ASSETS = Path(__file__).resolve().parent / "assets"

# ---------------------------------------------------------------- colours (same meaning on every page)
ORANGE = "#FC4C02"
PURPLE = "#7C5CC4"
TEAL = "#1F9D74"
SEGMENT_ORDER = ["Sedentary", "Low active", "Somewhat active", "Active"]
SEGMENT_COLORS = {"Sedentary": "#8DB3E2", "Low active": "#5B8FD6",
                  "Somewhat active": "#2F6BC2", "Active": "#1E4D91"}
TIER_ORDER = ["Barely using", "Irregular", "Consistent"]
TIER_COLORS = {"Barely using": "#F6AE84", "Irregular": "#EF7A3C", "Consistent": "#C2410C"}
PERSONA_ORDER = ["Committed Movers", "On-and-Off Movers", "Daily Strollers",
                 "Slipping Starters", "Fading Users"]
PERSONA_COLORS = dict(zip(PERSONA_ORDER, ["#2a78d6", "#1baf7a", "#eda100", "#eb6834", "#e87ba4"]))
STATUS_COLORS = {"worn": "#2a9d8f", "partial": "#e9c46a", "not_worn": "#e76f51",
                 "last_day": "#a8b5c4", "stopped": "#d9d9d9"}
TRACK = "#EEF0F3"   # light grey "track" behind horizontal bars


# ---------------------------------------------------------------- page-wide pieces
COUNT_UP_JS = """<script>
(function () {
  if (window.__countUp) return;                      // install once per browser tab
  window.__countUp = true;
  const noMotion = () => document.querySelector(".no-motion");

  // KPI numbers count up from 0
  function count(el) {
    if (el.dataset.done === el.dataset.count) return;  // already animated this value
    el.dataset.done = el.dataset.count;
    if (noMotion()) { el.textContent = el.dataset.final; return; }
    const target = parseFloat(el.dataset.count), dec = +el.dataset.dec || 0, suf = el.dataset.suf || "";
    const t0 = performance.now(), dur = 1100;
    function frame(now) {
      const p = Math.min((now - t0) / dur, 1), eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toLocaleString("en-US",
                         {minimumFractionDigits: dec, maximumFractionDigits: dec}) + suf;
      if (p < 1) requestAnimationFrame(frame); else el.textContent = el.dataset.final;
    }
    requestAnimationFrame(frame);
  }

  // charts: measure the line (for the draw effect), then let style.css un-pause the animation
  function startChart(el) {
    el.querySelectorAll(".js-line").forEach(l => l.style.setProperty("--len", l.getTotalLength()));
    el.dataset.inview = "1";
  }

  // play again: restart every animation inside a chart, or count a KPI up from 0 again
  function replay(el) {
    if (noMotion()) return;
    if (el.dataset.count !== undefined) { el.dataset.done = ""; count(el); return; }
    startChart(el);
    el.getAnimations({subtree: true}).forEach(a => { a.cancel(); a.play(); });
  }

  // start each animation when it scrolls into view, and remember what is on screen
  const visible = new Set();
  const seen = new IntersectionObserver(entries => entries.forEach(e => {
    if (!e.isIntersecting) { visible.delete(e.target); return; }
    visible.add(e.target);
    if (e.target.dataset.count !== undefined) count(e.target);
    else if (!e.target.dataset.inview) startChart(e.target);
  }), {threshold: 0.35});

  // every REPLAY_MS, replay whatever is on screen right now
  const REPLAY_MS = 15000;
  setInterval(() => visible.forEach(el => document.contains(el) ? replay(el) : visible.delete(el)), REPLAY_MS);

  const watched = new WeakSet();
  function scan() {
    document.querySelectorAll('[data-count], div[class*="st-key-anim_"]').forEach(el => {
      if (!watched.has(el)) { watched.add(el); seen.observe(el); }
      else if (visible.has(el) && el.dataset.count !== undefined) count(el);   // value changed after a filter
    });
  }
  new MutationObserver(scan).observe(document.body, {childList: true, subtree: true, attributes: true,
                                                     attributeFilter: ["data-count"]});
  scan();
})();
</script>"""

NO_MOTION_CSS = """<style>
*, *::before, *::after { animation: none !important; transition: none !important; }
</style><div class="no-motion"></div>"""


def apply_style(motion=True):
    """Load the stylesheet, the KPI count-up script, and (if motion is off) switch all animations off."""
    st.html(ASSETS / "style.css")
    st.html(COUNT_UP_JS, unsafe_allow_javascript=True)
    if not motion:
        st.html(NO_MOTION_CSS)


def page_header(eyebrow, title, question):
    """Orange eyebrow, page title, and the business question in grey."""
    st.html(f'<p class="eyebrow">{eyebrow}</p><h1 class="page-title">{title}</h1>'
            f'<p class="page-q">Business question: {question}</p>')


def footer():
    st.html('<div class="footer"><span>Student case study (Labmentrix internship) on the public Fitbit tracker '
            'dataset · 33 users · 12 Apr – 12 May 2016</span><span>Not affiliated with or endorsed by Strava</span></div>')


# ---------------------------------------------------------------- cards & text
def card(key):
    """A white rounded card. Use as:  with ui.card("trend"): ..."""
    return st.container(border=True, key=f"card_{key}")


def card_title(title, subtitle=None):
    sub = f'<p class="csub">{subtitle}</p>' if subtitle else ""
    st.html(f'<p class="ctitle">{title}</p>{sub}')


def section(title, takeaway=None):
    """A plain section heading with an optional one-line takeaway under it."""
    st.subheader(title)
    if takeaway:
        st.caption(takeaway)


def fmt_hours(h):
    """7.22 -> '7 h 13 m'."""
    if pd.isna(h):
        return "–"
    total = round(h * 60)
    return f"{total // 60} h {total % 60:02d} m"


# ---------------------------------------------------------------- KPI cards
def kpi(col, label, value, delta=None, help=None):
    """Simple bordered KPI card (Streamlit's built-in metric)."""
    col.metric(label, value, delta=delta, delta_color="off", help=help, border=True)


def _sparkline(values, color=ORANGE, w=64, h=24):
    """Tiny line chart (inline SVG) for a KPI card."""
    vals = [v for v in values if pd.notna(v)]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    pts = " ".join(f"{i * w / (len(vals) - 1):.1f},{h - 3 - (v - lo) / span * (h - 6):.1f}" for i, v in enumerate(vals))
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polyline points="{pts}" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def kpi_card(col, label, value, sub="", delta=None, help=None, accent=ORANGE, spark=None, count=None):
    """Mockup-style KPI card: accent bar, label, big value (+ optional sparkline), sub-line, optional comparison.

    count = (number, decimals, suffix) makes the value count up from 0 when it appears (see COUNT_UP_JS).
    """
    spark_svg = _sparkline(spark, accent) if spark is not None else ""
    delta_html = f'<div class="delta">{delta}</div>' if delta else ""
    counter = ""
    if count is not None and pd.notna(count[0]):
        counter = f' data-count="{count[0]}" data-dec="{count[1]}" data-suf="{count[2]}" data-final="{value}"'
    col.markdown(f'<div class="kcard" style="--accent:{accent}" title="{html.escape(help or "")}">'
                 f'<div class="bar"></div><div class="label">{label}</div>'
                 f'<div class="row"><span class="value"{counter}>{value}</span>{spark_svg}</div>'
                 f'<div class="sub">{sub}</div>{delta_html}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- chart + "Show data"
def chart(fig, data, *, key, height=320, note=None, anim=None):
    """Draw a Plotly chart in the house style, an optional note, and a 'Show data' button with the table.

    anim = how the chart enters (styled in style.css):
      "rise" vertical bars grow up · "grow" horizontal bars grow right · "draw" line draws itself · None = fade in
    """
    fig.update_layout(height=height, margin=dict(t=30, l=10, r=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.12, x=0, title_text=""))
    with st.container(key=f"anim_{anim or 'fade'}_{key}"):
        st.plotly_chart(fig, key=key, config={"displayModeBar": False})
    if note:
        st.caption(note)
    with st.container(horizontal=True, horizontal_alignment="right"):
        with st.popover("Show data", icon=":material/table_view:"):
            st.dataframe(data, hide_index=True)


# ---------------------------------------------------------------- hero banner (Overview)
ROUTE = "M 20 150 C 90 80, 160 60, 230 95 S 360 160, 420 90 S 520 40, 545 70"


def hero_text(typical_steps, n_people, n_days):
    """Left side of the hero: headline, data note, and footsteps toward 10K."""
    on = round(min(typical_steps / 10_000, 1) * 20)
    feet = "".join(f'<span class="{"on" if i < on else ""}" style="animation-delay:{i * 60}ms"></span>'
                   for i in range(20))
    st.markdown(
        '<div class="hero-title">Every metric tells<br>a movement story.</div>'
        f'<p class="hero-text">{n_people} tracker users · 12 Apr – 12 May 2016 · {n_days:,} clean days. '
        'Who moves, when, how they sleep — and which features they actually use.</p>'
        f'<div class="hero-typical">A typical day: {typical_steps:,.0f} steps — '
        f'{typical_steps / 100:.0f}% of the 10K goal</div>'
        f'<div class="steps">{feet}<div class="flag{" met" if typical_steps >= 10_000 else ""}">'
        '<span style="font-size:22px">🏁</span>10K</div></div>',
        unsafe_allow_html=True)


def hero_route(steps_for_speed):
    """Right side of the hero: hills, dotted route and a runner whose speed follows typical steps."""
    speed = max(3.0, 10 - steps_for_speed / 1500)
    st.markdown(
        '<div class="route-box"><svg width="560" height="190" viewBox="0 0 560 190">'
        '<polygon points="0,185 120,70 220,150 330,40 450,140 560,90 560,190 0,190" fill="#FBD5C3" opacity=".55"/>'
        '<polygon points="0,190 90,120 200,175 300,100 420,180 560,130 560,190" fill="#F9C2A8" opacity=".45"/>'
        f'<path class="route" d="{ROUTE}" fill="none" stroke="#FC4C02" stroke-width="4" stroke-linecap="round"/>'
        '</svg>'
        f'<div class="runner" style="offset-path: path(\'{ROUTE}\'); --speed: {speed:.1f}s">🏃</div></div>',
        unsafe_allow_html=True)

    # ---------------------------------------------------------------- shared chart builders
def track_bars(df, label_col, value_col, colors, room=1.18):
    """Horizontal bars drawn over a light grey full-length 'track', with 'n (share)' at the right end.

    df needs: label_col, value_col, "label" (text at the end), "legend", "show_legend", "rank".
    room = space kept on the right for the labels (use ~1.6 in narrow, one-third-width cards).
    """
    import plotly.graph_objects as go
    total = max(df[value_col].max(), 1) * 1.1
    fig = go.Figure()
    fig.add_bar(y=df[label_col], x=[total] * len(df), orientation="h", marker_color=TRACK,
                hoverinfo="skip", showlegend=False, text=df["label"], textposition="outside",
                textfont=dict(size=13, color="#17191D"))
    for _, r in df.iterrows():
        fig.add_bar(y=[r[label_col]], x=[r[value_col]], orientation="h", name=r["legend"],
                    marker_color=colors[r["legend"]], legendgroup=r["legend"],
                    showlegend=r["show_legend"], legendrank=r["rank"],
                    hovertemplate=f"{r[label_col]}: %{{x}}<extra></extra>")
    fig.update_layout(barmode="overlay", bargap=.38)
    fig.update_xaxes(visible=False, range=[0, total * room])
    fig.update_yaxes(categoryorder="array", categoryarray=list(df[label_col])[::-1], title=None)
    return fig


def stacked_share(df, label_col, parts, colors, order):
    """100% stacked horizontal bars: one row per label_col value, one colour per part (columns hold shares 0–1)."""
    import plotly.graph_objects as go
    fig = go.Figure()
    for part in parts:
        fig.add_bar(y=df[label_col], x=df[part] * 100, orientation="h", name=part, marker_color=colors[part],
                    text=[f"{v:.0%}" if v >= .08 else "" for v in df[part]], textposition="inside",
                    insidetextanchor="middle", textfont=dict(size=12, color="#FFFFFF" if part == parts[0] else "#17191D"),
                    hovertemplate="%{y}: %{x:.0f}%<extra>" + part + "</extra>")
    fig.update_layout(barmode="stack", bargap=.35, legend=dict(traceorder="normal"))
    fig.update_xaxes(visible=False, range=[0, 100])
    fig.update_yaxes(categoryorder="array", categoryarray=order[::-1], title=None)
    return fig

# ---------------------------------------------------------------- time formatting
def hour_label(h):
    """18 -> '6 PM' (whole hours)."""
    h = int(h) % 24
    return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


def clock(hours):
    """Hours since midnight (may be >24 or fractional) -> '11:11 PM'."""
    if pd.isna(hours):
        return "–"
    total = round(hours * 60) % (24 * 60)
    h, m = divmod(total, 60)
    return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def to_hours(text):
    """'7:02 AM' -> 7.03 (hours since midnight)."""
    if pd.isna(text):
        return float("nan")
    t, ampm = str(text).split()
    h, m = map(int, t.split(":"))
    return (h % 12 + (12 if ampm == "PM" else 0)) + m / 60

# ---------------------------------------------------------------- time formatting
def hour_label(h):
    """18 -> '6 PM' (whole hours)."""
    h = int(h) % 24
    return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


def clock(hours):
    """Hours since midnight (may be >24 or fractional) -> '11:11 PM'."""
    if pd.isna(hours):
        return "–"
    total = round(hours * 60) % (24 * 60)
    h, m = divmod(total, 60)
    return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def to_hours(text):
    """'7:02 AM' -> 7.03 (hours since midnight)."""
    if pd.isna(text):
        return float("nan")
    t, ampm = str(text).split()
    h, m = map(int, t.split(":"))
    return (h % 12 + (12 if ampm == "PM" else 0)) + m / 60