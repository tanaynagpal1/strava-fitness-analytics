"""Conclusion — what should the business take away from the analysis?"""
import streamlit as st

import report
import ui

ui.page_header("Conclusion", "Six Insights, Each With Its Evidence and a Recommendation",
               "What should the business take away from the analysis?")

insights = report.build_insights()
CONF = {"High": ("#1F9D74", "#E7F6F0"), "Medium": ("#B7791F", "#FFF6E0"), "Low": ("#D9534F", "#FDECEC")}

# ================================================================ scope note + PDF download
left, right = st.columns([3, 1], vertical_alignment="center")
left.html('<div class="note-warn">ℹ️ <b>Based on all 33 users and the full month</b> — the filters above don\'t change '
          'this page, so the conclusions stay the same for everyone who reads them.</div>')
right.download_button("Download PDF report", data=report.make_pdf(insights), icon=":material/download:",
                      file_name="Strava_Insights_and_Recommendations.pdf", mime="application/pdf",
                      type="primary", width="stretch")

# ================================================================ six insight cards, two per row
for row in (insights[0:2], insights[2:4], insights[4:6]):
    cols = st.columns(2)
    for col, ins in zip(cols, row):
        with col, ui.card(f"ins_{ins['n']}"):
            fg, bg = CONF[ins["confidence"]]
            st.html(f'<div class="ins-head"><span class="ins-n">{ins["n"]}</span>'
                    f'<span class="ins-title">{ins["title"]}</span>'
                    f'<span class="ins-conf" style="color:{fg}; background:{bg}; border-color:{fg}">'
                    f'● {ins["confidence"]} confidence</span></div>')
            with st.expander(f"**Evidence** · {ins['evidence']}"):
                facts = "".join(f"<div><span>{k}</span><b>{v}</b></div>" for k, v in ins["facts"])
                spark = ui._sparkline(ins["spark"], ui.ORANGE, w=220, h=60) if ins["spark"] else ""
                st.markdown(f'<div class="ins-ev"><div class="ux-rows">{facts}</div>{spark}</div>', unsafe_allow_html=True)
                st.page_link(ins["page"][0], label=f"See the full page: {ins['page'][1]} →", icon=":material/open_in_new:")
            chain = '<i>→</i>'.join(f"<div><small>{k}</small><b>{v}</b></div>" for k, v in ins["chain"].items())
            st.html(f'<p class="ins-rec-h">Recommendation</p><p class="ins-rec">{ins["rec"]}</p>'
                    f'<div class="ins-chain">{chain}</div>')

# ================================================================ limitations · next steps
cols = st.columns(2)
for col, (key, title, items) in zip(cols, [("limits", "Limitations", report.LIMITATIONS),
                                            ("next", "Next Steps", report.NEXT_STEPS)]):
    with col, ui.card(key):
        ui.card_title(title)
        st.html('<ul class="ins-list">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>")