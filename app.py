import streamlit as st
from datetime import date, datetime, timedelta
import json
import time
import random
import altair as alt
import pandas as pd
import feedparser
import re
from deep_translator import GoogleTranslator
import html
import io
import contextlib
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from appdb import (
    get_ai_info_by_date, add_ai_info, delete_ai_info, get_all_ai_info_dates,
    get_all_quiz_topics, get_quiz_by_topic, add_quiz, update_quiz, delete_quiz,
    get_user_progress, update_user_progress, get_user_stats, update_user_stats,
    get_all_prompts, add_prompt, update_prompt, delete_prompt,
    get_all_base_contents, add_base_content, update_base_content, delete_base_content
)

# deep-translator 기반 번역 함수

def translate_to_ko(text):
    try:
        return GoogleTranslator(source='auto', target='ko').translate(text)
    except Exception:
        return text  # 번역 실패 시 원문 반환

def clean_summary(summary, title):
    text = strip_html_tags(summary)
    text = html.unescape(text)
    text = text.replace('\xa0', ' ').replace('\n', ' ').strip()
    # 제목과 유사하거나 너무 짧으면 출력하지 않음
    if len(text) < 10 or text.replace(' ', '') in title.replace(' ', ''):
        return None
    return text

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[-–—:·.,!?"\'\\|/]', '', text)
    text = re.sub(r'\s+', '', text)
    return text

# 페이지 설정
st.set_page_config(
    page_title="AI Mastery Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* 전체 앱 스타일 */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* 메인 컨텐츠 카드 */
    .main-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* 정보 카드 스타일 */
    .info-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 10px 30px rgba(240,147,251,0.3);
        transition: transform 0.3s ease;
    }
    
    .info-card:hover {
        transform: translateY(-5px);
    }
    
    /* 통계 카드 */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(102,126,234,0.3);
    }
    
    /* 성취 배지 */
    .achievement-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.8em;
        margin: 5px;
        display: inline-block;
    }
    
    /* 프로그레스 바 */
    .progress-container {
        background: rgba(255,255,255,0.2);
        border-radius: 10px;
        padding: 3px;
        margin: 10px 0;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 20px;
        border-radius: 8px;
        transition: width 0.3s ease;
    }
    
    /* 제목 스타일 */
    .main-title {
        font-size: 3em;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .section-title {
        font-size: 1.8em;
        font-weight: 600;
        color: #333;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 600;
        box-shadow: 0 5px 15px rgba(102,126,234,0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102,126,234,0.4);
    }
    
    /* 입력 필드 스타일 */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid rgba(102,126,234,0.3);
        padding: 10px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
    }
    
    /* 학습 모드 카드 */
    .learning-mode {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    
    .learning-mode:hover {
        transform: translateY(-3px);
    }
    
    /* 퀴즈 카드 */
    .quiz-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 10px 30px rgba(255,236,210,0.3);
    }
    
    /* 알림 스타일 */
    .success-alert {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .warning-alert {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        color: #8b4513;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'user_progress' not in st.session_state:
    st.session_state.user_progress = {}
if 'user_stats' not in st.session_state:
    st.session_state.user_stats = {
        'total_learned': 0,
        'streak_days': 0,
        'last_learned_date': None,
        'quiz_score': 0,
        'achievements': []
    }
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}

# 관리자 비밀번호 상수 정의
ADMIN_PASSWORD = "admin123"  # 실제 배포시 환경변수 등으로 보안 강화 권장

# --- [1] 용어사전 데이터 추가 ---
ai_glossary = [
    {"term": "AI", "desc": "인공지능. 인간의 지능을 모방하는 컴퓨터 시스템."},
    {"term": "머신러닝", "desc": "데이터로부터 학습하는 인공지능의 한 분야."},
    {"term": "딥러닝", "desc": "신경망을 여러 층 쌓아 복잡한 패턴을 학습하는 방법."},
    {"term": "트랜스포머", "desc": "자연어 처리 등에서 쓰이는 현대적 신경망 구조."},
    {"term": "강화학습", "desc": "보상을 통해 최적의 행동을 학습하는 AI 방법."},
    {"term": "컴퓨터 비전", "desc": "이미지와 비디오를 이해하는 AI 분야."},
    {"term": "자연어 처리", "desc": "언어를 이해하고 생성하는 AI 기술."},
    {"term": "생성형 AI", "desc": "새로운 콘텐츠(텍스트, 이미지 등)를 생성하는 AI."},
    {"term": "지도학습", "desc": "정답이 있는 데이터로 학습하는 머신러닝 방법."},
    {"term": "비지도학습", "desc": "정답 없이 데이터의 패턴을 찾는 머신러닝 방법."},
    {"term": "LSTM", "desc": "장기 의존성 학습에 강한 순환 신경망 구조."},
    {"term": "CNN", "desc": "이미지 처리에 강한 합성곱 신경망."},
    {"term": "RNN", "desc": "순차 데이터(텍스트 등)에 적합한 신경망."},
    {"term": "파인튜닝", "desc": "사전학습된 모델을 특정 데이터에 맞게 추가 학습."},
    {"term": "파라미터", "desc": "모델이 학습하는 가중치 값."},
    {"term": "오버피팅", "desc": "학습 데이터에만 과하게 맞춰져 일반화가 안 되는 현상."},
    {"term": "언더피팅", "desc": "모델이 충분히 학습하지 못한 상태."},
    {"term": "하이퍼파라미터", "desc": "학습 과정에서 사람이 정하는 값."},
    {"term": "백프로파게이션", "desc": "오차를 역전파해 가중치를 조정하는 학습 방법."},
    {"term": "AI 윤리", "desc": "AI의 공정성, 투명성, 책임성 등 윤리적 문제 연구."},
]

# --- [2] 오답노트 세션 상태 추가 ---
if 'quiz_wrong_notes' not in st.session_state:
    st.session_state.quiz_wrong_notes = []

# --- [3] 오늘의 AI 트렌드(뉴스) 더미 데이터 ---
# ai_trends = [
#     {"date": "2025-07-14", "headline": "AI가 의료 진단 정확도 99% 달성", "summary": "최신 AI 모델이 의료 영상 진단에서 99%의 정확도를 기록했습니다."},
#     {"date": "2025-07-15", "headline": "생성형 AI, 예술 창작 분야 혁신", "summary": "AI가 그림, 음악, 소설 등 다양한 예술 분야에서 창작을 선도하고 있습니다."},
#     {"date": "2025-07-16", "headline": "AI 윤리 가이드라인 강화 발표", "summary": "정부와 기업이 AI 윤리 기준을 강화하는 새로운 가이드라인을 발표했습니다."},
#     {"date": "2025-07-17", "headline": "AI 기반 번역, 실시간 통역 시대 개막", "summary": "AI가 실시간으로 50개 언어를 통역하는 서비스가 출시되었습니다."},
#     {"date": "2025-07-18", "headline": "AI 로봇, 재난 구조 현장 투입", "summary": "AI 로봇이 재난 현장에서 인명 구조에 성공적으로 투입되었습니다."},
# ]

# --- [실시간 AI 뉴스 함수] ---
def fetch_ai_news():
    feed_url = "https://news.google.com/rss/search?q=AI"
    feed = feedparser.parse(feed_url)
    news_list = []
    for entry in feed.entries[:5]:
        news_list.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if hasattr(entry, 'summary') else ""
        })
    return news_list

def strip_html_tags(text):
    return re.sub('<.*?>', '', text)

# --- [4] 다크모드 토글 ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

def toggle_dark_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

# --- [5] 디자인 업그레이드: CSS 추가/수정 ---
# (기존 CSS에 추가)
st.markdown(f"""
<style>
    body, .stApp {{
        background: {'#181c2f' if st.session_state.dark_mode else 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'};
        color: {'#f5f6fa' if st.session_state.dark_mode else '#222'};
    }}
    .main-card {{
        background: {'rgba(24,28,47,0.98)' if st.session_state.dark_mode else 'rgba(255,255,255,0.95)'};
        color: {'#f5f6fa' if st.session_state.dark_mode else '#222'};
        box-shadow: 0 20px 40px rgba(24,28,47,0.2);
    }}
    .info-card, .quiz-card, .stat-card {{
        border: 1.5px solid {'#222' if st.session_state.dark_mode else 'rgba(255,255,255,0.3)'};
        box-shadow: 0 8px 24px rgba(24,28,47,0.15);
    }}
    .achievement-badge {{
        background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
        color: #fff;
    }}
    .stButton > button {{
        background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
        color: #fff;
        border-radius: 25px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, #185a9d 0%, #43cea2 100%);
        color: #fff;
    }}
    .stTextInput > div > div > input {{
        background: {'#232946' if st.session_state.dark_mode else '#fff'};
        color: {'#f5f6fa' if st.session_state.dark_mode else '#222'};
        border: 2px solid #43cea2;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: #185a9d;
        box-shadow: 0 0 0 3px rgba(67,206,162,0.15);
    }}
</style>
""", unsafe_allow_html=True)

# --- [6] AI 정보/퀴즈 데이터 보강 (7일치, 각 3개) ---
# ai_info_db = {...}  # <-- 완전 삭제/주석처리

quiz_db = {
    "AI 기초": [
        {"question": "AI가 데이터를 통해 스스로 학습하는 방법은?", "options": ["기계 학습", "수동 프로그래밍", "규칙 기반 시스템", "데이터베이스"], "correct": 0},
        {"question": "신경망을 여러 층으로 쌓은 구조를 무엇이라 하나요?", "options": ["얕은 학습", "딥러닝", "선형 회귀", "결정 트리"], "correct": 1},
        {"question": "AI의 핵심 응용 분야가 아닌 것은?", "options": ["자연어 처리", "컴퓨터 비전", "음성 인식", "요리"], "correct": 3},
        {"question": "AI 윤리의 주요 주제가 아닌 것은?", "options": ["공정성", "투명성", "책임성", "속도"], "correct": 3},
    ],
    "AI 응용": [
        {"question": "이미지와 비디오를 이해하는 AI 분야는?", "options": ["자연어 처리", "컴퓨터 비전", "음성 인식", "추천 시스템"], "correct": 1},
        {"question": "현대 AI 모델의 핵심 아키텍처는?", "options": ["CNN", "RNN", "트랜스포머", "LSTM"], "correct": 2},
        {"question": "AI가 예술 창작에 활용되는 분야는?", "options": ["생성형 AI", "강화학습", "지도학습", "비지도학습"], "correct": 0},
    ],
    "AI 용어": [
        {"question": "머신러닝의 대표적 학습 방법이 아닌 것은?", "options": ["지도학습", "비지도학습", "강화학습", "수동입력학습"], "correct": 3},
        {"question": "딥러닝에서 많이 쓰이는 신경망 구조는?", "options": ["CNN", "SVM", "KNN", "DT"], "correct": 0},
        {"question": "AI가 스스로 보상을 통해 학습하는 방법은?", "options": ["지도학습", "비지도학습", "강화학습", "딥러닝"], "correct": 2},
    ]
}

# 성취 시스템
achievements = [
    {"name": "첫 걸음", "description": "첫 번째 AI 정보 학습 완료", "condition": lambda stats: stats['total_learned'] >= 1},
    {"name": "꾸준한 학습자", "description": "3일 연속 학습 완료", "condition": lambda stats: stats['streak_days'] >= 3},
    {"name": "AI 마스터", "description": "총 10개의 AI 정보 학습 완료", "condition": lambda stats: stats['total_learned'] >= 10},
    {"name": "퀴즈 챔피언", "description": "퀴즈 점수 80점 이상 달성", "condition": lambda stats: stats['quiz_score'] >= 80},
]

def check_achievements():
    """성취 달성 확인"""
    new_achievements = []
    for achievement in achievements:
        if achievement['name'] not in st.session_state.user_stats['achievements']:
            if achievement['condition'](st.session_state.user_stats):
                st.session_state.user_stats['achievements'].append(achievement['name'])
                new_achievements.append(achievement)
    return new_achievements

def update_user_progress(date_str, info_index):
    """사용자 학습 진행상황 업데이트"""
    if date_str not in st.session_state.user_progress:
        st.session_state.user_progress[date_str] = []
    
    if info_index not in st.session_state.user_progress[date_str]:
        st.session_state.user_progress[date_str].append(info_index)
        st.session_state.user_stats['total_learned'] += 1
        
        # 연속 학습 일수 계산
        today = date.today()
        if st.session_state.user_stats['last_learned_date'] != today:
            if st.session_state.user_stats['last_learned_date'] == today - timedelta(days=1):
                st.session_state.user_stats['streak_days'] += 1
            else:
                st.session_state.user_stats['streak_days'] = 1
            st.session_state.user_stats['last_learned_date'] = today

def add_ai_info_checked(date_str, infos):
    if len(infos) != 3 or any(i.strip() == "" for i in infos):
        st.error("반드시 3개의 정보를 모두 입력해야 합니다.")
        return False
    add_ai_info(date_str, infos)
    st.success(f"✅ {date_str} 날짜에 AI 정보 3개가 등록되었습니다!")
    return True

def get_today_ai_info():
    """오늘의 AI 정보 반환"""
    today_str = date.today().isoformat()
    return get_ai_info_by_date(today_str)

def get_ai_info_by_date_wrapper(date_str):
    return get_ai_info_by_date(date_str)

def generate_quiz(topic):
    """퀴즈 생성"""
    if topic in quiz_db:
        return random.choice(quiz_db[topic])
    return None

def calculate_learning_progress():
    """학습 진행률 계산"""
    total_available = len(get_all_ai_info_dates()) * 3
    total_learned = st.session_state.user_stats['total_learned']
    return (total_learned / total_available * 100) if total_available > 0 else 0

# --- [9] 용어 랜덤 학습(오늘의 용어) 세션 상태 추가 ---
if 'glossary_learned' not in st.session_state:
    st.session_state.glossary_learned = []
if 'today_glossary_index' not in st.session_state:
    st.session_state.today_glossary_index = random.randint(0, len(ai_glossary)-1)

def get_today_glossary():
    return ai_glossary[st.session_state.today_glossary_index]

def render_info(info_text, key=None):
    info_text = info_text.strip()
    # 파이썬 코드 블록 실행 (matplotlib, plotly, altair 지원)
    if info_text.startswith('```python') and info_text.endswith('```'):
        code = info_text[9:-3]
        local_vars = {'plt': plt, 'go': go, 'alt': alt, 'st': st}
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(code, {}, local_vars)
            # plotly
            for v in local_vars.values():
                if hasattr(go, 'Figure') and isinstance(v, go.Figure):
                    st.plotly_chart(v, use_container_width=True, key=key)
            # altair
            for v in local_vars.values():
                if hasattr(alt, 'Chart') and isinstance(v, alt.Chart):
                    st.altair_chart(v, use_container_width=True, key=key)
            # matplotlib: plt.gcf() 자동 출력
            fig = plt.gcf()
            if fig and fig.get_axes():
                st.pyplot(fig)
                plt.close(fig)
        except Exception as e:
            st.error(f"코드 실행 오류: {e}")
    else:
        # 수식/마크다운 지원
        if info_text.startswith('$') and info_text.endswith('$'):
            st.latex(info_text.strip('$'))
        else:
            st.markdown(info_text, unsafe_allow_html=True)

# 메인 타이틀
st.markdown('<h1 class="main-title">🧠 AI Mastery Hub</h1>', unsafe_allow_html=True)

# 사이드바
# --- [사이드바: 파일 상단에서 단 한 번만 실행] ---
with st.sidebar:
    st.markdown("### 🌓 테마")
    if st.button("다크모드 토글", key="darkmode_btn_sidebar"):
        toggle_dark_mode()
        st.rerun()
    st.markdown("---")
    st.markdown("### 📚 용어사전")
    if st.button("랜덤 용어 보기", key="random_glossary_btn"):
        term = random.choice(ai_glossary)
        st.info(f"**{term['term']}**: {term['desc']}")
    search_term = st.text_input("용어 검색", "")
    if search_term:
        found = [t for t in ai_glossary if search_term.lower() in t["term"].lower()]
        if found:
            for t in found:
                st.success(f"**{t['term']}**: {t['desc']}")
        else:
            st.warning("검색 결과가 없습니다.")
    st.markdown("---")
    st.markdown("### 📰 오늘의 AI 트렌드")
    news = fetch_ai_news()
    for n in news:
        title_ko = translate_to_ko(n['title'])
        st.markdown(f"[{title_ko}]({n['link']})")
    # 요약(회색 줄) 출력 완전 제거

# 메인 컨텐츠
# --- [탭 UI로 전환] ---
tabs = st.tabs(["🏠 홈", "📚 오늘의 학습", "📖 학습 기록", "🎯 퀴즈", "📊 통계", "⚙️ 관리자"])

with tabs[0]:
    # 홈
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <h3>📚 총 학습 정보</h3>
            <h2>{}</h2>
            <p>개의 AI 정보를 학습했습니다</p>
        </div>
        """.format(st.session_state.user_stats['total_learned']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <h3>🔥 연속 학습</h3>
            <h2>{}</h2>
            <p>일 연속으로 학습 중입니다</p>
        </div>
        """.format(st.session_state.user_stats['streak_days']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <h3>🎯 퀴즈 점수</h3>
            <h2>{}</h2>
            <p>점이 최고 점수입니다</p>
        </div>
        """.format(st.session_state.user_stats['quiz_score']), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 오늘의 AI 정보 미리보기
    st.markdown('<h2 class="section-title">📅 오늘의 AI 정보</h2>', unsafe_allow_html=True)
    
    today_infos = get_today_ai_info()
    if today_infos:
        for i, info in enumerate(today_infos[:2]):  # 처음 2개만 미리보기
            st.markdown(f"""
            <div class="info-card">
                <h4>💡 정보 {i+1}</h4>
                <p>{info}</p>
            </div>
            """, unsafe_allow_html=True)
        
        if len(today_infos) > 2:
            st.info("더 많은 정보를 보려면 '📚 오늘의 학습' 메뉴를 방문해주세요!")
    else:
        st.info("오늘의 AI 정보가 아직 등록되지 않았습니다.")
    
    # 오늘의 용어 학습 카드
    st.markdown('<h2 class="section-title">📖 오늘의 AI 용어</h2>', unsafe_allow_html=True)
    today_glossary = get_today_glossary()
    learned = today_glossary['term'] in st.session_state.glossary_learned
    st.markdown(f'''
    <div class="info-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4>🔤 오늘의 용어</h4>
            <div>{'✅ 학습완료' if learned else '📖 학습하기'}</div>
        </div>
        <p style="font-size: 1.1em; line-height: 1.6; margin: 15px 0;"><b>{today_glossary['term']}</b>: {today_glossary['desc']}</p>
    </div>
    ''', unsafe_allow_html=True)
    if not learned:
        if st.button("✅ 오늘의 용어 학습 완료", key="learn_today_glossary_btn"):
            st.session_state.glossary_learned.append(today_glossary['term'])
            st.success(f"�� '{today_glossary['term']}' 용어를 학습하셨습니다!")
            st.rerun()
    # 최근 학습한 용어 리스트
    if st.session_state.glossary_learned:
        st.markdown("#### 최근 학습한 용어")
        for t in st.session_state.glossary_learned[-5:][::-1]:
            st.info(f"{t}")
    
    # 학습 모드 선택
    st.markdown('<h2 class="section-title">🎯 학습 모드</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📚 오늘의 학습 시작"):
            st.session_state.menu = "📚 오늘의 학습"
            st.rerun()
    
    with col2:
        if st.button("🎯 퀴즈 도전"):
            st.session_state.menu = "🎯 퀴즈"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    # 오늘의 학습
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">📚 오늘의 AI 정보 학습</h2>', unsafe_allow_html=True)
    # 날짜 선택 기능 추가
    all_dates = get_all_ai_info_dates()
    if all_dates:
        today_str = date.today().isoformat()
        selected_date = st.date_input("학습할 날짜를 선택하세요", value=date.fromisoformat(today_str), min_value=date.fromisoformat(all_dates[0]), max_value=date.fromisoformat(all_dates[-1]), key="learn_date_input")
        selected_date_str = selected_date.isoformat()
        infos = get_ai_info_by_date_wrapper(selected_date_str)
        if infos:
            for i, info in enumerate(infos, 1):
                learned = i-1 in st.session_state.user_progress.get(selected_date_str, [])
                st.markdown(f"""
                <div class="info-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4>💡 AI 정보 {i}</h4>
                        <div>{'✅ 학습완료' if learned else '📖 학습하기'}</div>
                    </div>
                """, unsafe_allow_html=True)
                render_info(info, key=f"learn_{selected_date_str}_{i}")
                st.markdown("</div>", unsafe_allow_html=True)
                if not learned:
                    if st.button(f"✅ 정보 {i} 학습 완료", key=f"learn_info_{selected_date_str}_{i}"):
                        update_user_progress(selected_date_str, i-1)
                        new_achievements = check_achievements()
                        st.success(f"🎉 정보 {i}을(를) 학습하셨습니다!")
                        if new_achievements:
                            for achievement in new_achievements:
                                st.balloons()
                                st.success(f"🏆 새로운 성취를 달성했습니다: {achievement['name']}")
                        st.rerun()
            # 학습 진행률 표시
            learned_count = len(st.session_state.user_progress.get(selected_date_str, []))
            progress = (learned_count / len(infos)) * 100
            st.markdown(f"""
            <div style="margin-top: 30px;">
                <h4>📊 학습 진행률</h4>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {progress}%"></div>
                </div>
                <p style="text-align: center; margin: 10px 0;">
                    {learned_count}/{len(infos)} 완료 ({progress:.1f}%)
                </p>
            </div>
            """, unsafe_allow_html=True)
            if learned_count == len(infos):
                st.success("🎉 이 날짜의 모든 AI 정보를 학습하셨습니다! 훌륭해요!")
                st.balloons()
        else:
            st.info("이 날짜의 AI 정보가 아직 등록되지 않았습니다.")
    else:
        st.info("등록된 AI 정보가 없습니다. 관리자에서 먼저 등록해 주세요.")
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    # 학습 기록
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">📖 학습 기록</h2>', unsafe_allow_html=True)
    # 날짜별 학습 기록
    for date_str in sorted(get_all_ai_info_dates(), reverse=True):
        infos = get_ai_info_by_date_wrapper(date_str)
        learned_infos = st.session_state.user_progress.get(date_str, [])
        with st.expander(f"📅 {date_str} ({len(learned_infos)}/{len(infos)} 학습완료)"):
            for i, info in enumerate(infos):
                learned = i in learned_infos
                status = "✅" if learned else "⏳"
                st.markdown(f"{status} 정보 {i+1}:")
                render_info(info, key=f"record_{date_str}_{i}")
            if learned_infos:
                st.success(f"이 날짜에 {len(learned_infos)}개의 정보를 학습했습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[3]:
    # 퀴즈
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">🎯 AI 퀴즈 도전</h2>', unsafe_allow_html=True)
    
    # 퀴즈 주제 선택
    quiz_topic = st.selectbox("퀴즈 주제 선택", list(quiz_db.keys()))
    
    if st.button("🎯 퀴즈 시작", key="quiz_start_btn"):
        st.session_state.current_quiz = generate_quiz(quiz_topic)
        st.session_state.quiz_answers = {}
    
    if st.session_state.current_quiz:
        quiz = st.session_state.current_quiz
        
        st.markdown(f"""
        <div class="quiz-card">
            <h3>❓ {quiz['question']}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 답변 선택
        selected_answer = st.radio("답을 선택해주세요:", quiz['options'])
        
        if st.button("정답 확인", key="quiz_answer_btn"):
            correct_answer = quiz['options'][quiz['correct']]
            
            if selected_answer == correct_answer:
                st.success("🎉 정답입니다!")
                score = st.session_state.user_stats['quiz_score']
                new_score = min(100, score + 10)
                st.session_state.user_stats['quiz_score'] = new_score
                st.balloons()
            else:
                st.error(f"❌ 틀렸습니다. 정답은 '{correct_answer}'입니다.")
                # 오답노트 저장
                st.session_state.quiz_wrong_notes.append({
                    'question': quiz['question'],
                    'your_answer': selected_answer,
                    'correct': correct_answer
                })
            
            st.info(f"현재 퀴즈 점수: {st.session_state.user_stats['quiz_score']}점")
            
            # 성취 확인
            new_achievements = check_achievements()
            if new_achievements:
                for achievement in new_achievements:
                    st.success(f"🏆 새로운 성취를 달성했습니다: {achievement['name']}")
    
    # 오답노트 보기
    if st.session_state.quiz_wrong_notes:
        st.markdown("---")
        st.markdown("### ❗ 오답노트")
        for note in st.session_state.quiz_wrong_notes[-5:][::-1]:
            st.warning(f"Q: {note['question']}\n\n내 답: {note['your_answer']}\n정답: {note['correct']}")
    
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[4]:
    # 통계
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">📊 상세 통계</h2>', unsafe_allow_html=True)
    # 전체 통계
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 학습 정보", st.session_state.user_stats['total_learned'])
    with col2:
        st.metric("연속 학습 일수", st.session_state.user_stats['streak_days'])
    with col3:
        st.metric("퀴즈 점수", st.session_state.user_stats['quiz_score'])
    with col4:
        st.metric("획득 성취", len(st.session_state.user_stats['achievements']))
    # 학습 진행률
    st.markdown("### 📈 학습 진행률")
    # 전체 정보 개수 계산 (DB 기준)
    all_dates = get_all_ai_info_dates()
    total_available = len(all_dates) * 3
    total_learned = st.session_state.user_stats['total_learned']
    progress = (total_learned / total_available * 100) if total_available > 0 else 0
    st.progress(progress / 100)
    st.write(f"전체 진행률: {progress:.1f}%")
    # 날짜별 학습 현황 (Plotly 그래프)
    st.markdown("### 📅 날짜별 학습 현황")
    chart_data = []
    for date_str in sorted(get_all_ai_info_dates()):
        infos = get_ai_info_by_date_wrapper(date_str)
        total_infos = len(infos)
        learned_infos = len(st.session_state.user_progress.get(date_str, []))
        chart_data.append({
            '날짜': date_str,
            '전체 정보': total_infos,
            '학습 완료': learned_infos
        })
    if chart_data:
        df = pd.DataFrame(chart_data)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['날짜'], y=df['전체 정보'], name='전체 정보', marker_color='#b2bfff', opacity=0.6))
        fig.add_trace(go.Bar(x=df['날짜'], y=df['학습 완료'], name='학습 완료', marker_color='#43cea2', opacity=0.9))
        fig.add_trace(go.Scatter(x=df['날짜'], y=df['학습 완료'], name='학습 완료(꺾은선)', mode='lines+markers', line=dict(color='#ff7f50', width=4)))
        fig.update_layout(
            barmode='overlay',
            height=400,
            template='plotly_white',
            title='날짜별 학습 현황',
            xaxis=dict(title='날짜', tickangle=-45),
            yaxis=dict(title='개수'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    # 성취 목록
    st.markdown("### 🏆 성취 시스템")
    for achievement in achievements:
        achieved = achievement['name'] in st.session_state.user_stats['achievements']
        status = "✅" if achieved else "⏳"
        st.markdown(f"{status} **{achievement['name']}**: {achievement['description']}")
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[5]:
    # 관리자
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">⚙️ 관리자 설정</h2>', unsafe_allow_html=True)
    st.info(f"관리자 비밀번호는 기본값으로 `{ADMIN_PASSWORD}` 입니다. 실제 배포시에는 환경변수 등으로 보안을 강화하세요.")
    # 관리자 인증 (간단한 패스워드)
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if not st.session_state.admin_authenticated:
        with st.form("admin_login_form"):
            password = st.text_input("관리자 비밀번호", type="password")
            submit_button = st.form_submit_button("로그인")
            if submit_button:
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_authenticated = True
                    st.success("관리자 인증이 완료되었습니다.")
                    st.rerun()
                else:
                    st.error("잘못된 비밀번호입니다.")
                    st.session_state.admin_authenticated = False
    else:
        # 관리자 탭 생성
        admin_tabs = st.tabs(["📊 데이터 관리", "🎯 퀴즈 관리", "🤖 프롬프트 관리"])
        # --- DB 전체 백업 버튼 추가 ---
        with st.expander("💾 DB 전체 백업/다운로드"):
            with open("ai_info.db", "rb") as f:
                st.download_button(
                    label="DB 전체 백업 다운로드 (ai_info.db)",
                    data=f,
                    file_name="ai_info.db",
                    mime="application/octet-stream"
                )
        # 1. 데이터 관리 탭
        with admin_tabs[0]:
            st.markdown('<h3 class="section-title">📊 데이터 관리</h3>', unsafe_allow_html=True)
            # --- AI 정보 추가 ---
            st.markdown("### 📝 AI 정보 추가")
            input_date = st.date_input("날짜 선택", date.today())
            input_date_str = input_date.isoformat()
            existing_infos = get_ai_info_by_date_wrapper(input_date_str)

            # session_state에 입력값 저장 (날짜별로 분리, 최초 렌더링 시에만)
            if f"info1_{input_date_str}" not in st.session_state:
                st.session_state[f"info1_{input_date_str}"] = existing_infos[0] if existing_infos else ""
            if f"info2_{input_date_str}" not in st.session_state:
                st.session_state[f"info2_{input_date_str}"] = existing_infos[1] if existing_infos else ""
            if f"info3_{input_date_str}" not in st.session_state:
                st.session_state[f"info3_{input_date_str}"] = existing_infos[2] if existing_infos else ""

            info1 = st.text_area("정보 1", key=f"info1_{input_date_str}")
            info2 = st.text_area("정보 2", key=f"info2_{input_date_str}")
            info3 = st.text_area("정보 3", key=f"info3_{input_date_str}")

            if st.button("저장"):
                add_ai_info_checked(input_date_str, [
                    st.session_state[f"info1_{input_date_str}"],
                    st.session_state[f"info2_{input_date_str}"],
                    st.session_state[f"info3_{input_date_str}"]
                ])
                st.success("저장되었습니다!")
                # 저장 후 입력값을 비우고 싶으면 아래 주석 해제
                # st.session_state[f"info1_{input_date_str}"] = ""
                # st.session_state[f"info2_{input_date_str}"] = ""
                # st.session_state[f"info3_{input_date_str}"] = ""

            with col2:
                if st.button("🗑️ 기존 정보 삭제") and existing_infos:
                    if input_date_str in ai_info_db:
                        del ai_info_db[input_date_str]
                        st.success("기존 정보가 삭제되었습니다.")
                        st.rerun()
            # --- 데이터 통계 ---
            st.markdown("---")
            st.markdown("### 📊 데이터 관리")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("등록된 날짜", len(get_all_ai_info_dates()))
            with col2:
                st.metric("총 AI 정보", len(get_all_ai_info_dates()) * 3)
            with col3:
                total_users_learned = sum(len(progress) for progress in st.session_state.user_progress.values())
                st.metric("총 학습 완료", total_users_learned)
            # --- 등록된 AI 정보 관리 ---
            st.markdown("#### 등록된 AI 정보 관리")
            for date_str in sorted(get_all_ai_info_dates(), reverse=True):
                infos = get_ai_info_by_date_wrapper(date_str)
                with st.expander(f"📅 {date_str}"):
                    for i, info in enumerate(infos):
                        key_prefix = f"aiinfo_{date_str}_{i}"
                        new_info = st.text_area(f"정보 {i+1}", value=info, key=f"edit_{key_prefix}")
                        st.markdown("**미리보기:**")
                        render_info(new_info)
                        col1, col2 = st.columns([1,1])
                        with col1:
                            if st.button("저장", key=f"save_{key_prefix}"):
                                ai_info_db[date_str][i] = new_info
                                st.success("정보가 수정되었습니다!")
                                st.rerun()
                        with col2:
                            if st.button("삭제", key=f"delete_{key_prefix}"):
                                ai_info_db[date_str].pop(i)
                                st.success("정보가 삭제되었습니다!")
                                if not ai_info_db[date_str]:
                                    del ai_info_db[date_str]
                                st.rerun()

        # 2. 퀴즈 관리 탭
        with admin_tabs[1]:
            st.markdown('<h3 class="section-title">🎯 퀴즈 관리</h3>', unsafe_allow_html=True)
            quiz_topic = st.selectbox("퀴즈 주제", list(quiz_db.keys()) + ["새 주제 추가"])
            if quiz_topic == "새 주제 추가":
                new_topic = st.text_input("새 주제 이름")
                if new_topic and st.button("주제 추가"):
                    quiz_db[new_topic] = []
                    st.success(f"새 주제 '{new_topic}'이 추가되었습니다.")
                    st.rerun()
            else:
                st.write(f"**{quiz_topic}** 주제의 퀴즈: {len(quiz_db[quiz_topic])}개")
                for idx, quiz in enumerate(quiz_db[quiz_topic]):
                    with st.expander(f"Q{idx+1}: {quiz['question']}"):
                        st.write(f"- 선택지: {quiz['options']}")
                        st.write(f"- 정답: {quiz['options'][quiz['correct']]}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"수정", key=f"edit_quiz_{quiz_topic}_{idx}"):
                                st.session_state[f"edit_quiz_{quiz_topic}_{idx}"] = True
                        with col2:
                            if st.button(f"삭제", key=f"delete_quiz_{quiz_topic}_{idx}"):
                                quiz_db[quiz_topic].pop(idx)
                                st.success("퀴즈가 삭제되었습니다!")
                                st.rerun()
                        if st.session_state.get(f"edit_quiz_{quiz_topic}_{idx}", False):
                            new_q = st.text_input("질문", value=quiz['question'], key=f"edit_q_{quiz_topic}_{idx}")
                            new_opts = [
                                st.text_input(f"선택지 1", value=quiz['options'][0], key=f"edit_opt1_{quiz_topic}_{idx}"),
                                st.text_input(f"선택지 2", value=quiz['options'][1], key=f"edit_opt2_{quiz_topic}_{idx}"),
                                st.text_input(f"선택지 3", value=quiz['options'][2], key=f"edit_opt3_{quiz_topic}_{idx}"),
                                st.text_input(f"선택지 4", value=quiz['options'][3], key=f"edit_opt4_{quiz_topic}_{idx}")
                            ]
                            new_correct = st.selectbox("정답", [1,2,3,4], index=quiz['correct'], key=f"edit_correct_{quiz_topic}_{idx}") - 1
                            if st.button("저장", key=f"save_quiz_{quiz_topic}_{idx}"):
                                quiz_db[quiz_topic][idx] = {
                                    "question": new_q,
                                    "options": new_opts,
                                    "correct": new_correct
                                }
                                st.session_state[f"edit_quiz_{quiz_topic}_{idx}"] = False
                                st.success("퀴즈가 수정되었습니다!")
                                st.rerun()
                            if st.button("수정 취소", key=f"cancel_edit_{quiz_topic}_{idx}"):
                                st.session_state[f"edit_quiz_{quiz_topic}_{idx}"] = False
                with st.expander("새 퀴즈 추가"):
                    # 프롬프트 선택 드롭다운
                    prompt_default = "프롬프트에서 불러오기 (선택)"
                    prompt_options = [prompt_default]
                    prompt_map = {}
                    if 'prompt_storage' in st.session_state and st.session_state.prompt_storage:
                        for i, p in enumerate(st.session_state.prompt_storage):
                            label = f"{p['title']} ({p['category']})"
                            prompt_options.append(label)
                            prompt_map[label] = p['content']
                    selected_prompt = st.selectbox("프롬프트 불러오기", prompt_options)
                    # 전체 입력 텍스트박스
                    if 'quiz_input_text' not in st.session_state:
                        st.session_state.quiz_input_text = ""
                    if selected_prompt != prompt_default:
                        st.session_state.quiz_input_text = prompt_map[selected_prompt]
                    quiz_input = st.text_area(
                        "퀴즈 전체 입력 (아래 예시처럼 입력)",
                        value=st.session_state.quiz_input_text,
                        height=200,
                        placeholder="질문: AI란 무엇인가요?\n선택지1: 인공지능\n선택지2: 기계학습\n선택지3: 데이터베이스\n선택지4: 하드웨어\n해설: 인공지능은 AI의 약자입니다."
                    )
                    # 파싱 함수
                    import re
                    def parse_quiz_input(text):
                        q = o1 = o2 = o3 = o4 = exp = None
                        lines = text.splitlines()
                        for line in lines:
                            if line.startswith("질문:"):
                                q = line.replace("질문:", "").strip()
                            elif line.startswith("선택지1:"):
                                o1 = line.replace("선택지1:", "").strip()
                            elif line.startswith("선택지2:"):
                                o2 = line.replace("선택지2:", "").strip()
                            elif line.startswith("선택지3:"):
                                o3 = line.replace("선택지3:", "").strip()
                            elif line.startswith("선택지4:"):
                                o4 = line.replace("선택지4:", "").strip()
                            elif line.startswith("해설:"):
                                exp = line.replace("해설:", "").strip()
                        return q, [o1, o2, o3, o4], exp
                    # 퀴즈 추가 버튼
                    if st.button("퀴즈 추가"):
                        question, options, explanation = parse_quiz_input(quiz_input)
                        if question and all(options):
                            new_quiz = {
                                "question": question,
                                "options": options,
                                "correct": 0,  # 기본값: 첫 번째 선택지가 정답
                                "explanation": explanation if explanation else ""
                            }
                            quiz_db[quiz_topic].append(new_quiz)
                            st.success("새 퀴즈가 추가되었습니다!")
                            st.session_state.quiz_input_text = ""
                            st.rerun()
                        else:
                            st.error("질문과 4개의 선택지를 모두 입력해주세요. (해설은 선택사항)")

        # 3. 프롬프트 관리 탭
        with admin_tabs[2]:
            st.markdown('<h3 class="section-title">🤖 프롬프트 관리</h3>', unsafe_allow_html=True)
            # --- 시스템 관리 ---
            st.markdown("### 🔄 시스템 관리")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 사용자 진행상황 초기화"):
                    st.session_state.user_progress = {}
                    st.session_state.user_stats = {
                        'total_learned': 0,
                        'streak_days': 0,
                        'last_learned_date': None,
                        'quiz_score': 0,
                        'achievements': []
                    }
                    st.success("사용자 진행상황이 초기화되었습니다.")
                    st.rerun()
            with col2:
                if st.button("📤 데이터 백업"):
                    backup_data = {
                        'ai_info_db': ai_info_db,
                        'quiz_db': quiz_db,
                        'user_progress': st.session_state.user_progress,
                        'user_stats': st.session_state.user_stats
                    }
                    st.download_button(
                        label="💾 백업 파일 다운로드",
                        data=json.dumps(backup_data, ensure_ascii=False, indent=2),
                        file_name=f"ai_learning_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

        # --- 프롬프트 관리 ---
        st.markdown("---")
        st.markdown("### 📝 새 프롬프트 추가")

        if 'prompt_storage' not in st.session_state:
            st.session_state.prompt_storage = []

        prompt_title = st.text_input("프롬프트 제목")
        prompt_content = st.text_area("프롬프트 내용", height=150, placeholder="예: AI 기술에 대해 설명해주세요. 특히 머신러닝과 딥러닝의 차이점을 중심으로...")
        prompt_category = st.selectbox("카테고리", ["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 프롬프트 저장"):
                if prompt_title and prompt_content:
                    new_prompt = {
                        "title": prompt_title,
                        "content": prompt_content,
                        "category": prompt_category,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.prompt_storage.append(new_prompt)
                    st.success("프롬프트가 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("제목과 내용을 모두 입력해주세요.")
        with col2:
            if st.button("🗑️ 입력 초기화"):
                st.rerun()

        if st.session_state.prompt_storage:
            st.markdown("#### 📚 저장된 프롬프트 목록")
            categories = list(set([p["category"] for p in st.session_state.prompt_storage]))
            selected_category = st.selectbox("카테고리 필터", ["전체"] + categories)
            filtered_prompts = st.session_state.prompt_storage

            if selected_category != "전체":
                filtered_prompts = [p for p in st.session_state.prompt_storage if p["category"] == selected_category]

            for i, prompt in enumerate(filtered_prompts):
                edit_key = f"edit_prompt_{i}"
                if st.session_state.get(edit_key, False):
                    with st.expander(f"📝 {prompt['title']} ({prompt['category']}) [수정 중]"):
                        new_title = st.text_input("프롬프트 제목", value=prompt['title'], key=f"edit_title_{i}")
                        new_content = st.text_area("프롬프트 내용", value=prompt['content'], height=150, key=f"edit_content_{i}")
                        new_category = st.selectbox(
                            "카테고리",
                            ["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"],
                            index=["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"].index(prompt['category']),
                            key=f"edit_category_{i}"
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("저장", key=f"save_edit_prompt_{i}"):
                                prompt['title'] = new_title
                                prompt['content'] = new_content
                                prompt['category'] = new_category
                                st.session_state[edit_key] = False
                                st.success("프롬프트가 수정되었습니다!")
                                st.rerun()
                        with col2:
                            if st.button("수정 취소", key=f"cancel_edit_prompt_{i}"):
                                st.session_state[edit_key] = False
                                st.rerun()
                else:
                    with st.expander(f"📝 {prompt['title']} ({prompt['category']})"):
                        st.markdown(f"**생성일:** {prompt['created_at']}")
                        st.markdown("**내용:**")
                        st.text_area("프롬프트 내용", value=prompt['content'], height=100, key=f"view_prompt_{i}", disabled=True)

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            if st.button("📋 복사", key=f"copy_prompt_{i}"):
                                st.write("프롬프트가 클립보드에 복사되었습니다!")
                                st.code(prompt['content'])
                        with col2:
                            if st.button("🔗 ChatGPT 링크", key=f"chatgpt_link_{i}"):
                                encoded_prompt = prompt['content'].replace('\n', '%0A').replace(' ', '%20')
                                chatgpt_url = f"https://chat.openai.com/?q={encoded_prompt}"
                                st.markdown(f"[🤖 ChatGPT에서 질문하기]({chatgpt_url})")
                                st.info("위 링크를 클릭하면 ChatGPT에서 이 프롬프트로 질문할 수 있습니다.")
                        with col3:
                            if st.button("🗑️ 삭제", key=f"delete_prompt_{i}"):
                                st.session_state.prompt_storage.pop(i)
                                st.success("프롬프트가 삭제되었습니다!")
                                st.rerun()
                        with col4:
                            if st.button("✏️ 수정", key=f"edit_btn_prompt_{i}"):
                                st.session_state[edit_key] = True
                                st.rerun()
        else:
            st.info("저장된 프롬프트가 없습니다. 새 프롬프트를 추가해보세요!")

        # --- 기반 내용 관리 ---
        st.markdown("---")
        st.markdown("### 📝 새 기반 내용 추가")

        if 'base_storage' not in st.session_state:
            st.session_state.base_storage = []

        base_title = st.text_input("기반 내용 제목")
        base_content = st.text_area("기반 내용", height=150, placeholder="예: AI의 역사적 발전 과정을 간략히 서술하세요.")
        base_category = st.selectbox("카테고리", ["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"], key="base_category_select")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 기반 내용 저장"):
                if base_title and base_content:
                    new_base = {
                        "title": base_title,
                        "content": base_content,
                        "category": base_category,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.base_storage.append(new_base)
                    st.success("기반 내용이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("제목과 내용을 모두 입력해주세요.")
        with col2:
            if st.button("🗑️ 입력 초기화", key="base_clear_btn"):
                st.rerun()

        if st.session_state.base_storage:
            st.markdown("#### 📚 저장된 기반 내용 목록")
            base_categories = list(set([b["category"] for b in st.session_state.base_storage]))
            selected_base_category = st.selectbox("카테고리 필터", ["전체"] + base_categories, key="base_category_filter")
            filtered_bases = st.session_state.base_storage

            if selected_base_category != "전체":
                filtered_bases = [b for b in st.session_state.base_storage if b["category"] == selected_base_category]

            for i, base in enumerate(filtered_bases):
                edit_key = f"edit_base_{i}"
                if st.session_state.get(edit_key, False):
                    with st.expander(f"📝 {base['title']} ({base['category']}) [수정 중]"):
                        new_title = st.text_input("기반 내용 제목", value=base['title'], key=f"edit_base_title_{i}")
                        new_content = st.text_area("기반 내용", value=base['content'], height=150, key=f"edit_base_content_{i}")
                        new_category = st.selectbox(
                            "카테고리",
                            ["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"],
                            index=["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"].index(base['category']),
                            key=f"edit_base_category_{i}"
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("저장", key=f"save_edit_base_{i}"):
                                base['title'] = new_title
                                base['content'] = new_content
                                base['category'] = new_category
                                st.session_state[edit_key] = False
                                st.success("기반 내용이 수정되었습니다!")
                                st.rerun()
                        with col2:
                            if st.button("수정 취소", key=f"cancel_edit_base_{i}"):
                                st.session_state[edit_key] = False
                                st.rerun()
                else:
                    with st.expander(f"📝 {base['title']} ({base['category']})"):
                        st.markdown(f"**생성일:** {base['created_at']}")
                        st.markdown("**내용:**")
                        st.text_area("기반 내용", value=base['content'], height=100, key=f"view_base_{i}", disabled=True)

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            if st.button("📋 복사", key=f"copy_base_{i}"):
                                st.write("기반 내용이 클립보드에 복사되었습니다!")
                                st.code(base['content'])
                        with col2:
                            if st.button("🔗 ChatGPT 링크", key=f"chatgpt_link_base_{i}"):
                                encoded_base = base['content'].replace('\n', '%0A').replace(' ', '%20')
                                chatgpt_url = f"https://chat.openai.com/?q={encoded_base}"
                                st.markdown(f"[🤖 ChatGPT에서 질문하기]({chatgpt_url})")
                                st.info("위 링크를 클릭하면 ChatGPT에서 이 기반 내용으로 질문할 수 있습니다.")
                        with col3:
                            if st.button("🗑️ 삭제", key=f"delete_base_{i}"):
                                st.session_state.base_storage.pop(i)
                                st.success("기반 내용이 삭제되었습니다!")
                                st.rerun()
                        with col4:
                            if st.button("✏️ 수정", key=f"edit_btn_base_{i}"):
                                st.session_state[edit_key] = True
                                st.rerun()
        else:
            st.info("저장된 기반 내용이 없습니다. 새 기반 내용을 추가해보세요!")

        # --- 프롬프트 + 기반 내용 ChatGPT 링크 생성기 ---
        st.markdown("---")
        st.markdown("### 🔗 프롬프트 + 기반 내용 ChatGPT 링크 생성기")

        with st.expander("🌐 프롬프트와 기반 내용 합치기"):
            st.markdown("**사용법:** 기존 프롬프트와 기반 내용을 각각 선택하면 합쳐진 내용으로 ChatGPT 링크를 생성합니다.")
            if 'base_storage' in st.session_state and st.session_state.prompt_storage and st.session_state.base_storage:
                prompt_options = [f"{p['title']} ({p['category']})" for p in st.session_state.prompt_storage]
                base_options = [f"{b['title']} ({b['category']})" for b in st.session_state.base_storage]
                selected_prompt_idx = st.selectbox("프롬프트 선택", range(len(st.session_state.prompt_storage)), format_func=lambda x: prompt_options[x], key="combine_prompt_select")
                selected_base_idx = st.selectbox("기반 내용 선택", range(len(st.session_state.base_storage)), format_func=lambda x: base_options[x], key="combine_base_select")
                selected_prompt = st.session_state.prompt_storage[selected_prompt_idx]
                selected_base = st.session_state.base_storage[selected_base_idx]
                st.markdown("**선택된 프롬프트:**")
                st.info(selected_prompt['content'])
                st.markdown("**선택된 기반 내용:**")
                st.info(selected_base['content'])
                combined_question = selected_prompt['content'] + "\n\n" + selected_base['content']
                st.markdown("**합쳐진 질문 미리보기:**")
                st.text_area("최종 질문", value=combined_question, height=200, disabled=False, key="combined_final_text")
                # ChatGPT 링크 생성
                encoded_combined = combined_question.replace('\n', '%0A').replace(' ', '%20')
                chatgpt_url = f"https://chat.openai.com/?q={encoded_combined}"
                st.markdown(f"[🤖 ChatGPT에서 질문하기]({chatgpt_url})")
            else:
                st.warning("프롬프트와 기반 내용이 모두 저장되어 있어야 합치기 기능을 사용할 수 있습니다.")


# --- 푸터 ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.7);">
    <p>🧠 AI Mastery Hub | 매일 새로운 AI 지식을 학습하세요!</p>
    <p>Made with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)

# 자동 저장 (실제 배포시에는 데이터베이스 사용 권장)
if 'data_saved' not in st.session_state:
    st.session_state.data_saved = True
