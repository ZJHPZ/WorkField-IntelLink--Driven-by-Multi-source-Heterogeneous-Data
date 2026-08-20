"""L3 抽取层：从清洗后的候选短语抽技能，LLM优先 + 规则兜底。

设计方案 §4.1/4.4：
- 抽取 Agent：星火 extract_json，每个技能回填证据（原文片段）
- 规则兜底：LLM 失败时，规则引擎二次扫描
- 双路径保证不丢数据
"""

from __future__ import annotations

import re

from app.pipeline.l1_clean import CleanedJD
from app.domain import ExtractedSkill

# ══════════════════════════════════════════════
# Prompt 模板
# ══════════════════════════════════════════════

_EXTRACT_SYSTEM = (
    "你是招聘数据分析师。从给定的岗位要求文本中抽取技术技能与硬性要求。"
    "只能抽取文本中真实出现的技能，禁止编造或补充文本外的技能。"
)

# 规则兜底信号词
_SKILL_HINT = re.compile(r"熟悉|掌握|精通|了解|熟练|会|具备|有.*经验|使用")

# 技能名上下文尾巴——从此词起截断
_TAIL_NOISE = re.compile(
    r"(模型训练|项目经验|使用经验|开发经验|实战经验|工作经验|相关经验|经验"
    r"|全流程|原理|架构|结构|部署|分析|调优|能力|功底|基础|协议|技术|框架"
    r"|容器化|调度|做\s*\w)"
)

# 组合技能分隔符
_SPLIT = re.compile(r"[/、,，]|与|以及|和(?![谐])|或")

# 英文技能名后接中文 → 在中文处截断（"C 语言" 除外）
_EN_THEN_CN = re.compile(r"^([A-Za-z0-9+#.]+)\s*(?!语言|语\b)[一-鿿]")


def _atomize(name: str) -> list[str]:
    """把 LLM 返回的带修饰/组合技能名拆成原子技能名列表。"""
    cleaned = re.sub(r"[（(].*?[)）]", "", name)
    out: list[str] = []
    for part in _SPLIT.split(cleaned):
        p = part.strip()
        if not p:
            continue
        m = _TAIL_NOISE.search(p)
        if m:
            p = p[:m.start()]
        m2 = _EN_THEN_CN.match(p)
        if m2:
            p = m2.group(1)
        p = p.strip("的地得 　").strip()
        if p:
            out.append(p)
    return out or [name.strip()]


def _build_extract_prompt(cleaned: CleanedJD) -> str:
    """构建抽取 prompt。"""
    req_lines = [item[1] if len(item) >= 2 else item[0] for item in cleaned.candidates
                 if item[0] == "requirement"]
    bonus_lines = [item[1] if len(item) >= 2 else item[0] for item in cleaned.candidates
                   if item[0] == "bonus"]

    block = ""
    if req_lines:
        block += "【任职要求】\n" + "\n".join(req_lines) + "\n"
    if bonus_lines:
        block += "【加分项】\n" + "\n".join(bonus_lines) + "\n"

    return (
        f"岗位：{cleaned.title}\n"
        f"以下是岗位的要求文本：\n{block}\n"
        '请返回 JSON 数组，每个元素形如 '
        '{"skill":"技能名","type":"必备或加分","evidence":"原文片段"}。\n'
        "要求：\n"
        "1. skill 必须是**最小原子技能名**，不要带任何修饰或上下文。\n"
        "2. 一个短语里若含多个技能，必须拆成多条。\n"
        "3. evidence 必须是从原文中**逐字摘录**的原文片段，禁止写指代词。\n"
        "4. type 判断：来自【加分项】标'加分'，来自【任职要求】标'必备'。\n"
        "5. 只抽取文本中真实出现的技能，禁止编造。"
    )


def _rule_extract(cleaned: CleanedJD) -> list[ExtractedSkill]:
    """规则兜底：从含技能信号词的短语中抽取。"""
    out: list[ExtractedSkill] = []
    for item in cleaned.candidates:
        # 兼容 2 元组 (sec, phrase) 和 4 元组 (sec, phrase, level, category)
        if len(item) == 2:
            sec, phrase = item
        elif len(item) >= 4:
            sec, phrase = item[0], item[1]
        else:
            sec, phrase = item[0], item[1] if len(item) > 1 else ("", "")
        if sec not in ("requirement", "bonus"):
            continue
        if not _SKILL_HINT.search(phrase):
            continue
        core = re.sub(r".*?[:：]", "", phrase)
        core = re.sub(r"^\s*\d+[\.\、\)）]\s*", "", core)  # 剥离 "1." "2、" 等编号前缀
        core = re.sub(r"^(熟悉|掌握|精通|了解|熟练|会|具备|使用)", "", core).strip()
        if core:
            rtype = "加分" if sec == "bonus" else "必备"
            out.append(ExtractedSkill(
                name=core, required_type=rtype, evidence=phrase, source="rule"
            ))
    return out


def extract(cleaned: CleanedJD, client=None) -> list[ExtractedSkill]:
    """抽取一条 JD 的技能。LLM 优先，失败/空则规则兜底。

    Args:
        cleaned: L1 清洗后的 JD
        client: SparkClient 实例，None 则纯规则

    Returns:
        抽取出的技能列表，每条带 evidence 溯源
    """
    if client is None:
        return _rule_extract(cleaned)

    prompt = _build_extract_prompt(cleaned)
    data = None
    try:
        data = client.extract_json(prompt, system=_EXTRACT_SYSTEM)
    except Exception:
        data = None

    if isinstance(data, list) and data:
        out: list[ExtractedSkill] = []
        seen: set[tuple[str, str]] = set()
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("skill", "")).strip()
            if not name:
                continue
            rtype = "加分" if "加分" in str(item.get("type", "")) else "必备"
            evidence = str(item.get("evidence", "")).strip()
            for atom in _atomize(name):
                key = (atom, rtype)
                if key in seen:
                    continue
                seen.add(key)
                out.append(ExtractedSkill(
                    name=atom, required_type=rtype, evidence=evidence, source="spark"
                ))
        if out:
            return out

    return _rule_extract(cleaned)
