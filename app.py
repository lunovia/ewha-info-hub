import streamlit as st
import streamlit.components.v1 as components
import requests
import re
import os
import hashlib
from bs4 import BeautifulSoup
from groq import Groq
from supabase import create_client

st.set_page_config(page_title="이화여대 정보 통합", page_icon="🌱", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "landing"
if "profile" not in st.session_state:
    st.session_state.profile = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []
if "notification_settings" not in st.session_state:
    st.session_state.notification_settings = {"장학금": True, "교환학생": True, "프로그램/취업": True}
if "editing_profile" not in st.session_state:
    st.session_state.editing_profile = False
if "selected_notice" not in st.session_state:
    st.session_state.selected_notice = None

# 로그인 안 된 상태에서 홈/다른 페이지 접근 시 랜딩으로 리다이렉트
if not st.session_state.logged_in and st.session_state.page not in ["landing", "login", "signup"]:
    st.session_state.page = "landing"
    st.rerun()

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
        div[data-testid="stButton"] > button:not(:disabled) {
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

@st.cache_resource
def get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

def save_to_db(notices, category):
    db = get_supabase()
    if not db:
        return
    try:
        rows = [{"category": category, "title": n.get("제목", ""), "date": n.get("날짜", "") or n.get("신청기간", ""), "link": n.get("링크", "")} for n in notices]
        db.table("notices").insert(rows).execute()
    except Exception:
        pass

def load_from_db(category):
    db = get_supabase()
    if not db:
        return []
    result = db.table("notices").select("*").eq("category", category).execute()
    return [{"제목": r["title"], "날짜": r["date"], "신청기간": r["date"], "링크": r["link"]} for r in result.data]

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def save_user_to_db(profile):
    db = get_supabase()
    if not db:
        return
    try:
        import json
        data = {
            "user_id": profile["아이디"],
            "grade": profile["학년"],
            "college": profile["단과대학"],
            "major": profile["전공"],
            "email": profile["이메일"],
            "interests": json.dumps(profile["관심분야"], ensure_ascii=False),
            "email_notification": profile.get("이메일알림", False)
        }
        if profile.get("비밀번호"):
            data["password"] = hash_password(profile["비밀번호"])
        db.table("users").upsert(data, on_conflict="user_id").execute()
    except Exception:
        pass

def load_user_from_db(user_id):
    db = get_supabase()
    if not db:
        return None
    try:
        import json
        result = db.table("users").select("*").eq("user_id", user_id).execute()
        if result.data:
            r = result.data[0]
            return {
                "아이디": r["user_id"],
                "학년": r["grade"],
                "단과대학": r["college"],
                "전공": r["major"],
                "이메일": r["email"],
                "관심분야": json.loads(r["interests"]) if r["interests"] else [],
                "이메일알림": r["email_notification"],
                "비밀번호해시": r.get("password", "")
            }
    except Exception:
        pass
    return None

def login_user(user_id, password):
    profile = load_user_from_db(user_id)
    if profile and profile.get("비밀번호해시") == hash_password(password):
        return profile
    return None

if st.session_state.profile is None:
    uid = st.query_params.get("uid")
    if uid:
        loaded = load_user_from_db(uid)
        if loaded:
            st.session_state.profile = loaded
            st.session_state.logged_in = True

def is_relevant(notice_title, profile):
    if not profile:
        return False
    title = notice_title
    grade = profile.get("학년", "")
    college = profile.get("단과대학", "")
    major = profile.get("전공", "")

    grade_num = grade.replace("학년", "").strip()
    grade_keywords = {
        "1": ["1학년", "신입생", "입학"],
        "2": ["2학년"],
        "3": ["3학년"],
        "4": ["4학년", "졸업예정"],
    }
    matched_grade = any(kw in title for kw in grade_keywords.get(grade_num, []))
    general = any(kw in title for kw in ["학부", "재학생", "전교생", "재학", "학부생"])
    matched_college = college and college != "선택 안 함" and college.replace("대학", "").replace("과학부", "") in title
    matched_major = major and major != "선택 안 함" and any(kw in title for kw in [major.replace("학과", "").replace("학부", "")])

    return matched_grade or general or matched_college or matched_major

COLLEGES = [
    "선택 안 함", "인문과학대학", "사회과학대학", "자연과학대학", "엘텍공과대학",
    "사범대학", "음악대학", "조형예술대학", "체육과학부",
    "의과대학", "약학대학", "간호과학대학", "경영대학", "신산업융합대학", "인공지능대학"
]
COLLEGE_MAJORS = {
    "선택 안 함": ["선택 안 함"],
    "인문과학대학": ["선택 안 함", "국어국문학과", "영어영문학과", "불어불문학과", "독어독문학과", "중어중문학과", "일어일본학과", "철학과", "사학과", "기독교학과"],
    "사회과학대학": ["선택 안 함", "정치외교학과", "행정학과", "경제학과", "사회학과", "심리학과", "소비자학과", "사회복지학과", "문헌정보학과"],
    "자연과학대학": ["선택 안 함", "수학과", "통계학과", "물리학과", "화학·나노과학과", "생명과학과"],
    "엘텍공과대학": ["선택 안 함", "전자전기공학부", "화공신소재공학부", "건축도시시스템공학부", "컴퓨터공학과", "소프트웨어학부", "휴먼기계바이오공학부"],
    "사범대학": ["선택 안 함", "교육학과", "유아교육학과", "초등교육학과", "교육공학과", "특수교육학과", "윤리교육학과", "과학교육학과", "수학교육학과", "영어교육학과"],
    "음악대학": ["선택 안 함", "피아노과", "관현악과", "성악과", "작곡과", "한국음악과"],
    "조형예술대학": ["선택 안 함", "회화·판화과", "조소과", "공예과", "섬유예술패션디자인과", "시각디자인과", "환경디자인과", "디지털미디어학부"],
    "체육과학부": ["선택 안 함", "체육과학부"],
    "의과대학": ["선택 안 함", "의학과"],
    "약학대학": ["선택 안 함", "약학과"],
    "간호과학대학": ["선택 안 함", "간호학과"],
    "경영대학": ["선택 안 함", "경영학부"],
    "신산업융합대학": ["선택 안 함", "식품공학과", "식품영양학과", "의류산업학과", "신산업융합학부"],
    "인공지능대학": ["선택 안 함", "인공지능학과", "데이터사이언스학부", "사이버보안학과"],
}
INTERESTS = ["장학금", "교환학생/해외", "취업/인턴", "창업", "연구", "봉사/사회활동", "문화/예술", "프로그램"]

@st.cache_data
def get_scholarship_notices():
    cached = load_from_db("장학금")
    if cached:
        return cached
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
    save_to_db(notices, "장학금")
    return notices

@st.cache_data
def get_exchange_notices():
    cached = load_from_db("교환학생")
    if cached:
        return cached
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
    save_to_db(notices, "교환학생")
    return notices

@st.cache_data
def get_job_notices():
    cached = load_from_db("프로그램/취업")
    if cached:
        return cached
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
    save_to_db(notices, "프로그램/취업")
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

def evaluate_target(target_text, profile):
    if not profile or not target_text:
        return None
    grade = profile.get("학년", "")
    college = profile.get("단과대학", "선택 안 함")
    major = profile.get("전공", "선택 안 함")
    notes = []

    grade_num = grade.replace("학년", "").strip()
    grade_keywords = {"1": ["1학년", "신입생"], "2": ["2학년"], "3": ["3학년"], "4": ["4학년", "졸업예정"]}
    specific_grade = any(kw in target_text for kws in grade_keywords.values() for kw in kws)
    if specific_grade:
        my_keywords = grade_keywords.get(grade_num, [])
        if any(kw in target_text for kw in my_keywords):
            notes.append(f"{grade} ✅")
        else:
            notes.append(f"{grade}은 해당 안 될 수 있음 ⚠️")

    if "재학생" in target_text or "학부생" in target_text or "본교생" in target_text:
        notes.append("재학생 해당 ✅")

    if "휴학" in target_text:
        notes.append("휴학 여부 입력 안 됨, 확인 필요 ⚠️")

    college_short = college.replace("대학", "").replace("과학부", "") if college != "선택 안 함" else ""
    if college_short and college_short in target_text:
        notes.append(f"{college} 해당 ✅")

    if not notes:
        return "프로필 기준 판단 어려움, 직접 확인 필요 ⚠️"
    return ", ".join(notes)

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
        if st.session_state.profile:
            notices = sorted(notices, key=lambda n: is_relevant(n["제목"], st.session_state.profile), reverse=True)
        st.write(f"총 **{len(notices)}개** 공지")
        for i, notice in enumerate(notices):
            date_val = notice.get(date_key, "") or notice.get("신청기간", "")
            is_bookmarked = any(b["제목"] == notice["제목"] for b in st.session_state.bookmarks)
            col_notice, col_btns = st.columns([8, 2])
            with col_notice:
                relevant = is_relevant(notice["제목"], st.session_state.profile)
                badge = "<span style='background:#e8f5e9; color:#2e7d32; font-size:12px; padding:2px 8px; border-radius:10px; margin-bottom:4px; display:inline-block;'>✨ 나에게 해당</span><br>" if relevant else ""
                st.markdown(f'<div class="notice-item">{badge}<b>{notice["제목"]}</b><br><span style="font-size:14px;">📅 {date_val if date_val else "-"}</span></div>', unsafe_allow_html=True)
            with col_btns:
                st.write("")
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if st.button("🔍", key=f"detail_{category}_{i}"):
                        st.session_state.selected_notice = {**notice, "카테고리": category, "date_key": date_key}
                        st.session_state.page = "detail"
                        st.rerun()
                with bcol2:
                    if st.button("⭐" if is_bookmarked else "☆", key=f"bm_{category}_{i}"):
                        if is_bookmarked:
                            st.session_state.bookmarks = [b for b in st.session_state.bookmarks if b["제목"] != notice["제목"]]
                        else:
                            st.session_state.bookmarks.append({**notice, "카테고리": category})
                        st.rerun()
    else:
        st.info("공지를 불러오는 중입니다...")

# ── 랜딩 페이지 ──────────────────────────────────────────
if st.session_state.page == "landing":
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.write("")
        st.write("")
        st.write("")
        st.markdown("<h1 style='text-align:center; font-size:48px;'>🌱</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>이화여대 정보 허브</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:18px; color:#555; line-height:2.2;'>매번 공지 찾아다니느라 지치지 않았나요? 🥲<br><br>장학금·교환학생·취업 정보, 이제 한 곳에서 —<br>내 학년·전공에 맞는 것만 골라 AI가 요약해드려요!</p>", unsafe_allow_html=True)
        st.write("")
        st.write("")
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            if st.button("→ 시작하기", use_container_width=True, key="landing_start"):
                st.session_state.page = "login"
                st.rerun()
        components.html("""
        <script>
        setTimeout(function() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(function(btn) {
                if (btn.innerText.trim() === '→ 시작하기') {
                    btn.style.setProperty('background-color', '#ddf0df', 'important');
                    btn.style.setProperty('color', '#1b5e20', 'important');
                    btn.style.setProperty('font-size', '16px', 'important');
                    btn.style.setProperty('font-weight', 'bold', 'important');
                    btn.style.setProperty('border-radius', '12px', 'important');
                    btn.style.setProperty('border', '2px solid #2e7d32', 'important');
                    btn.style.setProperty('padding', '14px 24px', 'important');
                }
            });
        }, 100);
        </script>
        """, height=0)
        st.write("")
        st.markdown("<p style='text-align:center; font-size:12px; color:#aaa;'>*이화여대 재학생이 만든 비공식 서비스</p>", unsafe_allow_html=True)

# ── 로그인 페이지 ──────────────────────────────────────────
elif st.session_state.page == "login":
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>🌱 이화여대 정보 허브</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666; margin-bottom:32px;'>공지 일일이 찾아다니지 마세요 ✨</p>", unsafe_allow_html=True)
        user_id = st.text_input("아이디", placeholder="아이디 입력")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
        st.write("")
        if st.button("로그인", use_container_width=True):
            result = login_user(user_id, password)
            if result:
                st.session_state.profile = result
                st.session_state.logged_in = True
                st.query_params["uid"] = user_id
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않아요.")
        st.write("")
        st.markdown("<p style='text-align:center; color:#666;'>아직 계정이 없으신가요?</p>", unsafe_allow_html=True)
        if st.button("회원가입하기", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

# ── 회원가입 페이지 ──────────────────────────────────────────
elif st.session_state.page == "signup":
    st.title("🌱 회원가입")
    st.write("")
    new_id = st.text_input("아이디 *", placeholder="영어, 숫자만 입력 가능")
    new_pw = st.text_input("비밀번호 *", type="password", placeholder="비밀번호 입력")
    new_pw2 = st.text_input("비밀번호 확인 *", type="password", placeholder="비밀번호 다시 입력")
    grade = st.selectbox("학년 *", ["1학년", "2학년", "3학년", "4학년"])
    college = st.selectbox("단과대학 *", COLLEGES)
    major_options = COLLEGE_MAJORS.get(college, ["선택 안 함"])
    major = st.selectbox("전공 *", major_options)
    col_email, col_domain = st.columns([3, 2])
    with col_email:
        email_prefix = st.text_input("학교 이메일 *", placeholder="이메일 앞부분 입력")
    with col_domain:
        st.write("")
        st.write("")
        st.markdown("**@ewha.ac.kr**")
    interests = st.multiselect("관심 분야 (선택)", INTERESTS)
    email_notify = st.checkbox("📧 이메일로 맞춤 정보 받기 (선택)")
    st.write("")
    if st.button("가입하기", use_container_width=True):
        if not new_id or not new_pw or not email_prefix or college == "선택 안 함" or major == "선택 안 함":
            st.error("필수 항목을 모두 입력해주세요.")
        elif not re.match(r'^[a-zA-Z0-9]+$', new_id):
            st.error("아이디는 영어, 숫자만 입력 가능해요.")
        elif new_pw != new_pw2:
            st.error("비밀번호가 일치하지 않아요.")
        elif len(new_pw) < 4:
            st.error("비밀번호는 4자 이상 입력해주세요.")
        else:
            existing = load_user_from_db(new_id)
            if existing:
                st.error("이미 사용 중인 아이디예요.")
            else:
                profile = {
                    "아이디": new_id, "학년": grade, "단과대학": college,
                    "전공": major, "이메일": f"{email_prefix}@ewha.ac.kr",
                    "이메일알림": email_notify, "관심분야": interests, "비밀번호": new_pw
                }
                save_user_to_db(profile)
                st.session_state.profile = profile
                st.session_state.logged_in = True
                st.query_params["uid"] = new_id
                st.session_state.page = "home"
                st.rerun()
    st.write("")
    if st.button("← 로그인으로 돌아가기"):
        st.session_state.page = "login"
        st.rerun()

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

    # 홈에서 미리 크롤링 캐시
    get_scholarship_notices()
    get_exchange_notices()
    get_job_notices()

    if st.session_state.profile:
        p = st.session_state.profile
        st.caption(f"👋 {p['아이디']}님 · {p['학년']} · {p['단과대학']}")

    st.markdown("<p style='font-size:16px; color:#444444;'>공지 일일이 찾아다니지 마세요. AI가 내 학년·전공에 맞는 장학금·교환학생 정보만 골라드려요 ✨</p>", unsafe_allow_html=True)
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
        if not st.session_state.profile:
            st.markdown("<p style='font-size:14px; color:#555;'>이전에 저장한 프로필이 있으면 아이디로 불러올 수 있어요.</p>", unsafe_allow_html=True)
            col_id, col_btn = st.columns([3, 1])
            with col_id:
                load_id = st.text_input("아이디 입력", placeholder="저장했던 아이디", label_visibility="collapsed")
            with col_btn:
                if st.button("불러오기"):
                    loaded = load_user_from_db(load_id)
                    if loaded:
                        st.session_state.profile = loaded
                        st.query_params["uid"] = load_id
                        st.success("프로필을 불러왔어요! 🎉")
                        st.rerun()
                    else:
                        st.error("해당 아이디의 프로필을 찾을 수 없어요.")
            st.divider()
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
            st.markdown("<p style='font-size:15px; color:#444444;'>입력하신 학년·전공 정보로 나에게 맞는 공지만 골라드려요!</p>", unsafe_allow_html=True)
            st.write("")
            user_id  = st.text_input("아이디 *", value=p.get("아이디", ""), placeholder="영어, 숫자만 입력 가능")
            grade    = st.selectbox("학년 *", ["1학년", "2학년", "3학년", "4학년"],
                                    index=["1학년","2학년","3학년","4학년"].index(p["학년"]) if p.get("학년") else 0)
            college  = st.selectbox("단과대학 *", COLLEGES,
                                    index=COLLEGES.index(p["단과대학"]) if p.get("단과대학") else 0)
            major_options = COLLEGE_MAJORS.get(college, ["선택 안 함"])
            saved_major = p.get("전공", "")
            major_index = major_options.index(saved_major) if saved_major in major_options else 0
            major = st.selectbox("전공 *", major_options, index=major_index)
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
            all_filled = bool(user_id and college != "선택 안 함" and major and major != "선택 안 함" and email_prefix and privacy)
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
                    save_user_to_db(st.session_state.profile)
                    st.query_params["uid"] = user_id
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
        lines = summary.split("\n")
        processed = []
        for line in lines:
            processed.append(line)
            stripped = line.strip()
            if "📌" in stripped and "대상" in stripped:
                target_text = stripped.split(":", 1)[-1].strip() if ":" in stripped else stripped
                evaluation = evaluate_target(target_text, st.session_state.profile)
                if evaluation:
                    processed.append(f"&nbsp;&nbsp;&nbsp;<span style='color:#e65100;'>→ 내 정보 기준: {evaluation}</span>")
        summary_html = "<br>".join(processed)
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
