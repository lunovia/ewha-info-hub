import streamlit as st
import streamlit.components.v1 as components
import requests
import re
import os
from bs4 import BeautifulSoup
from groq import Groq

st.set_page_config(page_title="이화여대 정보 통합", page_icon="🌱", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "home"
if "profile" not in st.session_state:
    st.session_state.profile = None
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []
if "notification_settings" not in st.session_state:
    st.session_state.notification_settings = {"장학금": True, "교환학생": True, "프로그램/취업": True}
if "editing_profile" not in st.session_state:
    st.session_state.editing_profile = False
if "selected_notice" not in st.session_state:
    st.session_state.selected_notice = None

if st.session_state.page == "home":
    st.markdown("""
    <style>
        .stApp { background-color: #e8f5e9; }
        h1, h2, h3, p, span, label { color: #000000 !important; }

        /* 모든 버튼 기본: 카드 스타일 */
        div[data-testid="stButton"] > button {
            width: 100% !important;
            height: 110px !important;
            min-height: 110px !important;
            max-height: 110px !important;
            background-color: #ffffff !important;
            border: 2px solid #a5d6a7 !important;
            border-radius: 16px !important;
            font-size: 20px !important;
            font-weight: bold !important;
            color: #000000 !important;
            overflow: hidden !important;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #c8e6c9 !important;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background-color: #e8f5e9; }
        h1, h2, h3, p, span, label, b, strong, small, .caption { color: #000000 !important; }
        div[data-testid="stCaptionContainer"] p { color: #000000 !important; }
        .notice-item, .notice-item * { color: #000000 !important; }

        /* 뒤로가기 버튼 — 박스 없는 텍스트 스타일 */
        div[data-testid="stHorizontalBlock"]:first-of-type button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #2e7d32 !important;
            font-size: 16px !important;
            font-weight: bold !important;
            padding: 0 !important;
            height: auto !important;
            min-height: 0 !important;
        }
        div[data-testid="stHorizontalBlock"]:first-of-type button:hover {
            text-decoration: underline !important;
            background: transparent !important;
        }

        /* 저장 버튼 */
        div[data-testid="stHorizontalBlock"]:first-of-type ~ div button {
            border-radius: 10px !important;
        }
        button:disabled {
            background-color: #ffffff !important;
            color: #cccccc !important;
            border: 1px solid #eeeeee !important;
            cursor: not-allowed !important;
        }
        button:not(:disabled).save-btn {
            background-color: #ffffff !important;
            color: #2e7d32 !important;
            border: 2px solid #a5d6a7 !important;
        }
        .notice-item {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 18px 22px;
            margin: 10px 0;
            border-left: 5px solid #66bb6a;
        }

        /* 원본 공지 보러가기 버튼 */
        div[data-testid="stLinkButton"] a {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #2e7d32 !important;
            border-radius: 8px !important;
        }

        /* 일반 버튼 (저장 등) — 뒤로가기 제외 */
        div[data-testid="stHorizontalBlock"]:first-of-type ~ div div[data-testid="stButton"] > button:not(:disabled) {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #2e7d32 !important;
        }

        /* 뒤로가기 버튼 — 박스 없이 텍스트만 */
        div[data-testid="stHorizontalBlock"]:first-of-type div[data-testid="stButton"] > button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #2e7d32 !important;
            font-size: 16px !important;
            font-weight: bold !important;
            padding: 0 !important;
            height: auto !important;
            min-height: 0 !important;
            text-decoration: none !important;
        }
        div[data-testid="stHorizontalBlock"]:first-of-type div[data-testid="stButton"] > button:hover {
            text-decoration: underline !important;
            background: transparent !important;
            border: none !important;
        }

        /* 텍스트 입력창 — 셀렉트박스와 동일한 스타일 */
        div[data-testid="stTextInput"] > div {
            background-color: #ffffff !important;
            border: 1px solid #2e7d32 !important;
            border-radius: 8px !important;
        }
        div[data-testid="stTextInput"] input {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: none !important;
        }
        div[data-testid="stTextInput"] input::placeholder {
            color: #aaaaaa !important;
        }

        /* 셀렉트박스 — 가장 바깥 div만 */
        div[data-testid="stSelectbox"] > div > div:first-child {
            background-color: #ffffff !important;
            border: 1px solid #2e7d32 !important;
            border-radius: 8px !important;
        }

        /* 멀티셀렉트 */
        div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:first-child {
            background-color: #ffffff !important;
            border: 1px solid #2e7d32 !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="tag"] {
            background-color: #e8f5e9 !important;
            border-radius: 4px !important;
        }
        div[data-baseweb="tag"] span {
            color: #2e7d32 !important;
        }

        /* 체크박스 */
        div[data-testid="stCheckbox"] input[type="checkbox"] {
            accent-color: #2e7d32 !important;
        }
    </style>
    """, unsafe_allow_html=True)

COLLEGES = [
    "선택 안 함", "인문과학대학", "사회과학대학", "자연과학대학", "엘텍공과대학",
    "사범대학", "음악대학", "조형예술대학", "체육과학부",
    "의과대학", "약학대학", "간호과학대학", "경영대학", "신산업융합대학", "인공지능대학"
]
INTERESTS = ["장학금", "교환학생/해외", "취업/인턴", "창업", "연구", "봉사/사회활동", "문화/예술", "프로그램"]

@st.cache_data(ttl=3600)
def get_scholarship_notices():
    BASE = "https://www.ewha.ac.kr/ewha/bachelor/scholarship-notice.do"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(BASE, headers=headers)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table tbody tr")
    notices = []
    for row in rows:
        cells = row.select("td")
        if not cells:
            continue
        title_tag = cells[1].select_one("a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        date = cells[2].get_text(strip=True) if len(cells) > 2 else ""
        href = title_tag.get("href", "")
        link = BASE + href if href.startswith("?") else href
        notices.append({"제목": title, "신청기간": date, "링크": link})
    return notices

@st.cache_data(ttl=3600)
def get_exchange_notices():
    DOMAIN = "https://oia.ewha.ac.kr"
    URL = f"{DOMAIN}/oia/1136/subview.do"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    notices = []
    for item in soup.select("ul.artclList li"):
        title_tag = item.select_one(".artclTitle strong")
        date_tag = item.select_one("dl dd")
        a_tag = item.select_one("a.artclLinkView")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        date = date_tag.get_text(strip=True) if date_tag else ""
        href = a_tag.get("href", "") if a_tag else ""
        link = DOMAIN + href if href.startswith("/") else href
        if title:
            notices.append({"제목": title, "날짜": date, "링크": link})
    return notices

@st.cache_data(ttl=3600)
def get_job_notices():
    BASE = "https://job.ewha.ac.kr/job/intro/Information-notice.do"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(BASE, headers=headers)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    notices = []
    for item in soup.select(".b-poster ul li"):
        title_tag = item.select_one(".b-title-box a")
        date_tags = item.select(".b-date span")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        date = date_tags[-1].get_text(strip=True) if len(date_tags) >= 2 else ""
        href = title_tag.get("href", "")
        link = BASE + href if href.startswith("?") else href
        if title:
            notices.append({"제목": title, "날짜": date, "링크": link})
    return notices

def fetch_notice_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        for selector in [".artclView", ".b-view-content", ".view-content", ".board-view", "article .content", ".artclContent"]:
            el = soup.select_one(selector)
            if el:
                return el.get_text(" ", strip=True)[:3000]
        return ""
    except:
        return ""

def get_ai_summary(title, content):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None, "GROQ_API_KEY가 설정되지 않았어요."
    try:
        client = Groq(api_key=api_key)
        context = f"제목: {title}\n내용: {content}" if content else f"제목: {title}"
        prompt = f"""다음 이화여대 공지를 아래 형식으로 정리해줘. 해당 항목이 없으면 '-'로 표시해.
모든 내용은 반드시 한국어로만 작성하고, 한자·영어·일본어 등 다른 언어가 포함된 경우 한국어로 번역해줘.

📋 주요 내용: (핵심 내용 1~2줄)
📌 대상: (지원 가능한 학생)
📅 신청 기간: (접수 기간)
✅ 지원 자격: (필수 요건)

공지:
{context}"""
        result = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        return result.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

def show_notices(notices, date_key="날짜", category=""):
    if notices:
        st.write(f"총 **{len(notices)}개** 공지")
        for i, notice in enumerate(notices):
            date_val = notice.get(date_key, "") or notice.get("신청기간", "")
            is_bookmarked = any(b["제목"] == notice["제목"] for b in st.session_state.bookmarks)
            col_notice, col_detail, col_btn = st.columns([10, 1, 1])
            with col_notice:
                st.markdown(f"""
                <div class="notice-item">
                    <b>{notice['제목']}</b><br>
                    <span style="font-size: 14px;">📅 {date_val if date_val else '-'}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_detail:
                st.write("")
                if st.button("🔍", key=f"detail_{category}_{i}"):
                    st.session_state.selected_notice = {**notice, "카테고리": category, "date_key": date_key}
                    st.session_state.page = "detail"
                    st.rerun()
            with col_btn:
                st.write("")
                if st.button("⭐" if is_bookmarked else "☆", key=f"bm_{category}_{i}"):
                    if is_bookmarked:
                        st.session_state.bookmarks = [b for b in st.session_state.bookmarks if b["제목"] != notice["제목"]]
                    else:
                        st.session_state.bookmarks.append({**notice, "카테고리": category})
                    st.rerun()
    else:
        st.info("공지를 불러오는 중입니다...")

# ── 홈 화면 ──────────────────────────────────────────
if st.session_state.page == "home":
    col_title, col_profile = st.columns([10, 1])
    with col_title:
        st.title("🌱 이화여대 정보 허브")
    with col_profile:
        st.write("")
        if st.button("👤"):
            st.session_state.page = "profile"
            st.rerun()

    # 👤 버튼 박스 제거 — JS로 직접 스타일 적용
    components.html("""
    <script>
    setTimeout(function() {
        const buttons = window.parent.document.querySelectorAll('button');
        buttons.forEach(function(btn) {
            if (btn.innerText.trim() === '👤') {
                btn.style.setProperty('background', 'transparent', 'important');
                btn.style.setProperty('border', 'none', 'important');
                btn.style.setProperty('box-shadow', 'none', 'important');
                btn.style.setProperty('height', 'auto', 'important');
                btn.style.setProperty('min-height', '0', 'important');
                btn.style.setProperty('font-size', '24px', 'important');
                btn.style.setProperty('padding', '4px', 'important');
                const inner = btn.querySelector('p') || btn;
                btn.onmouseover = function() {
                    inner.style.borderBottom = '2px solid #000';
                };
                btn.onmouseout = function() {
                    inner.style.borderBottom = 'none';
                };
            }
        });
    }, 300);
    </script>
    """, height=0)

    if st.session_state.profile:
        p = st.session_state.profile
        st.caption(f"👋 {p['아이디']}님 · {p['학년']} · {p['단과대학']}")

    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎓  장학금", use_container_width=True):
            st.session_state.page = "scholarship"
            st.rerun()
    with col2:
        if st.button("🌍  교환학생", use_container_width=True):
            st.session_state.page = "exchange"
            st.rerun()
    with col3:
        if st.button("💼  프로그램/취업", use_container_width=True):
            st.session_state.page = "job"
            st.rerun()

    st.write("")
    st.markdown("""
    <p style="text-align:center; font-size:12px; color:#888888;">
    🌱 이 서비스는 이화여대 재학생이 만든 비공식 정보 모음 서비스입니다.<br>
    학교 공식 서비스가 아니며, 정확한 정보는 각 공식 사이트를 확인해주세요.
    </p>
    """, unsafe_allow_html=True)

# ── 마이페이지 ──────────────────────────────────────
elif st.session_state.page == "profile":
    col_back, _ = st.columns([1, 9])
    with col_back:
        if st.button("← 뒤로"):
            st.session_state.page = "home"
            st.rerun()

    st.title("👤 마이페이지")
    st.write("")

    tab1, tab2, tab3 = st.tabs(["📋 내 프로필", "🔖 찜한 정보", "🔔 알림 설정"])

    # ── 탭1: 내 프로필 ──
    with tab1:
        st.write("")
        if st.session_state.profile and not st.session_state.editing_profile:
            p = st.session_state.profile
            st.markdown(f"""
            <div style="background:#ffffff; border:1px solid #2e7d32; border-radius:12px; padding:24px 28px;">
                <p style="margin:8px 0;"><b>아이디</b> &nbsp;&nbsp;&nbsp;&nbsp; {p['아이디']}</p>
                <p style="margin:8px 0;"><b>학년</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {p['학년']}</p>
                <p style="margin:8px 0;"><b>단과대학</b> &nbsp; {p['단과대학']}</p>
                <p style="margin:8px 0;"><b>전공</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {p['전공']}</p>
                <p style="margin:8px 0;"><b>이메일</b> &nbsp;&nbsp;&nbsp;&nbsp; {p['이메일']}</p>
                <p style="margin:8px 0;"><b>관심분야</b> &nbsp; {', '.join(p['관심분야']) if p['관심분야'] else '없음'}</p>
                <p style="margin:8px 0;"><b>이메일 알림</b> &nbsp; {'✅ 수신' if p.get('이메일알림') else '❌ 미수신'}</p>
            </div>
            """, unsafe_allow_html=True)
            st.write("")
            if st.button("✏️ 수정하기"):
                st.session_state.editing_profile = True
                st.rerun()
        else:
            p = st.session_state.profile or {}
            user_id  = st.text_input("아이디 *", value=p.get("아이디", ""), placeholder="영어, 숫자만 입력 가능")
            grade    = st.selectbox("학년 *", ["1학년", "2학년", "3학년", "4학년"],
                                    index=["1학년","2학년","3학년","4학년"].index(p["학년"]) if p.get("학년") else 0)
            college  = st.selectbox("단과대학 *", COLLEGES,
                                    index=COLLEGES.index(p["단과대학"]) if p.get("단과대학") else 0)
            major    = st.text_input("전공 *", value=p.get("전공", ""), placeholder="전공을 입력해주세요")
            col_email, col_domain = st.columns([3, 2])
            with col_email:
                email_prefix = st.text_input("학교 이메일 *",
                                             value=p.get("이메일", "").replace("@ewha.ac.kr", ""),
                                             placeholder="이메일 앞부분 입력")
            with col_domain:
                st.write("")
                st.write("")
                st.markdown("**@ewha.ac.kr**")
            interests = st.multiselect("관심 분야 (선택)", INTERESTS, default=p.get("관심분야", []))
            st.write("")
            privacy = st.checkbox("✅ 개인정보 수집 및 이용에 동의합니다 (필수)")
            st.markdown("<p style='font-size:13px; color:#000000;'>* 수집된 정보는 맞춤 공지 제공 목적으로만 사용되며, 외부에 제공되지 않습니다.</p>", unsafe_allow_html=True)
            st.write("")
            email_notify = st.checkbox("📧 이메일로 맞춤 정보 받기 (선택)", value=p.get("이메일알림", False))
            all_filled = bool(user_id and college != "선택 안 함" and major and email_prefix and privacy)
            st.write("")
            if st.button("저장", disabled=not all_filled):
                if not re.match(r'^[a-zA-Z0-9]+$', user_id):
                    st.error("아이디는 영어와 숫자만 입력 가능합니다.")
                elif not re.match(r'^[a-zA-Z0-9._-]+$', email_prefix):
                    st.error("올바른 이메일 형식을 입력해주세요.")
                else:
                    st.session_state.profile = {
                        "아이디": user_id, "학년": grade, "단과대학": college,
                        "전공": major, "이메일": f"{email_prefix}@ewha.ac.kr",
                        "이메일알림": email_notify, "관심분야": interests
                    }
                    st.session_state.editing_profile = False
                    st.success("프로필이 저장됐어요! 🎉")

    # ── 탭2: 찜한 정보 ──
    with tab2:
        st.write("")
        if st.session_state.bookmarks:
            st.write(f"총 **{len(st.session_state.bookmarks)}개** 저장됨")
            for i, notice in enumerate(st.session_state.bookmarks):
                date_val = notice.get("날짜", "") or notice.get("신청기간", "")
                col_notice, col_btn = st.columns([11, 1])
                with col_notice:
                    st.markdown(f"""
                    <div class="notice-item">
                        <span style="font-size:12px; color:#2e7d32;">#{notice.get('카테고리','')}</span><br>
                        <b>{notice['제목']}</b><br>
                        <span style="font-size: 14px;">📅 {date_val if date_val else '-'}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.write("")
                    if st.button("🗑️", key=f"del_bm_{i}"):
                        st.session_state.bookmarks.pop(i)
                        st.rerun()
        else:
            st.info("아직 찜한 정보가 없어요! 공지 옆 ☆ 버튼을 눌러 저장해보세요.")

    # ── 탭3: 알림 설정 ──
    with tab3:
        st.write("")
        st.write("이메일로 받을 알림 카테고리를 선택해주세요.")
        st.write("")
        ns = st.session_state.notification_settings
        noti_scholarship = st.checkbox("🎓 장학금 공지", value=ns.get("장학금", True))
        noti_exchange    = st.checkbox("🌍 교환학생 공지", value=ns.get("교환학생", True))
        noti_job         = st.checkbox("💼 프로그램/취업 공지", value=ns.get("프로그램/취업", True))
        st.write("")
        if st.button("알림 설정 저장"):
            st.session_state.notification_settings = {
                "장학금": noti_scholarship,
                "교환학생": noti_exchange,
                "프로그램/취업": noti_job
            }
            st.success("알림 설정이 저장됐어요! ✅")

# ── 장학금 페이지 ──────────────────────────────────────
elif st.session_state.page == "scholarship":
    col_back, _ = st.columns([1, 9])
    with col_back:
        if st.button("← 뒤로"):
            st.session_state.page = "home"
            st.rerun()
    st.title("🎓 장학금 공지")
    search = st.text_input("🔍 검색", placeholder="공지 제목으로 검색하세요")
    notices = get_scholarship_notices()
    if search:
        notices = [n for n in notices if search.lower() in n["제목"].lower()]
    show_notices(notices, date_key="신청기간", category="장학금")

# ── 교환학생 페이지 ──────────────────────────────────────
elif st.session_state.page == "exchange":
    col_back, _ = st.columns([1, 9])
    with col_back:
        if st.button("← 뒤로"):
            st.session_state.page = "home"
            st.rerun()
    st.title("🌍 교환학생")
    search = st.text_input("🔍 검색", placeholder="공지 제목으로 검색하세요")
    notices = get_exchange_notices()
    if search:
        notices = [n for n in notices if search.lower() in n["제목"].lower()]
    show_notices(notices, category="교환학생")

# ── 프로그램/취업 페이지 ──────────────────────────────────────
elif st.session_state.page == "job":
    col_back, _ = st.columns([1, 9])
    with col_back:
        if st.button("← 뒤로"):
            st.session_state.page = "home"
            st.rerun()
    st.title("💼 프로그램/취업")
    search = st.text_input("🔍 검색", placeholder="공지 제목으로 검색하세요")
    notices = get_job_notices()
    if search:
        notices = [n for n in notices if search.lower() in n["제목"].lower()]
    show_notices(notices, category="프로그램/취업")

# ── 공지 상세 페이지 ──────────────────────────────────────
elif st.session_state.page == "detail":
    notice = st.session_state.selected_notice
    if not notice:
        st.session_state.page = "home"
        st.rerun()

    category = notice.get("카테고리", "")
    back_page = {"장학금": "scholarship", "교환학생": "exchange", "프로그램/취업": "job"}.get(category, "home")

    col_back, _ = st.columns([1, 9])
    with col_back:
        if st.button("← 뒤로"):
            st.session_state.page = back_page
            st.rerun()

    st.markdown(f"<span style='color:#2e7d32; font-size:14px;'>#{category}</span>", unsafe_allow_html=True)
    st.title(notice["제목"])
    date_val = notice.get(notice.get("date_key", "날짜"), "") or notice.get("신청기간", "")
    if date_val:
        st.caption(f"📅 {date_val}")
    st.write("")

    with st.spinner("AI가 요약 중이에요..."):
        content = fetch_notice_content(notice.get("링크", ""))
        summary, error = get_ai_summary(notice["제목"], content)

    if summary:
        summary_html = summary.replace("\n", "<br>")
        st.markdown(f"""
        <div style="background:#f1f8e9; border-left:4px solid #66bb6a; border-radius:8px; padding:18px 22px; margin-bottom:16px;">
            <b style="color:#2e7d32;">✨ AI 요약</b><br><br>
            <span style="color:#000000; line-height:2;">{summary_html}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error(f"AI 요약 오류: {error}")

    st.write("")
    link = notice.get("링크", "")
    if link:
        st.link_button("🔗 원본 공지 보러가기", link, use_container_width=False)
