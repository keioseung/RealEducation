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
    get_all_base_contents, add_base_content, update_base_content, delete_base_content,
    update_ai_info_item, delete_ai_info_item
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
    # --- 추가 용어 50개 이상 ---
    {"term": "인공신경망", "desc": "뇌의 신경망을 모방한 머신러닝 모델."},
    {"term": "퍼셉트론", "desc": "가장 기본적인 인공신경망 구조."},
    {"term": "딥페이크", "desc": "AI로 합성된 가짜 이미지/영상."},
    {"term": "GAN", "desc": "생성적 적대 신경망. 이미지를 생성하는 데 자주 사용."},
    {"term": "BERT", "desc": "구글이 개발한 자연어 처리 사전학습 모델."},
    {"term": "GPT", "desc": "OpenAI의 대형 언어 생성 모델."},
    {"term": "어텐션", "desc": "입력의 중요도를 동적으로 반영하는 메커니즘."},
    {"term": "샘플링", "desc": "데이터에서 일부를 추출하는 과정."},
    {"term": "정규화", "desc": "데이터의 분포를 일정하게 맞추는 전처리."},
    {"term": "표준화", "desc": "평균 0, 분산 1로 데이터 변환."},
    {"term": "원-핫 인코딩", "desc": "범주형 데이터를 벡터로 변환하는 방법."},
    {"term": "임베딩", "desc": "고차원 데이터를 저차원 벡터로 변환."},
    {"term": "클러스터링", "desc": "비슷한 데이터끼리 묶는 비지도학습 방법."},
    {"term": "K-평균", "desc": "대표적인 클러스터링 알고리즘."},
    {"term": "PCA", "desc": "주성분 분석. 차원 축소 기법."},
    {"term": "t-SNE", "desc": "고차원 데이터를 2~3차원으로 시각화하는 기법."},
    {"term": "의사결정나무", "desc": "분류/회귀에 사용되는 트리 기반 모델."},
    {"term": "랜덤포레스트", "desc": "여러 결정나무를 앙상블하는 모델."},
    {"term": "그래디언트 부스팅", "desc": "오차를 줄이기 위해 여러 모델을 순차적으로 결합."},
    {"term": "XGBoost", "desc": "성능이 뛰어난 그래디언트 부스팅 라이브러리."},
    {"term": "로지스틱 회귀", "desc": "이진 분류에 사용되는 통계적 모델."},
    {"term": "선형 회귀", "desc": "연속형 값을 예측하는 기본 회귀 모델."},
    {"term": "SVM", "desc": "서포트 벡터 머신. 분류/회귀에 사용."},
    {"term": "KNN", "desc": "가장 가까운 이웃을 기준으로 분류/회귀."},
    {"term": "앙상블", "desc": "여러 모델을 결합해 성능을 높이는 방법."},
    {"term": "교차검증", "desc": "데이터를 여러 번 나눠 모델을 평가하는 방법."},
    {"term": "정확도", "desc": "전체 중 맞춘 비율."},
    {"term": "정밀도", "desc": "양성 예측 중 실제 양성 비율."},
    {"term": "재현율", "desc": "실제 양성 중 맞춘 비율."},
    {"term": "F1 점수", "desc": "정밀도와 재현율의 조화 평균."},
    {"term": "ROC 곡선", "desc": "분류 모델의 성능을 시각화하는 곡선."},
    {"term": "AUC", "desc": "ROC 곡선 아래 면적. 성능 지표."},
    {"term": "과적합 방지", "desc": "오버피팅을 막기 위한 다양한 기법."},
    {"term": "드롭아웃", "desc": "신경망 학습 시 일부 노드를 임의로 꺼서 과적합 방지."},
    {"term": "배치 정규화", "desc": "학습 안정성과 속도를 높이는 신경망 기법."},
    {"term": "활성화 함수", "desc": "신경망의 출력값을 결정하는 함수."},
    {"term": "ReLU", "desc": "대표적인 활성화 함수. 0 이하를 0, 이상은 그대로 출력."},
    {"term": "시그모이드", "desc": "출력을 0~1로 변환하는 활성화 함수."},
    {"term": "소프트맥스", "desc": "출력을 확률 분포로 변환."},
    {"term": "최적화 알고리즘", "desc": "모델의 성능을 높이기 위한 파라미터 조정 방법."},
    {"term": "SGD", "desc": "확률적 경사 하강법. 대표적 최적화 알고리즘."},
    {"term": "Adam", "desc": "적응적 학습률을 사용하는 최적화 알고리즘."},
    {"term": "러닝레이트", "desc": "학습 속도를 조절하는 하이퍼파라미터."},
    {"term": "에폭", "desc": "전체 데이터를 한 번 학습하는 주기."},
    {"term": "배치", "desc": "한 번에 학습에 사용하는 데이터 묶음."},
    {"term": "파이썬", "desc": "AI/머신러닝 개발에 가장 널리 쓰이는 프로그래밍 언어."},
    {"term": "텐서플로우", "desc": "구글이 개발한 딥러닝 프레임워크."},
    {"term": "파이토치", "desc": "페이스북이 개발한 딥러닝 프레임워크."},
    {"term": "오픈소스", "desc": "누구나 사용할 수 있도록 공개된 소프트웨어."},
    {"term": "빅데이터", "desc": "대용량, 다양한 데이터. AI의 원천."},
    {"term": "데이터 전처리", "desc": "AI 학습을 위해 데이터를 정제/가공하는 과정."},
    {"term": "피처 엔지니어링", "desc": "데이터에서 의미 있는 특징을 추출하는 작업."},
    {"term": "EDA", "desc": "탐색적 데이터 분석. 데이터의 특성을 파악하는 과정."},
    {"term": "AI 윤리", "desc": "AI의 공정성, 투명성, 책임성 등 윤리적 문제 연구."},
    {"term": "설명 가능한 AI", "desc": "AI의 의사결정 과정을 사람이 이해할 수 있게 설명."},
    {"term": "AI 트렌드", "desc": "최신 인공지능 연구 및 산업 동향."},
    {"term": "AI 실무", "desc": "현장에서 실제로 활용되는 AI 기술과 사례."},
    {"term": "AI 평가", "desc": "AI 모델의 성능을 측정하고 비교하는 방법."},
    {"term": "AI 활용", "desc": "AI를 다양한 분야에 적용하는 방법."},
    {"term": "AI 정책", "desc": "정부 및 기관의 인공지능 관련 정책."},
    {"term": "AI 교육", "desc": "AI를 배우고 가르치는 방법과 과정."},
    {"term": "AI 스타트업", "desc": "AI 기술을 기반으로 한 신생 기업."},
    {"term": "AI 윤리 가이드라인", "desc": "AI 개발과 활용 시 지켜야 할 윤리 기준."},
    {"term": "AI 거버넌스", "desc": "AI의 책임 있는 관리와 운영 체계."},
    {"term": "AI 규제", "desc": "AI 기술의 남용을 막기 위한 법적 규제."},
    {"term": "AI 보안", "desc": "AI 시스템의 안전성과 보안."},
    {"term": "AI 데이터셋", "desc": "AI 학습에 사용되는 데이터 모음."},
    {"term": "AI 벤치마크", "desc": "AI 모델의 성능을 비교하는 표준 테스트."},
    {"term": "AI 하드웨어", "desc": "AI 연산에 특화된 컴퓨터 장치."},
    {"term": "AI 칩", "desc": "AI 처리를 위한 전용 반도체."},
    {"term": "AI 클라우드", "desc": "클라우드 환경에서 제공되는 AI 서비스."},
    {"term": "AI API", "desc": "AI 기능을 쉽게 사용할 수 있게 해주는 인터페이스."},
    {"term": "AI 오픈소스 프로젝트", "desc": "공개된 AI 개발 프로젝트."},
    {"term": "AI 경진대회", "desc": "AI 기술력을 겨루는 대회."},
    {"term": "AI 논문", "desc": "최신 AI 연구 결과를 담은 논문."},
    {"term": "AI 저널", "desc": "AI 관련 학술지."},
    {"term": "AI 커뮤니티", "desc": "AI 개발자와 연구자들의 온라인 모임."},
    {"term": "AI 윤리적 이슈", "desc": "AI가 야기할 수 있는 사회적, 윤리적 문제."},
    {"term": "AI 인재", "desc": "AI 분야의 전문가와 인재."},
    {"term": "AI 직업", "desc": "AI와 관련된 다양한 직업."},
    {"term": "AI 미래", "desc": "AI가 바꿀 미래 사회와 산업."},
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
        for i, info in enumerate(today_infos):  # 모든 정보 표시
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                <div class="info-card">
                    <h4>💡 정보 {i+1}</h4>
                    <p>{info['title']}</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button(f"📖 학습하기", key=f"home_learn_info_{i}"):
                    st.session_state.menu = "📚 오늘의 학습"
                    st.rerun()
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
    all_dates = get_all_ai_info_dates()
    from datetime import date
    def safe_to_date(val):
        try:
            if isinstance(val, str) and val:
                return date.fromisoformat(val)
            elif isinstance(val, date):
                return val
        except Exception:
            pass
        return date.today()

    if all_dates and all_dates[0]:
        min_date = safe_to_date(all_dates[0])
        max_date = safe_to_date(all_dates[-1])
        today_date = date.today()
        # value가 범위 밖이면 min_date로 대체
        if not (min_date <= today_date <= max_date):
            today_date = min_date
        selected_date = st.date_input(
            "학습할 날짜를 선택하세요",
            value=today_date,
            min_value=min_date,
            max_value=max_date,
            key="learn_date_input"
        )
        selected_date_str = selected_date.isoformat()
        infos = get_ai_info_by_date_wrapper(selected_date_str)
        if infos:
            learned_list = st.session_state.user_progress.get(selected_date_str, [])
            st.markdown(f"<b>오늘의 목표:</b> {len(infos)}개 정보 모두 학습하기", unsafe_allow_html=True)
            st.progress(len(learned_list) / len(infos) if infos else 0.0, text=f"{len(learned_list)}/{len(infos)} 완료")
            for i, info in enumerate(infos, 1):
                learned = i-1 in learned_list
                st.markdown(f"""
                <div class="info-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4>{info['title'] or f'AI 정보 {i}'}</h4>
                        <div>{'✅ 학습완료' if learned else '📖 학습하기'}</div>
                    </div>
                """, unsafe_allow_html=True)
                render_info(info['content'], key=f"learn_{selected_date_str}_{i}")
                st.markdown("</div>", unsafe_allow_html=True)
                if not learned:
                    if st.button(f"✅ 정보 {i} 학습 완료", key=f"learn_info_{selected_date_str}_{i}_new"):
                        update_user_progress(selected_date_str, i-1)
                        new_achievements = check_achievements()
                        st.success(f"🎉 정보 {i}을(를) 학습하셨습니다!")
                        if new_achievements:
                            for achievement in new_achievements:
                                st.balloons()
                                st.success(f"🏆 새로운 성취를 달성했습니다: {achievement['name']}")
                        st.rerun()
            if len(learned_list) == len(infos):
                st.success("🎉 오늘의 모든 정보를 학습하셨습니다! AI 마스터에 한 걸음 더 가까워졌어요!")
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
                st.markdown(f"{status} <b>{info['title'] or f'정보 {i+1}'}</b>", unsafe_allow_html=True)
                render_info(info['content'], key=f"record_{date_str}_{i}")
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
            st.markdown("### 📝 AI 정보 추가")
            input_date = st.date_input("날짜 선택", date.today())
            input_date_str = input_date.isoformat()
            existing_infos = get_ai_info_by_date_wrapper(input_date_str)
            # 제목+내용 입력 필드
            for i in range(3):
                st.markdown(f"#### 정보 {i+1}")
                title_key = f"info{i+1}_title_{input_date_str}"
                content_key = f"info{i+1}_content_{input_date_str}"
                if title_key not in st.session_state:
                    st.session_state[title_key] = existing_infos[i]["title"] if existing_infos and len(existing_infos) > i else ""
                if content_key not in st.session_state:
                    st.session_state[content_key] = existing_infos[i]["content"] if existing_infos and len(existing_infos) > i else ""
                st.text_input("제목", key=title_key)
                st.text_area("내용", key=content_key)
            if st.button("저장"):
                infos = [
                    {"title": st.session_state[f"info1_title_{input_date_str}"], "content": st.session_state[f"info1_content_{input_date_str}"]},
                    {"title": st.session_state[f"info2_title_{input_date_str}"], "content": st.session_state[f"info2_content_{input_date_str}"]},
                    {"title": st.session_state[f"info3_title_{input_date_str}"], "content": st.session_state[f"info3_content_{input_date_str}"]},
                ]
                add_ai_info(input_date_str, infos)
                st.success("저장되었습니다!")
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
                                update_ai_info_item(date_str, i, new_info)
                                st.success("정보가 수정되었습니다!")
                                st.rerun()
                        with col2:
                            if st.button("삭제", key=f"delete_{key_prefix}"):
                                delete_ai_info_item(date_str, i)
                                st.success("정보가 삭제되었습니다!")
                                st.rerun()

        # 2. 퀴즈 관리 탭
        with admin_tabs[1]:
            st.markdown('<h3 class="section-title">🎯 퀴즈 관리</h3>', unsafe_allow_html=True)
            quiz_topics = get_all_quiz_topics()
            quiz_topic = st.selectbox("퀴즈 주제", quiz_topics + ["새 주제 추가"])
            if quiz_topic == "새 주제 추가":
                new_topic = st.text_input("새 주제 이름")
                if new_topic and st.button("주제 추가"):
                    st.session_state['new_quiz_topic'] = new_topic
                    st.success(f"새 주제 '{new_topic}'이 추가되었습니다! 새로고침 후 사용하세요.")
                    st.rerun()
            else:
                quizzes = get_quiz_by_topic(quiz_topic)
                st.write(f"**{quiz_topic}** 주제의 퀴즈: {len(quizzes)}개")
                for quiz in quizzes:
                    with st.expander(f"Q{quiz.id}: {quiz.question}"):
                        st.write(f"- 선택지: {[quiz.option1, quiz.option2, quiz.option3, quiz.option4]}")
                        st.write(f"- 정답: {[quiz.option1, quiz.option2, quiz.option3, quiz.option4][quiz.correct]}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"수정", key=f"edit_quiz_{quiz.id}"):
                                st.session_state[f"edit_quiz_{quiz.id}"] = True
                        with col2:
                            if st.button(f"삭제", key=f"delete_quiz_{quiz.id}"):
                                delete_quiz(quiz.id)
                                st.success("퀴즈가 삭제되었습니다!")
                                st.rerun()
                        if st.session_state.get(f"edit_quiz_{quiz.id}", False):
                            new_q = st.text_input("질문", value=quiz.question, key=f"edit_q_{quiz.id}")
                            new_opts = [
                                st.text_input(f"선택지 1", value=quiz.option1, key=f"edit_opt1_{quiz.id}"),
                                st.text_input(f"선택지 2", value=quiz.option2, key=f"edit_opt2_{quiz.id}"),
                                st.text_input(f"선택지 3", value=quiz.option3, key=f"edit_opt3_{quiz.id}"),
                                st.text_input(f"선택지 4", value=quiz.option4, key=f"edit_opt4_{quiz.id}")
                            ]
                            new_correct = st.selectbox("정답", [1,2,3,4], index=quiz.correct, key=f"edit_correct_{quiz.id}") - 1
                            new_exp = st.text_input("해설", value=quiz.explanation, key=f"edit_exp_{quiz.id}")
                            if st.button("저장", key=f"save_quiz_{quiz.id}"):
                                update_quiz(quiz.id, new_q, new_opts, new_correct, new_exp)
                                st.session_state[f"edit_quiz_{quiz.id}"] = False
                                st.success("퀴즈가 수정되었습니다!")
                                st.rerun()
                            if st.button("수정 취소", key=f"cancel_edit_{quiz.id}"):
                                st.session_state[f"edit_quiz_{quiz.id}"] = False
            with st.expander("새 퀴즈 추가"):
                question = st.text_input("질문", key="new_quiz_q")
                options = [
                    st.text_input("선택지 1", key="new_quiz_opt1"),
                    st.text_input("선택지 2", key="new_quiz_opt2"),
                    st.text_input("선택지 3", key="new_quiz_opt3"),
                    st.text_input("선택지 4", key="new_quiz_opt4")
                ]
                correct = st.selectbox("정답", [1,2,3,4], key="new_quiz_correct") - 1
                explanation = st.text_input("해설", key="new_quiz_exp")
                if st.button("퀴즈 추가", key="add_new_quiz"):
                    if question and all(options):
                        add_quiz(quiz_topic, question, options, correct, explanation)
                        st.success("새 퀴즈가 추가되었습니다!")
                        st.rerun()
                    else:
                        st.error("질문과 4개의 선택지를 모두 입력해주세요. (해설은 선택사항)")

        # 3. 프롬프트 관리 탭
        with admin_tabs[2]:
            st.markdown('<h3 class="section-title">🤖 프롬프트 관리</h3>', unsafe_allow_html=True)
            # 프롬프트 목록
            prompts = get_all_prompts()
            for prompt in prompts:
                edit_key = f"edit_prompt_{prompt.id}"
                if st.session_state.get(edit_key, False):
                    with st.expander(f"📝 {prompt.title} ({prompt.category}) [수정 중]"):
                        new_title = st.text_input("프롬프트 제목", value=prompt.title, key=f"edit_title_{prompt.id}")
                        new_content = st.text_area("프롬프트 내용", value=prompt.content, height=150, key=f"edit_content_{prompt.id}")
                        new_category = st.selectbox(
                            "카테고리",
                            ["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"],
                            index=["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"].index(prompt.category),
                            key=f"edit_category_{prompt.id}"
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("저장", key=f"save_edit_prompt_{prompt.id}"):
                                update_prompt(prompt.id, new_title, new_content, new_category)
                                st.session_state[edit_key] = False
                                st.success("프롬프트가 수정되었습니다!")
                                st.rerun()
                        with col2:
                            if st.button("수정 취소", key=f"cancel_edit_prompt_{prompt.id}"):
                                st.session_state[edit_key] = False
                                st.rerun()
                else:
                    with st.expander(f"📝 {prompt.title} ({prompt.category})"):
                        st.markdown(f"**생성일:** {prompt.created_at}")
                        st.markdown("**내용:**")
                        st.text_area("프롬프트 내용", value=prompt.content, height=100, key=f"view_prompt_{prompt.id}", disabled=True)
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            if st.button("📋 복사", key=f"copy_prompt_{prompt.id}"):
                                st.write("프롬프트가 클립보드에 복사되었습니다!")
                                st.code(prompt.content)
                        with col2:
                            if st.button("🔗 ChatGPT 링크", key=f"chatgpt_link_{prompt.id}"):
                                encoded_prompt = prompt.content.replace('\n', '%0A').replace(' ', '%20')
                                chatgpt_url = f"https://chat.openai.com/?q={encoded_prompt}"
                                st.markdown(f"[🤖 ChatGPT에서 질문하기]({chatgpt_url})")
                                st.info("위 링크를 클릭하면 ChatGPT에서 이 프롬프트로 질문할 수 있습니다.")
                        with col3:
                            if st.button("🗑️ 삭제", key=f"delete_prompt_{prompt.id}"):
                                delete_prompt(prompt.id)
                                st.success("프롬프트가 삭제되었습니다!")
                                st.rerun()
                        with col4:
                            if st.button("✏️ 수정", key=f"edit_btn_prompt_{prompt.id}"):
                                st.session_state[edit_key] = True
                                st.rerun()
            # 새 프롬프트 추가
            st.markdown("---")
            st.markdown("### 📝 새 프롬프트 추가")
            prompt_title = st.text_input("프롬프트 제목", key="new_prompt_title")
            prompt_content = st.text_area("프롬프트 내용", height=150, key="new_prompt_content", placeholder="예: AI 기술에 대해 설명해주세요. 특히 머신러닝과 딥러닝의 차이점을 중심으로...")
            prompt_category = st.selectbox("카테고리", ["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"], key="new_prompt_category")
            if st.button("💾 프롬프트 저장", key="save_new_prompt"):
                if prompt_title and prompt_content:
                    add_prompt(prompt_title, prompt_content, prompt_category, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    st.success("프롬프트가 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("제목과 내용을 모두 입력해주세요.")
            if st.button("🗑️ 입력 초기화", key="clear_new_prompt"):
                st.session_state["new_prompt_title"] = ""
                st.session_state["new_prompt_content"] = ""

            # --- 기반 내용 관리 ---
            st.markdown("---")
            st.markdown("### 📝 새 기반 내용 추가")
            bases = get_all_base_contents()
            for base in bases:
                edit_key = f"edit_base_{base.id}"
                if st.session_state.get(edit_key, False):
                    with st.expander(f"📝 {base.title} ({base.category}) [수정 중]"):
                        new_title = st.text_input("기반 내용 제목", value=base.title, key=f"edit_base_title_{base.id}")
                        new_content = st.text_area("기반 내용", value=base.content, height=150, key=f"edit_base_content_{base.id}")
                        new_category = st.selectbox(
                            "카테고리",
                            ["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"],
                            index=["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"].index(base.category),
                            key=f"edit_base_category_{base.id}"
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("저장", key=f"save_edit_base_{base.id}"):
                                update_base_content(base.id, new_title, new_content, new_category)
                                st.session_state[edit_key] = False
                                st.success("기반 내용이 수정되었습니다!")
                                st.rerun()
                        with col2:
                            if st.button("수정 취소", key=f"cancel_edit_base_{base.id}"):
                                st.session_state[edit_key] = False
                                st.rerun()
                else:
                    with st.expander(f"📝 {base.title} ({base.category})"):
                        st.markdown(f"**생성일:** {base.created_at}")
                        st.markdown("**내용:**")
                        st.text_area("기반 내용", value=base.content, height=100, key=f"view_base_{base.id}", disabled=True)
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            if st.button("📋 복사", key=f"copy_base_{base.id}"):
                                st.write("기반 내용이 클립보드에 복사되었습니다!")
                                st.code(base.content)
                        with col2:
                            if st.button("�� ChatGPT 링크", key=f"chatgpt_link_base_{base.id}"):
                                encoded_base = base.content.replace('\n', '%0A').replace(' ', '%20')
                                chatgpt_url = f"https://chat.openai.com/?q={encoded_base}"
                                st.markdown(f"[🤖 ChatGPT에서 질문하기]({chatgpt_url})")
                                st.info("위 링크를 클릭하면 ChatGPT에서 이 기반 내용으로 질문할 수 있습니다.")
                        with col3:
                            if st.button("��️ 삭제", key=f"delete_base_{base.id}"):
                                delete_base_content(base.id)
                                st.success("기반 내용이 삭제되었습니다!")
                                st.rerun()
                        with col4:
                            if st.button("✏️ 수정", key=f"edit_btn_base_{base.id}"):
                                st.session_state[edit_key] = True
                                st.rerun()
            # 새 기반 내용 추가
            base_title = st.text_input("기반 내용 제목", key="new_base_title")
            base_content = st.text_area("기반 내용", height=150, key="new_base_content", placeholder="예: AI의 역사적 발전 과정을 간략히 서술하세요.")
            base_category = st.selectbox("카테고리", ["AI 일반", "머신러닝", "딥러닝", "자연어처리", "컴퓨터비전", "기타"], key="new_base_category")
            if st.button("💾 기반 내용 저장", key="save_new_base"):
                if base_title and base_content:
                    add_base_content(base_title, base_content, base_category, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    st.success("기반 내용이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("제목과 내용을 모두 입력해주세요.")
            if st.button("🗑️ 입력 초기화", key="clear_new_base"):
                st.session_state["new_base_title"] = ""
                st.session_state["new_base_content"] = ""

        # --- 프롬프트 + 기반 내용 ChatGPT 링크 생성기 ---
        st.markdown("---")
        st.markdown("### 🔗 프롬프트 + 기반 내용 ChatGPT 링크 생성기")

        with st.expander("🌐 프롬프트와 기반 내용 합치기"):
            st.markdown("**사용법:** 기존 프롬프트와 기반 내용을 각각 선택하면 합쳐진 내용으로 ChatGPT 링크를 생성합니다.")
            prompts = get_all_prompts()
            bases = get_all_base_contents()
            if prompts and bases:
                prompt_options = [f"{p.title} ({p.category})" for p in prompts]
                base_options = [f"{b.title} ({b.category})" for b in bases]
                selected_prompt_idx = st.selectbox("프롬프트 선택", range(len(prompts)), format_func=lambda x: prompt_options[x], key="combine_prompt_select_db")
                selected_base_idx = st.selectbox("기반 내용 선택", range(len(bases)), format_func=lambda x: base_options[x], key="combine_base_select_db")
                selected_prompt = prompts[selected_prompt_idx]
                selected_base = bases[selected_base_idx]
                combined_question = selected_prompt.content + "\n\n" + selected_base.content
                st.markdown("**합쳐진 질문 미리보기:**")
                st.text_area("최종 질문", value=combined_question, height=200, disabled=False, key="combined_final_text_db")
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

# 프롬프트와 기반 내용 합치기 시 불필요한 안내 문구 제거 함수 추가
import re

def remove_prompt_base_labels(text):
    # '선택된 프롬프트:'와 '선택된 기반 내용:' 문구와 그 뒤 한 줄 제거
    text = re.sub(r'선택된 프롬프트:[^\n]*\n?', '', text)
    text = re.sub(r'선택된 기반 내용:[^\n]*\n?', '', text)
    return text

# ... 기존 코드 ...
# 합쳐진 프롬프트+기반내용을 표시/복사/링크 생성할 때 아래처럼 적용
# merged = ... (합쳐진 텍스트)
# merged = remove_prompt_base_labels(merged)
# st.write(merged)
# ... 기존 코드 ...
