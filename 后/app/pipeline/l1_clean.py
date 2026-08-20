"""L1 清洗层：正则抽强结构字段 + 段落定位 + L0 噪声过滤 + 分级归类。

设计方案 §2.2/2.3：
- 强结构字段用正则（薪资/经验/学历），不进大模型
- 段落定位：福利段直接判为低价值
- L0 纯噪声词典过滤（只手工维护 L0，L1-L3 由数据驱动）
- 分级归类：每个短语打 L0-L3 级别，软技能不删而是带岗位权重
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.domain import JobPosting, Paragraph, SectionType


# ══════════════════════════════════════════════
# L0 纯噪声词典（福利套话，有限且稳定）
# ══════════════════════════════════════════════

L0_NOISE = {
    "五险一金", "带薪年假", "弹性工作", "氛围好", "定期团建", "免费下午茶",
    "股票期权", "节日福利", "年度体检", "免费班车", "六险一金", "餐补",
    "话补", "房补", "双休", "年终奖", "扁平化管理", "零食",
}


# ══════════════════════════════════════════════
# 正则：强结构字段
# ══════════════════════════════════════════════

_SALARY_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*[kK千]?\s*[-~至到]\s*(\d+(?:\.\d+)?)\s*([kK千]|[wW万])"
)
# 备用薪资格式: "30-60K" (数字-K，中间无空格)
_SALARY_K_RE = re.compile(r"(\d+)\s*-\s*(\d+)\s*[kK](?!\w)")
_EXP_RE = re.compile(r"(\d+)\s*年")
_EDU_RE = re.compile(r"(博士|硕士|研究生|本科|大专|专科|高中)")
_SKILL_HINT = re.compile(r"熟悉|掌握|精通|了解|熟练|会|具备|有.*经验|使用")


def _parse_salary(text: str) -> tuple[int | None, int | None]:
    # 先试 "30-60K" 格式
    m = _SALARY_K_RE.search(text)
    if m:
        return int(m.group(1)) * 1000, int(m.group(2)) * 1000
    # 再试 "15K-30K" / "1.5万-3万" 格式
    m = _SALARY_RE.search(text)
    if not m:
        return None, None
    lo, hi, unit = float(m.group(1)), float(m.group(2)), m.group(3)
    mult = 10000 if unit in ("w", "W", "万") else 1000
    return int(lo * mult), int(hi * mult)


def _parse_experience(text: str) -> int | None:
    m = _EXP_RE.search(text)
    return int(m.group(1)) if m else None


def _parse_education(text: str) -> str | None:
    m = _EDU_RE.search(text)
    return m.group(1) if m else None


def _is_noise(text: str) -> bool:
    """整句是否为 L0 纯噪声。"""
    hits = sum(1 for w in L0_NOISE if w in text)
    return hits >= 2 or (hits >= 1 and len(text) <= 12)


def _split_phrases(text: str) -> list[str]:
    """按中文标点切成短语。"""
    parts = re.split(r"[，。；、\n]", text)
    return [p.strip() for p in parts if p.strip()]


# ══════════════════════════════════════════════
# 分级归类（设计方案 §2.3）
# ══════════════════════════════════════════════

# 泛化软技能信号词 —— 在几乎所有岗位都出现 → 倾向判 L1
_GENERIC_SOFT_SKILLS = {
    "抗压能力", "责任心", "积极主动", "学习能力", "团队合作", "沟通能力",
    "上进心", "敬业", "吃苦耐劳", "执行力", "有责任心",
}


def classify_skill(phrase: str, section: str) -> tuple[str, str]:
    """给一个短语打级别（L0-L3）+ 类别（hard/soft/tool）。

    Returns:
        (level, category): level ∈ {L0, L1, L2, L3}, category ∈ {hard, soft, tool, noise}
    """
    # L0: 命中噪声词
    if _is_noise(phrase):
        return ("L0", "noise")

    # L3: 识别硬技能信号（含英文/数字/技术栈词）
    if re.search(r"[A-Za-z+#./]", phrase):
        return ("L3", "hard")

    tech_keywords = {"框架", "算法", "模型", "数据库", "系统", "架构",
                     "协议", "部署", "容器", "网络", "测试", "运维",
                     "开发", "编程", "嵌入式", "前端", "后端", "云"}
    if any(kw in phrase for kw in tech_keywords):
        return ("L3", "hard")

    # L1: 泛化软技能
    for gs in _GENERIC_SOFT_SKILLS:
        if gs in phrase:
            return ("L1", "soft")

    # L2: 岗位相关软技能（非泛化且有技能信号词，默认判为 L2，实际权重由 IDF 浮调）
    if _SKILL_HINT.search(phrase):
        return ("L2", "soft")

    # 其余判为 L1 泛化
    return ("L1", "soft")


# ══════════════════════════════════════════════
# 清洗输出
# ══════════════════════════════════════════════

@dataclass
class CleanedJD:
    """L1 清洗输出：强字段已抽取 + 分级候选短语。"""
    jd_id: str
    title: str
    tech_stack: str
    posted_date: str
    salary_min: int | None = None
    salary_max: int | None = None
    experience_years: int | None = None
    education: str | None = None
    # 候选短语：[(section_type, phrase, level, category), ...]
    candidates: list[tuple[str, str, str, str]] = field(default_factory=list)


def clean(jd: JobPosting) -> CleanedJD:
    """清洗一条 JD：强字段正则抽取 + 段落定位 + L0 过滤 + 分级归类。"""
    full = jd.full_text()

    # 强字段
    sal_min, sal_max = jd.salary_min, jd.salary_max
    if sal_min is None:
        sal_min, sal_max = _parse_salary(full)
    exp = jd.experience_years or _parse_experience(full)
    edu = jd.education or _parse_education(full)

    # 候选短语：遍历段落，分级归类
    candidates: list[tuple[str, str, str, str]] = []
    for para in jd.paragraphs:
        sec = para.section.value if isinstance(para.section, SectionType) else para.section

        # 福利段/公司段/其他段跳过（other 通常是标题行，非技能内容）
        if sec in ("welfare", "company", "other"):
            continue

        for phrase in _split_phrases(para.text):
            level, category = classify_skill(phrase, sec)

            # L0 丢弃
            if level == "L0":
                continue

            candidates.append((sec, phrase, level, category))

    return CleanedJD(
        jd_id=jd.jd_id,
        title=jd.title,
        tech_stack=jd.tech_stack.value if hasattr(jd.tech_stack, 'value') else jd.tech_stack,
        posted_date=jd.posted_date,
        salary_min=sal_min,
        salary_max=sal_max,
        experience_years=exp,
        education=edu,
        candidates=candidates,
    )
