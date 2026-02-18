"""
SNS トレンドダッシュボード — サイバーパンク・エディション
============================================================
TikTok / X / Instagram / Pinterest のトレンドを一覧表示。
Google Trends RSS + Google News RSS でリアルタイムに収集。
モバイル完全対応 — 外出先でもトレンドをチェック。
"""

import re
import urllib.parse
from datetime import datetime

import feedparser
import streamlit as st

# ──────────────────────────────────────────────
# ページ設定
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="SNS トレンドダッシュボード",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# プラットフォーム定義
# ──────────────────────────────────────────────
PLATFORMS = {
    "TikTok": {
        "icon": "🎵",
        "color": "#ff0050",
        "glow": "rgba(255,0,80,.5)",
        "queries_ja": ["TikTok トレンド", "TikTok バズ", "TikTok 話題"],
        "queries_en": ["TikTok trending", "TikTok viral", "TikTok trend"],
    },
    "X": {
        "icon": "𝕏",
        "color": "#1da1f2",
        "glow": "rgba(29,161,242,.5)",
        "queries_ja": ["Twitter トレンド", "X トレンド", "Twitter 話題"],
        "queries_en": ["Twitter trending", "X trending", "Twitter viral"],
    },
    "Instagram": {
        "icon": "📸",
        "color": "#e4405f",
        "glow": "rgba(228,64,95,.5)",
        "queries_ja": ["Instagram トレンド", "Instagram バズ", "Instagram 話題"],
        "queries_en": ["Instagram trending", "Instagram viral", "Instagram trend"],
    },
    "Pinterest": {
        "icon": "📌",
        "color": "#bd081c",
        "glow": "rgba(189,8,28,.5)",
        "queries_ja": ["Pinterest トレンド", "Pinterest 人気", "Pinterest 話題"],
        "queries_en": ["Pinterest trending", "Pinterest popular", "Pinterest trend"],
    },
}

REGIONS = {
    "🇯🇵 日本": {"hl": "ja", "gl": "JP", "ceid": "JP:ja", "geo": "JP", "lang": "ja"},
    "🇺🇸 アメリカ": {"hl": "en", "gl": "US", "ceid": "US:en", "geo": "US", "lang": "en"},
    "🌍 グローバル": {"hl": "en", "gl": "", "ceid": "US:en", "geo": "", "lang": "en"},
}

# ──────────────────────────────────────────────
# サイバーパンク CSS
# ──────────────────────────────────────────────
st.markdown(
    """
<style>
/* ═══════════════════════════════════════════════
   フォント & グローバル
   ═══════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');

:root {
    --neon-cyan:    #00f0ff;
    --neon-magenta: #ff2a6d;
    --neon-yellow:  #f5e642;
    --neon-green:   #05ffa1;
    --dark-bg:      #0a0a12;
    --panel-bg:     #0d0d1a;
    --card-bg:      rgba(13, 13, 26, .85);
    --border-glow:  rgba(0, 240, 255, .2);
    --text-primary: #e0e0f0;
    --text-muted:   #7a7a9e;
    /* プラットフォームカラー */
    --tiktok:    #ff0050;
    --x-blue:    #1da1f2;
    --instagram: #e4405f;
    --pinterest: #bd081c;
}

html, body, [class*="css"] {
    font-family: 'Rajdhani', 'Inter', sans-serif;
    color: var(--text-primary);
}

/* Streamlit メイン背景 */
.stApp {
    background: var(--dark-bg);
    background-image:
        radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0,240,255,.06) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 100%, rgba(255,42,109,.05) 0%, transparent 55%),
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0,240,255,.015) 2px,
            rgba(0,240,255,.015) 4px
        );
}

/* ─── スキャンライン CRT オーバーレイ ─── */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        rgba(0,0,0,.08) 0px,
        rgba(0,0,0,.08) 1px,
        transparent 1px,
        transparent 3px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ═══════════════════════════════════════════════
   ヘッダー
   ═══════════════════════════════════════════════ */
.cyber-header {
    position: relative;
    text-align: center;
    padding: 2.8rem 2rem 2.2rem;
    margin-bottom: 2rem;
    background:
        linear-gradient(135deg, rgba(0,240,255,.08), rgba(255,42,109,.06)),
        var(--panel-bg);
    border: 1px solid var(--border-glow);
    border-radius: 4px;
    overflow: hidden;
    clip-path: polygon(
        0 0, calc(100% - 28px) 0, 100% 28px,
        100% 100%, 28px 100%, 0 calc(100% - 28px)
    );
}
.cyber-header::before,
.cyber-header::after {
    content: '';
    position: absolute;
    width: 40px; height: 40px;
    border: 2px solid var(--neon-cyan);
    opacity: .5;
}
.cyber-header::before { top: 6px; left: 6px; border-right: none; border-bottom: none; }
.cyber-header::after  { bottom: 6px; right: 6px; border-left: none; border-top: none; }

.cyber-header h1 {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: .12em;
    color: var(--neon-cyan);
    text-shadow:
        0 0 8px rgba(0,240,255,.6),
        0 0 30px rgba(0,240,255,.3),
        0 0 60px rgba(0,240,255,.15);
    margin: 0 0 .4rem;
    animation: flicker 4s infinite alternate;
}
.cyber-header .subtitle {
    font-family: 'Share Tech Mono', monospace;
    color: var(--neon-magenta);
    font-size: .92rem;
    letter-spacing: .15em;
    text-transform: uppercase;
    text-shadow: 0 0 10px rgba(255,42,109,.5);
}
.header-line {
    height: 2px;
    margin: .8rem auto 0;
    width: 60%;
    background: linear-gradient(
        90deg,
        transparent 0%,
        var(--neon-cyan) 30%,
        var(--neon-magenta) 70%,
        transparent 100%
    );
    box-shadow: 0 0 8px rgba(0,240,255,.4);
}

@keyframes flicker {
    0%, 93%, 95%, 97%, 100% { opacity: 1; }
    94% { opacity: .85; }
    96% { opacity: .9; }
}

/* ═══════════════════════════════════════════════
   プラットフォーム統計バー
   ═══════════════════════════════════════════════ */
.platform-stats {
    display: flex;
    flex-wrap: wrap;
    gap: .8rem;
    margin-bottom: 1.8rem;
    justify-content: center;
}
.platform-chip {
    font-family: 'Share Tech Mono', monospace;
    font-size: .82rem;
    color: var(--text-muted);
    background: rgba(0,240,255,.04);
    border: 1px solid rgba(0,240,255,.15);
    padding: .55rem 1rem;
    clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px));
    text-shadow: 0 0 4px rgba(0,240,255,.25);
    transition: all .28s ease;
}
.platform-chip strong {
    text-shadow: 0 0 8px currentColor;
}
.platform-chip.tiktok  { border-left: 3px solid var(--tiktok);  }
.platform-chip.tiktok  strong { color: var(--tiktok); }
.platform-chip.x       { border-left: 3px solid var(--x-blue);  }
.platform-chip.x       strong { color: var(--x-blue); }
.platform-chip.insta   { border-left: 3px solid var(--instagram); }
.platform-chip.insta   strong { color: var(--instagram); }
.platform-chip.pin     { border-left: 3px solid var(--pinterest); }
.platform-chip.pin     strong { color: var(--pinterest); }

/* ═══════════════════════════════════════════════
   タブ — カスタムスタイル
   ═══════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(0,240,255,.03);
    border: 1px solid rgba(0,240,255,.1);
    border-radius: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Orbitron', sans-serif;
    font-size: .78rem;
    font-weight: 600;
    letter-spacing: .06em;
    color: var(--text-muted);
    background: transparent;
    border-radius: 3px;
    padding: .6rem 1.2rem;
    transition: all .28s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--neon-cyan);
    background: rgba(0,240,255,.08);
}
.stTabs [aria-selected="true"] {
    color: var(--neon-cyan) !important;
    background: rgba(0,240,255,.12) !important;
    text-shadow: 0 0 10px rgba(0,240,255,.5);
    box-shadow: 0 0 15px rgba(0,240,255,.15);
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--neon-cyan) !important;
    height: 2px !important;
    box-shadow: 0 0 8px rgba(0,240,255,.6);
}
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ═══════════════════════════════════════════════
   トレンドカード
   ═══════════════════════════════════════════════ */
.trend-card-link {
    display: block;
    text-decoration: none !important;
    color: inherit !important;
    margin-bottom: 1rem;
}
.trend-card {
    position: relative;
    background: var(--card-bg);
    border: 1px solid rgba(0,240,255,.12);
    padding: 1.5rem 1.4rem;
    transition: all .28s cubic-bezier(.25,.8,.25,1);
    clip-path: polygon(
        0 0, calc(100% - 16px) 0, 100% 16px,
        100% 100%, 16px 100%, 0 calc(100% - 16px)
    );
    overflow: hidden;
}
.trend-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    opacity: .35;
    transition: opacity .28s ease;
}
/* プラットフォームごとのストライプ色 */
.trend-card.tiktok::before  { background: linear-gradient(180deg, var(--tiktok), #00f2ea); }
.trend-card.x::before       { background: linear-gradient(180deg, var(--x-blue), #0d8bd9); }
.trend-card.insta::before   { background: linear-gradient(180deg, #833ab4, var(--instagram), #fd1d1d); }
.trend-card.pin::before     { background: linear-gradient(180deg, var(--pinterest), #e60023); }
.trend-card.overview::before { background: linear-gradient(180deg, var(--neon-cyan), var(--neon-magenta)); }

/* ホバー */
.trend-card-link:hover .trend-card {
    border-color: var(--neon-cyan);
    background: rgba(0, 240, 255, .06);
    transform: translateY(-4px) scale(1.005);
    box-shadow:
        0 0 12px rgba(0,240,255,.25),
        0 0 40px rgba(0,240,255,.08),
        inset 0 0 30px rgba(0,240,255,.03);
}
.trend-card-link:hover .trend-card::before { opacity: 1; box-shadow: 0 0 10px currentColor; }
.trend-card-link:hover .t-card-title { color: var(--neon-cyan) !important; text-shadow: 0 0 12px rgba(0,240,255,.5); }

/* カード内部 */
.t-card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: .8rem;
    margin-bottom: .5rem;
}
.t-card-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.08rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.45;
    transition: color .28s ease, text-shadow .28s ease;
    flex: 1;
}
.t-card-badge {
    font-family: 'Share Tech Mono', monospace;
    font-size: .65rem;
    padding: .2rem .55rem;
    border-radius: 2px;
    white-space: nowrap;
    letter-spacing: .06em;
    transition: all .28s ease;
}
.t-card-badge.tiktok  { background: rgba(255,0,80,.15); color: var(--tiktok); }
.t-card-badge.x       { background: rgba(29,161,242,.15); color: var(--x-blue); }
.t-card-badge.insta   { background: rgba(228,64,95,.15); color: var(--instagram); }
.t-card-badge.pin     { background: rgba(189,8,28,.15); color: var(--pinterest); }
.t-card-badge.trend   { background: rgba(0,240,255,.12); color: var(--neon-cyan); }

.trend-card-link:hover .t-card-badge {
    background: var(--neon-magenta);
    box-shadow: 0 0 10px rgba(255,42,109,.5);
    color: #fff;
}
.t-card-date {
    font-family: 'Share Tech Mono', monospace;
    font-size: .75rem;
    color: var(--neon-magenta);
    margin-bottom: .6rem;
    text-shadow: 0 0 6px rgba(255,42,109,.3);
    letter-spacing: .04em;
}
.t-card-summary {
    font-size: .88rem;
    color: var(--text-muted);
    line-height: 1.7;
}
.t-card-footer {
    margin-top: .8rem;
    display: flex;
    align-items: center;
    gap: .5rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: .72rem;
    color: rgba(0,240,255,.45);
    letter-spacing: .08em;
}
.t-card-footer .arrow {
    transition: transform .28s ease;
}
.trend-card-link:hover .t-card-footer .arrow {
    transform: translateX(6px);
    color: var(--neon-cyan);
}

/* ═══════════════════════════════════════════════
   トレンドランキング（Overview用）
   ═══════════════════════════════════════════════ */
.trend-rank {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.2rem;
    background: var(--card-bg);
    border: 1px solid rgba(0,240,255,.08);
    margin-bottom: .6rem;
    transition: all .25s ease;
    clip-path: polygon(
        0 0, calc(100% - 10px) 0, 100% 10px,
        100% 100%, 10px 100%, 0 calc(100% - 10px)
    );
}
.trend-rank:hover {
    border-color: rgba(0,240,255,.3);
    background: rgba(0,240,255,.04);
    transform: translateX(4px);
}
.trend-rank-num {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.4rem;
    font-weight: 900;
    color: var(--neon-cyan);
    text-shadow: 0 0 10px rgba(0,240,255,.5);
    min-width: 2.5rem;
    text-align: center;
}
.trend-rank-num.top3 {
    color: var(--neon-magenta);
    text-shadow: 0 0 12px rgba(255,42,109,.6);
}
.trend-rank-content {
    flex: 1;
}
.trend-rank-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.3;
}
.trend-rank-meta {
    font-family: 'Share Tech Mono', monospace;
    font-size: .7rem;
    color: var(--text-muted);
    margin-top: .2rem;
}
.trend-rank-platform {
    font-family: 'Share Tech Mono', monospace;
    font-size: .72rem;
    padding: .15rem .5rem;
    border-radius: 2px;
    white-space: nowrap;
}

/* ═══════════════════════════════════════════════
   セクションヘッダー
   ═══════════════════════════════════════════════ */
.section-header {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--neon-cyan);
    letter-spacing: .08em;
    margin-bottom: 1.2rem;
    padding-bottom: .6rem;
    border-bottom: 1px solid rgba(0,240,255,.15);
    text-shadow: 0 0 8px rgba(0,240,255,.3);
}

/* ═══════════════════════════════════════════════
   サイドバー
   ═══════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #08081a 0%, #0e0e20 100%);
    border-right: 1px solid rgba(0,240,255,.1) !important;
}
section[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 1px; height: 100%;
    background: linear-gradient(180deg, var(--neon-cyan), transparent 40%, var(--neon-magenta));
    opacity: .5;
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'Orbitron', sans-serif;
    color: var(--neon-cyan);
    font-size: 1rem;
    letter-spacing: .1em;
    text-shadow: 0 0 8px rgba(0,240,255,.4);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li {
    color: var(--text-muted);
    font-size: .85rem;
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] select {
    font-family: 'Share Tech Mono', monospace !important;
    background: rgba(0,240,255,.04) !important;
    border: 1px solid rgba(0,240,255,.2) !important;
    color: var(--neon-cyan) !important;
}
section[data-testid="stSidebar"] input:focus,
section[data-testid="stSidebar"] select:focus {
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 0 12px rgba(0,240,255,.25) !important;
}

/* ═══════════════════════════════════════════════
   空状態
   ═══════════════════════════════════════════════ */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
}
.empty-state .icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    filter: drop-shadow(0 0 12px rgba(0,240,255,.5));
}
.empty-state p {
    font-family: 'Share Tech Mono', monospace;
    color: var(--text-muted);
    font-size: .92rem;
    letter-spacing: .04em;
}

/* ═══════════════════════════════════════════════
   フッター
   ═══════════════════════════════════════════════ */
.cyber-footer {
    text-align: center;
    padding: 1.5rem 0 1rem;
    margin-top: 2.5rem;
    border-top: 1px solid rgba(0,240,255,.08);
    font-family: 'Share Tech Mono', monospace;
    font-size: .72rem;
    color: var(--text-muted);
    letter-spacing: .08em;
}
.cyber-footer .highlight {
    color: var(--neon-cyan);
    text-shadow: 0 0 6px rgba(0,240,255,.3);
}

/* ═══════════════════════════════════════════════
   グリッチ・アニメーション
   ═══════════════════════════════════════════════ */
.glitch-wrapper {
    position: relative;
    display: inline-block;
}
.glitch {
    position: relative;
    display: inline-block;
}
.glitch::before,
.glitch::after {
    content: attr(data-text);
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
}
.glitch::before {
    color: var(--neon-magenta);
    z-index: -1;
    animation: glitch-1 3s infinite linear alternate-reverse;
}
.glitch::after {
    color: var(--neon-green);
    z-index: -2;
    animation: glitch-2 2.5s infinite linear alternate-reverse;
}
@keyframes glitch-1 {
    0%, 90%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); }
    92% { clip-path: inset(20% 0 40% 0); transform: translate(-3px, 1px); }
    94% { clip-path: inset(60% 0 10% 0); transform: translate(3px, -1px); }
    96% { clip-path: inset(40% 0 30% 0); transform: translate(-2px, 0); }
    98% { clip-path: inset(10% 0 70% 0); transform: translate(2px, 1px); }
}
@keyframes glitch-2 {
    0%, 88%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); }
    90% { clip-path: inset(50% 0 20% 0); transform: translate(2px, -1px); }
    93% { clip-path: inset(10% 0 60% 0); transform: translate(-2px, 1px); }
    96% { clip-path: inset(70% 0 5% 0); transform: translate(1px, 0); }
}

/* パルス・ドット */
.pulse-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--neon-green);
    box-shadow: 0 0 6px var(--neon-green), 0 0 16px var(--neon-green);
    animation: pulse 2s ease-in-out infinite;
    margin-right: .4rem;
    vertical-align: middle;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: .5; transform: scale(.8); }
}

/* ═══════════════════════════════════════════════
   レスポンシブ — モバイル対応
   ═══════════════════════════════════════════════ */
@media screen and (max-width: 768px) {
    .cyber-header {
        padding: 1.6rem 1rem 1.2rem;
        margin-bottom: 1.2rem;
        clip-path: polygon(
            0 0, calc(100% - 14px) 0, 100% 14px,
            100% 100%, 14px 100%, 0 calc(100% - 14px)
        );
    }
    .cyber-header h1 {
        font-size: 1.15rem;
        letter-spacing: .06em;
    }
    .cyber-header .subtitle {
        font-size: .65rem;
        letter-spacing: .08em;
    }
    .cyber-header::before,
    .cyber-header::after {
        width: 24px; height: 24px;
    }
    .header-line { width: 80%; }

    /* 統計バー */
    .platform-stats {
        gap: .4rem;
    }
    .platform-chip {
        font-size: .7rem;
        padding: .35rem .7rem;
    }

    /* タブ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        padding: 3px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: .62rem;
        padding: .45rem .6rem;
        letter-spacing: .02em;
    }

    /* カード */
    .trend-card {
        padding: 1.1rem 1rem;
        clip-path: polygon(
            0 0, calc(100% - 10px) 0, 100% 10px,
            100% 100%, 10px 100%, 0 calc(100% - 10px)
        );
    }
    .t-card-title { font-size: .95rem; }
    .t-card-badge { font-size: .58rem; padding: .15rem .4rem; }
    .t-card-date  { font-size: .68rem; }
    .t-card-summary { font-size: .8rem; line-height: 1.6; }
    .t-card-footer  { font-size: .65rem; }

    /* ランキング */
    .trend-rank {
        padding: .8rem 1rem;
        gap: .6rem;
    }
    .trend-rank-num { font-size: 1.1rem; min-width: 2rem; }
    .trend-rank-title { font-size: .9rem; }

    /* セクションヘッダー */
    .section-header { font-size: .9rem; }

    /* Streamlit カラム → 1列化 */
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
    }
    [data-testid="stHorizontalBlock"] > div {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }

    /* フッター */
    .cyber-footer { font-size: .62rem; padding: 1rem 0 .8rem; }

    /* 空状態 */
    .empty-state { padding: 2.5rem 1rem; }
    .empty-state .icon { font-size: 2.2rem; }
    .empty-state p { font-size: .82rem; }
}

/* iPhone SE 等 */
@media screen and (max-width: 400px) {
    .cyber-header h1 { font-size: .95rem; }
    .cyber-header .subtitle { font-size: .55rem; }
    .t-card-title { font-size: .88rem; }
    .stTabs [data-baseweb="tab"] {
        font-size: .55rem;
        padding: .35rem .4rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# サイドバー
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌐 トレンド設定")

    region_label = st.selectbox(
        "リージョン",
        list(REGIONS.keys()),
        index=0,
        help="トレンドを取得する地域を選択",
    )
    region = REGIONS[region_label]

    period = st.radio(
        "期間",
        ["📅 今日", "📆 今週"],
        index=0,
        horizontal=True,
    )

    max_articles = st.slider("表示件数（各プラットフォーム）", min_value=5, max_value=30, value=10, step=5)

    st.markdown("---")
    st.markdown(
        """
        ### 📖 操作ガイド
        1. リージョン & 期間を設定
        2. タブで各SNSのトレンドを閲覧
        3. **カード全体**をタップで元記事へ
        """
    )
    st.markdown("---")
    st.markdown(
        """
        **🔧 テクノロジー**
        - Python / Streamlit
        - feedparser
        - Google News RSS
        - Google Trends RSS
        """
    )


# ──────────────────────────────────────────────
# データ取得
# ──────────────────────────────────────────────

def build_google_news_url(keyword: str, region: dict, when: str = "") -> str:
    """Google News RSS URL を構築"""
    encoded = urllib.parse.quote_plus(keyword)
    base = f"https://news.google.com/rss/search?q={encoded}"
    if when:
        base += f"+when:{when}"
    base += f"&hl={region['hl']}&gl={region['gl']}&ceid={region['ceid']}"
    return base


def build_google_trends_url(geo: str) -> str:
    """Google Trends デイリートレンド RSS URL を構築"""
    url = "https://trends.google.com/trending/rss?geo="
    url += geo if geo else "US"
    return url


@st.cache_data(ttl=600, show_spinner=False)
def fetch_google_trends(geo: str) -> list[dict]:
    """Google Trends RSS からトレンドワードを取得"""
    url = build_google_trends_url(geo)
    feed = feedparser.parse(url)
    trends = []
    for entry in feed.entries[:30]:
        title = entry.get("title", "")
        traffic = ""
        # ht:approx_traffic タグからトラフィック量を取得
        if hasattr(entry, "ht_approx_traffic"):
            traffic = entry.ht_approx_traffic
        elif hasattr(entry, "ht_picture"):
            pass  # 画像URLは無視

        link = entry.get("link", "#")
        published = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                dt = datetime(*entry.published_parsed[:6])
                published = dt.strftime("%Y.%m.%d  %H:%M")
            except Exception:
                published = getattr(entry, "published", "")
        else:
            published = getattr(entry, "published", "")

        summary = getattr(entry, "summary", "")
        summary = re.sub(r"<[^>]+>", "", summary).strip()

        trends.append({
            "title": title,
            "link": link,
            "published": published,
            "traffic": traffic,
            "summary": summary,
        })
    return trends


@st.cache_data(ttl=600, show_spinner=False)
def fetch_platform_news(platform: str, region: dict, period_key: str, limit: int) -> list[dict]:
    """各SNSプラットフォームのトレンドニュースを Google News RSS から取得"""
    when = "1d" if period_key == "today" else "7d"
    lang = region.get("lang", "en")
    platform_cfg = PLATFORMS[platform]

    queries = platform_cfg["queries_ja"] if lang == "ja" else platform_cfg["queries_en"]

    all_articles = []
    seen_titles = set()

    for query in queries:
        url = build_google_news_url(query, region, when)
        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = entry.get("title", "タイトルなし")
            if title in seen_titles:
                continue
            seen_titles.add(title)

            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    published = dt.strftime("%Y.%m.%d  %H:%M")
                except Exception:
                    published = getattr(entry, "published", "")
            else:
                published = getattr(entry, "published", "")

            summary = getattr(entry, "summary", "")
            summary = re.sub(r"<[^>]+>", "", summary).strip()

            all_articles.append({
                "title": title,
                "link": entry.get("link", "#"),
                "published": published,
                "summary": summary if summary else "要約情報なし",
                "platform": platform,
            })

            if len(all_articles) >= limit:
                break
        if len(all_articles) >= limit:
            break

    return all_articles[:limit]


# ──────────────────────────────────────────────
# ヘルパー: カード描画
# ──────────────────────────────────────────────

def render_trend_card(article: dict, platform_key: str, badge_text: str):
    """トレンドカードを描画"""
    css_class = {
        "TikTok": "tiktok",
        "X": "x",
        "Instagram": "insta",
        "Pinterest": "pin",
        "overview": "overview",
    }.get(platform_key, "overview")

    st.markdown(
        f"""
        <a href="{article['link']}" target="_blank" rel="noopener noreferrer" class="trend-card-link">
            <div class="trend-card {css_class}">
                <div class="t-card-top">
                    <div class="t-card-title">{article['title']}</div>
                    <span class="t-card-badge {css_class}">{badge_text}</span>
                </div>
                <div class="t-card-date">▸ {article['published']}</div>
                <div class="t-card-summary">{article['summary']}</div>
                <div class="t-card-footer">
                    <span>元記事を表示</span>
                    <span class="arrow">▸▸</span>
                </div>
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(message: str):
    """空状態を描画"""
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="icon">📡</div>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# メインコンテンツ
# ──────────────────────────────────────────────

# ヘッダー
st.markdown(
    """
    <div class="cyber-header">
        <h1>
            <span class="glitch-wrapper">
                <span class="glitch" data-text="SNS TRENDS">SNS TRENDS</span>
            </span>
        </h1>
        <div class="subtitle">
            <span class="pulse-dot"></span>
            TikTok × X × Instagram × Pinterest — トレンドデータリンク稼働中
        </div>
        <div class="header-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# データ取得
period_key = "today" if "今日" in period else "week"

with st.spinner("⚡ 各SNSプラットフォームのトレンドデータを同期中..."):
    # Google Trends
    google_trends = fetch_google_trends(region["geo"])

    # 各プラットフォームのニュース
    platform_data = {}
    for pname in PLATFORMS:
        platform_data[pname] = fetch_platform_news(pname, region, period_key, max_articles)

# 統計バー
total_articles = sum(len(v) for v in platform_data.values())
st.markdown(
    f"""
    <div class="platform-stats">
        <div class="platform-chip tiktok">🎵 TikTok：<strong>{len(platform_data.get('TikTok', []))}</strong></div>
        <div class="platform-chip x">𝕏 X：<strong>{len(platform_data.get('X', []))}</strong></div>
        <div class="platform-chip insta">📸 Instagram：<strong>{len(platform_data.get('Instagram', []))}</strong></div>
        <div class="platform-chip pin">📌 Pinterest：<strong>{len(platform_data.get('Pinterest', []))}</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# タブ
tabs = st.tabs(["📊 OVERVIEW", "🎵 TIKTOK", "𝕏 X", "📸 INSTAGRAM", "📌 PINTEREST"])

# ─── OVERVIEW タブ ───
with tabs[0]:
    # Google Trends ランキング
    if google_trends:
        st.markdown('<div class="section-header">🔥 急上昇トレンド — Google Trends</div>', unsafe_allow_html=True)
        for i, trend in enumerate(google_trends[:10], 1):
            num_class = "top3" if i <= 3 else ""
            traffic_html = f'<span class="trend-rank-meta">📈 {trend["traffic"]}</span>' if trend["traffic"] else ""
            st.markdown(
                f"""
                <a href="{trend['link']}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;color:inherit;">
                    <div class="trend-rank">
                        <div class="trend-rank-num {num_class}">{i:02d}</div>
                        <div class="trend-rank-content">
                            <div class="trend-rank-title">{trend['title']}</div>
                            {traffic_html}
                        </div>
                    </div>
                </a>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # 各プラットフォームのハイライト
    st.markdown('<div class="section-header">⚡ プラットフォーム別ハイライト</div>', unsafe_allow_html=True)
    for pname, pconfig in PLATFORMS.items():
        articles = platform_data.get(pname, [])
        if articles:
            st.markdown(
                f'<div style="font-family:\'Orbitron\',sans-serif;font-size:.85rem;'
                f'color:{pconfig["color"]};letter-spacing:.06em;margin:1rem 0 .6rem;'
                f'text-shadow:0 0 8px {pconfig["glow"]};">'
                f'{pconfig["icon"]} {pname.upper()}</div>',
                unsafe_allow_html=True,
            )
            cols = st.columns(2, gap="medium")
            for idx, article in enumerate(articles[:4]):
                with cols[idx % 2]:
                    render_trend_card(article, pname, pname.upper())

# ─── 各プラットフォームタブ ───
for tab_idx, (pname, pconfig) in enumerate(PLATFORMS.items(), 1):
    with tabs[tab_idx]:
        articles = platform_data.get(pname, [])
        period_label = "今日" if period_key == "today" else "今週"

        st.markdown(
            f'<div class="section-header">'
            f'{pconfig["icon"]} {pname} — {period_label}のトレンド ({region_label})</div>',
            unsafe_allow_html=True,
        )

        if articles:
            cols = st.columns(2, gap="medium")
            for idx, article in enumerate(articles):
                with cols[idx % 2]:
                    render_trend_card(article, pname, pname.upper())
        else:
            render_empty_state(
                f"{pname} のトレンドデータが見つかりませんでした。<br>"
                f"リージョンや期間を変更して再検索してください。"
            )

# フッター
st.markdown(
    f"""
    <div class="cyber-footer">
        <span class="highlight">STREAMLIT</span> × <span class="highlight">FEEDPARSER</span>
        &nbsp;|&nbsp; データソース: <span class="highlight">GOOGLE TRENDS</span> + <span class="highlight">GOOGLE NEWS RSS</span>
        &nbsp;|&nbsp; {datetime.now().strftime("%Y.%m.%d")}
    </div>
    """,
    unsafe_allow_html=True,
)
