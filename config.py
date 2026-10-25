import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'mbti.db')

# 公网访问地址（cpolar 免费版每次重启会变，换了只改这里 + 重生成二维码）
PUBLIC_URL = 'http://6fb76092.r1.cpolar.top'

# 四个维度配置（可在后台编辑）
DEFAULT_DIMENSIONS = [
    {'name': 'E-I', 'element_a': 'E', 'element_b': 'I', 'style': 'red', 'order': 1},
    {'name': 'S-N', 'element_a': 'S', 'element_b': 'N', 'style': 'green', 'order': 2},
    {'name': 'T-F', 'element_a': 'T', 'element_b': 'F', 'style': 'blue', 'order': 3},
    {'name': 'J-P', 'element_a': 'J', 'element_b': 'P', 'style': 'yellow', 'order': 4},
]

# 展示样式配置
STYLES = {
    'red': {'label': '热情红', 'bg': '#FF6B6B', 'gradient': 'linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%)'},
    'green': {'label': '清新绿', 'bg': '#51CF66', 'gradient': 'linear-gradient(135deg, #51CF66 0%, #8CE99A 100%)'},
    'blue': {'label': '深邃蓝', 'bg': '#4DABF7', 'gradient': 'linear-gradient(135deg, #4DABF7 0%, #74C0FC 100%)'},
    'yellow': {'label': '活力黄', 'bg': '#FCC419', 'gradient': 'linear-gradient(135deg, #FCC419 0%, #FFD43B 100%)'},
}

# 选填项配置
GENDER_OPTIONS = [
    {'value': 'male', 'label': '小哥哥', 'style': 'male'},
    {'value': 'female', 'label': '小姐姐', 'style': 'female'},
]

CAREER_OPTIONS = [
    {'value': '0', 'label': '备考汪', 'desc': '大学未满'},
    {'value': '1', 'label': '天之觉子', 'desc': '大学生'},
    {'value': '2', 'label': '小小菜鸡', 'desc': '<3年'},
    {'value': '3', 'label': '佬鸟', 'desc': '3-5年'},
    {'value': '4', 'label': '谁都不鸟', 'desc': '>5年'},
]

EDUCATION_OPTIONS = [
    {'value': '0', 'label': '大赚', 'desc': '大专'},
    {'value': '1', 'label': '笨克', 'desc': '本科'},
    {'value': '2', 'label': '烟酒森', 'desc': '研究生'},
    {'value': '3', 'label': '波士', 'desc': '博士'},
    {'value': '4', 'label': '隐士', 'desc': '其他'},
]
