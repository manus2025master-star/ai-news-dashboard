"""
AI ニュース収集ダッシュボード — サイバーパンク・エディション
============================================================
Google News RSS × feedparser でリアルタイムにニュースを収集。
ネオン × グリッチ × CRT 風の没入型サイバーパンク UI。
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
    page_title="AI ニュースダッシュボード",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
/* 角のアクセント */
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
/* 横線ディバイダ */
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
   統計バー
   ═══════════════════════════════════════════════ */
.stats-bar {
    display: flex;
    flex-wrap: wrap;
    gap: .8rem;
    margin-bottom: 1.8rem;
}
.stat-chip {
    font-family: 'Share Tech Mono', monospace;
    font-size: .82rem;
    color: var(--text-muted);
    background: rgba(0,240,255,.04);
    border: 1px solid rgba(0,240,255,.15);
    border-left: 3px solid var(--neon-cyan);
    padding: .55rem 1rem;
    clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px));
    text-shadow: 0 0 4px rgba(0,240,255,.25);
}
.stat-chip strong {
    color: var(--neon-cyan);
    text-shadow: 0 0 8px rgba(0,240,255,.5);
}

/* ═══════════════════════════════════════════════
   ニュースカード — 全体クリック可能
   ═══════════════════════════════════════════════ */
.news-card-link {
    display: block;
    text-decoration: none !important;
    color: inherit !important;
    margin-bottom: 1rem;
}

.news-card {
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

/* 左ストライプ */
.news-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, var(--neon-cyan), var(--neon-magenta));
    opacity: .35;
    transition: opacity .28s ease;
}

/* ───── ホバー ───── */
.news-card-link:hover .news-card {
    border-color: var(--neon-cyan);
    background: rgba(0, 240, 255, .06);
    transform: translateY(-4px) scale(1.005);
    box-shadow:
        0 0 12px rgba(0,240,255,.25),
        0 0 40px rgba(0,240,255,.08),
        inset 0 0 30px rgba(0,240,255,.03);
}
.news-card-link:hover .news-card::before {
    opacity: 1;
    box-shadow: 0 0 10px var(--neon-cyan);
}
.news-card-link:hover .card-title {
    color: var(--neon-cyan) !important;
    text-shadow: 0 0 12px rgba(0,240,255,.5);
}
.news-card-link:hover .card-badge {
    background: var(--neon-magenta);
    box-shadow: 0 0 10px rgba(255,42,109,.5);
    color: #fff;
}

/* カード内部 */
.card-top-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: .8rem;
    margin-bottom: .5rem;
}
.card-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.08rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.45;
    transition: color .28s ease, text-shadow .28s ease;
    flex: 1;
}
.card-badge {
    font-family: 'Share Tech Mono', monospace;
    font-size: .65rem;
    background: rgba(0,240,255,.12);
    color: var(--neon-cyan);
    padding: .2rem .55rem;
    border-radius: 2px;
    white-space: nowrap;
    letter-spacing: .06em;
    transition: all .28s ease;
}
.card-date {
    font-family: 'Share Tech Mono', monospace;
    font-size: .75rem;
    color: var(--neon-magenta);
    margin-bottom: .6rem;
    text-shadow: 0 0 6px rgba(255,42,109,.3);
    letter-spacing: .04em;
}
.card-summary {
    font-size: .88rem;
    color: var(--text-muted);
    line-height: 1.7;
}
.card-footer {
    margin-top: .8rem;
    display: flex;
    align-items: center;
    gap: .5rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: .72rem;
    color: rgba(0,240,255,.45);
    letter-spacing: .08em;
}
.card-footer .arrow {
    transition: transform .28s ease;
}
.news-card-link:hover .card-footer .arrow {
    transform: translateX(6px);
    color: var(--neon-cyan);
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

/* サイドバー入力欄 */
section[data-testid="stSidebar"] input {
    font-family: 'Share Tech Mono', monospace !important;
    background: rgba(0,240,255,.04) !important;
    border: 1px solid rgba(0,240,255,.2) !important;
    color: var(--neon-cyan) !important;
}
section[data-testid="stSidebar"] input:focus {
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
   グリッチ・アニメーション（ヘッダー用）
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

/* ═══════════════════════════════════════════════
   パルス・ドット（ライブインジケーター）
   ═══════════════════════════════════════════════ */
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
    /* ヘッダー縮小 */
    .cyber-header {
        padding: 1.6rem 1rem 1.2rem;
        margin-bottom: 1.2rem;
        clip-path: polygon(
            0 0, calc(100% - 14px) 0, 100% 14px,
            100% 100%, 14px 100%, 0 calc(100% - 14px)
        );
    }
    .cyber-header h1 {
        font-size: 1.2rem;
        letter-spacing: .06em;
    }
    .cyber-header .subtitle {
        font-size: .7rem;
        letter-spacing: .08em;
    }
    .cyber-header::before,
    .cyber-header::after {
        width: 24px; height: 24px;
    }
    .header-line {
        width: 80%;
    }

    /* 統計バー — 縦積み */
    .stats-bar {
        flex-direction: column;
        gap: .5rem;
    }
    .stat-chip {
        font-size: .72rem;
        padding: .4rem .8rem;
    }

    /* ニュースカード */
    .news-card {
        padding: 1.1rem 1rem;
        clip-path: polygon(
            0 0, calc(100% - 10px) 0, 100% 10px,
            100% 100%, 10px 100%, 0 calc(100% - 10px)
        );
    }
    .card-title {
        font-size: .95rem;
    }
    .card-badge {
        font-size: .58rem;
        padding: .15rem .4rem;
    }
    .card-date {
        font-size: .68rem;
    }
    .card-summary {
        font-size: .8rem;
        line-height: 1.6;
    }
    .card-footer {
        font-size: .65rem;
    }

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
    .cyber-footer {
        font-size: .62rem;
        padding: 1rem 0 .8rem;
    }

    /* 空状態 */
    .empty-state {
        padding: 2.5rem 1rem;
    }
    .empty-state .icon {
        font-size: 2.2rem;
    }
    .empty-state p {
        font-size: .82rem;
    }
}

/* さらに小さい画面 (iPhone SE 等) */
@media screen and (max-width: 400px) {
    .cyber-header h1 {
        font-size: 1rem;
    }
    .cyber-header .subtitle {
        font-size: .6rem;
    }
    .card-title {
        font-size: .88rem;
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
    st.markdown("## ⚡ 検索設定")
    query = st.text_input(
        "キーワード入力",
        value="Artificial Intelligence",
        help="Google News で検索するキーワードを入力してください",
    )
    max_articles = st.slider("表示件数", min_value=5, max_value=50, value=20, step=5)
    st.markdown("---")
    st.markdown(
        """
        ### � 操作ガイド
        1. キーワードを入力して **Enter**
        2. 最新ニュースがカードで表示されます
        3. **カード全体**をクリックで元記事へ
        """
    )
    st.markdown("---")
    st.markdown(
        """
        **� テクノロジー**
        - Python / Streamlit
        - feedparser
        - Google News RSS
        """
    )

# ──────────────────────────────────────────────
# RSS 取得
# ──────────────────────────────────────────────

def build_google_news_url(keyword: str) -> str:
    """Google News RSS の URL をキーワードから動的生成"""
    encoded = urllib.parse.quote_plus(keyword)
    return f"https://news.google.com/rss/search?q={encoded}&hl=ja&gl=JP&ceid=JP:ja"


@st.cache_data(ttl=600, show_spinner=False)
def fetch_news(keyword: str, limit: int) -> list[dict]:
    """RSS フィードを取得し、整形されたリストを返す"""
    url = build_google_news_url(keyword)
    feed = feedparser.parse(url)

    articles: list[dict] = []
    for entry in feed.entries[:limit]:
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

        articles.append(
            {
                "title": entry.get("title", "タイトルなし"),
                "link": entry.get("link", "#"),
                "published": published,
                "summary": summary if summary else "要約情報なし",
            }
        )
    return articles


# ──────────────────────────────────────────────
# メインコンテンツ
# ──────────────────────────────────────────────

# ヘッダー
st.markdown(
    """
    <div class="cyber-header">
        <h1>
            <span class="glitch-wrapper">
                <span class="glitch" data-text="AI NEWS DASHBOARD">AI NEWS DASHBOARD</span>
            </span>
        </h1>
        <div class="subtitle">
            <span class="pulse-dot"></span>
            GOOGLE NEWS RSS リアルタイムフィード — ニューラルリンク接続中
        </div>
        <div class="header-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# データ取得
if query.strip():
    with st.spinner("⚡ データリンク同期中..."):
        articles = fetch_news(query.strip(), max_articles)

    # 統計バー
    st.markdown(
        f"""
        <div class="stats-bar">
            <div class="stat-chip">🔎 検索ワード：<strong>{query}</strong></div>
            <div class="stat-chip">📰 取得件数：<strong>{len(articles)}</strong></div>
            <div class="stat-chip">🕒 最終同期：<strong>{datetime.now().strftime("%H:%M:%S")}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if articles:
        # 2 カラムレイアウト
        cols = st.columns(2, gap="medium")
        for idx, article in enumerate(articles):
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <a href="{article["link"]}" target="_blank" rel="noopener noreferrer" class="news-card-link">
                        <div class="news-card">
                            <div class="card-top-row">
                                <div class="card-title">{article["title"]}</div>
                                <span class="card-badge">NEWS</span>
                            </div>
                            <div class="card-date">▸ {article["published"]}</div>
                            <div class="card-summary">{article["summary"]}</div>
                            <div class="card-footer">
                                <span>元記事を表示</span>
                                <span class="arrow">▸▸</span>
                            </div>
                        </div>
                    </a>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">�</div>
                <p>該当データが見つかりませんでした。<br>別のキーワードで再検索してください。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """
        <div class="empty-state">
            <div class="icon">🔍</div>
            <p>サイドバーにキーワードを入力して検索を開始してください。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# フッター
st.markdown(
    f"""
    <div class="cyber-footer">
        <span class="highlight">STREAMLIT</span> × <span class="highlight">FEEDPARSER</span>
        &nbsp;|&nbsp; データソース: <span class="highlight">GOOGLE NEWS RSS</span>
        &nbsp;|&nbsp; {datetime.now().strftime("%Y.%m.%d")}
    </div>
    """,
    unsafe_allow_html=True,
)
