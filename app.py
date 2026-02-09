"""
Agentic Pipeline — Streamlit UI
Run: streamlit run app.py
"""

import json
import os
import sys

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from agents import (
    run_architect,
    run_deal_estimator,
    run_email_writer,
    run_proposal_writer,
    run_quick_summary,
    run_researcher,
)
from emailer import is_configured as gmail_configured
from emailer import send_outreach_email
from knowledge import (
    CASE_STUDIES,
    MACHINE365_KNOWLEDGE,
    MV900_KNOWLEDGE,
)
from prospector import find_prospects, format_prospect_for_agent

# ── Page Config ──
st.set_page_config(
    page_title="Agentic Pipeline",
    page_icon="AP",
    layout="wide",
)

# ── Custom CSS ──
st.markdown(
    """
<style>
    .agent-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── Header ──
st.title("Agentic Pipeline")
st.caption(
    "AI-powered prospect research, proposal generation & outreach | RAG + Tool-Use | **MV900** + **Machine365.Ai**"
)

# ── Sidebar: Product Info ──
with st.sidebar:
    st.header("Products in Scope")

    with st.expander("MV900 — Process Monitoring Hardware"):
        st.write(MV900_KNOWLEDGE["description"])
        st.write("**Best for:**")
        for item in MV900_KNOWLEDGE["best_for"]:
            st.write(f"- {item}")

    with st.expander("Machine365.Ai — Monitoring Platform"):
        st.write(MACHINE365_KNOWLEDGE["description"])
        st.write("**Best for:**")
        for item in MACHINE365_KNOWLEDGE["best_for"]:
            st.write(f"- {item}")

    with st.expander("Case Studies"):
        for cs in CASE_STUDIES:
            st.write(f"**{cs['title']}**")
            st.write(f"→ {cs['result']}")
            st.write("---")

    st.header("Settings")
    model = st.selectbox(
        "LLM Model", ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"], index=0
    )


# ── Helpers ──


def _parse_deal_json(raw: str) -> dict:
    """Safely parse deal estimator JSON output."""
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "company_name": "Unknown",
            "industry": "Unknown",
            "estimated_machines": 0,
            "first_year_value": 0,
            "annual_recurring": 0,
            "deal_category": "Unknown",
            "confidence": "Low",
            "reasoning": f"Could not parse: {raw[:100]}",
        }


# ── Main Content: Two Tabs ──
EXAMPLES = {
    "Custom input": "",
    "Auto Parts Stamping (Germany)": (
        "Mueller Automotive GmbH, Germany. Mid-size automotive parts manufacturer "
        "specializing in metal stamping for car body panels and structural components. "
        "Operates 3 factories with approximately 150 press machines ranging from 200 to 2000 tons. "
        "Supplies to BMW and Volkswagen. Facing EU carbon reporting regulations and rising energy costs."
    ),
    "Copper Fittings (USA)": (
        "Pacific Brass & Copper, California, USA. Manufacturer of copper pipe fittings "
        "and brass valves for plumbing industry. Single factory with 40+ forging and forming machines. "
        "High energy costs due to California electricity rates. No current smart factory systems."
    ),
    "Electronics Stamping (Vietnam)": (
        "Vina Precision Parts Co., Ltd, Ho Chi Minh City, Vietnam. Precision metal stamping "
        "for consumer electronics — connector pins, shielding cases, battery contacts. "
        "80 high-speed stamping presses. Struggling with defect rates and no centralized monitoring. "
        "Japanese parent company requires detailed production reporting."
    ),
}

tab1, tab2 = st.tabs(["Single Proposal", "Prospect Search"])

# ════════════════════════════════════════════════
# TAB 1: Single Proposal (enhanced existing flow)
# ════════════════════════════════════════════════
with tab1:
    st.header("Target Company")

    selected = st.selectbox(
        "Choose an example or enter custom:", list(EXAMPLES.keys()), key="sp_example"
    )

    if selected == "Custom input":
        company_input = st.text_area(
            "Describe the target company",
            height=150,
            placeholder=(
                "Company name, location, what they manufacture, factory size, "
                "number of machines, known pain points..."
            ),
            key="sp_input_custom",
        )
    else:
        company_input = st.text_area(
            "Edit or use as-is:", value=EXAMPLES[selected], height=150, key="sp_input_example"
        )

    run_btn = st.button("Run Sales Agent Pipeline", type="primary", use_container_width=True)

    if run_btn and company_input.strip():
        company_name = company_input.split(",")[0].split("\n")[0].strip()
        st.session_state["sp_company_name"] = company_name

        # Agent 1: Researcher
        with st.status("Agent 1: Prospect Researcher — analyzing company...", expanded=True) as s:
            research = run_researcher(company_input)
            s.update(label="Agent 1: Research complete", state="complete")
        st.session_state["sp_research"] = research

        # Agent 2: Solution Architect
        with st.status("Agent 2: Solution Architect — mapping solutions...", expanded=True) as s:
            solution_map = run_architect(research)
            s.update(label="Agent 2: Solution mapping complete", state="complete")
        st.session_state["sp_solution_map"] = solution_map

        # Agent 3: Proposal Writer
        with st.status("Agent 3: Proposal Writer — generating proposal...", expanded=True) as s:
            proposal = run_proposal_writer(research, solution_map, company_name)
            s.update(label="Agent 3: Proposal complete", state="complete")
        st.session_state["sp_proposal"] = proposal
        st.session_state["sp_pipeline_complete"] = True

    elif run_btn:
        st.warning("Please enter a company description first.")

    # ── Display results if pipeline has been run ──
    if st.session_state.get("sp_pipeline_complete"):
        research = st.session_state["sp_research"]
        solution_map = st.session_state["sp_solution_map"]
        proposal = st.session_state["sp_proposal"]
        company_name = st.session_state["sp_company_name"]

        st.success("Pipeline complete! Proposal generated below.")

        with st.expander("Research Brief", expanded=False):
            st.markdown(research)
        with st.expander("Solution Mapping", expanded=False):
            st.markdown(solution_map)

        st.header("Generated Proposal")
        st.markdown(proposal)

        col_dl, col_email = st.columns(2)
        with col_dl:
            st.download_button(
                label="Download Proposal (Markdown)",
                data=proposal,
                file_name=f"3view_proposal_{company_name.replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_email:
            email_btn = st.button("Generate Cold Email", use_container_width=True)

        if email_btn:
            with st.status("Estimating deal size...", expanded=True) as s:
                deal_raw = run_deal_estimator(company_input)
                deal = _parse_deal_json(deal_raw)
                s.update(label="Deal estimate complete", state="complete")

            with st.status("Writing cold email...", expanded=True) as s:
                email_text = run_email_writer(research, json.dumps(deal, indent=2))
                s.update(label="Email generated", state="complete")

            st.session_state["sp_email_text"] = email_text

        if st.session_state.get("sp_email_text"):
            st.subheader("Cold Email Preview")
            edited_email = st.text_area(
                "Edit email before sending:",
                value=st.session_state["sp_email_text"],
                height=300,
                key="sp_email_editor",
            )

            recipient = st.text_input("Recipient email address:", key="sp_recipient")

            col_send, col_dl_email = st.columns(2)
            with col_send:
                if st.button("Send Email", use_container_width=True, key="sp_send"):
                    if not recipient or "@" not in recipient:
                        st.error("Please enter a valid email address.")
                    elif not gmail_configured():
                        st.error(
                            "Gmail not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env"
                        )
                    else:
                        result = send_outreach_email(recipient, edited_email)
                        if result["success"]:
                            st.success(f"Email sent to {recipient}!")
                        else:
                            st.error(f"Send failed: {result['error']}")
            with col_dl_email:
                st.download_button(
                    label="Download Email (.txt)",
                    data=edited_email,
                    file_name=f"email_{company_name.replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

    # ── Pipeline Architecture Diagram ──
    with st.expander("How the Pipeline Works"):
        st.markdown("""
        ```
        Company Input (name, industry, size, pain points)
                │
                ▼
        ┌─────────────────────────────┐
        │  Agent 1: Prospect          │
        │  Researcher                 │
        │  → Company profile          │
        │  → Manufacturing analysis   │
        │  → Energy & ESG exposure    │
        └──────────────┬──────────────┘
                       │
                       ▼
        ┌─────────────────────────────┐
        │  Agent 2: Solution          │
        │  Architect                  │
        │  → Pain point mapping       │
        │  → MV900 / Machine365.Ai    │
        │  → ROI estimation           │
        └──────────────┬──────────────┘
                       │
                       ▼
        ┌─────────────────────────────┐
        │  Agent 3: Proposal          │
        │  Writer                     │
        │  → Executive summary        │
        │  → Solution details         │
        │  → Implementation plan      │
        │  → Personalized proposal    │
        └─────────────────────────────┘
                │
                ▼
        Ready-to-Send Proposal (Markdown)
        ```
        """)


# ════════════════════════════════════════════════
# TAB 2: Prospect Search (new flow)
# ════════════════════════════════════════════════
with tab2:
    # ── Phase 1: Search Input ──
    st.header("Find Prospects")
    ps_query = st.text_input(
        "Search for companies (e.g. 'metal stamping companies Germany'):",
        key="ps_query",
    )
    ps_max = st.slider("Max results", min_value=5, max_value=20, value=10, key="ps_max")
    search_btn = st.button("Search", type="primary", use_container_width=True, key="ps_search_btn")

    # ── Phase 2: Search + Quick Qualify ──
    if search_btn and ps_query.strip():
        with st.status("Searching for companies...", expanded=True) as s:
            prospects = find_prospects(ps_query, max_results=ps_max, search_delay=0.5)
            s.update(label=f"Found {len(prospects)} companies", state="complete")

        if not prospects:
            st.warning("No companies found. Try a different search query.")
        else:
            deals = []
            summaries = []
            progress = st.progress(0, text="Qualifying prospects...")

            for i, p in enumerate(prospects):
                brief = format_prospect_for_agent(p)
                raw = run_deal_estimator(brief)
                deal = _parse_deal_json(raw)
                deals.append(deal)

                summary = run_quick_summary(brief, json.dumps(deal, indent=2))
                summaries.append(summary)

                progress.progress(
                    (i + 1) / len(prospects),
                    text=f"Qualified {i + 1}/{len(prospects)}: {p['title'][:40]}",
                )

            progress.empty()

            st.session_state["ps_prospects"] = prospects
            st.session_state["ps_deals"] = deals
            st.session_state["ps_summaries"] = summaries
            st.session_state["ps_search_done"] = True
            # Clear previous batch results when new search runs
            st.session_state.pop("ps_proposals", None)
            st.session_state.pop("ps_batch_done", None)

    # ── Phase 3: Results Table + Selection ──
    if st.session_state.get("ps_search_done"):
        prospects = st.session_state["ps_prospects"]
        deals = st.session_state["ps_deals"]
        summaries = st.session_state["ps_summaries"]

        st.subheader("Prospect Pipeline")

        # Build DataFrame
        rows = []
        for i, (p, d) in enumerate(zip(prospects, deals)):
            email = p["emails"][0] if p["emails"] else "—"
            rows.append(
                {
                    "#": i + 1,
                    "Company": p["title"][:35],
                    "Industry": d.get("industry", "—")[:20],
                    "Email": email,
                    "Est. Deal": f"${d.get('first_year_value', 0):,.0f}",
                    "Category": d.get("deal_category", "—"),
                    "Confidence": d.get("confidence", "—"),
                }
            )

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Expandable quick assessments
        with st.expander("Quick Assessments", expanded=False):
            for i, (p, summary) in enumerate(zip(prospects, summaries)):
                st.markdown(f"**{i + 1}. {p['title'][:40]}**")
                st.write(summary)
                st.write("---")

        # Selection
        options = [f"{i + 1}. {p['title'][:40]}" for i, p in enumerate(prospects)]
        selected_labels = st.multiselect(
            "Select companies for detailed proposals:",
            options,
            key="ps_selection",
        )

        generate_btn = st.button(
            "Generate Detailed Proposals",
            type="primary",
            use_container_width=True,
            disabled=len(selected_labels) == 0,
            key="ps_generate_btn",
        )

        # ── Phase 4: Batch Proposal Generation ──
        if generate_btn and selected_labels:
            selected_indices = [int(label.split(".")[0]) - 1 for label in selected_labels]
            proposal_results = {}

            for idx in selected_indices:
                p = prospects[idx]
                d = deals[idx]
                company_name = p["title"].split(" - ")[0].split(" | ")[0].strip()

                with st.status(
                    f"Generating proposal for {company_name[:30]}...", expanded=True
                ) as s:
                    brief = format_prospect_for_agent(p)

                    s.update(label=f"Researching {company_name[:30]}...")
                    research = run_researcher(brief)

                    s.update(label=f"Mapping solutions for {company_name[:30]}...")
                    solution_map = run_architect(research)

                    s.update(label=f"Writing proposal for {company_name[:30]}...")
                    proposal = run_proposal_writer(research, solution_map, company_name)

                    s.update(label=f"Writing email for {company_name[:30]}...")
                    deal_context = json.dumps(d, indent=2)
                    email_text = run_email_writer(research, deal_context)

                    s.update(label=f"Done: {company_name[:30]}", state="complete")

                proposal_results[idx] = {
                    "company_name": company_name,
                    "research": research,
                    "solution_map": solution_map,
                    "proposal": proposal,
                    "email_text": email_text,
                    "prospect": p,
                    "deal": d,
                }

            st.session_state["ps_proposals"] = proposal_results
            st.session_state["ps_batch_done"] = True

    # ── Phase 5: Display + Actions ──
    if st.session_state.get("ps_batch_done"):
        proposal_results = st.session_state["ps_proposals"]

        st.subheader("Generated Proposals")

        for idx, data in proposal_results.items():
            name = data["company_name"]
            with st.expander(f"{name}", expanded=False):
                ptab1, ptab2, ptab3 = st.tabs(["Proposal", "Email", "Research"])

                with ptab1:
                    st.markdown(data["proposal"])
                    st.download_button(
                        label="Download Proposal",
                        data=data["proposal"],
                        file_name=f"3view_proposal_{name.replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key=f"ps_dl_prop_{idx}",
                    )

                with ptab2:
                    edited = st.text_area(
                        "Edit email:",
                        value=data["email_text"],
                        height=250,
                        key=f"ps_email_edit_{idx}",
                    )
                    p = data["prospect"]
                    default_email = p["emails"][0] if p["emails"] else ""
                    recipient = st.text_input(
                        "Recipient:",
                        value=default_email,
                        key=f"ps_recipient_{idx}",
                    )

                    col_s, col_d = st.columns(2)
                    with col_s:
                        if st.button("Send Email", use_container_width=True, key=f"ps_send_{idx}"):
                            if not recipient or "@" not in recipient:
                                st.error("Please enter a valid email address.")
                            elif not gmail_configured():
                                st.error(
                                    "Gmail not configured. "
                                    "Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env"
                                )
                            else:
                                result = send_outreach_email(recipient, edited)
                                if result["success"]:
                                    st.success(f"Sent to {recipient}!")
                                else:
                                    st.error(f"Failed: {result['error']}")
                    with col_d:
                        st.download_button(
                            label="Download Email",
                            data=edited,
                            file_name=f"email_{name.replace(' ', '_')}.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key=f"ps_dl_email_{idx}",
                        )

                with ptab3:
                    st.markdown("**Research Brief**")
                    st.markdown(data["research"])
                    st.markdown("---")
                    st.markdown("**Solution Map**")
                    st.markdown(data["solution_map"])
