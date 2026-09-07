"""简历伪解析引擎 —— 未接入真实智能体前的确定性占位逻辑。

背景：真正的简历解析走 Agent（EXTRACT_SKILLS + LLM），但真智能体尚未对接，
上传后无法产出结果。此模块以**确定性规则 + 关键字嗅探**模拟智能体的分析效果，
返回与 `/api/resume/parse` 完全一致的 JSON 契约；将来接真智能体时仅需切换
`config.RESUME_PARSE_MODE = "agent"`，前端零改动。

设计要点：
1. **内容感知**：尽力从上传文件抽出文本（pdfplumber / python-docx）。技能嗅探
   基于「拉丁原子 token 匹配 + 相邻词对 + 中文字符串」三路探测，避免 CJK 与
   英文相邻时 Python `\\w` 把中文也当词字符、导致 `\\bpython\\b` 失效的问题。
2. **画像合成**：命中技能 → 推断领域 → 合成技能/经验/学历/城市。中文字段缺失
   时回落领域默认画像（保证演示始终饱满可信），可读时以真实内容为准。
3. **确定性**：同文件永远得到同一结果，便于稳定演示与单测。

契约（与 parse_resume 对齐）：
    {status, resume_id, skills: list[str], experience_years, education,
     city, skill_count, mode: "pseudo", engine}
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.adapters.resume import ResumeAdapter

# ═══════════════════════════════════════════════════════════════════
# 技能库
#   每项三选一（可组合）：
#     atoms    —— 单个拉丁 token 的命中拼写（全部小写，与 text 分词后逐 token 精确比）
#     pairs    —— 相邻 token 词对，如 spring+boot 命中 "Spring Boot/SpringBoot"
#     text     —— 中文字符串（原文本 `in` 探测）
#   展示名（name）尽量与前端岗位目标的技能同名，便于人岗匹配高亮。
# ═══════════════════════════════════════════════════════════════════

SKILL_KB: list[dict] = [
    # ── 大数据 / 数仓 ──
    {"name": "Hadoop",     "atoms": ["hadoop"], "text": ["hdfs 架构"]},
    {"name": "HDFS",       "atoms": ["hdfs"]},
    {"name": "Spark",      "atoms": ["spark", "sparksql"]},
    {"name": "Flink",      "atoms": ["flink"]},
    {"name": "Kafka",      "atoms": ["kafka"], "text": ["消息队列"]},
    {"name": "Hive",       "atoms": ["hive", "hql"], "text": ["hive 参数"]},
    {"name": "MapReduce",  "atoms": ["mapreduce"], "text": ["mapreduce", "mr 任务", "shuffle"]},
    {"name": "YARN",       "atoms": ["yarn"]},
    {"name": "Zookeeper",  "atoms": ["zookeeper"], "text": ["zkfc"]},
    {"name": "Sqoop",      "atoms": ["sqoop"]},
    {"name": "Flume",      "atoms": ["flume"]},
    {"name": "Maxwell",    "atoms": ["maxwell"]},
    {"name": "DataX",      "atoms": ["datax"]},
    {"name": "DolphinScheduler", "atoms": ["dolphinscheduler"]},
    {"name": "Superset",   "atoms": ["superset"]},
    {"name": "ClickHouse", "atoms": ["clickhouse"]},
    {"name": "Doris",      "atoms": ["doris"]},
    {"name": "Hudi",       "atoms": ["hudi"]},
    {"name": "Iceberg",    "atoms": ["iceberg"]},
    {"name": "ETL",        "atoms": ["etl"]},
    {"name": "数据仓库",     "text": ["数仓", "数据仓库", "维度建模"]},
    {"name": "Airflow",    "atoms": ["airflow"]},
    # ── AI / 算法 ──
    {"name": "Python",     "atoms": ["python"]},
    {"name": "PyTorch",    "atoms": ["pytorch", "torch"]},
    {"name": "TensorFlow", "atoms": ["tensorflow", "tf"]},
    {"name": "Keras",      "atoms": ["keras"]},
    {"name": "Scikit-learn", "atoms": ["sklearn"], "pairs": [["scikit", "learn"]]},
    {"name": "PaddlePaddle", "atoms": ["paddle", "paddlepaddle"], "text": ["飞桨"]},
    {"name": "NLP",        "atoms": ["nlp"], "text": ["自然语言"]},
    {"name": "Transformer", "atoms": ["transformer"]},
    {"name": "RAG",        "atoms": ["rag"], "text": ["检索增强"]},
    {"name": "LangChain",  "atoms": ["langchain"]},
    {"name": "DeepSpeed",  "atoms": ["deepspeed"]},
    {"name": "MLOps",      "atoms": ["mlops", "mlflow", "kubeflow"], "text": ["模型上线", "模型部署"]},
    {"name": "XGBoost",    "atoms": ["xgboost", "lightgbm", "gbdt"]},
    {"name": "OpenCV",     "atoms": ["opencv"]},
    {"name": "YOLO",       "atoms": ["yolo"]},
    {"name": "机器学习",     "text": ["机器学习"]},
    {"name": "深度学习",     "text": ["深度学习", "神经网络"]},
    {"name": "计算机视觉",   "text": ["计算机视觉"]},
    # ── 前端 ──
    {"name": "JavaScript", "atoms": ["javascript", "js"]},
    {"name": "TypeScript", "atoms": ["typescript", "ts"]},
    {"name": "Vue",        "atoms": ["vue", "vue3", "vuejs"]},
    {"name": "React",      "atoms": ["react"]},
    {"name": "Node.js",    "atoms": ["node", "nodejs"]},
    {"name": "Element Plus", "pairs": [["element", "plus"]]},
    {"name": "ECharts",    "atoms": ["echarts"]},
    {"name": "Axios",      "atoms": ["axios"]},
    {"name": "HTML5",      "atoms": ["html", "html5"]},
    {"name": "CSS3",       "atoms": ["css", "css3"]},
    {"name": "Vite",       "atoms": ["vite", "webpack"]},
    {"name": "Tailwind",   "atoms": ["tailwind"]},
    {"name": "小程序",       "atoms": ["uniapp"], "text": ["微信小程序", "小程序"]},
    # ── 后端 / Java ──
    {"name": "Java",       "atoms": ["java"], "text": ["jvm"]},
    {"name": "Spring Boot", "atoms": ["springboot"], "pairs": [["spring", "boot"]]},
    {"name": "Spring Cloud", "atoms": ["springcloud"], "pairs": [["spring", "cloud"]]},
    {"name": "MyBatis",    "atoms": ["mybatis", "mybati", "mybisti"]},
    {"name": "MySQL",      "atoms": ["mysql"]},
    {"name": "PostgreSQL", "atoms": ["postgres", "postgresql", "pgsql"]},
    {"name": "Redis",      "atoms": ["redis"]},
    {"name": "SQL",        "atoms": ["sql"]},
    {"name": "Docker",     "atoms": ["docker"]},
    {"name": "Kubernetes", "atoms": ["kubernetes", "k8s"]},
    {"name": "Go",         "atoms": ["go", "golang"]},
    {"name": "FastAPI",    "atoms": ["fastapi"]},
    {"name": "Flask",      "atoms": ["flask"]},
    {"name": "Django",     "atoms": ["django"]},
    {"name": "Spring",     "atoms": ["spring"], "text": ["ssm"]},
    {"name": "REST API",   "atoms": ["rest"], "text": ["接口设计", "接口开发", "restful"]},
    {"name": "微服务",       "text": ["微服务"]},
    {"name": "Nginx",      "atoms": ["nginx"]},
    # ── 基础设施 / 工具 ──
    {"name": "Git",        "atoms": ["git"]},
    {"name": "Linux",      "atoms": ["linux", "ubuntu", "centos"]},
    {"name": "Shell",      "atoms": ["shell"]},
    {"name": "AWS",        "atoms": ["aws"], "text": ["amazon web services"]},
    {"name": "阿里云",       "atoms": ["aliyun"], "text": ["阿里云"]},
    {"name": "CI/CD",      "atoms": ["jenkins"], "text": ["ci/cd", "持续集成"]},
    {"name": "Elasticsearch", "atoms": ["elasticsearch", "es"]},
]

# 领域 → 技能集合（用于画像分类）
DOMAIN_SKILLS: dict[str, set[str]] = {
    "big_data": {"Hadoop", "HDFS", "Spark", "Flink", "Kafka", "Hive", "MapReduce",
                 "YARN", "Zookeeper", "Sqoop", "Flume", "Maxwell", "DataX",
                 "DolphinScheduler", "Superset", "ClickHouse", "Doris", "Hudi",
                 "Iceberg", "ETL", "数据仓库", "Airflow", "SQL", "MySQL", "Redis",
                 "OpenCV"},
    "ai_ml":    {"Python", "PyTorch", "TensorFlow", "Keras", "Scikit-learn",
                 "PaddlePaddle", "NLP", "Transformer", "RAG", "LangChain",
                 "DeepSpeed", "MLOps", "XGBoost", "机器学习", "深度学习",
                 "计算机视觉", "OpenCV", "YOLO"},
    "frontend": {"JavaScript", "TypeScript", "Vue", "React", "Node.js",
                 "Element Plus", "ECharts", "Axios", "HTML5", "CSS3", "Vite",
                 "Tailwind", "小程序"},
    "backend":  {"Java", "Spring Boot", "Spring Cloud", "MyBatis", "MySQL",
                 "PostgreSQL", "Redis", "Docker", "Kubernetes", "Go", "FastAPI",
                 "Flask", "Django", "Spring", "REST API", "微服务", "Nginx"},
    "infra":    {"Git", "Linux", "Shell", "AWS", "阿里云", "CI/CD",
                 "Elasticsearch", "Docker", "Kubernetes"},
}

_DOMAIN_ORDER = ["big_data", "ai_ml", "frontend", "backend", "infra"]

# 领域默认画像（中文字段缺失时的回落；可读时以真实内容为准）
DOMAIN_PERSONA: dict[str, dict[str, str]] = {
    "big_data": {"education": "本科", "city": "杭州", "experience": "3-5年"},
    "ai_ml":    {"education": "本科", "city": "上海", "experience": "3-5年"},
    "frontend": {"education": "本科", "city": "深圳", "experience": "3-5年"},
    "backend":  {"education": "本科", "city": "北京", "experience": "4-6年"},
    "infra":    {"education": "本科", "city": "北京", "experience": "3-5年"},
    "generic":  {"education": "本科", "city": "北京", "experience": "3-5年"},
}

_CITIES = ["哈尔滨", "石家庄", "呼和浩特", "乌鲁木齐", "西宁", "银川", "兰州",
           "西安", "太原", "济南", "青岛", "天津", "北京", "上海", "广州", "深圳",
           "重庆", "成都", "杭州", "南京", "苏州", "武汉", "长沙", "郑州", "合肥",
           "福州", "厦门", "昆明", "贵阳", "南宁", "沈阳", "大连", "长春", "南昌",
           "无锡", "宁波", "东莞", "佛山"]
_EDU_LEVELS = ["博士后", "博士研究生", "博士", "硕士研究生", "硕士", "研究生",
               "大学本科", "本科生", "本科", "学士", "大专", "专科", "高职"]

_ATOM_RE = re.compile(r"[A-Za-z0-9_]+")  # '+' 等符号作分隔，避免 Flume+DataX 粘连成一个 token
_ASCII_YEAR_RE = re.compile(r"(20\d{2})")


@dataclass
class SimResult:
    """伪解析输出（与 /api/resume/parse 契约对齐）。"""
    resume_id: str = ""
    skills: list[str] = field(default_factory=list)
    experience_years: str = ""
    education: str = ""
    city: str = ""
    domain: str = "generic"
    filename_hint: str = ""


# ═══════════════════════════════════════════════════════════════════
# 文本嗅探
# ═══════════════════════════════════════════════════════════════════

def _atoms(text: str) -> list[str]:
    """抽取拉丁 token 序列（小写），忽略 CJK/符号粘连。"""
    return [t.lower() for t in _ATOM_RE.findall(text)]


def _sniff_skills(text: str) -> set[str]:
    """按 token / 词对 / 中文字符串 三路探测，返回命中技能名集合。"""
    atoms = _atoms(text)
    atom_set = set(atoms)
    lower_text = text.lower()
    found: set[str] = set()
    for kb in SKILL_KB:
        hit = False
        if kb.get("atoms"):
            if any(a in atom_set for a in kb["atoms"]):
                hit = True
        if not hit and kb.get("pairs"):
            for a, b in kb["pairs"]:
                for i in range(len(atoms) - 1):
                    if atoms[i] == a and atoms[i + 1] == b:
                        hit = True
                        break
                if hit:
                    break
        if not hit and kb.get("text"):
            if any(s.lower() in lower_text for s in kb["text"]):
                hit = True
        if hit:
            found.add(kb["name"])
    return found


def _detect_domain(skills: set[str]) -> str:
    """按命中技能与领域集合交集大小分类。"""
    best, best_score = _DOMAIN_ORDER[0], -1
    for dom in _DOMAIN_ORDER:
        score = len(skills & DOMAIN_SKILLS.get(dom, set()))
        if score > best_score:
            best, best_score = dom, score
    return best


def _sniff_education(text: str) -> str | None:
    for cand in _EDU_LEVELS:
        if cand in text:
            return cand
    return None


# 命中“城市”后紧随的高校/机构字样：视为校名一部分（如 北京工业大学、成都信息工程大学），跳过
_UNIV_SUFFIXES = ("大学", "学院", "科技大学", "师范大学", "理工大学", "工业大学",
                  "工程大学", "交通大学", "邮电大学", "财经大学", "农业大学",
                  "医科大学", "外国语大学", "工商大学", "职业技术学院", "信息工程",
                  "工程技术")


def _sniff_city(text: str) -> str | None:
    for city in _CITIES:
        idx = text.find(city)
        if idx < 0:
            continue
        tail = text[idx + len(city): idx + len(city) + 8]
        if any(suf in tail for suf in _UNIV_SUFFIXES):
            continue
        return city
    return None


# 模式一：“X年开发经验”“3年以上工作经验” —— 动词紧跟“年”
_EXP_DIRECT_RE = re.compile(
    r"(?<![\d.])([1-9]\d?)\s*年(?:以上|左右)?\s*(?:工作|从业|研发|开发|实习)经验"
)
# 模式二：“1年大数据开发实习经验” —— 动词与“经验”间夹着领域名词（≤14 字符）
_EXP_SPAN_RE = re.compile(
    r"(?<![\d.])([1-9]\d?)\s*年(?:以上|左右)?[^。\n，,；;]{0,14}?经验"
)
# 前后缀 `(?<![\d.])`：挡住 2022 这类四位年份被截成 “22年/2年” 误判


def _sniff_experience(text: str) -> str | None:
    """只认显式 “X年…经验/工作X年” 等写法；不做日期跨度推断。

    支持两类表述，且不把毕业/入学年份当工作年限（四位年份被前置断言拦截）。
    """
    for pat in (_EXP_DIRECT_RE, _EXP_SPAN_RE):
        m = pat.search(text)
        if m:
            y = int(m.group(1))
            if 1 <= y <= 15:
                return f"{y}年"
    return None


def _looks_unreadable(text: str) -> bool:
    if not text:
        return True
    sample = text[:2000]
    bad = sample.count("�")
    return bad / max(len(sample), 1) > 0.3


def _is_fresh_grad(text: str) -> bool:
    """毕业年份晚于当前年份 → 应届/在读（经验不再用领域画像年资）。"""
    yrs = [int(y) for y in _ASCII_YEAR_RE.findall(text)]
    if not yrs:
        return False
    import datetime
    return max(yrs) > datetime.date.today().year - 1


def _fill_person_fields(text: str, domain: str) -> tuple[str, str, str]:
    """返回 (experience_years, education, city)。

    中文字段可读时以真实内容为准；缺失/乱码回落领域默认画像。
    若明显在读/应届，经验统一标“应届”，避免用教育时段冒充工作年限。
    """
    persona = DOMAIN_PERSONA.get(domain, DOMAIN_PERSONA["generic"])
    unreadable = _looks_unreadable(text)
    fresh_grad = _is_fresh_grad(text)

    edu = _sniff_education(text) if not unreadable else None
    city = _sniff_city(text) if not unreadable else None
    exp = _sniff_experience(text) if not unreadable else None
    exp = exp or persona["experience"]
    if fresh_grad and exp == persona["experience"]:
        exp = "应届"

    return exp, edu or persona["education"], city or persona["city"]


def _ordered_skills(skills: set[str], domain: str) -> list[str]:
    """领域强相关技能优先，其余随其后；均按字典序保证稳定输出。"""
    in_dom = DOMAIN_SKILLS.get(domain, set())
    return sorted(skills, key=lambda s: (s not in in_dom, s))


# ═══════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════

def simulate_parse_text(raw_text: str, filename: str = "") -> dict:
    """对已提取文本做伪解析（内容感知、确定性）。"""
    if not raw_text or not raw_text.strip():
        # 空白/空文本 → 中性画像兜底（与空文件路径走同一兜底）
        return _neutral_profile(filename)
    skills = _sniff_skills(raw_text)
    domain = _detect_domain(skills)
    exp, edu, city = _fill_person_fields(raw_text, domain)
    ordered = _ordered_skills(skills, domain)

    resume_id = f"resume_sim::{hash(raw_text[:2000]) & 0xFFFFFFFF:08x}"
    return {
        "status": "ok",
        "resume_id": resume_id,
        "mode": "pseudo",
        "engine": "keyword-sniff",
        "domain": domain,
        "skills": ordered,
        "experience_years": exp,
        "education": edu,
        "city": city,
        "skill_count": len(ordered),
        "filename_hint": filename,
    }


def simulate_parse_file(file_path: str, filename: str = "") -> dict:
    """解析上传文件（PDF/Word/文本）→ 伪解析。复用 ResumeAdapter 做文本抽取。"""
    lower = (file_path or "").lower()
    text = ""
    try:
        if lower.endswith(".doc") and not lower.endswith(".docx"):
            text = _read_legacy_doc(file_path)
        else:
            docs = ResumeAdapter().parse(file_path)
            text = docs[0].raw_text if docs else ""
    except Exception:
        text = ""

    # 乱码/无文本：抽 ASCII 段保留技能词；仍失败则给中性画像兜底
    if not text or _looks_unreadable(text):
        text = _collect_ascii_only(text)

    result = simulate_parse_text(text, filename=filename)
    if not result["skills"]:
        result = _neutral_profile(filename)
    return result


def _read_legacy_doc(path: str) -> str:
    """旧版 .doc（非 .docx）：按二进制剥离空字节，尽力保留文本。"""
    try:
        with open(path, "rb") as f:
            data = f.read()
        return " ".join(w.decode("utf-8", "ignore")
                        for w in data.split(b"\x00") if len(w) > 2)
    except Exception:
        return ""


def _collect_ascii_only(text: str) -> str:
    """乱码文本中仅保留 ASCII 段（技能/数字仍可嗅探），丢弃 U+FFFD。"""
    return " ".join(
        tok for tok in re.findall(r"[A-Za-z0-9+#./_'-]{2,}", text) if "�" not in tok
    )


def _neutral_profile(filename: str = "") -> dict:
    """完全无法读取时给中性画像（模拟“人工录入”兜底）。"""
    p = DOMAIN_PERSONA["generic"]
    return {
        "status": "ok",
        "resume_id": f"resume_sim::{abs(hash(filename)) & 0xFFFFFFFF:08x}",
        "mode": "pseudo",
        "engine": "keyword-sniff",
        "domain": "generic",
        "skills": ["Python", "SQL", "Linux", "Git"],
        "experience_years": p["experience"],
        "education": p["education"],
        "city": p["city"],
        "skill_count": 4,
        "filename_hint": filename,
    }
