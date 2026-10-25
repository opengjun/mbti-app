"""
计分引擎 - 严格按照文档规则实现
正向计分: 选A → 给选项A对应元素加分, 选B → 给选项B对应元素加分
反向计分: 选A → 给选项B对应元素加分, 选B → 给选项A对应元素加分
每个维度: X=代表元素得分, Y=H-X(H为该维度题目数)
X > Y → 取X对应元素; X ≤ Y → 取Y对应元素
"""
from models import get_dimensions, get_test_questions

def calculate_scores(test_id, answers):
    """
    answers: [{question_id: 'A'或'B'}, ...]
    返回: {
        'dimension_scores': [{'dim_name': 'E-I', 'element_a': 'E', 'element_b': 'I', 'score_a': 4, 'score_b': 2, 'represent': 'E', 'total': 6}],
        'personality_type': 'ENFJ',
        'details': {...}
    }
    """
    questions = get_test_questions(test_id)
    dims_info = get_dimensions()
    dim_map = {d['id']: d for d in dims_info}
    dim_name_map = {d['name']: d for d in dims_info}

    # 按维度分组题目
    dim_questions = {}
    for q in questions:
        dim_id = q['dimension_id']
        if dim_id not in dim_questions:
            dim_questions[dim_id] = []
        dim_questions[dim_id].append(q)

    dimension_scores = []
    personality_letters = []

    # 关键：按维度的标准顺序（E-I → S-N → T-F → J-P）遍历，
    # 而不是按题目首次出现的顺序，否则类型代码字母顺序会错乱（如 PENF）
    for dim in dims_info:
        dim_id = dim['id']
        qs = dim_questions.get(dim_id, [])
        if not qs:
            continue

        element_a = dim['element_a'].upper()
        element_b = dim['element_b'].upper()
        H = len(qs)  # 该维度题目总数

        score_a = 0  # element_a 的得分
        score_b = 0  # element_b 的得分

        for q in qs:
            qid = q['id']
            ans = answers.get(str(qid), '')

            if not ans:
                continue

            is_positive = q['scoring_type'] == 'positive'

            if ans == 'A':
                if is_positive:
                    score_a += 1  # 正向: 选A → A的元素加分
                else:
                    score_b += 1  # 反向: 选A → B的元素加分
            elif ans == 'B':
                if is_positive:
                    score_b += 1  # 正向: 选B → B的元素加分
                else:
                    score_a += 1  # 反向: 选B → A的元素加分

        # 取代表元素
        # X = score_a 对应 element_a, Y = H - score_a = score_b 对应 element_b
        # 如果 score_a > score_b → 取 element_a
        # 如果 score_a ≤ score_b → 取 element_b
        if score_a >= score_b:
            represent = element_a
        else:
            represent = element_b

        personality_letters.append(represent)

        dimension_scores.append({
            'dim_name': dim['name'],
            'element_a': element_a,
            'element_b': element_b,
            'score_a': score_a,
            'score_b': score_b,
            'represent': represent,
            'total': H,
            'style': dim.get('style', 'red'),
        })

    personality_type = ''.join(personality_letters) if personality_letters else 'XXXX'

    return {
        'dimension_scores': dimension_scores,
        'personality_type': personality_type,
        'scores_summary': {ds['dim_name']: {'A': ds['score_a'], 'B': ds['score_b'], 'represent': ds['represent']} for ds in dimension_scores}
    }
