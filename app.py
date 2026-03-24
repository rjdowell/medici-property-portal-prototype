import html
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from datetime import date

DEBUG_MODE = False

st.set_page_config(page_title="County Search Portal", page_icon="🔎", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .stApp {margin-top: -80px;}
    </style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1200px;
            padding-top: 1.75rem;
            padding-bottom: 2rem;
        }

        .portal-header {
            text-align: center;
            margin-bottom: 0.28rem;
        }
        .portal-kicker {
            color: #66778d;
            font-size: 0.88rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            margin: 0 0 0.08rem 0;
        }
        .portal-title {
            color: #172739;
            font-size: 2rem;
            font-weight: 700;
            margin: 0 0 0.12rem 0;
            line-height: 1.18;
            letter-spacing: -0.02em;
        }
        .portal-subtitle {
            color: #6f8095;
            font-size: 0.95rem;
            line-height: 1.42;
            margin: 0;
            max-width: 36rem;
            margin-left: auto;
            margin-right: auto;
        }

        /* Tight gap before main workflow content */
        .portal-post-mode-spacer {
            height: 0.12rem;
            margin: 0;
            padding: 0;
        }

        /* Portal mode switcher — st.segmented_control (key portal_workflow_mode): one track, no outer “card” */
        [class*="st-key-portal_workflow_mode"] {
            display: flex !important;
            justify-content: center;
            width: 100%;
            max-width: 940px;
            margin-left: auto !important;
            margin-right: auto !important;
            margin-top: 0.18rem;
            margin-bottom: 0;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        [class*="st-key-portal_workflow_mode"] > div:not([data-testid="stButtonGroup"]) {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        [class*="st-key-portal_workflow_mode"] [data-testid="stButtonGroup"] {
            display: inline-flex !important;
            flex-direction: column;
            align-items: center;
            width: auto !important;
            max-width: 100%;
            margin: 0 auto;
            padding: 0 !important;
            gap: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        /* Single segmented track (inner row only — avoids double chrome with the outer stButtonGroup shell) */
        [class*="st-key-portal_workflow_mode"] [data-testid="stButtonGroup"] > div:last-child {
            display: inline-flex !important;
            align-items: stretch;
            gap: 0 !important;
            padding: 2px !important;
            border-radius: 7px !important;
            border: 1px solid #dfe3ea !important;
            background: #eef1f5 !important;
            box-shadow: none !important;
        }
        [class*="st-key-portal_workflow_mode"] [data-testid="stButtonGroup"] button {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
            color: #5c6678 !important;
            font-weight: 500 !important;
            font-size: 0.78rem !important;
            letter-spacing: 0.01em;
            min-height: 1.65rem !important;
            line-height: 1.2 !important;
            padding: 0.2rem 0.82rem !important;
            border-radius: 5px !important;
            transition: background-color 0.12s ease, color 0.12s ease;
        }
        [class*="st-key-portal_workflow_mode"] [data-testid="stButtonGroup"] button:hover {
            background: rgba(255, 255, 255, 0.55) !important;
            color: #2d3748 !important;
        }
        [class*="st-key-portal_workflow_mode"] [data-testid="stButtonGroup"] button[kind$="Active"],
        [class*="st-key-portal_workflow_mode"] [data-testid="stButtonGroup"] button[aria-pressed="true"] {
            background: #ffffff !important;
            color: #111827 !important;
            font-weight: 600 !important;
            box-shadow: none !important;
        }
        [class*="st-key-portal_workflow_mode"] [data-testid="stButtonGroup"] button:focus-visible {
            outline: 2px solid #b8c9df;
            outline-offset: 1px;
        }

        /*
         * Streamlit / Base Web focus borders use the app theme primary color on the *outer* widget
         * shell (e.g. [data-testid="stTextInputRootElement"]), not only the raw <input>.
         * Default primary is red, so focus reads as an error state. These overrides keep a clear
         * focus signal with a muted blue border and soft outer glow (invalid fields unchanged).
         */
        :root {
            --medici-field-border: #d9e4f2;
            --medici-focus-border: #8fafd6;
            --medici-focus-ring: 0 0 0 3px rgba(76, 118, 178, 0.22);
        }

        [data-testid="stTextInputRootElement"]:focus-within:not(:has([aria-invalid="true"])),
        [data-testid="stTextAreaRootElement"]:focus-within:not(:has([aria-invalid="true"])) {
            border-color: var(--medici-focus-border) !important;
            border-top-color: var(--medici-focus-border) !important;
            border-right-color: var(--medici-focus-border) !important;
            border-bottom-color: var(--medici-focus-border) !important;
            border-left-color: var(--medici-focus-border) !important;
            box-shadow: var(--medici-focus-ring) !important;
        }

        div[data-testid="stNumberInputContainer"].focused {
            border-color: var(--medici-focus-border) !important;
            box-shadow: var(--medici-focus-ring) !important;
        }

        div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within:not(:has([aria-invalid="true"])) {
            border-color: var(--medici-focus-border) !important;
            border-top-color: var(--medici-focus-border) !important;
            border-right-color: var(--medici-focus-border) !important;
            border-bottom-color: var(--medici-focus-border) !important;
            border-left-color: var(--medici-focus-border) !important;
            box-shadow: var(--medici-focus-ring) !important;
        }

        div[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div:first-child,
        div[data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within > div:first-child {
            border-color: var(--medici-focus-border) !important;
            border-top-color: var(--medici-focus-border) !important;
            border-right-color: var(--medici-focus-border) !important;
            border-bottom-color: var(--medici-focus-border) !important;
            border-left-color: var(--medici-focus-border) !important;
            box-shadow: var(--medici-focus-ring) !important;
        }

        /* Never show Streamlit's form text-input helper ("Press Enter to submit form" / char count) — avoids layout shift */
        [data-testid="InputInstructions"] {
            display: none !important;
        }

        /* Title Review intake form — align with centered search field; submit is content-width */
        [class*="st-key-title_review_intake_form"] {
            max-width: 940px;
            margin-left: auto !important;
            margin-right: auto !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            background: transparent !important;
        }
        [class*="st-key-title_review_form_submit"] {
            display: flex;
            justify-content: flex-start;
            margin-top: 0.1rem;
        }
        [class*="st-key-title_review_form_submit"] button[kind="primary"] {
            width: auto !important;
            min-width: 9rem;
            min-height: 2.1rem !important;
            padding: 0.26rem 1.05rem !important;
            font-size: 0.8125rem !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 1px rgba(23, 39, 57, 0.05) !important;
        }
        .title-review-intake-live-hint {
            display: block;
            min-height: 1.4rem;
            margin: 0.28rem auto 0.35rem auto;
            max-width: 940px;
            padding: 0 0.15rem;
            font-size: 0.75rem;
            font-weight: 400;
            color: #8a96a8;
            line-height: 1.4;
            box-sizing: border-box;
        }

        div[data-testid="stTextInput"] > div {
            max-width: 940px;
            margin: 0.38rem auto 0.5rem auto;
        }
        div[data-testid="stTextInput"] input {
            min-height: 3.2rem;
            font-size: 1rem;
            border-radius: 12px;
            border: 1px solid var(--medici-field-border);
            box-shadow: 0 2px 10px rgba(23, 39, 57, 0.06);
            background: #ffffff;
            outline: none;
        }
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextInput"] input:focus-visible {
            border-color: #b8cce8;
            box-shadow: 0 2px 10px rgba(23, 39, 57, 0.06), var(--medici-focus-ring);
        }

        /* Search Records — empty state (no query yet) */
        .search-empty-wrap {
            max-width: 940px;
            margin: 0.95rem auto 0 auto;
            padding: 1.35rem 1.15rem 0.85rem 1.15rem;
            text-align: center;
            background: #fafbfd;
            border: 1px solid #e8edf4;
            border-radius: 12px 12px 0 0;
            border-bottom: none;
            box-sizing: border-box;
        }
        [class*="st-key-search_ex_chip_band"] {
            max-width: 940px;
            margin: 0 auto 0 auto !important;
            padding: 0.35rem 0.85rem 1.15rem 0.85rem !important;
            background: #fafbfd;
            border: 1px solid #e8edf4;
            border-top: none;
            border-radius: 0 0 12px 12px;
            box-sizing: border-box;
        }
        .search-empty-wrap .detail-section-title {
            margin-bottom: 0.35rem;
            font-size: 1.05rem;
        }
        .search-empty-wrap .search-empty-lead {
            font-size: 0.88rem;
            color: #6f8095;
            line-height: 1.5;
            margin: 0 0 0.85rem 0;
        }
        .search-empty-wrap .search-empty-examples-label {
            font-size: 0.72rem;
            font-weight: 600;
            color: #7a8a9c;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin: 0 0 0.55rem 0;
        }

        /* Example chips — Search Records + Title Review (keys search_ex_*, title_ex_*) */
        [class*="st-key-search_ex_"] button,
        [class*="st-key-title_ex_"] button {
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            min-height: 1.85rem !important;
            padding: 0.2rem 0.62rem !important;
            border-radius: 999px !important;
            border: 1px solid #d5dee9 !important;
            background: #ffffff !important;
            color: #4d5f73 !important;
            box-shadow: none !important;
            width: auto !important;
            max-width: 100% !important;
            white-space: normal !important;
            text-align: center !important;
            line-height: 1.28 !important;
        }
        [class*="st-key-search_ex_"] button:hover,
        [class*="st-key-title_ex_"] button:hover {
            border-color: #c5d4e5 !important;
            background: #f5f9ff !important;
            color: #3d4f63 !important;
        }
        .title-review-examples-label {
            font-size: 0.72rem;
            font-weight: 600;
            color: #7a8a9c;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin: 0.75rem 0 0.5rem 0;
            text-align: center;
        }

        /* Mode cue — Search Records exploratory empty state */
        .search-empty-eyebrow {
            font-size: 0.68rem;
            font-weight: 600;
            color: #7d8fa3;
            letter-spacing: 0.065em;
            text-transform: uppercase;
            margin: 0 0 0.4rem 0;
        }
        .search-empty-wrap.mode-explore {
            box-shadow: inset 3px 0 0 #d0e0f7;
        }

        /* Search Records — query form inside explore band */
        [class*="st-key-search_records_explore_band"] div[data-testid="stTextInput"] input {
            border-color: #d2dff0;
        }
        [class*="st-key-search_records_explore_band"] div[data-testid="stTextInput"] input:focus,
        [class*="st-key-search_records_explore_band"] div[data-testid="stTextInput"] input:focus-visible {
            border-color: #a8c0e0;
            box-shadow: 0 2px 10px rgba(23, 39, 57, 0.06), var(--medici-focus-ring);
        }
        [class*="st-key-search_records_query_form"] {
            max-width: 940px;
            margin-left: auto !important;
            margin-right: auto !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            background: transparent !important;
        }
        [class*="st-key-search_records_form_submit"] {
            display: flex;
            justify-content: flex-start;
            margin-top: 0.12rem;
        }
        [class*="st-key-search_records_form_submit"] button[kind="primary"] {
            min-height: 2.4rem !important;
            padding: 0.35rem 1.2rem !important;
            font-size: 0.875rem !important;
            font-weight: 600 !important;
            border-radius: 9px !important;
        }
        div[data-testid="stTextArea"] textarea {
            outline: none;
        }
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stTextArea"] textarea:focus-visible {
            box-shadow: none;
        }

        /* Title Review guided shell (single light card; inner form has no second border) */
        [class*="st-key-title_review_guided_shell"] {
            padding: 0.85rem 1rem 1rem 1rem !important;
            border-radius: 12px !important;
            border-color: #e4ebf4 !important;
            background: #fcfdff !important;
        }
        .title-review-intake-header {
            font-size: 1.05rem;
            font-weight: 600;
            color: #1e2f41;
            margin: 0 0 0.4rem 0;
            text-align: center;
            letter-spacing: -0.015em;
        }
        .title-review-intake-lead {
            font-size: 0.88rem;
            color: #6f8095;
            line-height: 1.45;
            margin: 0 auto 0.55rem auto;
            max-width: 34rem;
            text-align: center;
        }

        .section-title { font-size: 1.02rem; font-weight: 600; color: #1e2f41; margin-bottom: 0.15rem; }
        .section-subtitle { font-size: 0.86rem; color: #76879a; margin-bottom: 0.9rem; }
        .filter-label { font-size: 0.8rem; color: #6f8095; font-weight: 500; margin: 0.1rem 0 0.35rem 0; }

        /* Results list header — count (left) + sort (right), single toolbar row */
        [class*="st-key-results_header_toolbar"] {
            margin-bottom: 0.2rem;
            padding-bottom: 0.48rem;
            border-bottom: 1px solid #edf2f8;
        }
        [class*="st-key-results_header_toolbar"] [data-testid="stHorizontalBlock"] {
            align-items: center !important;
            gap: 0.5rem !important;
        }
        [class*="st-key-results_header_toolbar"] div[data-testid="stSelectbox"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        [class*="st-key-results_header_toolbar"] div[data-testid="stSelectbox"] label {
            min-height: 0 !important;
        }

        .results-header {
            padding-top: 0;
            margin: 0;
            display: flex;
            align-items: center;
            min-height: 2.35rem;
        }
        .results-header .section-title { margin-bottom: 0; }
        .results-count {
            font-size: 0.92rem;
            font-weight: 600;
            color: #4a5c70;
            letter-spacing: 0.01em;
            line-height: 1.25;
        }

        .results-list-leader {
            height: 0.3rem;
            margin: 0;
            padding: 0;
        }

        .result-row {
            background: #fcfdff;
            border-bottom: 1px solid #edf2f8;
            border-radius: 10px;
            padding: 0.38rem 0.52rem 0.28rem 0.52rem;
            margin-bottom: 0.08rem;
            transition: background-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
            min-height: 4.15rem;
            box-sizing: border-box;
            box-shadow: 0 0 0 1px transparent;
        }
        .result-row.selected {
            background: #f3f5f9;
            box-shadow: inset 0 0 0 1px #e8ebf0;
        }
        .result-row:hover {
            background: #f3f7fd;
            box-shadow: 0 0 0 1px #d5e2f2, 0 2px 10px rgba(24, 46, 78, 0.06);
            transform: translateY(-0.5px);
        }
        .result-row.selected:hover {
            background: #eceff3;
            box-shadow: inset 0 0 0 1px #dce1e8, 0 0 0 1px #cdd9e8, 0 2px 10px rgba(24, 46, 78, 0.055);
            transform: translateY(-0.5px);
        }

        /* Full-width invisible hit target over main row (keys: row_click_*) — same action as Open */
        [class*="st-key-row_click_"] {
            margin-top: -4.52rem;
            margin-bottom: 0.08rem;
            position: relative;
            z-index: 2;
        }
        [class*="st-key-row_click_"] button {
            min-height: 4.52rem;
            opacity: 0;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: transparent !important;
            cursor: pointer !important;
        }
        [class*="st-key-row_click_"] button:hover {
            opacity: 0.05;
            background: rgba(24, 46, 78, 0.04) !important;
        }
        /* Row hover when pointer is on overlay (Streamlit button sits above markdown) */
        div[data-testid="column"]:has([class*="st-key-row_click_"] button:hover) .result-row:not(.selected) {
            background: #f3f7fd !important;
            box-shadow: 0 0 0 1px #d5e2f2, 0 2px 10px rgba(24, 46, 78, 0.06) !important;
            transform: translateY(-0.5px) !important;
        }
        div[data-testid="column"]:has([class*="st-key-row_click_"] button:hover) .result-row.selected {
            background: #eceff3 !important;
            box-shadow: inset 0 0 0 1px #dce1e8, 0 0 0 1px #cdd9e8, 0 2px 10px rgba(24, 46, 78, 0.055) !important;
            transform: translateY(-0.5px) !important;
        }

        /* Title Review — parcel-linked instruments: same full-row hit target as search (keys: pr_row_click_*) */
        [class*="st-key-pr_row_click_"] {
            margin-top: -4.52rem;
            margin-bottom: 0.08rem;
            position: relative;
            z-index: 2;
        }
        [class*="st-key-pr_row_click_"] button {
            min-height: 4.52rem;
            opacity: 0;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: transparent !important;
            cursor: pointer !important;
        }
        [class*="st-key-pr_row_click_"] button:hover {
            opacity: 0.05;
            background: rgba(24, 46, 78, 0.04) !important;
        }
        div[data-testid="column"]:has([class*="st-key-pr_row_click_"] button:hover) .result-row {
            background: #f3f7fd !important;
            box-shadow: 0 0 0 1px #d5e2f2, 0 2px 10px rgba(24, 46, 78, 0.06) !important;
            transform: translateY(-0.5px) !important;
        }

        /* Title Review — match picker rows (keys: title_review_row_click_*) */
        [class*="st-key-title_review_row_click_"] {
            margin-top: -4.52rem;
            margin-bottom: 0.08rem;
            position: relative;
            z-index: 2;
        }
        [class*="st-key-title_review_row_click_"] button {
            min-height: 4.52rem;
            opacity: 0;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: transparent !important;
            cursor: pointer !important;
        }
        [class*="st-key-title_review_row_click_"] button:hover {
            opacity: 0.05;
            background: rgba(24, 46, 78, 0.04) !important;
        }
        div[data-testid="column"]:has([class*="st-key-title_review_row_click_"] button:hover) .result-row {
            background: #f3f7fd !important;
            box-shadow: 0 0 0 1px #d5e2f2, 0 2px 10px rgba(24, 46, 78, 0.06) !important;
            transform: translateY(-0.5px) !important;
        }

        div[data-testid="stButton"] button[kind="secondary"] {
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.12rem 0.5rem;
            min-height: 1.55rem;
            line-height: 1.1;
            border-radius: 999px;
            border: 1px solid #dde6f2;
            background: transparent;
            color: #5f6f83;
            box-shadow: none;
            white-space: nowrap;
            width: auto;
        }

        div[data-testid="stButton"] button[kind="secondary"]:hover {
            border-color: #cfdbea;
            background: #f6f9fe;
            color: #4f6177;
        }

        .result-grid {
            display: grid;
            grid-template-columns: 1.35fr 2.1fr 1.05fr;
            gap: 0.75rem;
            align-items: center;
        }

        .doc-type-tag {
            display: inline-block;
            font-size: 0.74rem;
            font-weight: 600;
            line-height: 1.2;
            padding: 0.2rem 0.48rem;
            border-radius: 999px;
            border: 1px solid transparent;
            letter-spacing: 0.01em;
        }
        .doc-type-deed {
            background: #eef4ff;
            color: #2b4f86;
            border-color: #dbe8ff;
        }
        .doc-type-mortgage {
            background: #eefaf4;
            color: #226347;
            border-color: #d7f0e2;
        }
        .doc-type-lien {
            background: #fff5ee;
            color: #8a4b22;
            border-color: #ffe4d2;
        }
        .doc-type-neutral {
            background: #f2f5f9;
            color: #4e6074;
            border-color: #e3eaf2;
        }
        .result-tag-line {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.32rem;
        }
        .result-status-badge {
            display: inline-block;
            font-size: 0.62rem;
            font-weight: 600;
            letter-spacing: 0.055em;
            text-transform: uppercase;
            padding: 0.14rem 0.36rem;
            border-radius: 4px;
            line-height: 1.2;
            border: 1px solid transparent;
            flex-shrink: 0;
        }
        .result-status-badge.is-transfer {
            color: #4d6682;
            background: rgba(238, 244, 255, 0.85);
            border-color: #d8e4f4;
        }
        .result-status-badge.is-active {
            color: #6b5430;
            background: rgba(255, 248, 235, 0.9);
            border-color: #edd9b8;
        }
        .result-status-badge.is-released {
            color: #2f5d47;
            background: rgba(236, 248, 241, 0.9);
            border-color: #c8e8d6;
        }
        .result-status-badge.is-ownership {
            color: #4a5568;
            background: rgba(244, 246, 250, 0.95);
            border-color: #dce2ec;
        }
        .result-status-badge.is-contractor {
            color: #7a4a32;
            background: rgba(255, 245, 238, 0.92);
            border-color: #edd5c4;
        }
        .result-status-badge.is-neutral {
            color: #6b7788;
            background: rgba(248, 250, 252, 0.95);
            border-color: #e2e8f0;
        }
        .date-subtle {
            font-size: 0.74rem;
            font-weight: 500;
            color: #8b96a4;
            line-height: 1.3;
            margin-top: 0.06rem;
        }
        /* Primary scan line: party / title (center column) */
        .party-main {
            font-size: 1.04rem;
            font-weight: 700;
            color: #101c2c;
            line-height: 1.26;
            letter-spacing: -0.015em;
        }
        /* County in results grid — distinct from party line, still scannable */
        .party-main.right-note {
            font-size: 0.88rem;
            font-weight: 600;
            color: #3d4f63;
            letter-spacing: 0;
        }
        .addr-sub {
            font-size: 0.72rem;
            font-weight: 500;
            color: #96a1ae;
            line-height: 1.3;
            margin-top: 0.08rem;
        }
        .right-note { text-align: right; }
        .meta-sub {
            font-size: 0.76rem;
            font-weight: 500;
            color: #8a96a5;
            margin-top: 0.06rem;
            line-height: 1.3;
        }

        .detail-back { margin-bottom: 0.75rem; }
        .detail-hero { margin-bottom: 1.4rem; }
        .detail-hero-eyebrow {
            font-size: 0.68rem;
            font-weight: 600;
            color: #8e9dad;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            margin-bottom: 0.42rem;
        }
        .detail-hero-title {
            font-size: 1.52rem;
            font-weight: 700;
            color: #142434;
            line-height: 1.28;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .detail-hero-docid {
            font-size: 0.8rem;
            font-weight: 500;
            color: #7d8c9d;
            margin-top: 0.45rem;
            letter-spacing: 0.02em;
        }
        .detail-hero-docid-label { color: #9aa8b6; font-weight: 600; margin-right: 0.28rem; }
        .detail-hero-meta {
            font-size: 0.87rem;
            color: #5c6c7e;
            margin-top: 0.58rem;
            line-height: 1.5;
        }
        .detail-hero-meta-type { font-weight: 600; color: #3a4c61; }
        .detail-hero-meta-sep {
            color: #c5ced9;
            margin: 0 0.35rem;
            font-weight: 400;
        }
        .detail-title-status-wrap {
            margin: 0 0 1.05rem 0;
            padding: 0.72rem 0.95rem;
            background: #f9fbfd;
            border: 1px solid #e6ecf4;
            border-radius: 10px;
        }
        .detail-title-status-head {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            flex-wrap: wrap;
            margin-bottom: 0.42rem;
        }
        .detail-title-status-label {
            font-size: 0.66rem;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: #8b99a8;
        }
        .detail-title-status-badge {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            line-height: 1.25;
            border: 1px solid transparent;
        }
        .detail-title-status-badge.is-clear {
            color: #2d6a4f;
            background: #ecf8f2;
            border-color: #c5e6d6;
        }
        .detail-title-status-badge.is-issues {
            color: #8a5b16;
            background: #fdf6e9;
            border-color: #f0dcb8;
        }
        .detail-title-status-badge.is-review {
            color: #3d5a80;
            background: #f0f4fa;
            border-color: #d0dce8;
        }
        .detail-title-status-bullets {
            margin: 0;
            padding-left: 1.05rem;
            font-size: 0.82rem;
            color: #4d5f72;
            line-height: 1.45;
        }
        .detail-title-status-bullets li { margin: 0.12rem 0; }
        .detail-title-status-bullets li::marker { color: #a8b4c2; }
        .detail-title-status-confidence {
            font-size: 0.72rem;
            color: #97a6b6;
            margin: 0.38rem 0 0 0;
            line-height: 1.35;
            font-weight: 400;
        }
        .pr-status-headline {
            font-size: 1.12rem;
            font-weight: 700;
            color: #1e2f41;
            letter-spacing: -0.015em;
            margin: 0.1rem 0 0.32rem 0;
            line-height: 1.28;
        }
        .pr-status-narrative {
            font-size: 0.86rem;
            color: #40556b;
            line-height: 1.48;
            margin: 0 0 0.28rem 0;
        }
        .detail-title-status-filing-count {
            font-size: 0.72rem;
            font-weight: 400;
            color: #8a96a8;
            line-height: 1.35;
            margin: 0 0 0.38rem 0;
        }
        .pr-review-doc-link {
            font-size: 0.78rem;
            font-weight: 600;
            margin: 0.06rem 0 0.28rem 0;
        }
        .pr-review-doc-link a { color: #4d6280; text-decoration: none; }
        .pr-review-doc-link a:hover { text-decoration: underline; }
        /* Title Review — parcel page: hierarchy + spacing (detail screen unchanged) */
        .detail-hero.pr-page-hero {
            margin-bottom: 0.32rem;
            padding-bottom: 0.62rem;
            border-bottom: 1px solid #e6ebf2;
        }
        .detail-hero.pr-page-hero .detail-hero-title {
            font-size: 1.66rem;
            line-height: 1.22;
            letter-spacing: -0.022em;
        }
        .detail-hero.pr-page-hero .detail-hero-eyebrow {
            margin-bottom: 0.32rem;
        }
        .detail-hero.pr-page-hero .detail-hero-docid {
            margin-top: 0.38rem;
        }
        .detail-hero.pr-page-hero .pr-hero-chain-summary {
            margin-top: 0.35rem;
            font-size: 0.84rem;
            font-weight: 500;
            color: #55677d;
            line-height: 1.4;
            letter-spacing: 0.012em;
        }
        .pr-spaced-card {
            margin-bottom: 0.48rem;
        }
        .pr-ownership-compact {
            margin-bottom: 0.48rem !important;
            padding: 0.52rem 0.88rem 0.55rem !important;
            background: #fafcfd;
            border: 1px solid #e8edf4;
            border-radius: 10px;
            box-sizing: border-box;
        }
        .pr-ownership-compact .detail-extracted-heading {
            font-size: 0.98rem;
            margin-bottom: 0.28rem;
        }
        .pr-ownership-compact .detail-extracted-group {
            margin-top: 0.25rem !important;
        }
        .pr-ownership-compact .detail-extracted-row {
            padding: 0.08rem 0;
        }
        .pr-enc-wrap-tight .detail-encumbrance-title {
            margin-bottom: 0.32rem;
        }
        .pr-notes-panel {
            margin-bottom: 0.48rem;
            padding: 0.48rem 0.88rem 0.52rem;
            background: #f9fafc;
            border: 1px solid #e8edf2;
            border-radius: 10px;
            box-sizing: border-box;
        }
        .pr-notes-panel .detail-section-title {
            font-size: 0.94rem;
            margin-bottom: 0.2rem;
        }
        .pr-notes-panel .detail-title-status-bullets {
            font-size: 0.8rem;
            line-height: 1.4;
            margin-top: 0.22rem !important;
        }
        .pr-notes-panel .detail-title-status-bullets li {
            margin: 0.08rem 0;
        }
        .pr-section-divider {
            display: block;
            height: 0;
            margin: 0.48rem 0 0.32rem 0;
            border: none;
            border-top: 1px solid #e8edf4;
        }
        .pr-chain-shell {
            margin-bottom: 0.15rem;
        }
        .pr-chain-shell .detail-timeline-wrap {
            margin-top: 0.08rem;
            margin-bottom: 0.1rem;
            padding-top: 0.52rem;
        }
        .pr-chain-shell .detail-section-title {
            margin-bottom: 0.3rem;
        }
        .pr-instruments-head {
            margin-top: 0.12rem;
        }
        #medici-pr-records {
            height: 0;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        #medici-pr-records ~ .detail-preview-source-caption {
            margin-top: 0.02rem;
            margin-bottom: 0.28rem;
        }
        .pr-posture-card {
            padding: 0.6rem 0.88rem 0.65rem !important;
        }
        .pr-posture-card .pr-status-narrative {
            margin-bottom: 0.4rem;
        }
        .pr-posture-card .detail-title-status-confidence {
            margin-top: 0.32rem;
        }
        .pr-after-hero-gap {
            height: 0.1rem;
            margin: 0;
            padding: 0;
        }
        .detail-encumbrance-wrap {
            margin: 0 0 0.85rem 0;
            padding: 0.55rem 0.85rem;
            background: #fafbfd;
            border: 1px solid #e8edf4;
            border-radius: 9px;
        }
        .detail-encumbrance-title {
            font-size: 0.66rem;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: #8b99a8;
            margin: 0 0 0.4rem 0;
        }
        .detail-encumbrance-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(10.5rem, 1fr));
            gap: 0.28rem 0.75rem;
        }
        .detail-encumbrance-row {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 0.5rem;
            font-size: 0.82rem;
            line-height: 1.35;
            color: #3d4f62;
        }
        .detail-encumbrance-count {
            font-weight: 700;
            font-variant-numeric: tabular-nums;
            color: #1e2f41;
            min-width: 1.1rem;
            text-align: right;
        }
        .detail-encumbrance-label { color: #5a6e82; font-weight: 500; }
        .detail-section-title { font-size: 1rem; font-weight: 600; color: #1e2f41; margin: 0 0 0.5rem 0; }
        /* Extracted Data: dense grid; values are html-escaped in Python */
        .detail-extracted-panel { margin: 0; padding: 0; }
        .detail-extracted-heading {
            font-size: 1rem;
            font-weight: 600;
            color: #1e2f41;
            margin: 0 0 0.35rem 0;
            padding: 0;
            line-height: 1.25;
        }
        .detail-extracted-group {
            margin-top: 0.95rem;
            padding-top: 0.72rem;
            border-top: 1px solid #e8ecf3;
        }
        .detail-extracted-group:first-of-type {
            margin-top: 0.15rem;
            padding-top: 0;
            border-top: none;
        }
        .detail-extracted-group-title {
            font-size: 0.66rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: #97a6b6;
            margin: 0 0 0.32rem 0;
            line-height: 1.2;
        }
        .detail-extracted-row {
            display: grid;
            grid-template-columns: minmax(7.35rem, 33%) minmax(0, 1fr);
            column-gap: 0.34rem;
            align-items: first baseline;
            padding: 0.12rem 0;
            border-bottom: 1px solid #f1f4f8;
        }
        .detail-extracted-group .detail-extracted-row:last-child {
            border-bottom: none;
            padding-bottom: 0.02rem;
        }
        .detail-extracted-label {
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.035em;
            color: #8b99a8;
            line-height: 1.34;
            padding-top: 0.06em;
        }
        .detail-extracted-value {
            font-size: 0.86rem;
            font-weight: 500;
            color: #243548;
            line-height: 1.34;
            min-width: 0;
        }
        .detail-preview-box {
            width: 100%;
            background: linear-gradient(180deg, #f3f7fb 0%, #e9f0f7 100%);
            border: 1px dashed #c0cfe0;
            border-radius: 12px;
            min-height: 240px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.25rem 1rem;
            margin-bottom: 0.35rem;
            box-sizing: border-box;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
        }
        .detail-preview-inner {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            gap: 0.42rem;
            max-width: 16.5rem;
            width: 100%;
            margin: 0 auto;
        }
        .detail-preview-badge {
            display: inline-block;
            font-size: 0.62rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: #4d6280;
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid #c9d6e6;
            padding: 0.22rem 0.5rem;
            border-radius: 999px;
            line-height: 1.2;
        }
        .detail-preview-icon {
            width: 2.5rem;
            height: 2.5rem;
            color: #5a6e8a;
            flex-shrink: 0;
        }
        .detail-preview-icon svg {
            display: block;
            width: 100%;
            height: 100%;
        }
        .detail-preview-label {
            font-size: 0.86rem;
            font-weight: 600;
            color: #2a3a4d;
            letter-spacing: 0.012em;
            line-height: 1.3;
        }
        .detail-preview-sub {
            font-size: 0.76rem;
            color: #566b82;
            line-height: 1.42;
        }
        .detail-preview-docref {
            color: #4d5f75;
            font-weight: 500;
        }
        .detail-preview-note {
            font-size: 0.74rem;
            color: #6d8199;
            margin-top: 0.26rem;
            line-height: 1.35;
            text-align: center;
        }
        .detail-preview-source-caption {
            font-size: 0.74rem;
            font-weight: 600;
            color: #8a9aac;
            letter-spacing: 0.02em;
            line-height: 1.35;
            margin: 0.08rem 0 0.42rem 0;
        }
        .detail-pdf-open-row {
            display: flex;
            justify-content: flex-end;
            width: 100%;
            margin: 0 0 0.35rem 0;
        }
        .detail-open-doc-link {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            border: 1px solid #dde6f2;
            background: transparent;
            color: #5f6f83;
            text-decoration: none;
            line-height: 1.2;
        }
        .detail-open-doc-link:hover {
            border-color: #cfdbea;
            background: #f6f9fe;
            color: #4f6177;
        }
        /* Record detail: st.image preview inside bordered container (matches prior PDF shell) */
        div.st-key-detail_doc_preview[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #d0dce8 !important;
            border-radius: 12px !important;
            background: #f8fafc !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72) !important;
            max-height: 500px;
            overflow-y: auto !important;
            box-sizing: border-box !important;
        }
        .detail-insights-wrap {
            margin-top: 1.35rem;
            padding-top: 1rem;
            border-top: 1px solid #eef2f8;
        }
        .detail-insight-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.32rem 0.4rem;
            margin-top: 0.36rem;
        }
        @media (max-width: 720px) {
            .detail-insight-grid { grid-template-columns: 1fr; }
        }
        .detail-insight-card {
            display: flex;
            align-items: flex-start;
            gap: 0.34rem;
            min-width: 0;
            background: #f8fafc;
            border: 1px solid #e8eef5;
            border-radius: 8px;
            padding: 0.28rem 0.44rem 0.3rem 0.4rem;
            box-shadow: none;
            font-size: 0.84rem;
            color: #33475c;
            line-height: 1.34;
        }
        .detail-insight-marker {
            flex-shrink: 0;
            width: 2px;
            min-height: 1.32rem;
            margin-top: 0.08rem;
            border-radius: 2px;
            background: linear-gradient(180deg, #8fa8cc 0%, #6d87b0 100%);
            opacity: 0.72;
        }
        .detail-insight-text {
            flex: 1;
            min-width: 0;
        }
        .detail-ai-wrap { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #eef2f8; }
        .detail-ai-text { font-size: 0.95rem; color: #33455a; line-height: 1.55; margin-top: 0.35rem; }
        .detail-timeline-wrap { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #eef2f8; }
        .detail-timeline-helper {
            font-size: 0.78rem;
            color: #8a9aac;
            line-height: 1.42;
            margin: 0 0 0.42rem 0;
            font-weight: 400;
        }
        .detail-parcel-history-jump {
            font-size: 0.8rem;
            margin: 0 0 0.38rem 0;
            line-height: 1.35;
        }
        .detail-parcel-history-jump a {
            color: #4d6280;
            text-decoration: none;
            font-weight: 500;
        }
        .detail-parcel-history-jump a:hover {
            color: #3a5270;
            text-decoration: underline;
        }
        #medici-parcel-chain { scroll-margin-top: 3.5rem; }
        .detail-timeline {
            position: relative;
            margin: 0.22rem 0 0 0;
            padding: 0;
        }
        /* Single subtle spine through all events (dots sit on top) */
        .detail-timeline::before {
            content: "";
            position: absolute;
            left: calc(0.475rem - 1px);
            top: 0.38rem;
            bottom: 0.42rem;
            width: 2px;
            background: linear-gradient(180deg, #d8e3ed 0%, #c5d4e2 55%, #d0dce8 100%);
            border-radius: 2px;
            opacity: 0.92;
        }
        .detail-timeline-item {
            display: grid;
            grid-template-columns: 0.95rem 1fr;
            gap: 0.44rem;
            align-items: start;
            padding-bottom: 0.16rem;
        }
        .detail-timeline-item:last-child { padding-bottom: 0.02rem; }
        .detail-timeline-item-current .detail-timeline-body {
            background: linear-gradient(180deg, #fafbfd 0%, #f5f7fb 100%);
            border: 1px solid #e2e9f2;
            border-radius: 8px;
            padding: 0.2rem 0.36rem 0.22rem 0.36rem;
            margin-top: -0.04rem;
            box-shadow: none;
        }
        .detail-timeline-rail {
            position: relative;
            display: flex;
            justify-content: center;
            padding-top: 0.08rem;
        }
        .detail-timeline-item-current .detail-timeline-rail {
            padding-top: 0.14rem;
        }
        .detail-timeline-dot {
            width: 0.44rem;
            height: 0.44rem;
            border-radius: 50%;
            background: #5f7aad;
            border: 2px solid #f6f9fc;
            box-sizing: border-box;
            flex-shrink: 0;
            z-index: 1;
        }
        .detail-timeline-dot-current {
            background: #5c7394;
            border-color: #ffffff;
            box-shadow: 0 0 0 1px rgba(92, 115, 148, 0.14);
        }
        .detail-timeline-date-row {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.38rem;
            margin-bottom: 0.04rem;
            line-height: 1.2;
        }
        .detail-timeline-current-badge {
            font-size: 0.64rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: #3a5370;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid #c5d2e4;
            padding: 0.14rem 0.38rem;
            border-radius: 999px;
            line-height: 1.15;
            box-shadow: 0 1px 1px rgba(30, 50, 80, 0.04);
        }
        .detail-timeline-item-closed .detail-timeline-body {
            background: linear-gradient(180deg, #f5f7fa 0%, #f0f2f6 100%);
            border: 1px solid #e4e8ef;
            border-radius: 8px;
            padding: 0.2rem 0.36rem 0.22rem 0.36rem;
            margin-top: -0.04rem;
        }
        .detail-timeline-item-closed .detail-timeline-rail {
            padding-top: 0.14rem;
        }
        .detail-timeline-dot-closed {
            background: #8e9dad;
            border-color: #ffffff;
            box-shadow: 0 0 0 1px rgba(110, 125, 142, 0.2);
        }
        .detail-timeline-closed-badge {
            font-size: 0.64rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #2a3544;
            background: #ffffff;
            border: 1px solid #9aaaba;
            padding: 0.14rem 0.38rem;
            border-radius: 999px;
            line-height: 1.15;
            box-shadow: 0 1px 2px rgba(30, 45, 65, 0.08);
        }
        .detail-timeline-closed-badge.is-satisfied {
            border-color: #7a9ab8;
            color: #254060;
        }
        .detail-timeline-closed-badge.is-released {
            border-color: #8b96a8;
            color: #333d4d;
        }
        .detail-timeline-date {
            font-size: 0.78rem;
            font-weight: 700;
            color: #1f3245;
            letter-spacing: 0.015em;
            margin-bottom: 0.04rem;
            line-height: 1.2;
        }
        .detail-timeline-date-row .detail-timeline-date {
            margin-bottom: 0;
        }
        .detail-timeline-parties {
            font-size: 0.85rem;
            font-weight: 600;
            color: #1c3044;
            line-height: 1.28;
        }
        .detail-timeline-type {
            font-size: 0.72rem;
            color: #6f8095;
            margin-top: 0.03rem;
            line-height: 1.26;
        }
        .detail-timeline-empty {
            font-size: 0.8rem;
            color: #8b99a8;
            margin: 0.4rem 0 0 0;
            line-height: 1.4;
        }
        .detail-related-wrap { margin-top: 1.35rem; padding-top: 1rem; border-top: 1px solid #eef2f8; }
        .related-result-row {
            background: #fbfcfe;
            border: 1px solid #e8edf5;
            border-radius: 10px;
            padding: 0.18rem 0.52rem 0.16rem 0.52rem;
            margin-bottom: 0.08rem;
            min-height: 2.68rem;
            box-sizing: border-box;
            transition: background-color 0.16s ease;
        }
        .related-result-grid {
            display: grid;
            grid-template-columns: minmax(0, 6.75rem) minmax(0, 1fr);
            gap: 0.42rem 0.58rem;
            align-items: center;
        }
        .related-doc-tag {
            font-size: 0.65rem !important;
            font-weight: 600 !important;
            padding: 0.1rem 0.32rem !important;
            line-height: 1.12 !important;
        }
        .related-result-date {
            font-size: 0.72rem;
            color: #8b97a8;
            margin-top: 0.08rem;
            line-height: 1.26;
        }
        .related-result-party {
            font-size: 0.86rem;
            font-weight: 600;
            color: #1c3044;
            line-height: 1.28;
        }
        .related-result-docnum {
            font-size: 0.7rem;
            color: #9aa6b5;
            margin-top: 0.04rem;
            letter-spacing: 0.01em;
            line-height: 1.22;
        }

        /* Related-record row hit target (keys: rel_click_*) */
        [class*="st-key-rel_click_"] {
            margin-top: -2.92rem;
            margin-bottom: 0.08rem;
            position: relative;
            z-index: 2;
        }
        [class*="st-key-rel_click_"] button {
            min-height: 2.92rem;
            opacity: 0;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: transparent !important;
        }
        [class*="st-key-rel_click_"] button:hover {
            opacity: 0.06;
            background: rgba(24, 46, 78, 0.05) !important;
        }
        div[data-testid="column"]:has([class*="st-key-rel_click_"] button:hover) .related-result-row {
            background: #f4f7fc !important;
            border-color: #dde6f2 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

mock_results = pd.DataFrame(
    [
        {
            "document_number": "2026-001245",
            "document_type": "Warranty Deed",
            "recording_date": "2026-02-14",
            "county": "Cook County",
            "party": "James Carter -> Lila Morris",
            "address_parcel": "1458 River Bend Rd | PIN 08-14-302-011",
            "summary": "Ownership Transfer",
            "grantor": "James Carter",
            "grantee": "Lila Morris",
            "address": "1458 River Bend Rd",
            "parcel_id": "08-14-302-011",
            "amount": "$250,000",
            "ai_summary": (
                "The conveyance uses a warranty deed, which ordinarily signals a conventional sale with seller representations "
                "about title—useful context when the stated consideration aligns with market norms. "
                "The filing fits a typical purchase pattern; any open financing on the same parcel should be read together "
                "with this deed when assessing lien priority."
            ),
            "key_insights": [
                "Warranty covenants mean the grantor warrants good title—materially stronger for buyers than a quitclaim (mock).",
                "Typical resale instrument; insurers usually underwrite around scheduled exceptions, not this deed form (mock).",
                "Same parcel chain often includes financing—map lien priority if multiple encumbrances appear (mock).",
                "Focus diligence on easements, unpaid taxes, and unreleased prior liens rather than deed shape alone (mock).",
            ],
        },
        {
            "document_number": "2026-001132",
            "document_type": "Mortgage",
            "recording_date": "2026-02-10",
            "county": "Cook County",
            "party": "Oak Ridge Lending -> James Carter",
            "address_parcel": "1458 River Bend Rd | PIN 08-14-302-011",
            "summary": "Loan filing",
            "grantor": "Oak Ridge Lending",
            "grantee": "James Carter",
            "address": "1458 River Bend Rd",
            "parcel_id": "08-14-302-011",
            "amount": "$310,000",
            "ai_summary": (
                "This instrument establishes a voluntary lien in favor of the lender and generally takes priority over "
                "later-recorded encumbrances, subject to exceptions (taxes, earlier liens, etc.). "
                "Until satisfied or released, expect it to appear on title commitments and to require payoff documentation "
                "before a clean transfer."
            ),
            "key_insights": [
                "Creates a voluntary lien on the property until satisfied or formally released (mock).",
                "Priority against later liens generally follows recording order—review the full encumbrance stack (mock).",
                "Borrower obligations survive until payoff; expect payoff letters or reconveyance before ‘clear title’ claims (mock).",
                "Title policies typically list open mortgages as exceptions until a release is recorded (mock).",
            ],
        },
        {
            "document_number": "2026-000988",
            "document_type": "Release of Lien",
            "recording_date": "2026-01-29",
            "county": "Cook County",
            "party": "Metro Bank -> Lila Morris",
            "address_parcel": "1458 River Bend Rd | PIN 08-14-302-011",
            "summary": "Lien release",
            "grantor": "Metro Bank",
            "grantee": "Lila Morris",
            "address": "1458 River Bend Rd",
            "parcel_id": "08-14-302-011",
            "amount": None,
            "ai_summary": (
                "The release removes a specific prior claim from the public record, which usually improves clarity for "
                "downstream buyers and insurers. "
                "It does not, by itself, certify that no other liens or mortgages remain—those still warrant a full "
                "parcel review."
            ),
            "key_insights": [
                "Clears the specified encumbrance from the record—usually improves insurability for the next transaction (mock).",
                "Does not prove absence of other liens; still canvass open mortgages, judgments, and tax certificates (mock).",
                "Often follows payoff or settlement—tie to lender satisfaction docs when refinancing the same chain (mock).",
                "Read alongside deeds and mortgages on the parcel; releases rarely stand alone in the story of title (mock).",
            ],
        },
        {
            "document_number": "2025-009874",
            "document_type": "Quitclaim Deed",
            "recording_date": "2025-12-18",
            "county": "DuPage County",
            "party": "Estate of Hill -> M. Turner",
            "address_parcel": "1120 Oak Meadow Ln | PIN 09-22-118-004",
            "summary": "Ownership update",
            "grantor": "Estate of Hill",
            "grantee": "M. Turner",
            "address": "1120 Oak Meadow Ln",
            "parcel_id": "09-22-118-004",
            "amount": None,
            "ai_summary": (
                "A quitclaim here suggests the grantor is conveying whatever interest they held, without warranties—"
                "often seen in estate settlements or related-party transfers. "
                "That raises the bar on chain-of-title review: underwriters may look harder at authority to convey and "
                "at earlier deeds for stronger covenants."
            ),
            "key_insights": [
                "Quitclaim carries no warranty of title—buyer takes whatever interest existed, with higher diligence risk (mock).",
                "Common after estates or family transfers; verify signatory authority, probate orders, and any restrictions (mock).",
                "Underwriters may require curative steps if this deed is central to the insured chain (mock).",
                "Compare against earlier warranty deeds in the chain; older covenants may still matter for older links (mock).",
            ],
        },
        {
            "document_number": "2025-009721",
            "document_type": "Mechanic Lien",
            "recording_date": "2025-12-02",
            "county": "Lake County",
            "party": "Summit Roofing -> C. Patel",
            "address_parcel": "77 Northpoint Dr | PIN 11-03-551-210",
            "summary": "Contractor claim",
            "grantor": "Summit Roofing",
            "grantee": "C. Patel",
            "address": "77 Northpoint Dr",
            "parcel_id": "11-03-551-210",
            "amount": "$18,500",
            "ai_summary": (
                "A mechanic lien functions as a cloud on title: buyers and lenders typically want it released, bonded, or "
                "otherwise addressed before closing. "
                "The recorded amount reflects the claimant’s position, not a final court figure—validity and timing "
                "still depend on local notice and statute rules."
            ),
            "key_insights": [
                "Mechanic liens cloud title—buyers typically demand release, bond, or escrow holdback before closing (mock).",
                "Face amount reflects the claimant’s position, not a court judgment; amounts can be contested (mock).",
                "Notice, licensing, and enforcement windows are state-specific—validate timing against local statute (mock).",
                "If this sits with recent deeds or mortgages, stress-test the whole stack for competing claims (mock).",
            ],
        },
        {
            "document_number": "2026-002050",
            "document_type": "Satisfaction of Mortgage",
            "recording_date": "2026-03-05",
            "county": "Cook County",
            "party": "Oak Ridge Lending -> James Carter",
            "address_parcel": "1458 River Bend Rd | PIN 08-14-302-011",
            "summary": "Mortgage satisfied",
            "grantor": "Oak Ridge Lending",
            "grantee": "James Carter",
            "address": "1458 River Bend Rd",
            "parcel_id": "08-14-302-011",
            "amount": None,
            "ai_summary": (
                "Lender-filed satisfaction indicating the referenced mortgage obligation has been released of record "
                "(mock prototype pairing)."
            ),
            "key_insights": [
                "Removes the mortgage lien from the public index subject to recording accuracy (mock).",
                "Confirm payoff and policy schedules still align with any newer financing (mock).",
            ],
        },
        {
            "document_number": "2026-001610",
            "document_type": "Release of Lien",
            "recording_date": "2026-01-18",
            "county": "Lake County",
            "party": "Summit Roofing -> C. Patel",
            "address_parcel": "77 Northpoint Dr | PIN 11-03-551-210",
            "summary": "Lien released",
            "grantor": "Summit Roofing",
            "grantee": "C. Patel",
            "address": "77 Northpoint Dr",
            "parcel_id": "11-03-551-210",
            "amount": None,
            "ai_summary": (
                "Contractor release of the prior mechanic lien claim, recorded after the original filing (mock prototype)."
            ),
            "key_insights": [
                "Clears the named lien from the chain for diligence purposes if indexed correctly (mock).",
                "Verify no successor claims or bonded substitutes remain (mock).",
            ],
        },
        # --- Additional realistic parcel scenarios (mock) ---
        # Will Co. PIN 10-08-404-033: purchase + open first-lien mortgage (no satisfaction on record).
        {
            "document_number": "2024-044120",
            "document_type": "Warranty Deed",
            "recording_date": "2024-01-28",
            "county": "Will County",
            "party": "Keller Family Trust -> Elena Ruiz",
            "address_parcel": "892 Birch Creek Dr | PIN 10-08-404-033",
            "summary": "Arms-length purchase",
            "grantor": "Keller Family Trust",
            "grantee": "Elena Ruiz",
            "address": "892 Birch Creek Dr",
            "parcel_id": "10-08-404-033",
            "amount": "$312,500",
            "ai_summary": (
                "A warranty deed to an individual buyer on a suburban lot—typical fee-simple acquisition. "
                "Downstream title review should still pair this conveyance with any purchase-money mortgage "
                "recorded shortly after closing."
            ),
            "key_insights": [
                "Warranty deed suggests negotiated sale; confirm consideration and any simultaneous financing (mock).",
                "Later-recorded mortgages generally trail the deed’s transfer of title but prime intervening rights (mock).",
                "Insurers still schedule taxes, easements, and prior unreleased liens unless cleared (mock).",
                "Read the next filings on this PIN for the lien stack (mock).",
            ],
        },
        {
            "document_number": "2024-044201",
            "document_type": "Mortgage",
            "recording_date": "2024-02-05",
            "county": "Will County",
            "party": "First Prairie Bank -> Elena Ruiz",
            "address_parcel": "892 Birch Creek Dr | PIN 10-08-404-033",
            "summary": "Purchase-money loan",
            "grantor": "First Prairie Bank",
            "grantee": "Elena Ruiz",
            "address": "892 Birch Creek Dr",
            "parcel_id": "10-08-404-033",
            "amount": "$250,000",
            "ai_summary": (
                "Recorded purchase-money financing following the deed by one week—common closing sequence. "
                "With no satisfaction or reconveyance in the mock set, expect this lien to remain an open "
                "exception until payoff documentation is obtained."
            ),
            "key_insights": [
                "Creates a voluntary lien on the property until satisfied or formally released (mock).",
                "Priority against later liens generally follows recording order—review the full encumbrance stack (mock).",
                "Borrower obligations survive until payoff; expect payoff letters or reconveyance before ‘clear title’ claims (mock).",
                "Title policies typically list open mortgages as exceptions until a release is recorded (mock).",
            ],
        },
        # Will Co. PIN 10-08-415-021: prior deed (supplement) + mortgage later satisfied.
        {
            "document_number": "2022-018877",
            "document_type": "Mortgage",
            "recording_date": "2022-03-14",
            "county": "Will County",
            "party": "Liberty Home Loans -> David Okonkwo",
            "address_parcel": "1640 Sycamore Station Rd | PIN 10-08-415-021",
            "summary": "Refinance lien",
            "grantor": "Liberty Home Loans",
            "grantee": "David Okonkwo",
            "address": "1640 Sycamore Station Rd",
            "parcel_id": "10-08-415-021",
            "amount": "$268,000",
            "ai_summary": (
                "Refinance-style mortgage in favor of a national correspondent lender. "
                "A later-recorded satisfaction in the mock data pairs to this lien for a complete payoff story."
            ),
            "key_insights": [
                "Creates a voluntary lien on the property until satisfied or formally released (mock).",
                "Priority against later liens generally follows recording order—review the full encumbrance stack (mock).",
                "Borrower obligations survive until payoff; expect payoff letters or reconveyance before ‘clear title’ claims (mock).",
                "Title policies typically list open mortgages as exceptions until a release is recorded (mock).",
            ],
        },
        {
            "document_number": "2025-092200",
            "document_type": "Satisfaction of Mortgage",
            "recording_date": "2025-11-30",
            "county": "Will County",
            "party": "Liberty Home Loans -> David Okonkwo",
            "address_parcel": "1640 Sycamore Station Rd | PIN 10-08-415-021",
            "summary": "Mortgage satisfied",
            "grantor": "Liberty Home Loans",
            "grantee": "David Okonkwo",
            "address": "1640 Sycamore Station Rd",
            "parcel_id": "10-08-415-021",
            "amount": None,
            "ai_summary": (
                "Lender-filed satisfaction referencing the prior Liberty Home Loans mortgage on this parcel. "
                "For underwriting, confirm no replacement financing was recorded the same day that could leave "
                "a new open lien."
            ),
            "key_insights": [
                "Removes the mortgage lien from the public index subject to recording accuracy (mock).",
                "Confirm payoff and policy schedules still align with any newer financing (mock).",
            ],
        },
        # Cook Co. PIN 07-22-190-045: four ownership transfers over time (two deeds here; two in supplement).
        {
            "document_number": "2018-220011",
            "document_type": "Warranty Deed",
            "recording_date": "2018-09-04",
            "county": "Cook County",
            "party": "R. Vargas -> K. Brennan",
            "address_parcel": "445 W Armitage Ave Unit 3B | PIN 07-22-190-045",
            "summary": "Condo resale",
            "grantor": "R. Vargas",
            "grantee": "K. Brennan",
            "address": "445 W Armitage Ave Unit 3B",
            "parcel_id": "07-22-190-045",
            "amount": "$415,000",
            "ai_summary": (
                "Warranty deed conveying a condominium unit—starts a multi-step ownership chain in the mock data. "
                "Later quitclaim and warranty deeds show entity and investor transfers typical of small portfolios."
            ),
            "key_insights": [
                "Warranty covenants mean the grantor warrants good title—materially stronger for buyers than a quitclaim (mock).",
                "Typical resale instrument; insurers usually underwrite around scheduled exceptions, not this deed form (mock).",
                "Same parcel chain often includes financing—map lien priority if multiple encumbrances appear (mock).",
                "Focus diligence on easements, unpaid taxes, and unreleased prior liens rather than deed shape alone (mock).",
            ],
        },
        {
            "document_number": "2020-088340",
            "document_type": "Quitclaim Deed",
            "recording_date": "2020-02-11",
            "county": "Cook County",
            "party": "K. Brennan -> 445 Armitage Holdings LLC",
            "address_parcel": "445 W Armitage Ave Unit 3B | PIN 07-22-190-045",
            "summary": "Entity drop",
            "grantor": "K. Brennan",
            "grantee": "445 Armitage Holdings LLC",
            "address": "445 W Armitage Ave Unit 3B",
            "parcel_id": "07-22-190-045",
            "amount": None,
            "ai_summary": (
                "Quitclaim into a single-asset LLC—often done for estate planning or holding structure without "
                "a traditional arm’s-length sale. Chain-of-title review should confirm LLC authority and "
                "any operating-agreement restrictions."
            ),
            "key_insights": [
                "Quitclaim carries no warranty of title—buyer takes whatever interest existed, with higher diligence risk (mock).",
                "Common after estates or family transfers; verify signatory authority, probate orders, and any restrictions (mock).",
                "Underwriters may require curative steps if this deed is central to the insured chain (mock).",
                "Compare against earlier warranty deeds in the chain; older covenants may still matter for older links (mock).",
            ],
        },
        # Lake Co. PIN 11-05-112-077: open contractor lien (no release in mock data).
        {
            "document_number": "2024-060011",
            "document_type": "Mechanic Lien",
            "recording_date": "2024-08-19",
            "county": "Lake County",
            "party": "Apex Electric LLC -> Jordan Reeves",
            "address_parcel": "18 Harbor View Ct | PIN 11-05-112-077",
            "summary": "Contractor claim",
            "grantor": "Apex Electric LLC",
            "grantee": "Jordan Reeves",
            "address": "18 Harbor View Ct",
            "parcel_id": "11-05-112-077",
            "amount": "$9,200",
            "ai_summary": (
                "Electrical contractor lien following a residential remodel—still open in the mock dataset with "
                "no recorded release. Buyers and lenders would typically require payoff, bonding, or a title "
                "holdback before closing."
            ),
            "key_insights": [
                "Mechanic liens cloud title—buyers typically demand release, bond, or escrow holdback before closing (mock).",
                "Face amount reflects the claimant’s position, not a court judgment; amounts can be contested (mock).",
                "Notice, licensing, and enforcement windows are state-specific—validate timing against local statute (mock).",
                "If this sits with recent deeds or mortgages, stress-test the whole stack for competing claims (mock).",
            ],
        },
    ]
)
mock_results["recording_date_dt"] = pd.to_datetime(mock_results["recording_date"]).dt.date


def search_records_text_matches(df: pd.DataFrame, query_text: str) -> pd.DataFrame:
    """
    Text-only Search Records match (same combined fields as the main search bar).
    `query_text` must be lowercased (e.g. from query_stripped.lower()); returns newest-first.
    """
    qt = (query_text or "").strip().lower()
    if not qt:
        return df.iloc[0:0].copy()
    out = df.copy()
    if "dupage" in qt:
        return out[
            out["county"].str.lower().str.contains("dupage", na=False, regex=False)
        ].sort_values("recording_date_dt", ascending=False)
    amt = out["amount"].fillna("").astype(str)
    combined = (
        out["document_number"].str.lower()
        + " "
        + out["document_type"].str.lower()
        + " "
        + out["county"].str.lower()
        + " "
        + out["party"].str.lower()
        + " "
        + out["address_parcel"].str.lower()
        + " "
        + out["summary"].str.lower()
        + " "
        + out["grantor"].str.lower()
        + " "
        + out["grantee"].str.lower()
        + " "
        + out["address"].str.lower()
        + " "
        + out["parcel_id"].str.lower()
        + " "
        + amt.str.lower()
    )
    return out[combined.str.contains(qt, na=False, regex=False)].sort_values(
        "recording_date_dt", ascending=False
    )


# Prior deed-only events for ownership timeline (same parcels as mock_results; not duplicate document_numbers).
OWNERSHIP_TIMELINE_SUPPLEMENT: dict[str, list[dict]] = {
    "08-14-302-011": [
        {
            "document_number": "2019-004102",
            "document_type": "Warranty Deed",
            "recording_date": "2019-04-12",
            "grantor": "Riverbend Holdings LLC",
            "grantee": "James Carter",
        },
        {
            "document_number": "2014-116600",
            "document_type": "Quitclaim Deed",
            "recording_date": "2014-11-08",
            "grantor": "M. Nguyen",
            "grantee": "Riverbend Holdings LLC",
        },
    ],
    "09-22-118-004": [
        {
            "document_number": "2001-008812",
            "document_type": "Warranty Deed",
            "recording_date": "2001-03-22",
            "grantor": "Oak Meadow Investors LP",
            "grantee": "R. Hill",
        },
    ],
    "11-03-551-210": [
        {
            "document_number": "2020-002901",
            "document_type": "Warranty Deed",
            "recording_date": "2020-01-14",
            "grantor": "Northpoint Dev LLC",
            "grantee": "C. Patel",
        },
        {
            "document_number": "2015-031044",
            "document_type": "Quitclaim Deed",
            "recording_date": "2015-08-30",
            "grantor": "County Land Trust",
            "grantee": "Northpoint Dev LLC",
        },
    ],
    # Will Co.: deed into owner before refinance mortgage + satisfaction (mock).
    "10-08-415-021": [
        {
            "document_number": "2021-005544",
            "document_type": "Warranty Deed",
            "recording_date": "2021-05-10",
            "grantor": "Sycamore Builders Inc",
            "grantee": "David Okonkwo",
        },
    ],
    # Cook Co.: completes four-deed chain (entity transfer + resale) with main-table 2018 WD + 2020 QCD (mock).
    "07-22-190-045": [
        {
            "document_number": "2022-031100",
            "document_type": "Warranty Deed",
            "recording_date": "2022-06-22",
            "grantor": "445 Armitage Holdings LLC",
            "grantee": "Maria Santos",
        },
        {
            "document_number": "2025-014422",
            "document_type": "Warranty Deed",
            "recording_date": "2025-03-07",
            "grantor": "Maria Santos",
            "grantee": "Linh Nguyen",
        },
    ],
    # Lake Co.: fee acquisition predating open mechanic lien (mock).
    "11-05-112-077": [
        {
            "document_number": "2019-077300",
            "document_type": "Warranty Deed",
            "recording_date": "2019-10-02",
            "grantor": "Harbor View Dev LLC",
            "grantee": "Jordan Reeves",
        },
    ],
}


def chain_of_title_events(parcel_id: str, df: pd.DataFrame, current_doc: str) -> list[dict]:
    """
    Full parcel chain: every instrument in mock data for the PIN (deeds, mortgages, liens, releases, etc.),
    plus supplemental historical deeds, newest first. Ensures encumbrances and satisfactions appear so status
    badges can attach to the original mortgage/lien rows.
    """
    pid = str(parcel_id or "").strip()
    if not pid:
        return []
    events: list[dict] = []
    sub = df.loc[df["parcel_id"].astype(str) == pid]
    for _, row in sub.iterrows():
        events.append(
            {
                "document_number": row["document_number"],
                "recording_date": row["recording_date"],
                "recording_date_dt": row["recording_date_dt"],
                "grantor": row.get("grantor", "") or "",
                "grantee": row.get("grantee", "") or "",
                "document_type": row["document_type"],
            }
        )
    for extra in OWNERSHIP_TIMELINE_SUPPLEMENT.get(pid, []):
        try:
            dt = date.fromisoformat(str(extra["recording_date"])[:10])
        except ValueError:
            continue
        num = str(extra.get("document_number", ""))
        if not num or any(str(e.get("document_number", "")) == num for e in events):
            continue
        events.append({**extra, "recording_date_dt": dt})
    seen: set[str] = set()
    out: list[dict] = []
    for e in sorted(events, key=lambda x: x["recording_date_dt"], reverse=True):
        n = str(e.get("document_number", ""))
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(e)
    cur = str(current_doc or "").strip()
    listed = {str(x.get("document_number", "")) for x in out}
    if cur and cur not in listed:
        match = df.loc[df["document_number"].astype(str) == cur]
        if not match.empty:
            row = match.iloc[0]
            if str(row.get("parcel_id", "") or "") == pid:
                out.append(
                    {
                        "document_number": row["document_number"],
                        "recording_date": row["recording_date"],
                        "recording_date_dt": row["recording_date_dt"],
                        "grantor": row.get("grantor", "") or "",
                        "grantee": row.get("grantee", "") or "",
                        "document_type": row["document_type"],
                    }
                )
                out.sort(key=lambda x: x["recording_date_dt"], reverse=True)
    return out


def is_active_encumbrance_record(document_type: str) -> bool:
    """True for mortgages and liens that typically remain active on the record; not deeds or satisfaction/release filings."""
    dt = str(document_type or "").lower()
    if "deed" in dt:
        return False
    if "satisfaction" in dt or "reconveyance" in dt or "discharge" in dt:
        return False
    if "release" in dt:
        return False
    if "mortgage" in dt:
        return True
    if "lien" in dt:
        return True
    return False


_CLOSING_INSTRUMENT_RE = re.compile(
    r"release|satisfaction|reconveyance|discharge",
    re.IGNORECASE,
)


def is_release_or_satisfaction_filing(document_type: str) -> bool:
    """Recorded instrument that can close a prior mortgage or lien."""
    return bool(_CLOSING_INSTRUMENT_RE.search(str(document_type or "")))


def encumbrance_closure_badge_from_release(release_document_type: str) -> str:
    """Label shown on the *original* encumbrance row, based on the type of closing instrument."""
    rt = str(release_document_type or "").lower()
    if "satisfaction" in rt or "reconveyance" in rt:
        return "Satisfied"
    if "discharge" in rt:
        return "Satisfied"
    return "Released"


def parcel_encumbrance_closure_map(parcel_id: str, df: pd.DataFrame) -> dict[str, str]:
    """
    Map encumbrance document_number -> 'Satisfied' or 'Released' when a later closing instrument on the same
    parcel pairs to it. Walks chronologically; each closing doc pairs to one open encumbrance — prefer
    same grantor+grantee, else same grantor, else nearest prior encumbrance.
    """
    pid = str(parcel_id or "").strip()
    if not pid:
        return {}
    sub = df.loc[df["parcel_id"].astype(str) == pid].sort_values("recording_date_dt", ascending=True)
    open_enc: list[dict] = []
    out: dict[str, str] = {}
    for _, row in sub.iterrows():
        dtype = str(row.get("document_type", "") or "")
        if is_active_encumbrance_record(dtype):
            open_enc.append(
                {
                    "document_number": str(row["document_number"]),
                    "recording_date_dt": row["recording_date_dt"],
                    "grantor": str(row.get("grantor", "") or "").strip(),
                    "grantee": str(row.get("grantee", "") or "").strip(),
                }
            )
        elif is_release_or_satisfaction_filing(dtype):
            r_dt = row["recording_date_dt"]
            r_g = str(row.get("grantor", "") or "").strip()
            r_e = str(row.get("grantee", "") or "").strip()
            prior = [e for e in open_enc if e["recording_date_dt"] < r_dt]
            if not prior:
                continue
            same_ge = [e for e in prior if r_g and r_e and e["grantor"] == r_g and e["grantee"] == r_e]
            same_g = [e for e in prior if r_g and e["grantor"] == r_g]
            pool = same_ge if same_ge else (same_g if same_g else prior)
            chosen = max(pool, key=lambda x: x["recording_date_dt"])
            out[str(chosen["document_number"])] = encumbrance_closure_badge_from_release(dtype)
            cnum = chosen["document_number"]
            open_enc = [e for e in open_enc if e["document_number"] != cnum]
    return out


county_options = ["All counties", "Cook County", "DuPage County", "Lake County", "Will County"]
doc_type_options = [
    "Warranty Deed",
    "Quitclaim Deed",
    "Mortgage",
    "Satisfaction of Mortgage",
    "Release of Lien",
    "Mechanic Lien",
]


def record_for_state(row) -> dict:
    """Serializable record for session state (no internal dataframe columns)."""
    d = row.to_dict() if hasattr(row, "to_dict") else dict(row)
    d.pop("recording_date_dt", None)
    return d


if "selected_doc_number" not in st.session_state:
    st.session_state.selected_doc_number = mock_results.iloc[0]["document_number"]
if "selected_record" not in st.session_state:
    st.session_state.selected_record = record_for_state(mock_results.iloc[0])
if "active_screen" not in st.session_state:
    st.session_state.active_screen = "search"
if "detail_return_screen" not in st.session_state:
    st.session_state.detail_return_screen = "search"
if "search_committed" not in st.session_state:
    _sq_leg = str(st.session_state.get("search_query") or "").strip()
    st.session_state.search_committed = _sq_leg
    if _sq_leg:
        st.session_state.search_query_draft = _sq_leg


def result_scan_status_badge(row, df: pd.DataFrame) -> tuple[str, str]:
    """Short scan label and CSS modifier for search result rows (mock, parcel-aware for closures)."""
    dtype = str(row.get("document_type") or "")
    dt = dtype.lower()
    pid = str(row.get("parcel_id") or "").strip()
    docn = str(row.get("document_number") or "").strip()
    if pid and docn and is_active_encumbrance_record(dtype):
        if docn in parcel_encumbrance_closure_map(pid, df):
            return "Released", "is-released"
    if "mechanic" in dt:
        return "Contractor claim", "is-contractor"
    if is_release_or_satisfaction_filing(dtype):
        return "Released", "is-released"
    if is_active_encumbrance_record(dtype):
        return "Active", "is-active"
    if "quitclaim" in dt:
        return "Ownership update", "is-ownership"
    if "deed" in dt:
        return "Ownership Transfer", "is-transfer"
    return "Recorded", "is-neutral"


def doc_type_tag_class(doc_type: str) -> str:
    dt = doc_type.lower()
    if "deed" in dt:
        return "doc-type-tag doc-type-deed"
    if "mortgage" in dt:
        return "doc-type-tag doc-type-mortgage"
    if "lien" in dt:
        return "doc-type-tag doc-type-lien"
    return "doc-type-tag doc-type-neutral"


def recording_date_compact(raw) -> str:
    if raw in (None, ""):
        return "—"
    try:
        d = date.fromisoformat(str(raw)[:10])
        return f"{d.strftime('%b')} {d.day}, {d.year}"
    except ValueError:
        return str(raw)


def related_party_headline(row) -> str:
    g = str(row.get("grantor", "") or "").strip()
    e = str(row.get("grantee", "") or "").strip()
    if g and e:
        return f"{g} → {e}"
    p = str(row.get("party", "") or "").strip()
    if p:
        return p.replace(" -> ", " → ").replace("->", "→")
    return "—"


def open_detail_view(
    row_data: dict,
    *,
    detail_nav_source: str | None = None,
) -> None:
    """
    Open document detail. detail_nav_source:
      - \"search\" (default): back action returns to search results.
      - \"property_review\": back action returns to parcel title review; parcel id kept in session.
      - \"inherit\": keep prior detail_return_screen (e.g. related-record drill-down from title review).
    """
    st.session_state["selected_doc_number"] = row_data["document_number"]
    st.session_state["selected_record"] = dict(row_data)
    st.session_state.active_screen = "detail"
    src = detail_nav_source or "search"
    if src == "property_review":
        st.session_state.detail_return_screen = "property_review"
        pid = str(row_data.get("parcel_id") or "").strip()
        if pid:
            st.session_state.title_review_parcel_id = pid
    elif src == "inherit":
        pass
    else:
        st.session_state.detail_return_screen = "search"
    st.rerun()


def open_property_review(parcel_id: str) -> None:
    st.session_state.title_review_parcel_id = str(parcel_id).strip()
    st.session_state.active_screen = "property_review"
    st.session_state.title_review_last_failed_query = None
    st.session_state.pop("title_review_ambiguous", None)
    st.session_state.pop("title_review_match_candidates", None)
    st.rerun()


def get_related_records(document_number: str, parcel_id: str, df: pd.DataFrame, limit: int = 3) -> pd.DataFrame:
    """Other filings on the same parcel only (exact parcel_id match); excludes current document_number."""
    pid = str(parcel_id or "").strip()
    cur = str(document_number or "").strip()
    if not pid:
        return df.iloc[0:0].copy()
    pcol = df["parcel_id"].astype(str).str.strip()
    dcol = df["document_number"].astype(str).str.strip()
    sub = df.loc[(pcol == pid) & (dcol != cur)].copy()
    sub = sub.sort_values("recording_date_dt", ascending=False)
    sub = sub.drop_duplicates(subset=["document_number"], keep="first")
    return sub.head(limit)


def _derive_key_insights(sel: dict) -> list[str]:
    """Fallback interpretive bullets when `key_insights` is missing (avoid restating raw extracted fields)."""
    dt = str(sel.get("document_type") or "").lower()
    out: list[str] = []
    if "mortgage" in dt:
        out.append("Creates a voluntary lien until payoff or release; priority vs later filings usually follows recording order (mock).")
        out.append("Expect payoff or subordination evidence before claiming unencumbered title for resale or refinance (mock).")
    elif "release" in dt and "lien" in dt:
        out.append("Removes a named encumbrance from the chain; improves marketability but is not a blanket ‘all clear’ (mock).")
        out.append("Still review unrelated mortgages, judgments, and tax liens on the same parcel history (mock).")
    elif "quitclaim" in dt:
        out.append("No warranty of title—higher risk than warranty deeds; common in estates and informal transfers (mock).")
        out.append("Validate grantor authority and read older deeds in the chain for stronger covenants (mock).")
    elif "mechanic" in dt or ("lien" in dt and "release" not in dt):
        out.append("Liens cloud title; closings usually require release, bond, or negotiated holdback (mock).")
        out.append("Stated amounts are claims, not final judgments—timing and validity are jurisdiction-specific (mock).")
    elif "warranty" in dt:
        out.append("Grantor warrants good title—buyer-facing protections exceed a quitclaim (mock).")
        out.append("Underwriting focus shifts to scheduled exceptions, easements, and unreleased prior liens (mock).")
    elif "deed" in dt:
        out.append("Conveys ownership subject to the deed’s covenants; interpret form against your underwriting standard (mock).")
        out.append("Correlate with mortgages and releases on the parcel for a coherent lien story (mock).")
    else:
        out.append("Recorded instrument may affect title or parties—read it in context with the rest of the chain (mock).")
    if len(out) < 3:
        out.append("Scan the parcel history for paired patterns: deed + mortgage, lien + later release (mock).")
    if len(out) < 4:
        out.append("Do not rely on a single instrument—cross-check index data and prior policies where available (mock).")
    return out[:4]


def key_insights_for_record(sel: dict) -> list[str]:
    raw = sel.get("key_insights")
    if raw is None:
        return _derive_key_insights(sel)
    if hasattr(raw, "tolist"):
        raw = raw.tolist()
    if not isinstance(raw, (list, tuple)):
        return _derive_key_insights(sel)
    texts = [str(s).strip() for s in raw if s is not None and str(s).strip()]
    if not texts:
        return _derive_key_insights(sel)
    return texts[:4]


def ai_summary_title_workflow_sentence(sel: dict) -> str:
    """One concise title-workflow interpretation from record type (mock)."""
    dtype = str(sel.get("document_type") or "")
    dt = dtype.lower()
    if not dt.strip():
        return ""
    if "quitclaim" in dt:
        return (
            "This deed may require additional diligence because quitclaim transfers do not "
            "provide warranty of title."
        )
    if "warranty" in dt and "deed" in dt:
        return (
            "This is typically a buyer-favorable conveyance; underwriting still focuses on "
            "scheduled exceptions and any unreleased liens in the chain."
        )
    if is_release_or_satisfaction_filing(dtype):
        return "This improves insurability by clearing a prior encumbrance."
    if is_active_encumbrance_record(dtype):
        return "This would likely remain an open exception until satisfied or released."
    if "deed" in dt:
        return (
            "Compare this conveyance to the rest of the parcel index to confirm continuity "
            "and lien posture for closing."
        )
    return "Read this filing with the rest of the parcel index to judge its effect on insurable title."


def title_status_for_record(sel: dict, related_df: pd.DataFrame, full_df: pd.DataFrame) -> tuple[str, str, list[str]]:
    """
    Mock title posture for the detail view: (display label, badge class suffix, 2–4 bullets).
    Uses current instrument type, parcel-level index, encumbrance closure map, and related rows.
    """
    parcel_id = str(sel.get("parcel_id") or "").strip()
    cur_doc = str(sel.get("document_number") or "").strip()
    cur_type = str(sel.get("document_type") or "")
    cur_lower = cur_type.lower()

    closure_map = parcel_encumbrance_closure_map(parcel_id, full_df) if parcel_id else {}
    has_closure = bool(cur_doc and cur_doc in closure_map)

    psub = full_df[full_df["parcel_id"].astype(str) == parcel_id] if parcel_id else pd.DataFrame()
    types_lower = psub["document_type"].astype(str).str.lower() if len(psub) else pd.Series(dtype=str)
    has_quitclaim_parcel = bool(types_lower.str.contains("quitclaim", na=False).any()) if len(types_lower) else (
        "quitclaim" in cur_lower
    )
    release_on_parcel = (
        psub["document_type"].astype(str).map(is_release_or_satisfaction_filing).any() if len(psub) else False
    )
    release_other = False
    if len(psub):
        for _, r in psub.iterrows():
            if str(r.get("document_number") or "") == cur_doc:
                continue
            if is_release_or_satisfaction_filing(str(r.get("document_type") or "")):
                release_other = True
                break

    related_types: list[str] = []
    related_has_release_same_parcel = False
    if related_df is not None and len(related_df):
        for _, r in related_df.iterrows():
            related_types.append(str(r.get("document_type") or "").lower())
            if str(r.get("parcel_id") or "").strip() != parcel_id:
                continue
            if is_release_or_satisfaction_filing(str(r.get("document_type") or "")):
                related_has_release_same_parcel = True

    cur_is_encumbrance = is_active_encumbrance_record(cur_type)
    cur_open = cur_is_encumbrance and not has_closure

    bullets: list[str] = []
    seen: set[str] = set()

    def add_bullet(text: str) -> None:
        if text in seen or len(bullets) >= 4:
            return
        seen.add(text)
        bullets.append(text)

    if cur_open:
        if "mortgage" in cur_lower:
            add_bullet("No linked release found for prior mortgage")
        else:
            add_bullet("Open encumbrance detected")

    if has_closure or (is_release_or_satisfaction_filing(cur_type) and release_on_parcel):
        add_bullet("Released lien found in chain")
    elif release_other or related_has_release_same_parcel:
        add_bullet("Released lien found in chain")

    if has_quitclaim_parcel or "quitclaim" in cur_lower:
        add_bullet("Quitclaim deed present in parcel history")

    if len(bullets) < 2:
        if "warranty" in cur_lower and not cur_open and not has_quitclaim_parcel:
            add_bullet("Warranty deed on file; corroborate with remainder of parcel history (mock)")
        elif len(related_types):
            add_bullet("Related filings on this search should be read with the current instrument (mock)")
        else:
            add_bullet("Limited related index in prototype—expand search for a fuller chain read (mock)")

    if len(bullets) < 2:
        add_bullet("Mock summary only—not a title opinion or insurance determination")

    status = "Incomplete / Needs Review"
    variant = "review"
    if cur_open and "mortgage" in cur_lower:
        status = "Incomplete / Needs Review"
        variant = "review"
    elif cur_open:
        status = "Potential Issues"
        variant = "issues"
    elif has_quitclaim_parcel or "quitclaim" in cur_lower:
        status = "Potential Issues"
        variant = "issues"
    elif is_release_or_satisfaction_filing(cur_type) or (has_closure and not cur_open):
        status = "Clear (based on indexed records)"
        variant = "clear"
    elif "warranty" in cur_lower and not has_quitclaim_parcel and not cur_open:
        status = "Clear (based on indexed records)"
        variant = "clear"
    elif "mortgage" in cur_lower and has_closure:
        status = "Clear (based on indexed records)"
        variant = "clear"

    return status, variant, bullets[:4]


def encumbrance_summary_stats(
    parcel_id: str, df: pd.DataFrame, *, current_doc: str = ""
) -> dict[str, int]:
    """
    Parcel-level mock counts aligned with Chain of Title: same event list as chain_of_title_events
    and the same parcel_encumbrance_closure_map pairing (later release/satisfaction on the parcel).
    Active mortgages = no matching release/satisfaction in the map; closed_mortgages + released_liens
    count resolved mortgages and liens (including judgment liens once released).
    """
    pid = str(parcel_id or "").strip()
    out = {
        "active_mortgages": 0,
        "closed_mortgages": 0,
        "released_liens": 0,
        "open_liens": 0,
        "open_judgments": 0,
    }
    if not pid:
        return out
    closure = parcel_encumbrance_closure_map(pid, df)
    events = chain_of_title_events(pid, df, current_doc)
    seen_enc: set[str] = set()
    for ev in events:
        docn = str(ev.get("document_number") or "").strip()
        dtype = str(ev.get("document_type") or "")
        if not docn or docn in seen_enc:
            continue
        if not is_active_encumbrance_record(dtype):
            continue
        seen_enc.add(docn)
        dtl = dtype.lower()
        closed = docn in closure
        if "mortgage" in dtl:
            if closed:
                out["closed_mortgages"] += 1
            else:
                out["active_mortgages"] += 1
        elif "judgment" in dtl:
            if closed:
                out["released_liens"] += 1
            else:
                out["open_judgments"] += 1
        else:
            if closed:
                out["released_liens"] += 1
            else:
                out["open_liens"] += 1

    return out


def parcel_aggregated_title_status(parcel_id: str, df: pd.DataFrame) -> tuple[str, str, str, list[str]]:
    """
    Parcel-wide posture for title review (not tied to a single open document).
    Returns (display headline, badge variant suffix, narrative paragraph, short fact bullets).
    """
    pid = str(parcel_id or "").strip()
    stt = encumbrance_summary_stats(pid, df, current_doc="")
    psub = df[df["parcel_id"].astype(str).str.strip() == pid] if pid else pd.DataFrame()
    has_quitclaim = (
        bool(psub["document_type"].astype(str).str.lower().str.contains("quitclaim", na=False).any())
        if len(psub)
        else False
    )
    am, ol, oj = stt["active_mortgages"], stt["open_liens"], stt["open_judgments"]
    rel_sat = stt["closed_mortgages"] + stt["released_liens"]

    bullets: list[str] = []
    if am:
        bullets.append(f"{am} open mortgage(s) on the parcel-linked indexed chain")
    if ol:
        bullets.append(f"{ol} unreleased non-mortgage lien(s) in parcel-linked filings")
    if oj:
        bullets.append("Open judgment lien(s) in indexed parcel-linked filings")
    if has_quitclaim and not (am or ol or oj):
        bullets.append("Quitclaim(s) in chain—verify grantor authority and warranty coverage on prior links")
    if not bullets and rel_sat > 0:
        bullets.append("Release or satisfaction of a prior encumbrance appears in indexed filings")
    if not bullets:
        bullets.append("No open mortgage or unreleased contractor lien identified in parcel-linked filings (prototype scope)")

    if am or oj:
        return (
            "Review recommended before reliance",
            "review",
            "Open mortgage or judgment lien remains on the indexed chain. Expect schedule exceptions until payoff, "
            "recorded release, or curative is confirmed against the county index.",
            bullets[:4],
        )
    if ol:
        return (
            "Potential issue in indexed parcel history",
            "issues",
            "Unreleased non-mortgage lien on file. Underwriting will typically require release, bond, or negotiated "
            "holdback before clearance.",
            bullets[:4],
        )
    if has_quitclaim:
        return (
            "Potential issue in indexed parcel history",
            "issues",
            "Quitclaim in the indexed chain—no general warranty from grantor. Verify authority and continuity with "
            "adjacent instruments before reliance.",
            bullets[:4],
        )
    return (
        "Indexed chain appears clear",
        "clear",
        "No open mortgage or unreleased lien identified in parcel-linked filings on this extract. "
        "Off-record matters and tax status are not evaluated here.",
        bullets[:4],
    )


def parcel_ownership_summary_from_chain(parcel_id: str, df: pd.DataFrame) -> dict[str, str]:
    """Most recent deed event in chain (newest first) → current / prior owner labels."""
    empty = {
        "current_owner": "—",
        "prior_owner": "—",
        "transfer_date": "—",
        "transfer_doc_type": "—",
    }
    pid = str(parcel_id or "").strip()
    if not pid:
        return empty
    for ev in chain_of_title_events(pid, df, ""):
        dtype = str(ev.get("document_type") or "").lower()
        if "deed" not in dtype:
            continue
        g, e = str(ev.get("grantor") or "").strip(), str(ev.get("grantee") or "").strip()
        return {
            "current_owner": e or "—",
            "prior_owner": g or "—",
            "transfer_date": str(ev.get("recording_date") or "—"),
            "transfer_doc_type": str(ev.get("document_type") or "—"),
        }
    return empty


def parcel_key_risk_bullets(parcel_id: str, df: pd.DataFrame) -> list[str]:
    """2–4 decision-oriented notes derived from mock encumbrance posture."""
    pid = str(parcel_id or "").strip()
    stt = encumbrance_summary_stats(pid, df, current_doc="") if pid else encumbrance_summary_stats("", df)
    out: list[str] = []
    open_enc = stt["active_mortgages"] + stt["open_liens"] + stt["open_judgments"]
    if open_enc == 0:
        out.append("No unreleased lien found in parcel-linked filings (prototype scope).")
    else:
        out.append(
            "Open encumbrance on indexed chain—requires payoff, recorded release, or underwriting clearance."
        )
    if stt["closed_mortgages"] + stt["released_liens"] > 0:
        out.append(
            "Later indexed release or satisfaction present—tie to the correct open item before clearing."
        )
    out.append("Judgment exposure limited to indexed lien filings in this prototype.")
    out.append("Off-record matters and tax status not evaluated in this prototype.")
    seen: set[str] = set()
    deduped: list[str] = []
    for t in out:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped[:4]


def render_parcel_chain_of_title_section(
    parcel_id_str: str,
    df: pd.DataFrame,
    current_doc: str,
    esc,
    *,
    include_detail_view_copy: bool = True,
    property_review_layout: bool = False,
) -> None:
    """Shared Chain of Title timeline (same logic as record detail)."""
    parcel_id_str = str(parcel_id_str or "").strip()
    encumbrance_closure_map = parcel_encumbrance_closure_map(parcel_id_str, df)
    timeline_events = chain_of_title_events(parcel_id_str, df, current_doc)

    if timeline_events:
        timeline_rows = []
        for ev in timeline_events:
            g = str(ev.get("grantor", "") or "").strip()
            e = str(ev.get("grantee", "") or "").strip()
            parties = f"{g} → {e}" if g and e else "—"
            dtype = str(ev.get("document_type", "") or "")
            ev_doc = str(ev.get("document_number", "") or "")
            show_active = is_active_encumbrance_record(dtype)
            closure = encumbrance_closure_map.get(ev_doc) if show_active else None
            if closure:
                item_cls = "detail-timeline-item detail-timeline-item-closed"
                dot_cls = "detail-timeline-dot detail-timeline-dot-closed"
                closure_mod = (
                    " is-satisfied"
                    if closure == "Satisfied"
                    else (" is-released" if closure == "Released" else "")
                )
                date_str = esc(recording_date_compact(ev.get("recording_date")))
                date_html = (
                    f'<div class="detail-timeline-date-row">'
                    f'<span class="detail-timeline-date">{date_str}</span>'
                    f'<span class="detail-timeline-closed-badge{closure_mod}">{esc(closure)}</span>'
                    f"</div>"
                )
            elif show_active:
                item_cls = "detail-timeline-item detail-timeline-item-current"
                dot_cls = "detail-timeline-dot detail-timeline-dot-current"
                date_str = esc(recording_date_compact(ev.get("recording_date")))
                date_html = (
                    f'<div class="detail-timeline-date-row">'
                    f'<span class="detail-timeline-date">{date_str}</span>'
                    f'<span class="detail-timeline-current-badge">Active</span>'
                    f"</div>"
                )
            else:
                item_cls = "detail-timeline-item"
                dot_cls = "detail-timeline-dot"
                date_str = esc(recording_date_compact(ev.get("recording_date")))
                date_html = f'<div class="detail-timeline-date">{date_str}</div>'
            timeline_rows.append(
                f'<div class="{item_cls}">'
                f'<div class="detail-timeline-rail"><span class="{dot_cls}"></span></div>'
                f'<div class="detail-timeline-body">'
                f"{date_html}"
                f'<div class="detail-timeline-parties">{esc(parties)}</div>'
                f'<div class="detail-timeline-type">{esc(str(ev.get("document_type", "") or "—"))}</div>'
                f"</div></div>"
            )
        timeline_body = f'<div class="detail-timeline">{"".join(timeline_rows)}</div>'
    else:
        timeline_body = (
            '<p class="detail-timeline-empty">No chain entries in mock data for this parcel.</p>'
        )

    if include_detail_view_copy:
        helper = (
            '<p class="detail-timeline-helper">Shows ownership and encumbrance events associated with this parcel over '
            "time—not only the document you are viewing.</p>"
        )
        jump = '<p class="detail-parcel-history-jump"><a href="#medici-parcel-chain">View full parcel history →</a></p>'
    else:
        helper = (
            '<p class="detail-timeline-helper">Parcel-linked ownership and encumbrance events in indexed order '
            "(prototype scope).</p>"
        )
        jump = ""

    _shell_open = '<div class="pr-chain-shell">' if property_review_layout else ""
    _shell_close = "</div>" if property_review_layout else ""
    # st.markdown parses Markdown first; any newline + indentation inside the string is treated as a
    # code fence and raw tags appear. st.html injects markup without that pass (same HTML for both flows).
    _chain_html = (
        f"{_shell_open}"
        f'<div class="detail-timeline-wrap">'
        f"{helper}{jump}"
        f'<div class="detail-section-title" id="medici-parcel-chain">Chain of Title</div>'
        f"{timeline_body}"
        f"</div>{_shell_close}"
    )
    st.html(_chain_html)


def ai_summary_outcome_sentence(sel: dict, df: pd.DataFrame) -> str:
    """Closing 'so what' line from the indexed parcel chain and current instrument (mock)."""
    pid = str(sel.get("parcel_id") or "").strip()
    cur_doc = str(sel.get("document_number") or "").strip()
    dtype = str(sel.get("document_type") or "")
    if not pid:
        return "Confirm against the full county index—this read uses limited mock data only."
    closure = parcel_encumbrance_closure_map(pid, df)
    stats = encumbrance_summary_stats(pid, df, current_doc=cur_doc)
    active_mortgages = stats["active_mortgages"]
    open_liens = stats["open_liens"]
    open_judgments = stats["open_judgments"]
    active_total = active_mortgages + open_liens + open_judgments
    cur_open_enc = is_active_encumbrance_record(dtype) and bool(cur_doc) and cur_doc not in closure
    if cur_open_enc:
        return "This would likely remain an open exception until satisfied or released."
    if active_total == 0:
        if is_release_or_satisfaction_filing(dtype):
            return (
                "No active encumbrances remain based on the available chain; this filing records "
                "release or satisfaction of an earlier matched item."
            )
        return "No active encumbrances remain based on the available chain."
    if is_release_or_satisfaction_filing(dtype):
        return "No new encumbrance is added here; the intended effect is to clear a matched item earlier on the available chain."
    return "Open encumbrances still appear on the available chain; read this filing together with those entries."


_SAMPLE_DOCS_DIR = Path(__file__).resolve().parent / "sample_docs"

# Canonical normalized document type -> PNG under sample_docs/ (preferred filename first, then legacy double-extension).
_PREVIEW_IMAGE_FILES: dict[str, tuple[str, ...]] = {
    "mortgage": ("mortgage.png", "mortgage.png.png"),
    "warranty deed": ("warranty_deed.png", "warranty_deed.png.png"),
    "release of lien": ("release_of_lien.png", "release_of_lien.png.png"),
    "mechanic lien": ("mechanic_lien.png", "mechanic_lien.png.png"),
    "quitclaim deed": ("quitclaim_deed.png", "quitclaim_deed.png.png"),
    "satisfaction of mortgage": (
        "satisfaction_of_mortgage.png",
        "satisfaction_of_mortgage.png.png",
    ),
}

# Normalized synonym / county label -> canonical key in _PREVIEW_IMAGE_FILES (values must be canonical keys).
_PREVIEW_DOCUMENT_TYPE_ALIASES: dict[str, str] = {
    "release of mortgage": "satisfaction of mortgage",
    "mortgage satisfaction": "satisfaction of mortgage",
    "satisfaction piece": "satisfaction of mortgage",
}


def normalize_document_type_for_preview(raw: object) -> str:
    """strip(), lowercase, collapse any run of whitespace to a single space."""
    return _collapse_spaces(str(raw or "").strip().lower())


def preview_image_map_key(raw: object) -> str:
    """Normalized document type, then alias/synonym resolution for preview file lookup."""
    norm = normalize_document_type_for_preview(raw)
    seen: set[str] = set()
    while norm in _PREVIEW_DOCUMENT_TYPE_ALIASES and norm not in seen:
        seen.add(norm)
        norm = _PREVIEW_DOCUMENT_TYPE_ALIASES[norm]
    return norm


def get_preview_image_path(record: dict) -> Path | None:
    """
    Return an absolute Path to a local preview PNG if the record's document type maps
    and a candidate file exists under sample_docs/. Otherwise None.
    """
    key = preview_image_map_key(record.get("document_type"))
    names = _PREVIEW_IMAGE_FILES.get(key)
    if not names:
        return None
    for name in names:
        p = _SAMPLE_DOCS_DIR / name
        if p.exists() and p.is_file():
            return p.resolve()
    return None


def _unique_parcel_ids_ordered(df: pd.DataFrame) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for pid in df["parcel_id"].astype(str).str.strip():
        if pid not in seen:
            seen.add(pid)
            out.append(pid)
    return out


def _collapse_spaces(s: str) -> str:
    return " ".join(str(s).split())


def normalize_title_review_input(raw: object) -> str:
    """Trim, lowercase, collapse repeated internal whitespace."""
    return _collapse_spaces(str(raw or "").strip().lower())


def normalize_parcel_pin_key(raw: object) -> str:
    """Alphanumeric only, lowercase (ignores hyphens/spaces in PIN typing)."""
    return "".join(c for c in str(raw or "").lower() if c.isalnum())


def normalize_parcel_display_key(raw: object) -> str:
    """Lowercase PIN/parcel string with spaces collapsed; hyphens preserved for display match."""
    return _collapse_spaces(str(raw or "").strip().lower())


def normalize_address_match_key(raw: object) -> str:
    """
    Lowercase, collapsed spaces, strip common punctuation (periods, commas, # units, semicolons, quotes, slashes).
    Hyphens kept so street and PIN-like fragments stay distinguishable from pin-key path.
    """
    s = normalize_title_review_input(raw)
    for ch in ".,#;:'\"\\/":
        s = s.replace(ch, " ")
    return _collapse_spaces(s)


def _prefix_match_score(haystack: str, q: str, *, strong: int, weak: int) -> int:
    """Prefix match with a boundary so short queries (e.g. '7') don't match '77 Northpoint Dr'."""
    if not q or not haystack or len(q) < 2:
        return 0
    if not haystack.startswith(q):
        return 0
    if len(haystack) == len(q):
        return strong
    nxt = haystack[len(q) : len(q) + 1]
    if nxt.isalnum():
        return 0
    return weak


def _contains_match_score(haystack: str, q: str, *, min_q: int, score: int) -> int:
    if not q or len(q) < min_q:
        return 0
    return score if q in haystack else 0


def _pin_partial_score(pin_key: str, q_pin: str) -> int:
    if not q_pin or not pin_key:
        return 0
    if pin_key == q_pin:
        return 0  # handled by exact tier
    if len(q_pin) >= 2 and pin_key.startswith(q_pin):
        return 78
    if len(q_pin) >= 4 and q_pin in pin_key:
        return 72
    if len(q_pin) >= 4 and pin_key in q_pin:
        return 70
    return 0


def _title_review_parcel_index(df: pd.DataFrame) -> list[dict]:
    """One row per distinct parcel_id (document-agnostic)."""
    rows: list[dict] = []
    for pid in _unique_parcel_ids_ordered(df):
        r0 = df[df["parcel_id"].astype(str).str.strip() == pid].iloc[0]
        addr = str(r0.get("address", "") or "").strip()
        ap = str(r0.get("address_parcel", "") or "").strip()
        rows.append(
            {
                "parcel_id": pid,
                "address": addr,
                "address_parcel": ap,
                "county": str(r0.get("county", "") or "").strip(),
                "pid_display_key": normalize_parcel_display_key(pid),
                "pin_key": normalize_parcel_pin_key(pid),
                "addr_key": normalize_address_match_key(addr),
                "ap_key": normalize_address_match_key(ap),
            }
        )
    return rows


def lookup_parcel_for_title_review(query: str, df: pd.DataFrame) -> dict:
    """
    Resolve freeform user input to parcel(s) for Title Review Mode.

    Returns:
      - kind: "none" | "auto_open" | "choose"
      - parcel_id: set only when kind == "auto_open" (single strong exact match)
      - candidates: list[dict] with keys parcel_id, address, county (non-empty when kind == "choose")

    Normalization: trim, lowercase, collapsed whitespace; address keys also drop common punctuation.
    Matching: exact parcel display / normalized PIN / exact address (and address_parcel line),
    then prefix and contains on address fields, then PIN prefix/substring. Scores are per-parcel max.

    auto_open only when exactly one parcel meets the strong-exact threshold (clear PIN/address/parcel match).
    Otherwise users pick from candidates (including a single row for weak/partial matches).
    """
    empty = {"kind": "none", "parcel_id": None, "candidates": []}
    q_raw = str(query or "").strip()
    if not q_raw:
        return empty

    q_disp = normalize_parcel_display_key(q_raw)
    q_pin = normalize_parcel_pin_key(q_raw)
    q_addr = normalize_address_match_key(q_raw)

    STRONG_EXACT = 96  # auto-open threshold (exact parcel / PIN / primary address line)
    LIST_FLOOR = 42  # minimum score to appear in candidate list
    MAX_LIST = 40

    index = _title_review_parcel_index(df)
    scores: dict[str, int] = {}
    for row in index:
        pid = row["parcel_id"]
        ak = row["addr_key"]
        apk = row["ap_key"]
        sc = 0
        if row["pid_display_key"] == q_disp:
            sc = max(sc, 100)
        if q_pin and q_pin == row["pin_key"]:
            sc = max(sc, 99)
        if q_addr and q_addr == ak:
            sc = max(sc, 96)
        if q_addr and q_addr == apk:
            sc = max(sc, 95)
        sc = max(
            sc,
            _prefix_match_score(ak, q_addr, strong=92, weak=88),
            _prefix_match_score(apk, q_addr, strong=90, weak=86),
        )
        sc = max(
            sc,
            _contains_match_score(ak, q_addr, min_q=3, score=74),
            _contains_match_score(apk, q_addr, min_q=3, score=72),
        )
        if len(q_addr) >= 4 and len(ak) >= 4 and ak in q_addr:
            sc = max(sc, 68)
        if len(q_addr) >= 4 and len(apk) >= 4 and apk in q_addr:
            sc = max(sc, 66)
        sc = max(sc, _pin_partial_score(row["pin_key"], q_pin))
        if sc:
            scores[pid] = sc

    if not scores:
        return empty

    by_pid = {r["parcel_id"]: r for r in index}
    ranked = sorted(
        scores.items(),
        key=lambda kv: (-kv[1], len(by_pid[kv[0]]["address"]), kv[0]),
    )
    ranked = [(p, s) for p, s in ranked if s >= LIST_FLOOR][:MAX_LIST]

    if not ranked:
        return empty

    cand_payload = [
        {"parcel_id": p, "address": by_pid[p]["address"], "county": by_pid[p]["county"]}
        for p, _ in ranked
    ]

    if len(ranked) == 1 and ranked[0][1] >= STRONG_EXACT:
        return {"kind": "auto_open", "parcel_id": ranked[0][0], "candidates": []}

    return {"kind": "choose", "parcel_id": None, "candidates": cand_payload}


def title_review_intake_live_hint_message(query: str, df: pd.DataFrame) -> str:
    """
    Live preview line for title review intake (same lookup as process_title_review_intake).
    Returns empty string when query is blank (caller reserves fixed height).
    """
    q = str(query or "").strip()
    if not q:
        return ""
    lookup = lookup_parcel_for_title_review(q, df)
    if lookup["kind"] == "none":
        return "No matches found"
    if lookup["kind"] == "auto_open":
        return "1 matching property"
    n = len(lookup["candidates"])
    if n == 1:
        return "1 matching property"
    return f"{n} matching properties"


# Example chip values (keep aligned with on-screen demo copy)
_SEARCH_RECORDS_EXAMPLE_QUERIES: tuple[str, ...] = (
    "James Carter",
    "2026-001245",
    "08-14-302-011",
    "1458 River Bend Rd",
)
_TITLE_REVIEW_EXAMPLE_QUERIES: tuple[str, ...] = (
    "1458 River Bend Rd",
    "08-14-302-011",
    "1120 Oak Meadow Ln",
    "77 Northpoint Dr",
    "18 Harbor View Ct",
)


def queue_search_records_example_query(q: str) -> None:
    """Widget callback only: queue value for next run (never assign widget keys from callbacks)."""
    st.session_state["_search_records_example_pending"] = str(q or "").strip()


def queue_title_review_example_query(q: str) -> None:
    """Widget callback only: queue intake text for next run before st.text_input binds its key."""
    st.session_state["_title_review_intake_pending"] = str(q or "").strip()


def process_title_review_intake(qin: str) -> None:
    """
    Title Review lookup / navigation from the current intake query.
    The text field value must already live in session_state.title_review_intake_query (widget-managed);
    do not assign to that key here—Streamlit forbids mutating widget state after instantiation.

    - auto_open: one clear strong match → open_property_review immediately.
    - choose: multiple or weaker matches → title_review_match_candidates for card picker.
    - none: no match → title_review_last_failed_query.
    """
    q = str(qin or "").strip()
    st.session_state.pop("title_review_ambiguous", None)
    st.session_state.pop("title_review_match_candidates", None)
    if not q:
        st.session_state.title_review_last_failed_query = None
        return
    _lookup = lookup_parcel_for_title_review(q, mock_results)
    if _lookup["kind"] == "auto_open":
        st.session_state.title_review_last_failed_query = None
        open_property_review(_lookup["parcel_id"])
    elif _lookup["kind"] == "choose":
        st.session_state.title_review_last_failed_query = None
        st.session_state.title_review_match_candidates = _lookup["candidates"]
    else:
        st.session_state.title_review_last_failed_query = q


def dataframe_for_parcel(parcel_id: str, df: pd.DataFrame) -> pd.DataFrame:
    """All mock rows for a parcel (parcel-level slice for title review)."""
    pid = str(parcel_id or "").strip()
    if not pid:
        return df.iloc[0:0].copy()
    return df[df["parcel_id"].astype(str).str.strip() == pid].copy()


def parcel_linked_indexed_filing_count(parcel_id: str, df: pd.DataFrame) -> int:
    """Count of indexed rows for the parcel (same slice as parcel-level title / chain analysis)."""
    return len(dataframe_for_parcel(parcel_id, df))


def format_indexed_filings_context_line(parcel_id: str, df: pd.DataFrame) -> str:
    """Caption for title status UI, e.g. 'Based on 3 indexed filings'."""
    n = parcel_linked_indexed_filing_count(parcel_id, df)
    if n == 1:
        return "Based on 1 indexed filing"
    return f"Based on {n} indexed filings"


def render_property_review_screen() -> None:
    """Parcel-level title review workflow (property-first) using mock data and shared parcel helpers."""
    parcel_id = str(st.session_state.get("title_review_parcel_id") or "").strip()
    if not parcel_id:
        st.session_state.active_screen = "search"
        st.rerun()
        return

    def esc(x) -> str:
        if x is None:
            return ""
        return html.escape(str(x))

    sub = dataframe_for_parcel(parcel_id, mock_results)
    if sub.empty:
        st.session_state.active_screen = "search"
        st.rerun()
        return

    sub_sorted = sub.sort_values("recording_date_dt", ascending=False)
    anchor = sub_sorted.iloc[0]

    st.markdown('<div class="detail-back">', unsafe_allow_html=True)
    if st.button("← Back to portal", type="tertiary"):
        st.session_state.active_screen = "search"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    addr = esc(str(anchor.get("address") or "—"))
    county = esc(str(anchor.get("county") or "—"))
    pin = esc(parcel_id)

    st.markdown(
        f"""
        <div class="detail-hero pr-page-hero">
            <div class="detail-hero-eyebrow">Parcel title review</div>
            <div class="detail-hero-title">{addr}</div>
            <div class="detail-hero-docid">
                <span class="detail-hero-docid-label">Parcel ID</span>{pin}
            </div>
            <div class="detail-hero-meta">
                <span>{county}</span>
            </div>
            <div class="detail-hero-meta pr-hero-chain-summary">
                Indexed chain summary—parcel-linked filings only
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    link_col, btn_col = st.columns([1.15, 1], gap="small")
    with link_col:
        st.markdown(
            '<p class="pr-review-doc-link"><a href="#medici-pr-records">Supporting instruments →</a></p>',
            unsafe_allow_html=True,
        )
    with btn_col:
        if st.button("Open latest indexed filing", type="secondary", key="pr_open_latest"):
            open_detail_view(record_for_state(anchor), detail_nav_source="property_review")

    st.markdown('<div class="pr-after-hero-gap" aria-hidden="true"></div>', unsafe_allow_html=True)

    ph, _pv, narrative, fact_bullets = parcel_aggregated_title_status(parcel_id, mock_results)
    fact_items = "".join(f"<li>{esc(b)}</li>" for b in fact_bullets)
    _filings_ctx = esc(format_indexed_filings_context_line(parcel_id, mock_results))
    st.markdown(
        f"""
        <div class="detail-title-status-wrap pr-spaced-card pr-posture-card">
            <div class="detail-title-status-head">
                <span class="detail-title-status-label">Indexed posture</span>
            </div>
            <div class="pr-status-headline" role="status">{esc(ph)}</div>
            <p class="pr-status-narrative">{esc(narrative)}</p>
            <p class="detail-title-status-filing-count">{_filings_ctx}</p>
            <ul class="detail-title-status-bullets">{fact_items}</ul>
            <p class="detail-title-status-confidence">Source: indexed records in prototype scope. Not a title opinion, commitment, or policy.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    own = parcel_ownership_summary_from_chain(parcel_id, mock_results)
    own_rows = (
        ("Vested owner (indexed)", own["current_owner"], False),
        ("Last conveyance date", own["transfer_date"], False),
        ("Last conveyance instrument", own["transfer_doc_type"], False),
        ("Grantor on last deed (indexed)", own["prior_owner"], False),
    )
    own_body = "".join(
        f'<div class="detail-extracted-row">'
        f'<span class="detail-extracted-label">{esc(lbl)}</span>'
        f'<span class="detail-extracted-value">{esc(str(val) if val is not None else "—")}</span>'
        f"</div>"
        for lbl, val, _ in own_rows
    )
    st.markdown(
        f"""
        <div class="detail-extracted-panel pr-spaced-card pr-ownership-compact">
            <div class="detail-extracted-heading">Ownership (indexed chain)</div>
            <div class="detail-extracted-group" style="margin-top:0.35rem;padding-top:0;border-top:none;">
                {own_body}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    es_counts = encumbrance_summary_stats(parcel_id, mock_results, current_doc="")
    released_satisfied = es_counts["closed_mortgages"] + es_counts["released_liens"]
    enc_snapshot_rows = [
        (es_counts["active_mortgages"], "Open mortgage", "Open mortgages"),
        (released_satisfied, "Released or satisfied encumbrance", "Released or satisfied encumbrances"),
        (es_counts["open_liens"], "Open lien (non-mortgage)", "Open liens (non-mortgage)"),
        (es_counts["open_judgments"], "Open judgment lien", "Open judgment liens"),
    ]
    enc_cells = "".join(
        f'<div class="detail-encumbrance-row">'
        f'<span class="detail-encumbrance-count">{n}</span>'
        f'<span class="detail-encumbrance-label">{esc(singular if n == 1 else plural)}</span>'
        f"</div>"
        for n, singular, plural in enc_snapshot_rows
    )
    st.markdown(
        f"""
        <div class="detail-encumbrance-wrap pr-spaced-card pr-enc-wrap-tight">
            <div class="detail-encumbrance-title">Encumbrance snapshot (indexed)</div>
            <div class="detail-encumbrance-grid">{enc_cells}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    risk_bullets = parcel_key_risk_bullets(parcel_id, mock_results)
    risk_items = "".join(f"<li>{esc(t)}</li>" for t in risk_bullets)
    st.markdown(
        f"""
        <div class="pr-notes-panel">
            <div class="detail-section-title">Review notes</div>
            <ul class="detail-title-status-bullets">{risk_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="pr-section-divider" role="presentation"></div>', unsafe_allow_html=True)

    render_parcel_chain_of_title_section(
        parcel_id,
        mock_results,
        "",
        esc,
        include_detail_view_copy=False,
        property_review_layout=True,
    )

    st.markdown(
        """
        <div id="medici-pr-records"></div>
        <div class="detail-section-title pr-instruments-head">Parcel-linked instruments</div>
        <div class="detail-preview-source-caption">Indexed filings for this parcel—click a row or Open for instrument detail</div>
        """,
        unsafe_allow_html=True,
    )

    for _, row in sub_sorted.iterrows():
        doc_tag_class = doc_type_tag_class(row["document_type"])
        _scan_lbl, _scan_mod = result_scan_status_badge(row, mock_results)
        _scan_class = f"result-status-badge {_scan_mod}"
        row_main, row_view = st.columns([0.82, 0.18], gap="xxsmall")
        with row_main:
            st.markdown(
                f"""
                <div class="result-row">
                    <div class="result-grid">
                        <div>
                            <div class="result-tag-line">
                                <span class="{doc_tag_class}">{row["document_type"]}</span>
                                <span class="{_scan_class}">{html.escape(_scan_lbl)}</span>
                            </div>
                            <div class="date-subtle">{row["recording_date"]}</div>
                        </div>
                        <div>
                            <div class="party-main">{html.escape(str(row["party"]))}</div>
                            <div class="addr-sub">{html.escape(str(row["address_parcel"]))}</div>
                        </div>
                        <div>
                            <div class="party-main right-note">{html.escape(str(row["county"]))}</div>
                            <div class="meta-sub right-note">{html.escape(str(row["summary"]))}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                " ",
                key=f"pr_row_click_{row['document_number']}",
                type="tertiary",
                use_container_width=True,
                help="Open record (row)",
            ):
                open_detail_view(record_for_state(row), detail_nav_source="property_review")
        with row_view:
            with st.container(
                height="stretch",
                vertical_alignment="center",
                horizontal_alignment="right",
                gap=None,
            ):
                if st.button("Open", key=f"pr_row_{row['document_number']}", type="secondary"):
                    open_detail_view(record_for_state(row), detail_nav_source="property_review")


def render_detail_screen() -> None:
    sel = dict(st.session_state.get("selected_record") or {})
    if not sel:
        sel = record_for_state(mock_results.iloc[0])
        st.session_state["selected_record"] = sel
    # Prefer canonical row from mock data so all detail fields exist.
    match = mock_results[mock_results["document_number"] == sel.get("document_number")]
    if not match.empty:
        sel = record_for_state(match.iloc[0])

    def esc(x) -> str:
        if x is None:
            return ""
        return html.escape(str(x))

    st.markdown('<div class="detail-back">', unsafe_allow_html=True)
    _ret = str(st.session_state.get("detail_return_screen") or "search")
    _pr_pid = str(st.session_state.get("title_review_parcel_id") or "").strip()
    if _ret == "property_review" and _pr_pid:
        if st.button("← Back to title review", type="tertiary", key="detail_back_title_review"):
            st.session_state.active_screen = "property_review"
            st.rerun()
    else:
        if st.button("← Back to results", type="tertiary", key="detail_back_search"):
            st.session_state.active_screen = "search"
            st.session_state.detail_return_screen = "search"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    def party_headline() -> str:
        g = (sel.get("grantor") or "").strip()
        e = (sel.get("grantee") or "").strip()
        if g and e:
            return f"{g} → {e}"
        p = (sel.get("party") or "").strip()
        if p:
            return (
                p.replace(" -> ", " → ")
                .replace("->", "→")
                .replace(" —> ", " → ")
            )
        return "—"

    hero_doc_id = esc(sel.get("document_number", "") or "—")
    doc_type = esc(sel.get("document_type", "") or "—")
    county = esc(sel.get("county", "") or "—")
    date_line = esc(recording_date_compact(sel.get("recording_date")))

    st.markdown(
        f"""
        <div class="detail-hero">
            <div class="detail-hero-eyebrow">Record detail</div>
            <div class="detail-hero-title">{esc(party_headline())}</div>
            <div class="detail-hero-docid">
                <span class="detail-hero-docid-label">Document</span>{hero_doc_id}
            </div>
            <div class="detail-hero-meta">
                <span class="detail-hero-meta-type">{doc_type}</span>
                <span class="detail-hero-meta-sep">·</span>
                <span>{date_line}</span>
                <span class="detail-hero-meta-sep">·</span>
                <span>{county}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    related_for_title = get_related_records(
        str(sel.get("document_number") or ""),
        str(sel.get("parcel_id") or ""),
        mock_results,
        limit=6,
    )
    ts_label, ts_variant, ts_bullets = title_status_for_record(sel, related_for_title, mock_results)
    ts_badge_class = f"detail-title-status-badge is-{ts_variant}"
    ts_items = "".join(f"<li>{esc(b)}</li>" for b in ts_bullets)
    _ts_pid = str(sel.get("parcel_id") or "").strip()
    _ts_filings_ctx = esc(format_indexed_filings_context_line(_ts_pid, mock_results))
    st.markdown(
        f"""
        <div class="detail-title-status-wrap">
            <div class="detail-title-status-head">
                <span class="detail-title-status-label">Title status</span>
                <span class="{ts_badge_class}" role="status">{esc(ts_label)}</span>
            </div>
            <ul class="detail-title-status-bullets">{ts_items}</ul>
            <p class="detail-title-status-filing-count">{_ts_filings_ctx}</p>
            <p class="detail-title-status-confidence">Data confidence: High (based on indexed records)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_d, right_d = st.columns([0.6, 0.4], gap="large")

    with left_d:
        st.markdown(
            """
            <div class="detail-section-title">Document Preview</div>
            <div class="detail-preview-source-caption">Recorded Document (Source)</div>
            """,
            unsafe_allow_html=True,
        )
        preview_doc = esc(sel.get("document_number", "") or "—")
        _resolved_path = get_preview_image_path(sel)

        _preview_rendered = False
        if _resolved_path is not None:
            with st.container(border=True, height=500, key="detail_doc_preview"):
                st.image(_resolved_path, use_container_width=True)
            _preview_rendered = True

        if _preview_rendered:
            st.markdown(
                '<div class="detail-preview-note">Sample recorded document (preview image)</div>',
                unsafe_allow_html=True,
            )
        else:
            _fallback_copy = (
                "This document image is not available in the prototype. In production, the recorded PDF "
                "or scanned image would be displayed here."
            )
            _preview_sub = (
                f"{_fallback_copy}<br/>"
                f'<span class="detail-preview-docref">Document {preview_doc}</span>'
            )
            st.markdown(
                f"""
            <div class="detail-preview-box">
                <div class="detail-preview-inner">
                    <div class="detail-preview-icon" aria-hidden="true">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M8 3h6.2L19 7.8V19a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
                                  stroke="currentColor" stroke-width="1.45" stroke-linejoin="round"/>
                            <path d="M14 3v5h5" stroke="currentColor" stroke-width="1.45" stroke-linejoin="round"/>
                            <path d="M8.5 13h7M8.5 16.5h5" stroke="currentColor" stroke-width="1.15"
                                  stroke-linecap="round" opacity="0.58"/>
                        </svg>
                    </div>
                    <span class="detail-preview-badge">Preview placeholder</span>
                    <div class="detail-preview-label">Recorded document</div>
                    <div class="detail-preview-sub">{_preview_sub}</div>
                </div>
            </div>
            <div class="detail-preview-note">Document preview (mock)</div>
                """,
                unsafe_allow_html=True,
            )

        if DEBUG_MODE:
            _raw_doc_type = sel.get("document_type")
            _norm_doc_type = normalize_document_type_for_preview(_raw_doc_type)
            _map_key = preview_image_map_key(_raw_doc_type)
            _candidates = _PREVIEW_IMAGE_FILES.get(_map_key)
            _canonical_path = (_SAMPLE_DOCS_DIR / _candidates[0]) if _candidates else None
            _path_for_debug = _resolved_path if _resolved_path is not None else _canonical_path
            _path_exists = _resolved_path is not None
            st.markdown(
                "<div class='detail-preview-debug' style='font-size:0.72rem;color:#5a6e8a;margin:0.45rem 0 0 0;"
                "font-family:ui-monospace,monospace;line-height:1.45;'>"
                f"<strong>DEBUG (preview)</strong><br/>"
                f"raw document_type: {esc(repr(_raw_doc_type))}<br/>"
                f"normalized: {esc(repr(_norm_doc_type))}<br/>"
                f"preview map key: {esc(repr(_map_key))}<br/>"
                f"resolved path: {esc(str(_path_for_debug) if _path_for_debug else '—')}<br/>"
                f"file exists: {esc(str(_path_exists))}"
                "</div>",
                unsafe_allow_html=True,
            )

    with right_d:

        def format_field_value(raw_val, *, is_amount: bool = False) -> str:
            if is_amount:
                if raw_val is None or str(raw_val).strip() == "":
                    return "—"
                try:
                    if pd.isna(raw_val):
                        return "—"
                except (TypeError, ValueError):
                    pass
                return str(raw_val)
            if raw_val in (None, ""):
                return "—"
            return str(raw_val)

        extracted_groups = [
            (
                "Transaction",
                [
                    ("Document Type", sel.get("document_type"), False),
                    ("Recording Date", sel.get("recording_date"), False),
                    ("Amount", sel.get("amount"), True),
                ],
            ),
            (
                "Parties",
                [
                    ("Grantor", sel.get("grantor"), False),
                    ("Grantee", sel.get("grantee"), False),
                ],
            ),
            (
                "Property",
                [
                    ("Address", sel.get("address"), False),
                    ("Parcel ID", sel.get("parcel_id"), False),
                ],
            ),
        ]
        group_html_parts: list[str] = []
        for group_title, fields in extracted_groups:
            rows_html = "".join(
                f'<div class="detail-extracted-row">'
                f'<span class="detail-extracted-label">{esc(lbl)}</span>'
                f'<span class="detail-extracted-value">{esc(format_field_value(raw_val, is_amount=amt_flag))}</span>'
                f"</div>"
                for lbl, raw_val, amt_flag in fields
            )
            group_html_parts.append(
                f'<div class="detail-extracted-group">'
                f'<div class="detail-extracted-group-title">{esc(group_title)}</div>'
                f"{rows_html}</div>"
            )
        extracted_html = (
            f'<div class="detail-extracted-panel">'
            f'<div class="detail-extracted-heading">Extracted Data</div>'
            f'{"".join(group_html_parts)}'
            f"</div>"
        )
        st.markdown(extracted_html, unsafe_allow_html=True)

    insights = key_insights_for_record(sel)
    insight_cards = "".join(
        f'<div class="detail-insight-card">'
        f'<span class="detail-insight-marker" aria-hidden="true"></span>'
        f'<span class="detail-insight-text">{esc(t)}</span>'
        f"</div>"
        for t in insights
    )
    st.markdown(
        f"""
        <div class="detail-insights-wrap">
            <div class="detail-section-title">Key Insights</div>
            <div class="detail-insight-grid">{insight_cards}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _ai_base = str(sel.get("ai_summary") or "").strip()
    _ai_wf = ai_summary_title_workflow_sentence(sel).strip()
    _ai_out = ai_summary_outcome_sentence(sel, mock_results).strip()
    _ai_full = " ".join(p for p in (_ai_base, _ai_wf, _ai_out) if p)

    st.markdown(
        f"""
        <div class="detail-ai-wrap">
            <div class="detail-section-title">AI Summary</div>
            <div class="detail-ai-text">{esc(_ai_full)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_doc = str(sel.get("document_number", "") or "")
    parcel_id_str = str(sel.get("parcel_id", "") or "")
    es_counts = encumbrance_summary_stats(
        parcel_id_str, mock_results, current_doc=current_doc
    )

    closed_enc = es_counts["closed_mortgages"] + es_counts["released_liens"]
    enc_rows = [
        (es_counts["active_mortgages"], "Active Mortgage", "Active Mortgages"),
        (closed_enc, "Released or Satisfied", "Released or Satisfied"),
        (es_counts["open_liens"], "Open Lien", "Open Liens"),
        (es_counts["open_judgments"], "Open Judgment", "Open Judgments"),
    ]
    enc_cells = "".join(
        f'<div class="detail-encumbrance-row">'
        f'<span class="detail-encumbrance-count">{n}</span>'
        f'<span class="detail-encumbrance-label">{esc(singular if n == 1 else plural)}</span>'
        f"</div>"
        for n, singular, plural in enc_rows
    )
    st.markdown(
        f"""
        <div class="detail-encumbrance-wrap">
            <div class="detail-encumbrance-title">Encumbrance summary</div>
            <div class="detail-encumbrance-grid">{enc_cells}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_parcel_chain_of_title_section(
        parcel_id_str, mock_results, current_doc, esc, include_detail_view_copy=True
    )

    parcel = sel.get("parcel_id", "")
    doc_num = sel.get("document_number", "")
    related = get_related_records(doc_num, parcel, mock_results, limit=3)

    st.markdown('<div class="detail-related-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="detail-section-title">Related Records</div>', unsafe_allow_html=True)
    if related.empty:
        st.caption("No additional records found for this parcel")
    for _, rrow in related.iterrows():
        rdoc = rrow["document_number"]
        tag_cls = doc_type_tag_class(str(rrow.get("document_type", "") or ""))
        date_txt = esc(recording_date_compact(rrow.get("recording_date")))
        party_txt = esc(related_party_headline(rrow))
        dtype_txt = esc(str(rrow.get("document_type", "") or "—"))
        c_rel, c_btn = st.columns([0.82, 0.18], gap="xxsmall")
        with c_rel:
            st.markdown(
                f"""
                <div class="related-result-row">
                    <div class="related-result-grid">
                        <div>
                            <span class="{tag_cls} related-doc-tag">{dtype_txt}</span>
                            <div class="related-result-date">{date_txt}</div>
                        </div>
                        <div>
                            <div class="related-result-party">{party_txt}</div>
                            <div class="related-result-docnum">{esc(str(rdoc))}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                " ",
                key=f"rel_click_{rdoc}",
                type="tertiary",
                use_container_width=True,
                help="Open related record",
            ):
                open_detail_view(record_for_state(rrow), detail_nav_source="inherit")
        with c_btn:
            with st.container(height="stretch", vertical_alignment="center", horizontal_alignment="right", gap=None):
                if st.button("Open", key=f"rel_view_{rdoc}", type="secondary"):
                    open_detail_view(record_for_state(rrow), detail_nav_source="inherit")
    st.markdown("</div>", unsafe_allow_html=True)


if st.session_state.active_screen == "detail":
    render_detail_screen()
    st.stop()

if st.session_state.active_screen == "property_review":
    render_property_review_screen()
    st.stop()

# Legacy segmented labels (session stores the selected option string)
_pw = st.session_state.get("portal_workflow_mode")
if _pw == "Search Records":
    st.session_state.portal_workflow_mode = "Search Documents"
elif _pw == "Title Review Mode":
    st.session_state.portal_workflow_mode = "Review Property"

_portal_mode_for_copy = str(st.session_state.get("portal_workflow_mode", "Search Documents"))
if _portal_mode_for_copy == "Review Property":
    _portal_subtitle = "Property-first review of indexed ownership, encumbrances, and title status."
else:
    _portal_subtitle = "Exploratory search across parties, document numbers, parcels, and addresses."

st.markdown(
    f"""
    <div class="portal-header">
        <div class="portal-title">Cook County Search Portal</div>
        <div class="portal-subtitle">{_portal_subtitle}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

portal_workflow_mode = st.segmented_control(
    "Workflow mode",
    options=["Search Documents", "Review Property"],
    default="Search Documents",
    label_visibility="hidden",
    key="portal_workflow_mode",
    width="content",
)

if portal_workflow_mode == "Search Documents":
    st.session_state.title_review_last_failed_query = None
    st.session_state.pop("title_review_ambiguous", None)
    st.session_state.pop("title_review_match_candidates", None)

st.markdown('<div class="portal-post-mode-spacer" aria-hidden="true"></div>', unsafe_allow_html=True)

if portal_workflow_mode == "Review Property":
    _tr_pending = st.session_state.pop("_title_review_intake_pending", None)
    if _tr_pending is not None:
        st.session_state.title_review_intake_query = _tr_pending
        st.session_state["_title_review_process_intake"] = True

    with st.container(key="title_review_guided_shell", border=True):
        st.markdown(
            """
            <div class="title-review-intake-header">Start title review</div>
            <p class="title-review-intake-lead">Start with a property to review ownership, encumbrances, and indexed title status.</p>
            """,
            unsafe_allow_html=True,
        )
        # st.form: Enter in the field submits the same form as "Review Property" (no in-form callbacks except submit).
        with st.form("title_review_intake_form", clear_on_submit=False, border=False):
            st.text_input(
                "Address or parcel ID",
                key="title_review_intake_query",
                placeholder="Address or parcel ID",
                label_visibility="collapsed",
            )
            _q_live = str(st.session_state.get("title_review_intake_query") or "")
            _live_hint = title_review_intake_live_hint_message(_q_live, mock_results)
            _live_hint_body = html.escape(_live_hint) if _live_hint else "\u00a0"
            st.markdown(
                f'<p class="title-review-intake-live-hint">{_live_hint_body}</p>',
                unsafe_allow_html=True,
            )
            _title_submitted = st.form_submit_button(
                "Review Property",
                type="primary",
                width="content",
                key="title_review_form_submit",
            )

    st.markdown(
        '<div class="title-review-examples-label">Example properties</div>',
        unsafe_allow_html=True,
    )
    _tex, _te_mid, _tex2 = st.columns([0.04, 0.92, 0.04])
    with _te_mid:
        _te_cols = st.columns(len(_TITLE_REVIEW_EXAMPLE_QUERIES), gap="small")
        for _te_i, _te_q in enumerate(_TITLE_REVIEW_EXAMPLE_QUERIES):
            with _te_cols[_te_i]:
                st.button(
                    _te_q,
                    key=f"title_ex_{_te_i}",
                    type="tertiary",
                    on_click=queue_title_review_example_query,
                    args=(_te_q,),
                )

    if _title_submitted or st.session_state.pop("_title_review_process_intake", None):
        qin = str(st.session_state.get("title_review_intake_query") or "").strip()
        process_title_review_intake(qin)

    _cands = st.session_state.get("title_review_match_candidates") or []
    if _cands:
        st.markdown(
            '<div class="detail-section-title" style="margin-top:0.85rem;">Select a property to review</div>'
            '<div class="section-subtitle" style="margin-bottom:0.55rem;color:#6d7d90;">'
            "Click a row or the Open button to start parcel-level title review.</div>",
            unsafe_allow_html=True,
        )
        st.markdown('<div class="results-list-leader" aria-hidden="true"></div>', unsafe_allow_html=True)
        for _ti, _c in enumerate(_cands):
            _addr = html.escape(str(_c.get("address") or "—"))
            _pid = html.escape(str(_c.get("parcel_id") or ""))
            _cty = html.escape(str(_c.get("county") or "—"))
            row_main, row_view = st.columns([0.905, 0.095], gap="xxsmall")
            with row_main:
                st.markdown(
                    f"""
                    <div class="result-row">
                        <div class="result-grid">
                            <div>
                                <div class="result-tag-line">
                                    <span class="doc-type-neutral">PARCEL</span>
                                </div>
                                <div class="date-subtle">&nbsp;</div>
                            </div>
                            <div>
                                <div class="party-main">{_addr}</div>
                                <div class="addr-sub">Parcel ID {_pid}</div>
                            </div>
                            <div>
                                <div class="party-main right-note">{_cty}</div>
                                <div class="meta-sub right-note">&nbsp;</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    " ",
                    key=f"title_review_row_click_{_ti}",
                    type="tertiary",
                    use_container_width=True,
                    help="Open parcel title review",
                ):
                    open_property_review(str(_c["parcel_id"]))
            with row_view:
                with st.container(
                    height="stretch",
                    vertical_alignment="center",
                    horizontal_alignment="right",
                    gap=None,
                ):
                    if st.button("Open", key=f"title_review_pick_{_ti}", type="secondary"):
                        open_property_review(str(_c["parcel_id"]))

    _intake_cur = str(st.session_state.get("title_review_intake_query") or "").strip()
    _lfq = st.session_state.get("title_review_last_failed_query")
    if _lfq is not None and _lfq == _intake_cur:
        st.markdown(
            '<div class="section-subtitle" style="color:#5a6b7d;margin-top:0.35rem;">'
            "No matching parcel found in the current prototype dataset."
            "</div>",
            unsafe_allow_html=True,
        )
    st.stop()

# Search Records: draft text in st.form; committed query in session_state only updates on submit (Enter or button).
# Example chips pre-fill draft and set search_committed in the same run so results apply immediately.
with st.container(key="search_records_explore_band"):
    _sq_pending = st.session_state.pop("_search_records_example_pending", None)
    if _sq_pending is not None:
        _pq = str(_sq_pending).strip()
        st.session_state.search_query_draft = _pq
        st.session_state.search_committed = _pq

    with st.form("search_records_query_form", clear_on_submit=False, border=False):
        search_draft_raw = st.text_input(
            "Search",
            key="search_query_draft",
            placeholder="Party, address, parcel ID, or document number",
            label_visibility="collapsed",
            autocomplete="off",
        )
        _search_submitted = st.form_submit_button(
            "Search records",
            type="primary",
            width="content",
            key="search_records_form_submit",
        )

if _search_submitted:
    st.session_state.search_committed = (search_draft_raw or "").strip()

committed_stripped = str(st.session_state.get("search_committed") or "").strip()
draft_stripped = (search_draft_raw or "").strip()
query_text = committed_stripped.lower()
search_has_committed_query = len(committed_stripped) > 0

if not draft_stripped and not committed_stripped:
    st.markdown(
        """
        <div class="search-empty-wrap mode-explore">
            <p class="search-empty-eyebrow">Exploratory search</p>
            <div class="detail-section-title">Search recorded documents</div>
            <p class="search-empty-lead">Nothing is listed until you search. Enter a query to explore parties, document numbers, parcels, and addresses in the prototype index.</p>
            <p class="search-empty-examples-label">Sample queries</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="search_ex_chip_band"):
        _sex, _se_mid, _sex2 = st.columns([0.1, 0.8, 0.1])
        with _se_mid:
            _se_cols = st.columns(len(_SEARCH_RECORDS_EXAMPLE_QUERIES), gap="small")
            for _se_i, _se_q in enumerate(_SEARCH_RECORDS_EXAMPLE_QUERIES):
                with _se_cols[_se_i]:
                    st.button(
                        _se_q,
                        key=f"search_ex_{_se_i}",
                        type="tertiary",
                        on_click=queue_search_records_example_query,
                        args=(_se_q,),
                    )
    st.stop()

if not search_has_committed_query:
    st.stop()

left_col, right_col = st.columns([0.9, 2.35], gap="large")

with left_col:
    st.markdown('<div class="section-title">Filters</div><div class="section-subtitle">Narrow search results</div>', unsafe_allow_html=True)
    st.markdown('<div class="filter-label">Document Type</div>', unsafe_allow_html=True)
    selected_doc_types = st.multiselect("Document Type", options=doc_type_options, default=[], label_visibility="collapsed")
    st.markdown('<div class="filter-label">Date Range</div>', unsafe_allow_html=True)
    selected_date_range = st.date_input("Date Range", value=(date(2025, 12, 1), date(2026, 2, 28)), label_visibility="collapsed")
    st.markdown('<div class="filter-label">County</div>', unsafe_allow_html=True)
    selected_county = st.selectbox("County", options=county_options, index=0, label_visibility="collapsed")
    _ = (selected_doc_types, selected_date_range, selected_county)

# Filter pipeline: text match from last committed search only; then sidebar filters.
filtered_results = (
    search_records_text_matches(mock_results, query_text) if query_text else mock_results.copy()
)

if selected_doc_types:
    filtered_results = filtered_results[filtered_results["document_type"].isin(selected_doc_types)]

if selected_county and selected_county != "All counties":
    filtered_results = filtered_results[filtered_results["county"] == selected_county]

if isinstance(selected_date_range, (tuple, list)) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
else:
    start_date = end_date = selected_date_range
filtered_results = filtered_results[
    (filtered_results["recording_date_dt"] >= start_date)
    & (filtered_results["recording_date_dt"] <= end_date)
]

if not filtered_results.empty and st.session_state.selected_doc_number not in filtered_results["document_number"].tolist():
    st.session_state.selected_doc_number = filtered_results.iloc[0]["document_number"]
    st.session_state.selected_record = record_for_state(filtered_results.iloc[0])

with right_col:
    with st.container(key="results_header_toolbar"):
        h_left, h_right = st.columns([3.95, 1.05], gap="small")
        with h_right:
            with st.container(horizontal_alignment="right", vertical_alignment="center"):
                sort_option = st.selectbox(
                    "Sort",
                    options=["Newest first", "Oldest first"],
                    index=0,
                    label_visibility="collapsed",
                )
        _ = sort_option

        if sort_option == "Oldest first":
            filtered_results = filtered_results.sort_values("recording_date_dt", ascending=True)
        else:
            filtered_results = filtered_results.sort_values("recording_date_dt", ascending=False)

        with h_left:
            st.markdown(
                f'<div class="results-header"><div class="results-count">{len(filtered_results)} results</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="results-list-leader" aria-hidden="true"></div>', unsafe_allow_html=True)
    if filtered_results.empty:
        st.markdown(
            '<div class="section-subtitle" style="color:#5a6b7d;">No records match this search with the current filters. '
            "Try different keywords or adjust filters.</div>",
            unsafe_allow_html=True,
        )
    for _, row in filtered_results.iterrows():
        is_selected = row["document_number"] == st.session_state.selected_doc_number
        row_class = "result-row selected" if is_selected else "result-row"
        doc_tag_class = doc_type_tag_class(row["document_type"])
        _scan_lbl, _scan_mod = result_scan_status_badge(row, mock_results)
        _scan_class = f"result-status-badge {_scan_mod}"
        # One closed markdown for the row body avoids Streamlit rendering an empty open <div>
        # as a separate block (stray highlight bar above the row).
        row_main, row_view = st.columns([0.905, 0.095], gap="xxsmall")
        with row_main:
            st.markdown(
                f"""
                <div class="{row_class}">
                    <div class="result-grid">
                        <div>
                            <div class="result-tag-line">
                                <span class="{doc_tag_class}">{row["document_type"]}</span>
                                <span class="{_scan_class}">{html.escape(_scan_lbl)}</span>
                            </div>
                            <div class="date-subtle">{row["recording_date"]}</div>
                        </div>
                        <div>
                            <div class="party-main">{row["party"]}</div>
                            <div class="addr-sub">{row["address_parcel"]}</div>
                        </div>
                        <div>
                            <div class="party-main right-note">{row["county"]}</div>
                            <div class="meta-sub right-note">{row["summary"]}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Transparent full-width button pulled up over the row (CSS) — same navigation as Open
            if st.button(
                " ",
                key=f"row_click_{row['document_number']}",
                type="tertiary",
                use_container_width=True,
                help="Open record details",
            ):
                open_detail_view(record_for_state(row), detail_nav_source="search")
        with row_view:
            with st.container(
                height="stretch",
                vertical_alignment="center",
                horizontal_alignment="right",
                gap=None,
            ):
                if st.button("Open", key=f"row_{row['document_number']}", type="secondary"):
                    open_detail_view(record_for_state(row), detail_nav_source="search")
