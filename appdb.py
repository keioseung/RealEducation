from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import json

DB_PATH = 'sqlite:///ai_info.db'
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# --- DB 모델 정의 ---
class AIInfo(Base):
    __tablename__ = 'ai_info'
    id = Column(Integer, primary_key=True)
    date = Column(String, index=True)
    info1 = Column(Text)
    info2 = Column(Text)
    info3 = Column(Text)

class Quiz(Base):
    __tablename__ = 'quiz'
    id = Column(Integer, primary_key=True)
    topic = Column(String, index=True)
    question = Column(Text)
    option1 = Column(Text)
    option2 = Column(Text)
    option3 = Column(Text)
    option4 = Column(Text)
    correct = Column(Integer)
    explanation = Column(Text)

class UserProgress(Base):
    __tablename__ = 'user_progress'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    date = Column(String, index=True)
    learned_info = Column(Text)  # JSON 직렬화 문자열
    stats = Column(Text)         # JSON 직렬화 문자열

class Prompt(Base):
    __tablename__ = 'prompt'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    category = Column(String)
    created_at = Column(String)

class BaseContent(Base):
    __tablename__ = 'base_content'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    category = Column(String)
    created_at = Column(String)

Base.metadata.create_all(engine)

# --- AI 정보 CRUD ---
def get_ai_info_by_date(date_str):
    db = SessionLocal()
    ai_info = db.query(AIInfo).filter(AIInfo.date == date_str).first()
    db.close()
    if ai_info:
        return [ai_info.info1, ai_info.info2, ai_info.info3]
    return []

def add_ai_info(date_str, infos):
    db = SessionLocal()
    ai_info = db.query(AIInfo).filter(AIInfo.date == date_str).first()
    if ai_info:
        ai_info.info1, ai_info.info2, ai_info.info3 = infos
    else:
        ai_info = AIInfo(date=date_str, info1=infos[0], info2=infos[1], info3=infos[2])
        db.add(ai_info)
    db.commit()
    db.close()

def delete_ai_info(date_str):
    db = SessionLocal()
    ai_info = db.query(AIInfo).filter(AIInfo.date == date_str).first()
    if ai_info:
        db.delete(ai_info)
        db.commit()
    db.close()

def get_all_ai_info_dates():
    db = SessionLocal()
    dates = [row.date for row in db.query(AIInfo).order_by(AIInfo.date).all()]
    db.close()
    return dates

def update_ai_info_item(date_str, index, new_info):
    db = SessionLocal()
    ai_info = db.query(AIInfo).filter(AIInfo.date == date_str).first()
    if ai_info:
        if index == 0:
            ai_info.info1 = new_info
        elif index == 1:
            ai_info.info2 = new_info
        elif index == 2:
            ai_info.info3 = new_info
        db.commit()
    db.close()

def delete_ai_info_item(date_str, index):
    db = SessionLocal()
    ai_info = db.query(AIInfo).filter(AIInfo.date == date_str).first()
    if ai_info:
        if index == 0:
            ai_info.info1 = None
        elif index == 1:
            ai_info.info2 = None
        elif index == 2:
            ai_info.info3 = None
        db.commit()
    db.close()

# --- 퀴즈 CRUD ---
def get_all_quiz_topics():
    db = SessionLocal()
    topics = list(set([row.topic for row in db.query(Quiz).all()]))
    db.close()
    return topics

def get_quiz_by_topic(topic):
    db = SessionLocal()
    quizzes = db.query(Quiz).filter(Quiz.topic == topic).all()
    db.close()
    return quizzes

def add_quiz(topic, question, options, correct, explanation):
    db = SessionLocal()
    quiz = Quiz(
        topic=topic,
        question=question,
        option1=options[0],
        option2=options[1],
        option3=options[2],
        option4=options[3],
        correct=correct,
        explanation=explanation
    )
    db.add(quiz)
    db.commit()
    db.close()

def update_quiz(quiz_id, question, options, correct, explanation):
    db = SessionLocal()
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz:
        quiz.question = question
        quiz.option1 = options[0]
        quiz.option2 = options[1]
        quiz.option3 = options[2]
        quiz.option4 = options[3]
        quiz.correct = correct
        quiz.explanation = explanation
        db.commit()
    db.close()

def delete_quiz(quiz_id):
    db = SessionLocal()
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz:
        db.delete(quiz)
        db.commit()
    db.close()

# --- 사용자 진행상황 CRUD ---
def get_user_progress(session_id):
    db = SessionLocal()
    progress = db.query(UserProgress).filter(UserProgress.session_id == session_id).all()
    db.close()
    result = {}
    for p in progress:
        if p.learned_info:
            result[p.date] = json.loads(p.learned_info)
    return result

def update_user_progress(session_id, date_str, info_index):
    db = SessionLocal()
    progress = db.query(UserProgress).filter(UserProgress.session_id == session_id, UserProgress.date == date_str).first()
    if progress:
        learned = json.loads(progress.learned_info) if progress.learned_info else []
        if info_index not in learned:
            learned.append(info_index)
            progress.learned_info = json.dumps(learned)
    else:
        learned = [info_index]
        progress = UserProgress(session_id=session_id, date=date_str, learned_info=json.dumps(learned), stats=None)
        db.add(progress)
    db.commit()
    db.close()

def get_user_stats(session_id):
    db = SessionLocal()
    progress = db.query(UserProgress).filter(UserProgress.session_id == session_id, UserProgress.date == '__stats__').first()
    db.close()
    if progress and progress.stats:
        return json.loads(progress.stats)
    return {
        'total_learned': 0,
        'streak_days': 0,
        'last_learned_date': None,
        'quiz_score': 0,
        'achievements': []
    }

def update_user_stats(session_id, stats_dict):
    db = SessionLocal()
    progress = db.query(UserProgress).filter(UserProgress.session_id == session_id, UserProgress.date == '__stats__').first()
    if progress:
        progress.stats = json.dumps(stats_dict)
    else:
        progress = UserProgress(session_id=session_id, date='__stats__', learned_info=None, stats=json.dumps(stats_dict))
        db.add(progress)
    db.commit()
    db.close()

# --- 프롬프트 CRUD ---
def get_all_prompts():
    db = SessionLocal()
    prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
    db.close()
    return prompts

def add_prompt(title, content, category, created_at):
    db = SessionLocal()
    prompt = Prompt(title=title, content=content, category=category, created_at=created_at)
    db.add(prompt)
    db.commit()
    db.close()

def update_prompt(prompt_id, title, content, category):
    db = SessionLocal()
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt:
        prompt.title = title
        prompt.content = content
        prompt.category = category
        db.commit()
    db.close()

def delete_prompt(prompt_id):
    db = SessionLocal()
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt:
        db.delete(prompt)
        db.commit()
    db.close()

# --- 기반 내용 CRUD ---
def get_all_base_contents():
    db = SessionLocal()
    bases = db.query(BaseContent).order_by(BaseContent.created_at.desc()).all()
    db.close()
    return bases

def add_base_content(title, content, category, created_at):
    db = SessionLocal()
    base = BaseContent(title=title, content=content, category=category, created_at=created_at)
    db.add(base)
    db.commit()
    db.close()

def update_base_content(base_id, title, content, category):
    db = SessionLocal()
    base = db.query(BaseContent).filter(BaseContent.id == base_id).first()
    if base:
        base.title = title
        base.content = content
        base.category = category
        db.commit()
    db.close()

def delete_base_content(base_id):
    db = SessionLocal()
    base = db.query(BaseContent).filter(BaseContent.id == base_id).first()
    if base:
        db.delete(base)
        db.commit()
    db.close()