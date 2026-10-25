import os
import json
import math
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory

from models import (
    init_db, get_tests, get_test_by_id, get_test_questions,
    get_dimensions, get_dimension_by_id,
    get_personality_types, get_personality_type,
    create_user, get_user, update_user, get_user_test_count, get_user_detail_view_count,
    save_test_result, get_test_results, record_detail_view, get_user_latest_result,
)
from scoring import calculate_scores
from config import STYLES, GENDER_OPTIONS, CAREER_OPTIONS, EDUCATION_OPTIONS, PUBLIC_URL

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mbti-secret-key-2026')

# 全局注入公网地址到所有模板
@app.context_processor
def inject_public_url():
    return dict(public_url=PUBLIC_URL)

# 初始化数据库
init_db()

# ============ 用户端路由 ============

@app.route('/')
def index():
    """首页 - 题型选择"""
    tests = [t for t in get_tests() if t['status'] == 1]
    return render_template('index.html', tests=tests)

@app.route('/select_source', methods=['POST'])
def select_source():
    """模拟登录 - 设置进入方式"""
    source = request.form.get('source', 'wechat_search')
    nickname = request.form.get('nickname', '') or '测试用户'
    avatar = request.form.get('avatar', '') or ''
    user_id = create_user(nickname=nickname, avatar=avatar, enter_source=source)
    session['user_id'] = user_id
    session['nickname'] = nickname
    session['avatar'] = avatar
    return redirect(url_for('intro', test_id=request.form.get('test_id')))

@app.route('/intro/<int:test_id>')
def intro(test_id):
    """答题提示页"""
    test = get_test_by_id(test_id)
    if not test:
        return redirect(url_for('index'))
    return render_template('intro.html', test=test)

@app.route('/test/<int:test_id>')
def test_page(test_id):
    """答题页面"""
    test = get_test_by_id(test_id)
    if not test:
        return redirect(url_for('index'))
    questions = get_test_questions(test_id)

    # 按维度随机打乱（但保留每个维度内部的顺序）
    # 文档说"根据四维度题型做不同的展示（通过颜色/形式/动效表现），随机出现"
    import random
    random.seed(datetime.now().microsecond)
    random.shuffle(questions)

    session['current_test_id'] = test_id
    session['answers'] = {}
    return render_template('test.html', test=test, questions=questions, styles=STYLES)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """提交单题答案 (AJAX)"""
    data = request.get_json()
    qid = str(data.get('question_id'))
    ans = data.get('answer')
    answers = session.get('answers', {})
    answers[qid] = ans
    session['answers'] = answers
    return jsonify({'status': 'ok', 'count': len(answers)})

@app.route('/finish_questions', methods=['GET', 'POST'])
def finish_questions():
    """完成答题 → 进入选填资料页"""
    test_id = session.get('current_test_id')
    if not test_id:
        return redirect(url_for('index'))
    return render_template('submit_form.html', test_id=test_id,
                          gender_options=GENDER_OPTIONS,
                          career_options=CAREER_OPTIONS,
                          education_options=EDUCATION_OPTIONS)

@app.route('/submit_test', methods=['POST'])
def submit_test():
    """最终提交 → 计分 → 结果"""
    test_id = session.get('current_test_id')
    user_id = session.get('user_id')
    answers = session.get('answers', {})

    if not test_id or not user_id or not answers:
        return redirect(url_for('index'))

    # 获取选填项
    gender = request.form.get('gender', '')
    career = request.form.get('career', '')
    education = request.form.get('education', '')

    # 更新用户资料
    update_user(user_id, gender=gender, career_stage=career, education=education)

    # 计分
    scores_result = calculate_scores(test_id, answers)

    # 保存结果
    save_test_result(user_id, test_id, answers,
                    scores_result['dimension_scores'],
                    scores_result['personality_type'])

    # 清除session中的答题状态
    session.pop('answers', None)
    session.pop('current_test_id', None)

    session['last_result_type'] = scores_result['personality_type']

    return redirect(url_for('result', ptype=scores_result['personality_type']))

def build_radar_points(dimension_scores):
    """构建8方向雷达网状图数据：E/S/T/J/I/N/F/P 八个顶点
    E-I、S-N、T-F、J-P 四条轴两两相对，对向同色（红/绿/蓝/黄）
    标签布局：字母为主(大号彩色)+百分比，中文标注为辅(小号)，按方位定锚点防溢出"""
    if not dimension_scores:
        return None
    letter_pct = {}
    for ds in dimension_scores:
        total = ds.get('total') or (ds.get('score_a', 0) + ds.get('score_b', 0))
        if total <= 0:
            pct_a, pct_b = 50, 50
        else:
            pct_a = ds.get('score_a', 0) / total * 100
            pct_b = 100 - pct_a
        letter_pct[ds['element_a']] = round(pct_a)
        letter_pct[ds['element_b']] = round(pct_b)

    # 顶点顺序（顺时针，从正上方开始）：E, S, T, J, I, N, F, P
    order = ['E', 'S', 'T', 'J', 'I', 'N', 'F', 'P']
    cx, cy, r = 160, 142, 76   # 画布 320x300
    # 对向同色：E/I红 S/N绿 T/F蓝 J/P黄
    pair_colors = {'E': '#ff8a8a', 'I': '#ff8a8a',
                   'S': '#7de8a8', 'N': '#7de8a8',
                   'T': '#8ab8ff', 'F': '#8ab8ff',
                   'J': '#ffd76e', 'P': '#ffd76e'}
    subtext_map = {'E': '外向', 'S': '感觉', 'T': '思考', 'J': '判断',
                   'I': '内向', 'N': '直觉', 'F': '情感', 'P': '感知'}
    points = []
    for i, letter in enumerate(order):
        angle = math.radians(-90 + i * 45)
        pct = max(letter_pct.get(letter, 0), 12)   # 最低显示12，避免过小不可见
        x = cx + r * pct / 100 * math.cos(angle)
        y = cy + r * pct / 100 * math.sin(angle)
        # 标签锚点按方位设置，保证完整显示不裁切
        dx, dy = math.cos(angle), math.sin(angle)
        if i == 0:      # E 正上
            lx, ly, anchor = cx, cy - r - 16, 'middle'
        elif i == 4:    # I 正下
            lx, ly, anchor = cx, cy + r + 24, 'middle'
        elif i == 2:    # T 正右
            lx, ly, anchor = cx + r + 14, cy + 4, 'start'
        elif i == 6:    # F 正左
            lx, ly, anchor = cx - r - 14, cy + 4, 'end'
        elif i == 1:    # S 右上
            lx, ly, anchor = cx + r * 0.707 + 10, cy - r * 0.707, 'start'
        elif i == 3:    # J 右下
            lx, ly, anchor = cx + r * 0.707 + 10, cy + r * 0.707 + 12, 'start'
        elif i == 5:    # N 左下
            lx, ly, anchor = cx - r * 0.707 - 10, cy + r * 0.707 + 12, 'end'
        else:           # P 左上
            lx, ly, anchor = cx - r * 0.707 - 10, cy - r * 0.707, 'end'
        points.append({
            'letter': letter, 'pct': round(pct),
            'subtext': subtext_map[letter],
            'color': pair_colors[letter],
            'x': round(x, 1), 'y': round(y, 1),
            'lx': round(lx, 1), 'ly': round(ly, 1),
            'anchor': anchor,
        })
    polygon = ' '.join(f"{p['x']},{p['y']}" for p in points)
    # 四条对向轴线（成对同色，穿过圆心）
    axes = []
    for i in range(4):
        a = math.radians(-90 + i * 45)
        axes.append({
            'x1': round(cx + r * math.cos(a), 1), 'y1': round(cy + r * math.sin(a), 1),
            'x2': round(cx - r * math.cos(a), 1), 'y2': round(cy - r * math.sin(a), 1),
            'color': pair_colors[order[i]],
        })
    return {'points': points, 'polygon': polygon, 'cx': cx, 'cy': cy, 'r': r, 'axes': axes}

def build_discover_links(code):
    """根据类型生成发现页外链卡片（B站学习 / Boss直聘工作 / 豆瓣·知乎成长小组）"""
    links_path = os.path.join(os.path.dirname(__file__), 'data', 'discover_links.json')
    with open(links_path, 'r', encoding='utf-8') as f:
        conf = json.load(f)
    cfg = conf.get(code, {'study': code + '提升', 'job': '职场', 'growth': code + '成长'})
    import urllib.parse as up
    q = lambda s: up.quote(s)
    return {
        'study_links': [
            {'icon': '🧠', 'title': f'{cfg["study"]}（视频课）', 'desc': 'B站优质学习资源', 'url': f'https://search.bilibili.com/all?keyword={q(code + " " + cfg["study"])}'},
            {'icon': '📖', 'title': f'{code}如何提升自己', 'desc': '知乎经验与方法论', 'url': f'https://www.zhihu.com/search?type=content&q={q(code + "人格 如何提升")}'},
        ],
        'job_links': [
            {'icon': '💼', 'title': f'「{cfg["job"]}」相关职位', 'desc': 'Boss直聘 · 全国', 'url': f'https://www.zhipin.com/web/geek/job?query={q(cfg["job"])}&city=100010000'},
            {'icon': '🔍', 'title': f'{code}适合的职业方向', 'desc': '知乎 · 职业规划讨论', 'url': f'https://www.zhihu.com/search?type=content&q={q(code + "人格 适合的职业")}'},
        ],
        'growth_links': [
            {'icon': '👥', 'title': f'{code}同类人社区', 'desc': '豆瓣小组 · 找到同类', 'url': f'https://www.douban.com/group/search?cat=1019&q={q(code)}'},
            {'icon': '🤝', 'title': f'{cfg["growth"]}线上互助小组', 'desc': '知乎 · 交流与成长', 'url': f'https://www.zhihu.com/search?type=content&q={q(code + "人格 小组")}'},
        ],
    }

@app.route('/result/<ptype>')
def result(ptype):
    """结果海报页"""
    ptype_info = get_personality_type(ptype)
    user_id = session.get('user_id')
    user = get_user(user_id) if user_id else {}
    test_count = get_user_test_count(user_id) if user_id else 0

    # 判断是否首次展示详情入口
    show_detail_entry = False
    if ptype_info:
        if ptype_info.get('detail_first_show') == 1:
            show_detail_entry = True
        elif test_count >= 2:
            show_detail_entry = True

    # 获取雷达图数据（从当前用户自己的最新结果获取）
    dimension_scores = []
    if user_id:
        last = get_user_latest_result(user_id)
        if last and last.get('dimension_scores'):
            try:
                dimension_scores = json.loads(last['dimension_scores'])
            except:
                pass
    radar = build_radar_points(dimension_scores)

    # 名人数据
    celebs = []
    if ptype_info and ptype_info.get('celebs_json'):
        try:
            celebs = json.loads(ptype_info['celebs_json'])
        except:
            celebs = []

    return render_template('result.html',
                          ptype_info=ptype_info or {},
                          personality_type=ptype,
                          user=user,
                          dimension_scores=dimension_scores,
                          radar=radar,
                          celebs=celebs,
                          show_detail_entry=show_detail_entry,
                          test_count=test_count)

def parse_detail_sections(detail_html):
    """把 detail_content HTML 按 <h3> 拆分为章节列表 [{icon, title, html}]
    同时把 markdown **粗体** 转为 <b>粗体</b>，避免星号原样显示"""
    if not detail_html:
        return []
    sections = []
    import re
    # 先把 **text** 转成 <b>text</b>
    detail_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', detail_html)
    parts = re.split(r'<h3>(.*?)</h3>', detail_html)
    # parts: [前置内容, 标题1, 内容1, 标题2, 内容2, ...]
    for i in range(1, len(parts), 2):
        raw_title = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ''
        # 标题格式通常是 "🧩 个性特征描述" → 拆出图标和纯标题
        m = re.match(r'^([^\u4e00-\u9fa5\w\s])\s*(.*)$', raw_title)
        if m:
            icon, title = m.group(1), m.group(2).strip()
        else:
            icon, title = '📌', raw_title
        sections.append({'icon': icon, 'title': title, 'html': body})
    return sections

@app.route('/discover/<ptype>')
def discover(ptype):
    """发现自己·更好前行 —— 深度解析页（章节化排版，学习/工作/成长链接融入对应章节）"""
    ptype_info = get_personality_type(ptype)
    if not ptype_info:
        return redirect(url_for('index'))
    links = build_discover_links(ptype)
    sections = parse_detail_sections(ptype_info.get('detail_content'))
    return render_template('discover.html', ptype_info=ptype_info,
                          personality_type=ptype, links=links, sections=sections)

@app.route('/detail/<ptype>')
def personality_detail(ptype):
    """性格详情页"""
    ptype_info = get_personality_type(ptype)
    user_id = session.get('user_id')
    if user_id:
        record_detail_view(user_id, ptype)
    # 把 markdown **粗体** 转为 <b>粗体</b>
    if ptype_info and ptype_info.get('detail_content'):
        import re
        ptype_info['detail_content'] = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', ptype_info['detail_content'])
    return render_template('detail.html', ptype_info=ptype_info or {}, personality_type=ptype)

# ============ 后台管理路由 ============

@app.route('/admin')
def admin_dashboard():
    """后台首页"""
    results = get_test_results(10)
    return render_template('admin/dashboard.html', results=results)

@app.route('/admin/tests')
def admin_tests():
    """测试管理"""
    tests = get_tests()
    return render_template('admin/tests.html', tests=tests)

@app.route('/admin/dimensions')
def admin_dimensions():
    """维度管理"""
    dims = get_dimensions()
    return render_template('admin/dimensions.html', dims=dims, styles=STYLES)

@app.route('/admin/types')
def admin_types():
    """性格类型管理"""
    types = get_personality_types()
    return render_template('admin/types.html', types=types)

@app.route('/admin/stats')
def admin_stats():
    """数据统计"""
    results = get_test_results(200)
    tests = get_tests()
    return render_template('admin/stats.html', results=results, tests=tests)

# ============ API 接口 ============

@app.route('/api/results/export')
def export_results():
    """导出数据为JSON"""
    results = get_test_results(5000)
    from flask import Response
    data = json.dumps(results, ensure_ascii=False, indent=2)
    return Response(data, mimetype='application/json',
                    headers={'Content-Disposition': 'attachment; filename=mbti_results.json'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
