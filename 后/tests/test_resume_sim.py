"""resume_sim 伪解析引擎单元测试 —— 纯函数，无需 DB/LLM/联网。"""

from __future__ import annotations

import re

import pytest

from app.services import resume_sim


# 一份合成中文简历（覆盖：中英混排、多段技能、词对、在读应届）
SAMPLE_RESUME = """张三
大数据开发工程师 全职
电话：13800000000 现住城市：成都
教育经历
成都信息工程大学 本科 计算机科学与技术 2022.09-2026.06
- 主修：数据结构、操作系统、Java/Python程序设计、机器学习基础。
项目经历
xx离线数仓 数仓建模与加工 2025.03-至今
应用技术：Hadoop+Hive+Spark SQL+Flume+DataX+MySQL+Superset
1. 使用Hive SQL清洗数据，搭建数仓分层模型，配合ETL落地；
2. 使用Vue 3 + Element Plus 开发数据看板，ECharts 可视化，Axios 调接口；
3. 熟悉SpringBoot后端接口开发，MySQL 存储，Redis 缓存。
自我评价：1年大数据开发实习经验，本科毕业。
"""


def test_detect_skills_content_aware():
    r = resume_sim.simulate_parse_text(SAMPLE_RESUME)
    sk = set(r["skills"])
    # 技能应覆盖简历真实技术栈
    for expect in ["Python", "Java", "Hadoop", "Hive", "Spark", "SQL", "MySQL",
                   "DataX", "Flume", "Superset", "Vue", "Element Plus",
                   "ECharts", "Axios", "Spring Boot", "Redis"]:
        assert expect in sk, f"漏判技能 {expect}"
    # 领域归为大数仓
    assert r["domain"] == "big_data"


def test_person_fields_sniffed():
    r = resume_sim.simulate_parse_text(SAMPLE_RESUME)
    assert r["city"] == "成都"          # 可读中文字段按真实内容
    assert r["education"] == "本科"
    assert r["experience_years"] == "1年"   # 显式 “1年…实习经验”


def test_university_not_mistaken_for_city():
    # “成都信息工程大学”里的“成都”不应因紧邻高校名而误判为居住地……但下方另给出真实城市
    text = "成都信息工程大学 计算机本科\n现住城市：上海"
    r = resume_sim.simulate_parse_text(text)
    assert r["city"] == "上海"


def test_deterministic_same_input():
    a = resume_sim.simulate_parse_text(SAMPLE_RESUME)
    b = resume_sim.simulate_parse_text(SAMPLE_RESUME)
    assert a == b
    assert a["skills"] == b["skills"]


def test_fresh_grad_overrides_seniority_persona():
    # 毕业年份在未来 → 即便领域画像默认多年，也应标“应届”
    text = "郑州某大学 计算机 2023.09-2027.06 本科\nHadoop Hive Spark 数据仓库"
    r = resume_sim.simulate_parse_text(text)
    assert r["experience_years"] == "应届"


def test_mojibake_pdf_style_still_sniffs_ascii_skills():
    # 模拟 PDF 中文字段乱码、仅 ASCII 可辨的情形（对应真实 简历(2).pdf）
    garbled = "".join("�" for _ in range(40)) + " HDFS YARN MapReduce Hive Vue3 " + "".join("�" for _ in range(40))
    r = resume_sim.simulate_parse_text(garbled)
    sk = set(r["skills"])
    assert "HDFS" in sk and "YARN" in sk and "Hive" in sk and "Vue" in sk
    # 乱码文本不给随意画像，仍由领域画像兜底
    assert r["experience_years"] != ""


def test_ascii_token_not_fragmented_by_plus():
    # “Flume+DataX+MySQL” 这类 + 连接串必须各自成 token 命中
    text = "技术栈：Flume+Maxwell+DataX+MySQL+Superset"
    sk = set(resume_sim.simulate_parse_text(text)["skills"])
    for expect in ["Flume", "Maxwell", "DataX", "MySQL", "Superset"]:
        assert expect in sk


def test_bilingual_boundary_python():
    # CJK 紧邻英文时 python 仍应命中（曾经的 \\bpython\\b 失效场景）
    text = "主修 Java/Python程序设计、Web前端开发。"
    r = resume_sim.simulate_parse_text(text)
    assert "Python" in set(r["skills"])
    assert "Java" in set(r["skills"])


def test_neutral_profile_when_empty():
    r = resume_sim.simulate_parse_text("")
    assert r["skills"]  # 非空（中性兜底）
    assert r["status"] == "ok"
    assert re.fullmatch(r"[0-9a-f]{8}", r["resume_id"].split("::")[-1])
