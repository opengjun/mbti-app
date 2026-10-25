import sqlite3
import os
from config import DB_PATH, DEFAULT_DIMENSIONS

def get_conn():
    conn = sqlite3.connect('/tmp/mbti.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # 维度表
    c.execute('''CREATE TABLE IF NOT EXISTS dimensions
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT NOT NULL UNIQUE,
         element_a TEXT NOT NULL,
         element_b TEXT NOT NULL,
         style TEXT DEFAULT 'red',
         sort_order INTEGER DEFAULT 1)''')

    # 性格类型表（16种）
    c.execute('''CREATE TABLE IF NOT EXISTS personality_types
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         code TEXT NOT NULL UNIQUE,
         nickname TEXT DEFAULT '',
         description TEXT DEFAULT '',
         celebrities TEXT DEFAULT '',
         poster_bg TEXT DEFAULT '',
         detail_first_show INTEGER DEFAULT 0,
         detail_content TEXT DEFAULT '',
         sort_order INTEGER DEFAULT 1)''')

    # 测试表
    c.execute('''CREATE TABLE IF NOT EXISTS tests
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT NOT NULL UNIQUE,
         description TEXT DEFAULT '',
         estimated_time INTEGER DEFAULT 10,
         status INTEGER DEFAULT 0,
         publish_time TEXT DEFAULT '',
         scan_count INTEGER DEFAULT 0,
         submit_count INTEGER DEFAULT 0,
         sort_order INTEGER DEFAULT 1)''')

    # 题目表
    c.execute('''CREATE TABLE IF NOT EXISTS questions
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         test_id INTEGER NOT NULL,
         question_no INTEGER NOT NULL,
         question_text TEXT NOT NULL,
         dimension_id INTEGER NOT NULL,
         scoring_type TEXT DEFAULT 'positive',
         option_a TEXT NOT NULL,
         option_b TEXT NOT NULL,
         FOREIGN KEY (test_id) REFERENCES tests(id),
         FOREIGN KEY (dimension_id) REFERENCES dimensions(id))''')

    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         nickname TEXT DEFAULT '',
         avatar TEXT DEFAULT '',
         gender TEXT DEFAULT '',
         career_stage TEXT DEFAULT '',
         education TEXT DEFAULT '',
         city TEXT DEFAULT '',
         enter_source TEXT DEFAULT '',
         create_time TEXT DEFAULT '')''')

    # 测试结果表
    c.execute('''CREATE TABLE IF NOT EXISTS test_results
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER NOT NULL,
         test_id INTEGER NOT NULL,
         answers TEXT DEFAULT '',
         dimension_scores TEXT DEFAULT '',
         personality_type TEXT DEFAULT '',
         submit_time TEXT DEFAULT '',
         FOREIGN KEY (user_id) REFERENCES users(id),
         FOREIGN KEY (test_id) REFERENCES tests(id))''')

    # 详情查看记录表
    c.execute('''CREATE TABLE IF NOT EXISTS detail_views
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER NOT NULL,
         personality_type TEXT DEFAULT '',
         view_time TEXT DEFAULT '',
         FOREIGN KEY (user_id) REFERENCES users(id))''')

    # ===== 开始插入基础数据 =====

    # 1. 初始化默认维度
    for d in DEFAULT_DIMENSIONS:
        c.execute('SELECT COUNT(*) FROM dimensions WHERE name=?', (d['name'],))
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO dimensions (name, element_a, element_b, style, sort_order) VALUES (?,?,?,?,?)',
                     (d['name'], d['element_a'], d['element_b'], d['style'], d['order']))

    # 2. 初始化16种性格类型
    default_types = [
        ('INTJ', '建筑师', '独立的战略家', '#4A90D9', 1),
        ('INTP', '逻辑学家', '创新的思考者', '#9B59B6', 2),
        ('ENTJ', '指挥官', '天生的领导者', '#E74C3C', 3),
        ('ENTP', '辩论家', '聪明的挑战者', '#F39C12', 4),
        ('INFJ', '提倡者', '理想的守护者', '#1ABC9C', 5),
        ('INFP', '调停者', '诗意的梦想家', '#3498DB', 6),
        ('ENFJ', '主人公', '鼓舞的领袖', '#E67E22', 7),
        ('ENFP', '竞选者', '热情的创造者', '#FF6B9D', 8),
        ('ISTJ', '物流师', '可靠的实干将', '#34495E', 9),
        ('ISFJ', '守卫者', '温暖的保护者', '#5D6D7E', 10),
        ('ESTJ', '总经理', '高效的组织者', '#7F8C8D', 11),
        ('ESFJ', '执政官', '热心的帮助者', '#F1C40F', 12),
        ('ISTP', '鉴赏家', '灵活的实践者', '#27AE60', 13),
        ('ISFP', '探险家', '自由的艺术家', '#16A085', 14),
        ('ESTP', '企业家', '大胆的行动派', '#D35400', 15),
        ('ESFP', '表演者', '快乐的明星', '#E91E63', 16),
    ]
    for t in default_types:
        c.execute('SELECT COUNT(*) FROM personality_types WHERE code=?', (t[0],))
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO personality_types (code, nickname, description, poster_bg, detail_first_show, sort_order) VALUES (?,?,?,?,0,?)', t)

    # 3. 插入测试题（从你旧的 seed_data.py 搬过来的逻辑）
    # 获取维度 ID 映射
    dims = {}
    for row in c.execute('SELECT id, name FROM dimensions').fetchall():
        dims[row['name']] = row['id']

    # 插入 28题精简版
    c.execute("INSERT OR IGNORE INTO tests (name, description, estimated_time, status, publish_time, sort_order) VALUES (?,?,?,?,datetime('now','localtime'),?)",
        ('精简版（28题）', '佛系点 · 一首歌的时间', 3, 1, 1))
    test1_id = c.execute("SELECT id FROM tests WHERE name='精简版（28题）'").fetchone()['id']

    sample_questions_28 = [
        (test1_id, 1, '参加一个大型派对后，你通常会？', dims['E-I'], 'positive', '感到精力充沛，想要继续社交', '感到疲惫，需要独处恢复'),
        (test1_id, 2, '在陌生人群中，你是？', dims['E-I'], 'positive', '主动与陌生人交谈', '等待别人先搭话'),
        (test1_id, 3, '独处对你来说是？', dims['E-I'], 'positive', '偶尔想要的放松', '最舒适的状态'),
        (test1_id, 4, '你的朋友圈通常是？', dims['E-I'], 'positive', '广泛而多样', '小而精'),
        (test1_id, 5, '在团队中，你更倾向于？', dims['E-I'], 'positive', '发言和带动讨论', '倾听和深思'),
        (test1_id, 6, '你更喜欢的工作环境是？', dims['E-I'], 'positive', '开放式办公空间', '独立办公室'),
        (test1_id, 7, '表达想法时，你通常是？', dims['E-I'], 'positive', '边想边说', '想好了再说'),
        (test1_id, 8, '你更关注？', dims['S-N'], 'positive', '此时此刻发生的事', '未来的可能性'),
        (test1_id, 9, '面对问题，你倾向于？', dims['S-N'], 'positive', '用已验证的方法解决', '尝试全新的思路'),
        (test1_id, 10, '学习新知识时，你更喜欢？', dims['S-N'], 'positive', '看具体案例和实操', '先理解理论框架'),
        (test1_id, 11, '你的记忆更擅长记？', dims['S-N'], 'positive', '具体的数字和事实', '概念和关键词'),
        (test1_id, 12, '做决定时，你更依赖？', dims['S-N'], 'positive', '过往经验和数据', '直觉和第六感'),
        (test1_id, 13, '你认为自己是？', dims['S-N'], 'positive', '脚踏实地的实用主义者', '充满想象力的理想主义者'),
        (test1_id, 14, '阅读时你更偏好？', dims['S-N'], 'positive', '纪实类/商业类', '科幻类/哲学类'),
        (test1_id, 15, '做决策时你更看重？', dims['T-F'], 'positive', '逻辑和公平', '情感和和谐'),
        (test1_id, 16, '朋友找你倾诉，你会？', dims['T-F'], 'positive', '帮他分析问题给出建议', '先共情陪伴，让他感受支持'),
        (test1_id, 17, '面对批评，你通常？', dims['T-F'], 'positive', '冷静分析是否合理', '容易感到受伤害'),
        (test1_id, 18, '你认为自己更偏向？', dims['T-F'], 'positive', '客观理性', '温暖感性'),
        (test1_id, 19, '在团队里，你更擅长？', dims['T-F'], 'positive', '发现逻辑漏洞', '维护团队氛围'),
        (test1_id, 20, '购物时你更倾向于？', dims['T-F'], 'positive', '对比参数，追求性价比', '凭感觉，好看就买'),
        (test1_id, 21, '你觉得"好人"应该是？', dims['T-F'], 'positive', '坚持原则不妥协', '总是照顾他人感受'),
        (test1_id, 22, '你的生活方式更偏向？', dims['J-P'], 'positive', '有计划有条理', '随机应变灵活自由'),
        (test1_id, 23, '面对截止日期，你通常？', dims['J-P'], 'positive', '提前规划好节奏', '最后冲刺完成'),
        (test1_id, 24, '旅行时你更喜欢？', dims['J-P'], 'positive', '详细攻略', '说走就走随遇而安'),
        (test1_id, 25, '工作空间通常是？', dims['J-P'], 'positive', '整洁有序', '看似混乱但你清楚在哪'),
        (test1_id, 26, '做决定时，你倾向于？', dims['J-P'], 'positive', '尽快敲定', '保持开放继续观察'),
        (test1_id, 27, '你的日程表通常？', dims['J-P'], 'positive', '排得满满当当', '只记重要事项'),
        (test1_id, 28, '面对突发状况，你更觉得？', dims['J-P'], 'positive', '计划被打乱很烦', '随机应对挺有意思'),
    ]
    for q in sample_questions_28:
        c.execute("INSERT OR IGNORE INTO questions (test_id, question_no, question_text, dimension_id, scoring_type, option_a, option_b) VALUES (?,?,?,?,?,?,?)", q)

    # 插入 93题经典版 (占位)
    import random
    c.execute("INSERT OR IGNORE INTO tests (name, description, estimated_time, status, publish_time, sort_order) VALUES (?,?,?,?,datetime('now','localtime'),?)",
        ('经典版（93题）', '认真点 · 深度探索', 10, 1, 2))
    test2_id = c.execute("SELECT id FROM tests WHERE name='经典版（93题）'").fetchone()['id']

    q_count = c.execute("SELECT COUNT(*) FROM questions WHERE test_id=?", (test2_id,)).fetchone()[0]
    if q_count == 0: # 如果还没有题目才生成，防止重复
        random.seed(42)
        templates = {
            'E-I': ['在大型聚会上你通常？', '新环境里你倾向？', '日常社交对你来说？', '长时间独处后你会？'],
            'S-N': ['你更相信？', '解决问题的首选是？', '你被称为？', '你关注的重点是？'],
            'T-F': ['做决定先看？', '你是一个？', '面对冲突你选择？', '朋友求助时你会？'],
            'J-P': ['面对计划被打乱？', '你的周末通常？', '做事情的方式？', '待办清单存在吗？'],
        }
        q_no = 0
        for dim_name in ['E-I', 'S-N', 'T-F', 'J-P']:
            for i in range(24):
                q_no += 1
                if q_no > 93: break
                template = random.choice(templates[dim_name])
                scoring = random.choice(['positive', 'reverse'])
                c.execute("INSERT INTO questions (test_id, question_no, question_text, dimension_id, scoring_type, option_a, option_b) VALUES (?,?,?,?,?,?,?)",
                    (test2_id, q_no, f'{template} #{i+1}', dims[dim_name], scoring, 'A选项（待补充）', 'B选项（待补充）'))

    conn.commit()
    conn.close()
    print("数据库初始化完成（含测试题库）")

# ---------- 维度相关 ----------
def get_dimensions():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM dimensions ORDER BY sort_order ASC, id ASC').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_dimension_by_id(dim_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM dimensions WHERE id=?', (dim_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

# ---------- 测试相关 ----------
def get_tests():
    conn = get_conn()
    rows = conn.execute('''SELECT t.*, COUNT(q.id) as question_count
        FROM tests t LEFT JOIN questions q ON t.id = q.test_id
        GROUP BY t.id ORDER BY t.sort_order ASC, t.id ASC''').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_test_by_id(test_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM tests WHERE id=?', (test_id,)).fetchone()
    if row:
        q_rows = conn.execute('SELECT * FROM questions WHERE test_id=? ORDER BY question_no ASC', (test_id,)).fetchall()
        questions = [dict(r) for r in q_rows]
        result = dict(row)
        result['questions'] = questions
    conn.close()
    return result if row else None

def get_test_questions(test_id):
    conn = get_conn()
    rows = conn.execute('''SELECT q.*, d.name as dim_name, d.element_a, d.element_b, d.style
        FROM questions q JOIN dimensions d ON q.dimension_id = d.id
        WHERE q.test_id=? ORDER BY q.question_no ASC''', (test_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------- 性格类型相关 ----------
def get_personality_types():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM personality_types ORDER BY sort_order ASC, id ASC').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_personality_type(code):
    conn = get_conn()
    row = conn.execute('SELECT * FROM personality_types WHERE code=?', (code,)).fetchone()
    conn.close()
    return dict(row) if row else None

# ---------- 用户相关 ----------
def create_user(nickname='', avatar='', enter_source=''):
    from datetime import datetime
    conn = get_conn()
    conn.execute('INSERT INTO users (nickname, avatar, enter_source, create_time) VALUES (?,?,?,?)',
                 (nickname, avatar, enter_source, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    uid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return uid

def get_user(user_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_user(user_id, **kwargs):
    conn = get_conn()
    fields = ','.join([f'{k}=?' for k in kwargs.keys()])
    conn.execute(f'UPDATE users SET {fields} WHERE id=?', list(kwargs.values()) + [user_id])
    conn.commit()
    conn.close()

def get_user_test_count(user_id):
    conn = get_conn()
    row = conn.execute('SELECT COUNT(*) as cnt FROM test_results WHERE user_id=?', (user_id,)).fetchone()
    conn.close()
    return row['cnt'] if row else 0

def get_user_detail_view_count(user_id):
    conn = get_conn()
    row = conn.execute('SELECT COUNT(*) as cnt FROM detail_views WHERE user_id=?', (user_id,)).fetchone()
    conn.close()
    return row['cnt'] if row else 0

# ---------- 结果相关 ----------
def save_test_result(user_id, test_id, answers, dim_scores, personality_type):
    from datetime import datetime
    import json
    conn = get_conn()
    conn.execute('INSERT INTO test_results (user_id, test_id, answers, dimension_scores, personality_type, submit_time) VALUES (?,?,?,?,?,?)',
                 (user_id, test_id, json.dumps(answers), json.dumps(dim_scores), personality_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    # 更新测试提交次数
    conn.execute('UPDATE tests SET submit_count = submit_count + 1 WHERE id=?', (test_id,))
    conn.commit()
    result_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return result_id

def get_test_results(limit=100):
    conn = get_conn()
    rows = conn.execute('''SELECT r.*, u.nickname, u.avatar, u.gender, u.career_stage, u.education, u.city, u.enter_source,
        t.name as test_name FROM test_results r
        JOIN users u ON r.user_id = u.id
        JOIN tests t ON r.test_id = t.id
        ORDER BY r.submit_time DESC LIMIT ?''', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_latest_result(user_id):
    """获取指定用户自己的最新测试结果"""
    conn = get_conn()
    row = conn.execute('SELECT * FROM test_results WHERE user_id=? ORDER BY submit_time DESC, id DESC LIMIT 1',
                       (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def record_detail_view(user_id, personality_type):
    from datetime import datetime
    conn = get_conn()
    conn.execute('INSERT INTO detail_views (user_id, personality_type, view_time) VALUES (?,?,?)',
                 (user_id, personality_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
