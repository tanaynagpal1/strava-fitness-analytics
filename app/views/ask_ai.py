"""Ask AI — a Gemini chatbot that answers from the project data and from general health & fitness knowledge."""
import streamlit as st

import assistant
import ui

STARTERS = {
    "About our data": ["Who are our most active users?", "Why were some days removed?",
                       "When should we send notifications?", "How were personas built?",
                       "Which people should we go after?", "What are the limitations?"],
    "Health & fitness": ["How many calories does a 30-min run burn?", "Is 10,000 steps a day really needed?",
                         "How much sleep do adults need?", "What is a good resting heart rate?",
                         "Give me a 4-week beginner walking plan"],
}
BOT = str(ui.ASSETS / "strava_icon.png")
USER = ":material/person:"

st.session_state.setdefault("ai_msgs", [])


def ask_later(q):
    """Chip / button click: remember the question, the chat answers it on this run."""
    st.session_state.ai_pending = q


def clear():
    st.session_state.ai_msgs = []


# ================================================================ header
ui.page_header("Ask AI", "Your Questions, Answered — From Our Data and From Fitness Science",
               "Ask anything about the data, the cleaning, the EDA, this dashboard — or health, exercise and calories")
key = assistant.api_key()
left, right = st.columns([2.1, 1])

# ================================================================ chat
with left, ui.card("ai_chat"):
    with st.container(horizontal=True, vertical_alignment="center"):
        st.html('<div class="ai-head"><span class="ai-dot"></span><b>Fitness &amp; Data Assistant</b>'
                '<small>Powered by Gemini · project data + health &amp; fitness knowledge</small></div>')
        st.button("Clear chat", on_click=clear, icon=":material/delete_sweep:", disabled=not st.session_state.ai_msgs)

    box = st.container(height=640, key="ai_box", border=False)
    with box:
        if not key:
            st.warning("**Ask AI needs a free Gemini API key.** Add `GEMINI_API_KEY = \"…\"` to "
                       "`.streamlit/secrets.toml`, then restart the app. The calorie calculator and the glossary "
                       "below work without it.", icon=":material/key:")
        if not st.session_state.ai_msgs:
            with st.chat_message("assistant", avatar=BOT):
                st.markdown("Hi! I'm your **Fitness & Data Assistant**. Ask me about:\n"
                            "- **Our data & dashboard** — users, personas, cleaning, insights, any user ID "
                            "(I check the live numbers for your current filter)\n"
                            "- **Health & fitness** — exercise, steps, sleep, heart rate, calories burned, "
                            "beginner plans\n"
                            "- **Any keyword** — type a term like *MVPA*, *wear rate*, *BMI* or *VO2 max*")
        last = len(st.session_state.ai_msgs) - 1
        for i, m in enumerate(st.session_state.ai_msgs):
            with st.chat_message(m["role"], avatar=BOT if m["role"] == "assistant" else USER):
                if m.get("error"):
                    st.error(m["content"], icon=":material/error:")
                else:
                    st.markdown(m["content"])
                if m.get("tools"):
                    st.html('<div class="ai-used">Checked: ' + " · ".join(f"<code>{t}</code>" for t in m["tools"])
                            + "</div>")
            if i == last and m.get("followups"):
                with st.container(horizontal=True, key="ai_fu"):
                    for j, q in enumerate(m["followups"]):
                        st.button(q, key=f"fu_{j}", on_click=ask_later, args=(q,))

    prompt = st.chat_input("Ask about the data, a user ID, a keyword, exercise or calories…", disabled=not key)
    question = prompt or st.session_state.pop("ai_pending", None)

    if question and key:
        history = [m for m in st.session_state.ai_msgs if not m.get("error")]
        st.session_state.ai_msgs.append({"role": "user", "content": question})
        with box:
            with st.chat_message("user", avatar=USER):
                st.markdown(question)
            with st.chat_message("assistant", avatar=BOT):
                status, out = st.empty(), st.empty()
                status.html('<div class="ai-typing"><i></i><i></i><i></i><span>Thinking …</span></div>')
                used = []

                def on_tool(name):
                    used.append(name)
                    status.html(f'<div class="ai-typing"><i></i><i></i><i></i><span>Looking up <code>{name}</code> …</span></div>')

                text = ""
                try:
                    for piece in assistant.ask(history, question, on_tool):
                        if not text:
                            status.empty()
                        text += piece
                        out.markdown(text.split("<<")[0].rstrip("<") + " ▌")
                    body, follow = assistant.split_followups(text)
                    reply = {"role": "assistant", "content": body or "Sorry, I couldn't find an answer — try rephrasing.",
                             "followups": follow, "tools": used}
                except Exception as e:          # network, key or free-limit problems -> friendly message
                    reply = {"role": "assistant", "content": assistant.explain_error(e), "error": True}
        st.session_state.ai_msgs.append(reply)
        st.rerun()

# ================================================================ side panel
with right:
    with ui.card("ai_start"):
        ui.card_title("Start With a Question", "Click one — the answer appears in the chat")
        for group, qs in STARTERS.items():
            st.html(f'<p class="ai-group">{group}</p>')
            with st.container(horizontal=True, key=f"ai_chips_{group[:5].strip().lower()}"):
                for n, q in enumerate(qs):
                    st.button(q, key=f"st_{group[:3]}_{n}", on_click=ask_later, args=(q,), disabled=not key)

    with ui.card("ai_filter"):
        ui.card_title("Filters in Use")
        st.html(f'<p class="ai-filter">{assistant.filter_text()}</p>'
                '<p class="ai-muted">"This group" in your question means the current filter. '
                "Change the filter bar above and ask again to compare.</p>")

# ================================================================ tools that work without AI
c1, c2 = st.columns(2)
with c1, ui.card("ai_cal"):
    ui.card_title("Calorie Burn Calculator", "MET method (Compendium of Physical Activities) · works without the AI")
    acts = list(assistant.MET)
    a1, a2, a3 = st.columns([2, 1, 1])
    act = a1.selectbox("Activity", acts, index=acts.index("Running, 10 km/h (6:00 min/km)"), key="cal_act")
    mins = a2.number_input("Minutes", 1, 600, 30, step=5, key="cal_min")
    kg = a3.number_input("Weight (kg)", 30, 250, 70, step=1, key="cal_kg")
    burn = assistant.kcal(assistant.MET[act], mins, kg)
    walk = assistant.kcal(assistant.MET["Walking, moderate (5 km/h)"], mins, kg)
    st.html(f'<div class="ai-cal"><div class="big"><b>{burn:,.0f}</b><span>kcal</span></div>'
            f'<p>MET <b>{assistant.MET[act]}</b> × 3.5 × {kg} kg ÷ 200 × {mins} min'
            f'<br>≈ <b>{burn / max(walk, 1):.1f}×</b> a moderate walk of the same length · real burn varies about ±20%</p></div>')

with c2, ui.card("ai_gloss"):
    ui.card_title("Keyword Glossary", f"{len(assistant.GLOSSARY)} terms used on this dashboard · works without the AI")
    term = st.selectbox("Look up a keyword", list(assistant.GLOSSARY), key="gl_term")
    st.html(f'<div class="ai-def"><b>{term}</b><p>{assistant.GLOSSARY[term]}</p></div>')
    st.button(f"Ask AI to explain “{term}” in detail", on_click=ask_later, icon=":material/auto_awesome:",
              args=(f"Explain the keyword '{term}' in detail — what it means on this dashboard and in general.",),
              disabled=not key, key="gl_ask")

# ================================================================ what it knows · guardrails
k1, k2 = st.columns(2)
with k1, ui.card("ai_knows"):
    ui.card_title("What the Assistant Knows")
    st.html('<ul class="ai-list">'
            "<li><b>Project docs</b> — data source, 63 cleaning checks, rules, segments, personas</li>"
            "<li><b>Live numbers</b> — 8 safe data functions (KPIs, segments, personas, any user, hours, "
            "weekdays, sleep, calories)</li>"
            "<li><b>The 6 insights</b> and recommendations from the Conclusion page</li>"
            "<li><b>Health &amp; fitness</b> — WHO / ACSM / sleep guidance, MET calorie science</li>"
            f"<li><b>{len(assistant.GLOSSARY)} dashboard keywords</b> — ask any term</li></ul>")

with k2, ui.card("ai_guard"):
    ui.card_title("Guardrails")
    st.html('<ul class="ai-list">'
            "<li>Never invents numbers — says <i>\"not in our data\"</i> instead</li>"
            "<li>Cites the source of every answer (data, docs or general knowledge)</li>"
            "<li>“Linked with”, not “caused by”</li>"
            "<li>General education, <b>not medical advice</b> — points to a doctor when needed</li>"
            "<li>Your API key stays in <code>secrets.toml</code>, never in GitHub</li></ul>")