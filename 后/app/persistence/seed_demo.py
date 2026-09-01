"""种子脚本 —— 为 demo_user 填充档案 / 技能 / 匹配 / 学习路径（幂等，可重复运行）。

用法：python -m app.persistence.seed_demo

数据与前端 web/zhiyu-frontend/src/stores/personal.ts 的 demo 数据保持一致，
使 AI 对话顾问能看到与用户仪表盘一致的技能画像。
仅当某类数据为空时插入，不会覆盖已有数据。
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select, func

from app.config import get_settings
from app.persistence.database import get_session, init_db, close_db
from app.persistence.zhiyv_models import (
    UserProfile, UserSkill, UserMatch, LearningStepModel, EnterpriseProfile,
)

DEFAULT_USER = "demo_user"

# ── 职业档案（与前端个人侧一致：张明 · 高级前端开发工程师）──
_PROFILE = dict(
    name="张明",
    title="高级前端开发工程师",
    phone="13800138000",
    email="zhangming@example.com",
    birth_year=1995,
    status="employed_looking",
    industry="互联网/IT",
    education="本科",
    major="计算机科学与技术",
    english_level="CET-6",
    experience_years="5-8年",
    city="北京",
    target_role="全栈工程师",
    target_city="上海",
    target_industry="互联网/IT",
    salary_min=25,
    salary_max=40,
    priority="tech_growth",
)

# ── 技能（与前端 demoSkills 一致）──
# 注意：user_skills 有唯一索引 uk_user_skill(user_id, canonical_name)，必须提供不重复的 canonical_name。
_SKILLS = [
    dict(skill_name="Python", canonical_name="python", category="编程语言", level="expert", market_demand=92, market_df=245,
         emergence=0.05, decline=0.02, freshness=90, years_of_experience=6.0, confidence=0.98, status="healthy"),
    dict(skill_name="深度学习", canonical_name="深度学习", category="AI/ML", level="advanced", market_demand=95, market_df=210,
         emergence=0.80, decline=0.01, freshness=88, years_of_experience=4.0, confidence=0.92, status="healthy"),
    dict(skill_name="TypeScript", canonical_name="typescript", category="前端", level="advanced", market_demand=80, market_df=178,
         emergence=0.15, decline=0.03, freshness=76, years_of_experience=3.0, confidence=0.90, status="healthy"),
    dict(skill_name="React", canonical_name="react", category="前端", level="advanced", market_demand=78, market_df=195,
         emergence=0.08, decline=0.05, freshness=82, years_of_experience=4.0, confidence=0.95, status="matched"),
    dict(skill_name="SQL", canonical_name="sql", category="数据", level="expert", market_demand=75, market_df=320,
         emergence=0.02, decline=0.01, freshness=92, years_of_experience=7.0, confidence=0.99, status="healthy"),
    dict(skill_name="Docker/K8s", canonical_name="docker_k8s", category="DevOps", level="intermediate", market_demand=85, market_df=230,
         emergence=0.12, decline=0.04, freshness=65, years_of_experience=2.0, confidence=0.85, status="alert"),
    dict(skill_name="NLP", canonical_name="nlp", category="AI/ML", level="intermediate", market_demand=88, market_df=165,
         emergence=0.70, decline=0.02, freshness=80, years_of_experience=3.0, confidence=0.88, status="healthy"),
    dict(skill_name="系统设计", canonical_name="系统设计", category="架构", level="intermediate", market_demand=82, market_df=140,
         emergence=0.10, decline=0.03, freshness=70, years_of_experience=3.0, confidence=0.82, status="healthy"),
    dict(skill_name="Go", canonical_name="go", category="编程语言", level="basic", market_demand=72, market_df=130,
         emergence=0.25, decline=0.02, freshness=45, years_of_experience=1.0, confidence=0.75, status="alert"),
    dict(skill_name="Kubernetes", canonical_name="kubernetes", category="DevOps", level="basic", market_demand=85, market_df=185,
         emergence=0.30, decline=0.01, freshness=35, years_of_experience=0.5, confidence=0.70, status="alert"),
    dict(skill_name="MLOps", canonical_name="mlops", category="AI/ML", level="basic", market_demand=78, market_df=95,
         emergence=0.65, decline=0.01, freshness=40, years_of_experience=1.0, confidence=0.72, status="alert"),
    dict(skill_name="数据分析", canonical_name="数据分析", category="数据", level="intermediate", market_demand=70, market_df=155,
         emergence=0.08, decline=0.06, freshness=85, years_of_experience=4.0, confidence=0.90, status="healthy"),
]

# ── 人岗匹配（与前端 richDemoMatches 一致，前 4 条）──
_MATCHES = [
    dict(position_id="pos-ai-algo", position_name="AI 算法工程师", company="某头部 AI 研发平台", match_rate=82.0,
         matched_skills={"Python": 3, "深度学习": 3, "NLP": 2, "PyTorch": 1},
         missing_skills={"MLOps": 0, "分布式训练": 0, "模型部署": 0}, salary_range="40-70K"),
    dict(position_id="pos-fullstack", position_name="全栈开发工程师", company="某一线互联网大厂", match_rate=85.0,
         matched_skills={"TypeScript": 3, "React": 3, "SQL": 3, "Node.js": 1},
         missing_skills={"AWS": 0, "Redis": 0, "Docker 编排": 0}, salary_range="30-50K"),
    dict(position_id="pos-ml-eng", position_name="ML Engineer", company="某 AI 独角兽", match_rate=78.0,
         matched_skills={"Python": 3, "深度学习": 3, "NLP": 2, "Kubernetes": 1},
         missing_skills={"MLOps": 0, "模型评估": 0, "A/B 实验": 0}, salary_range="45-80K"),
    dict(position_id="pos-fe-arch", position_name="前端架构工程师", company="某大型金融科技集团", match_rate=88.0,
         matched_skills={"TypeScript": 3, "React": 3, "SQL": 3, "系统设计": 2},
         missing_skills={"微前端": 0, "Webpack 性能调优": 0}, salary_range="35-60K"),
]

# ── 学习路径（与前端 demoLearningPath 一致）──
_STEPS = [
    dict(title="Kubernetes 基础", skill="Kubernetes", resource="K8s 官方教程 + CKAD 认证",
         estimated_hours=40, status="available", progress=0, sort_order=1),
    dict(title="MLOps 实践", skill="MLOps", resource="MLflow + Kubeflow 实战",
         estimated_hours=30, status="available", progress=0, sort_order=2),
    dict(title="Go 语言进阶", skill="Go", resource="Go 高级编程 + 并发模式",
         estimated_hours=25, status="in_progress", progress=35, sort_order=3),
    dict(title="系统设计面试", skill="系统设计", resource="DDIA + 案例分析",
         estimated_hours=20, status="in_progress", progress=60, sort_order=4),
    dict(title="React 性能优化", skill="React", resource="React 性能优化指南",
         estimated_hours=15, status="completed", progress=100, sort_order=5),
]

# ── 企业侧人才库：独立虚拟候选人（user_id 均 ≠ demo_user，与个人侧张明无关）──
# 注意：UserSkill 唯一索引 uk_user_skill(user_id, canonical_name)——候选人内部 canonical_name 不可重复；
# 不同候选人之间可共享技能名。match_rate 存百分制（88.0）。
CANDIDATES = [
    {
        "user_id": "cand_li_wei",
        "profile": dict(name="李伟", title="高级后端开发工程师", target_role="资深后端工程师",
                        target_city="上海", city="上海", industry="互联网/IT", experience_years="8-10年",
                        education="本科", major="计算机科学与技术", english_level="CET-6",
                        salary_min=35, salary_max=55, status="employed_looking", birth_year=1991,
                        work_mode="hybrid", relocate_ok=True, travel_ok=False, avatar_emoji="🧑‍💻", level=48),
        "skills": [
            dict(skill_name="Go", canonical_name="go", category="编程语言", level="expert", market_demand=90, market_df=210, emergence=0.12, decline=0.01, freshness=92, years_of_experience=8.0, confidence=0.96, status="healthy"),
            dict(skill_name="Kubernetes", canonical_name="kubernetes", category="DevOps", level="advanced", market_demand=85, market_df=185, emergence=0.30, decline=0.01, freshness=78, years_of_experience=4.0, confidence=0.88, status="healthy"),
            dict(skill_name="MySQL", canonical_name="mysql", category="数据", level="expert", market_demand=80, market_df=300, emergence=0.01, decline=0.03, freshness=85, years_of_experience=8.0, confidence=0.95, status="healthy"),
            dict(skill_name="Redis", canonical_name="redis", category="数据", level="advanced", market_demand=72, market_df=150, emergence=0.03, decline=0.05, freshness=75, years_of_experience=6.0, confidence=0.90, status="healthy"),
            dict(skill_name="Kafka", canonical_name="kafka", category="中间件", level="intermediate", market_demand=70, market_df=120, emergence=0.15, decline=0.02, freshness=60, years_of_experience=3.0, confidence=0.82, status="healthy"),
            dict(skill_name="系统设计", canonical_name="系统设计", category="架构", level="expert", market_demand=82, market_df=140, emergence=0.10, decline=0.03, freshness=82, years_of_experience=8.0, confidence=0.94, status="healthy"),
        ],
        "matches": [
            dict(position_id="pos-go-senior", position_name="资深后端工程师", company="某云原生平台", match_rate=88.0,
                 matched_skills={"Go": 3, "系统设计": 3, "Kubernetes": 2, "MySQL": 3},
                 missing_skills={"Rust": 0, "eBPF": 0}, salary_range="45-82K"),
            dict(position_id="pos-platform", position_name="平台工程师", company="某互联网大厂", match_rate=82.0,
                 matched_skills={"Go": 3, "Kubernetes": 3, "Redis": 2},
                 missing_skills={"云原生安全": 0}, salary_range="40-70K"),
        ],
    },
    {
        "user_id": "cand_wang_fang",
        "profile": dict(name="王芳", title="AI 算法工程师", target_role="大模型算法工程师",
                        target_city="北京", city="北京", industry="互联网/IT", experience_years="5-8年",
                        education="硕士", major="模式识别与智能系统", english_level="IELTS 7.0",
                        salary_min=40, salary_max=65, status="employed_looking", birth_year=1994,
                        work_mode="remote", relocate_ok=False, travel_ok=False, avatar_emoji="👩‍💻", level=42),
        "skills": [
            dict(skill_name="Python", canonical_name="python", category="编程语言", level="expert", market_demand=92, market_df=245, emergence=0.05, decline=0.02, freshness=90, years_of_experience=7.0, confidence=0.98, status="healthy"),
            dict(skill_name="PyTorch", canonical_name="pytorch", category="AI/ML", level="advanced", market_demand=90, market_df=180, emergence=0.60, decline=0.01, freshness=85, years_of_experience=5.0, confidence=0.93, status="healthy"),
            dict(skill_name="NLP", canonical_name="nlp", category="AI/ML", level="expert", market_demand=88, market_df=165, emergence=0.70, decline=0.02, freshness=88, years_of_experience=6.0, confidence=0.96, status="healthy"),
            dict(skill_name="LLM 微调", canonical_name="llm微调", category="AI/ML", level="advanced", market_demand=95, market_df=220, emergence=0.95, decline=0.0, freshness=95, years_of_experience=3.0, confidence=0.90, status="healthy"),
            dict(skill_name="RAG", canonical_name="rag", category="AI/ML", level="intermediate", market_demand=88, market_df=160, emergence=0.85, decline=0.0, freshness=80, years_of_experience=2.0, confidence=0.85, status="healthy"),
        ],
        "matches": [
            dict(position_id="pos-llm", position_name="大模型算法工程师", company="某头部大模型公司", match_rate=90.0,
                 matched_skills={"Python": 3, "深度学习": 3, "NLP": 3, "RAG": 2},
                 missing_skills={"分布式训练": 0, "推理优化": 0}, salary_range="60-90K"),
            dict(position_id="pos-ml-eng", position_name="ML Engineer", company="某 AI 独角兽", match_rate=85.0,
                 matched_skills={"Python": 3, "PyTorch": 3, "NLP": 2},
                 missing_skills={"MLOps": 0}, salary_range="45-80K"),
        ],
    },
    {
        "user_id": "cand_chen_jie",
        "profile": dict(name="陈杰", title="资深前端开发工程师", target_role="前端架构工程师",
                        target_city="杭州", city="杭州", industry="互联网/IT", experience_years="5-8年",
                        education="本科", major="软件工程", english_level="CET-6",
                        salary_min=28, salary_max=45, status="employed_looking", birth_year=1993,
                        work_mode="hybrid", relocate_ok=True, travel_ok=True, avatar_emoji="🧑‍💻", level=40),
        "skills": [
            dict(skill_name="TypeScript", canonical_name="typescript", category="前端", level="expert", market_demand=80, market_df=178, emergence=0.15, decline=0.03, freshness=88, years_of_experience=6.0, confidence=0.95, status="healthy"),
            dict(skill_name="React", canonical_name="react", category="前端", level="expert", market_demand=78, market_df=195, emergence=0.08, decline=0.05, freshness=85, years_of_experience=6.0, confidence=0.96, status="healthy"),
            dict(skill_name="Vue", canonical_name="vue", category="前端", level="advanced", market_demand=72, market_df=160, emergence=0.02, decline=0.08, freshness=78, years_of_experience=4.0, confidence=0.90, status="healthy"),
            dict(skill_name="微前端", canonical_name="微前端", category="架构", level="advanced", market_demand=70, market_df=95, emergence=0.20, decline=0.02, freshness=82, years_of_experience=3.0, confidence=0.86, status="healthy"),
            dict(skill_name="Node.js", canonical_name="nodejs", category="后端", level="intermediate", market_demand=75, market_df=140, emergence=0.05, decline=0.06, freshness=70, years_of_experience=3.0, confidence=0.84, status="healthy"),
        ],
        "matches": [
            dict(position_id="pos-fe-arch", position_name="前端架构工程师", company="某大型金融科技集团", match_rate=89.0,
                 matched_skills={"TypeScript": 3, "React": 3, "微前端": 2, "系统设计": 2},
                 missing_skills={"Webpack 性能调优": 0}, salary_range="35-60K"),
            dict(position_id="pos-fullstack", position_name="全栈开发工程师", company="某一线互联网大厂", match_rate=83.0,
                 matched_skills={"TypeScript": 3, "React": 3, "Node.js": 2},
                 missing_skills={"AWS": 0, "Redis": 0}, salary_range="30-50K"),
        ],
    },
    {
        "user_id": "cand_liu_yang",
        "profile": dict(name="刘洋", title="数据分析师", target_role="数据产品经理 / AI BI",
                        target_city="深圳", city="深圳", industry="互联网/IT", experience_years="3-5年",
                        education="本科", major="统计学", english_level="CET-6",
                        salary_min=18, salary_max=30, status="employed_looking", birth_year=1998,
                        work_mode="hybrid", relocate_ok=True, travel_ok=False, avatar_emoji="🧑‍💻", level=25),
        "skills": [
            dict(skill_name="SQL", canonical_name="sql", category="数据", level="advanced", market_demand=75, market_df=320, emergence=0.02, decline=0.01, freshness=80, years_of_experience=4.0, confidence=0.92, status="healthy"),
            dict(skill_name="Python", canonical_name="python", category="编程语言", level="intermediate", market_demand=92, market_df=245, emergence=0.05, decline=0.02, freshness=72, years_of_experience=3.0, confidence=0.86, status="healthy"),
            dict(skill_name="Pandas", canonical_name="pandas", category="数据", level="advanced", market_demand=70, market_df=120, emergence=0.04, decline=0.03, freshness=75, years_of_experience=3.0, confidence=0.88, status="healthy"),
            dict(skill_name="Tableau", canonical_name="tableau", category="数据", level="intermediate", market_demand=65, market_df=90, emergence=0.01, decline=0.04, freshness=65, years_of_experience=2.0, confidence=0.80, status="healthy"),
            dict(skill_name="A/B 实验", canonical_name="ab实验", category="数据", level="intermediate", market_demand=72, market_df=110, emergence=0.10, decline=0.01, freshness=70, years_of_experience=2.0, confidence=0.82, status="healthy"),
        ],
        "matches": [
            dict(position_id="pos-data-analyst", position_name="数据分析师", company="某电商平台", match_rate=86.0,
                 matched_skills={"SQL": 3, "Python": 2, "Pandas": 2},
                 missing_skills={"A/B 实验": 0}, salary_range="20-35K"),
            dict(position_id="pos-data-product", position_name="数据产品经理", company="某金融科技公司", match_rate=78.0,
                 matched_skills={"SQL": 3, "Tableau": 2},
                 missing_skills={"产品设计": 0}, salary_range="25-40K"),
        ],
    },
    {
        "user_id": "cand_zhao_min",
        "profile": dict(name="赵敏", title="DevOps 工程师", target_role="平台工程架构师",
                        target_city="北京", city="北京", industry="互联网/IT", experience_years="6-8年",
                        education="本科", major="自动化", english_level="CET-6",
                        salary_min=32, salary_max=55, status="employed_looking", birth_year=1992,
                        work_mode="onsite", relocate_ok=False, travel_ok=True, avatar_emoji="🧑‍💻", level=38),
        "skills": [
            dict(skill_name="Kubernetes", canonical_name="kubernetes", category="DevOps", level="expert", market_demand=85, market_df=185, emergence=0.30, decline=0.01, freshness=88, years_of_experience=5.0, confidence=0.94, status="healthy"),
            dict(skill_name="Terraform", canonical_name="terraform", category="DevOps", level="advanced", market_demand=80, market_df=130, emergence=0.40, decline=0.01, freshness=80, years_of_experience=3.0, confidence=0.88, status="healthy"),
            dict(skill_name="CI/CD", canonical_name="cicd", category="DevOps", level="expert", market_demand=78, market_df=170, emergence=0.10, decline=0.03, freshness=90, years_of_experience=6.0, confidence=0.95, status="healthy"),
            dict(skill_name="Docker", canonical_name="docker", category="DevOps", level="expert", market_demand=82, market_df=200, emergence=0.05, decline=0.04, freshness=85, years_of_experience=6.0, confidence=0.96, status="healthy"),
            dict(skill_name="可观测性", canonical_name="可观测性", category="DevOps", level="advanced", market_demand=75, market_df=100, emergence=0.25, decline=0.01, freshness=78, years_of_experience=4.0, confidence=0.87, status="healthy"),
            dict(skill_name="Linux", canonical_name="linux", category="操作系统", level="expert", market_demand=80, market_df=240, emergence=0.01, decline=0.02, freshness=92, years_of_experience=7.0, confidence=0.97, status="healthy"),
        ],
        "matches": [
            dict(position_id="pos-devops", position_name="DevOps 工程师", company="某大型云服务商", match_rate=90.0,
                 matched_skills={"Kubernetes": 3, "Terraform": 3, "CI/CD": 3, "Docker": 2},
                 missing_skills={"服务网格": 0}, salary_range="45-75K"),
            dict(position_id="pos-sre", position_name="SRE 工程师", company="某金融科技集团", match_rate=84.0,
                 matched_skills={"Kubernetes": 3, "可观测性": 2, "Linux": 3},
                 missing_skills={"SRE 方法论": 0}, salary_range="40-68K"),
        ],
    },
    {
        "user_id": "cand_sun_yue",
        "profile": dict(name="孙悦", title="测试开发工程师", target_role="质量架构工程师 / AI 测试",
                        target_city="成都", city="成都", industry="互联网/IT", experience_years="3-5年",
                        education="本科", major="软件工程", english_level="CET-4",
                        salary_min=15, salary_max=25, status="employed_looking", birth_year=1999,
                        work_mode="hybrid", relocate_ok=True, travel_ok=False, avatar_emoji="👩‍💻", level=22),
        "skills": [
            dict(skill_name="自动化测试", canonical_name="自动化测试", category="测试", level="expert", market_demand=72, market_df=120, emergence=0.15, decline=0.02, freshness=86, years_of_experience=4.0, confidence=0.93, status="healthy"),
            dict(skill_name="Playwright", canonical_name="playwright", category="测试", level="advanced", market_demand=70, market_df=80, emergence=0.35, decline=0.01, freshness=78, years_of_experience=3.0, confidence=0.88, status="healthy"),
            dict(skill_name="API 测试", canonical_name="api测试", category="测试", level="advanced", market_demand=68, market_df=95, emergence=0.10, decline=0.03, freshness=80, years_of_experience=4.0, confidence=0.90, status="healthy"),
            dict(skill_name="性能测试", canonical_name="性能测试", category="测试", level="intermediate", market_demand=65, market_df=70, emergence=0.05, decline=0.05, freshness=65, years_of_experience=2.0, confidence=0.80, status="healthy"),
            dict(skill_name="SQL", canonical_name="sql", category="数据", level="intermediate", market_demand=75, market_df=320, emergence=0.02, decline=0.01, freshness=70, years_of_experience=3.0, confidence=0.84, status="healthy"),
        ],
        "matches": [
            dict(position_id="pos-qa", position_name="QA 工程师", company="某大型电商", match_rate=88.0,
                 matched_skills={"自动化测试": 3, "Playwright": 3, "API 测试": 2},
                 missing_skills={"性能分析": 0}, salary_range="18-30K"),
            dict(position_id="pos-quality", position_name="质量工程", company="某车企", match_rate=80.0,
                 matched_skills={"自动化测试": 3, "SQL": 2},
                 missing_skills={"质量度量": 0}, salary_range="20-32K"),
        ],
    },
    {
        "user_id": "cand_zhou_qi",
        "profile": dict(name="周琪", title="初级全栈开发工程师", target_role="全栈工程师",
                        target_city="广州", city="广州", industry="互联网/IT", experience_years="1-3年",
                        education="本科", major="计算机科学", english_level="CET-6",
                        salary_min=12, salary_max=20, status="employed_looking", birth_year=2001,
                        work_mode="hybrid", relocate_ok=True, travel_ok=False, avatar_emoji="🧑‍💻", level=12),
        "skills": [
            dict(skill_name="JavaScript", canonical_name="javascript", category="前端", level="advanced", market_demand=85, market_df=260, emergence=0.01, decline=0.05, freshness=80, years_of_experience=2.0, confidence=0.90, status="healthy"),
            dict(skill_name="Vue", canonical_name="vue", category="前端", level="intermediate", market_demand=72, market_df=160, emergence=0.02, decline=0.08, freshness=75, years_of_experience=2.0, confidence=0.86, status="healthy"),
            dict(skill_name="Node.js", canonical_name="nodejs", category="后端", level="intermediate", market_demand=75, market_df=140, emergence=0.05, decline=0.06, freshness=70, years_of_experience=1.5, confidence=0.82, status="healthy"),
            dict(skill_name="MongoDB", canonical_name="mongodb", category="数据", level="intermediate", market_demand=65, market_df=100, emergence=0.02, decline=0.07, freshness=65, years_of_experience=1.0, confidence=0.78, status="healthy"),
        ],
        "matches": [
            dict(position_id="pos-fullstack-jr", position_name="全栈开发工程师", company="某创业公司", match_rate=79.0,
                 matched_skills={"JavaScript": 3, "Vue": 2, "Node.js": 2},
                 missing_skills={"React": 0, "微服务": 0}, salary_range="15-25K"),
            dict(position_id="pos-fe-jr", position_name="前端开发工程师", company="某中厂", match_rate=75.0,
                 matched_skills={"JavaScript": 3, "Vue": 3},
                 missing_skills={"TypeScript": 0}, salary_range="13-22K"),
        ],
    },
    {
        "user_id": "cand_wu_jun",
        "profile": dict(name="吴军", title="数据工程师", target_role="大数据平台架构师",
                        target_city="南京", city="南京", industry="互联网/IT", experience_years="5-8年",
                        education="本科", major="计算机科学", english_level="CET-6",
                        salary_min=25, salary_max=40, status="employed_looking", birth_year=1993,
                        work_mode="hybrid", relocate_ok=True, travel_ok=True, avatar_emoji="🧑‍💻", level=35),
        "skills": [
            dict(skill_name="SQL", canonical_name="sql", category="数据", level="expert", market_demand=75, market_df=320, emergence=0.02, decline=0.01, freshness=85, years_of_experience=7.0, confidence=0.95, status="healthy"),
            dict(skill_name="Python", canonical_name="python", category="编程语言", level="advanced", market_demand=92, market_df=245, emergence=0.05, decline=0.02, freshness=80, years_of_experience=5.0, confidence=0.90, status="healthy"),
            dict(skill_name="Spark", canonical_name="spark", category="数据", level="expert", market_demand=85, market_df=170, emergence=0.08, decline=0.04, freshness=88, years_of_experience=5.0, confidence=0.94, status="healthy"),
            dict(skill_name="Flink", canonical_name="flink", category="数据", level="advanced", market_demand=82, market_df=120, emergence=0.20, decline=0.02, freshness=82, years_of_experience=3.0, confidence=0.88, status="healthy"),
            dict(skill_name="Kafka", canonical_name="kafka", category="中间件", level="advanced", market_demand=70, market_df=120, emergence=0.15, decline=0.02, freshness=78, years_of_experience=4.0, confidence=0.86, status="healthy"),
            dict(skill_name="Hive", canonical_name="hive", category="数据", level="expert", market_demand=65, market_df=110, emergence=0.01, decline=0.10, freshness=84, years_of_experience=6.0, confidence=0.92, status="healthy"),
        ],
        "matches": [
            dict(position_id="pos-data-eng", position_name="数据工程师", company="某大型电商", match_rate=87.0,
                 matched_skills={"SQL": 3, "Python": 3, "Spark": 3},
                 missing_skills={"实时数仓": 0}, salary_range="28-45K"),
            dict(position_id="pos-bigdata", position_name="大数据平台", company="某金融科技", match_rate=82.0,
                 matched_skills={"Spark": 3, "Flink": 2, "Kafka": 3},
                 missing_skills={"Hadoop 调优": 0}, salary_range="30-50K"),
        ],
    },
]


# ── 企业侧「当前登录企业」demo 档案（云启科技 —— 虚构，不与「职域智联」/「某…」候选公司撞名）──
_ENTERPRISE = {
    "enterprise_id": "demo_ent",
    "name": "云启智能科技有限公司",
    "short_name": "云启智能",
    "logo_emoji": "🚀",
    "uscc": "91110108MA01KJ7X2P",
    "nature": "民营",
    "industry": "人工智能 · 企业服务",
    "founded_year": 2015,
    "headcount": "500-999人",
    "financing": "C 轮",
    "city": "北京",
    "address": "北京市海淀区中关村软件园 9 号楼",
    "website": "https://www.yunqi.tech",
    "description": (
        "云启智能是一家专注企业级 AI 平台与智能招聘系统的科技公司。"
        "以 LLM/RAG 技术为底座，为大型企业提供岗位能力图谱、人岗匹配与人才洞察服务。"
        "在招岗位覆盖后端 / AI 算法 / 前端架构 / 数据分析 / 平台工程 / 质量架构 / 全栈 / 大数据等方向。"
    ),
    "tags": ["弹性工作", "六险一金", "扁平管理", "股票期权", "免费三餐", "年度体检"],
    "tech_stack": ["Go", "Python", "Kubernetes", "RAG / LLM", "大数据"],
    "hiring_channels": ["BOSS 直聘", "猎聘", "校招官网", "内推渠道"],
    "hr_name": "沈静",
    "hr_title": "招聘总监",
    "hr_phone": "010-89012345",
    "hr_email": "hr@yunqi.tech",
}


async def _count(session, model, user_id: str) -> int:
    stmt = select(func.count()).select_from(model).where(model.user_id == user_id)
    return (await session.execute(stmt)).scalar() or 0


async def seed_user(session, user_id: str, profile: dict, skills: list[dict],
                    matches: list[dict], steps: list[dict] | None = None) -> dict:
    """通用幂等种子：仅当该 user 某类数据为空时插入。返回各表插入条数。"""
    inserted = {"profile": 0, "skills": 0, "matches": 0, "steps": 0}

    if await _count(session, UserProfile, user_id) == 0:
        session.add(UserProfile(user_id=user_id, **profile))
        inserted["profile"] = 1

    if await _count(session, UserSkill, user_id) == 0:
        for s in skills:
            session.add(UserSkill(user_id=user_id, **s))
        inserted["skills"] = len(skills)

    if await _count(session, UserMatch, user_id) == 0:
        for m in matches:
            session.add(UserMatch(user_id=user_id, **m))
        inserted["matches"] = len(matches)

    if steps and await _count(session, LearningStepModel, user_id) == 0:
        for st in steps:
            session.add(LearningStepModel(user_id=user_id, **st))
        inserted["steps"] = len(steps)

    if inserted["profile"] or inserted["skills"] or inserted["matches"] or inserted["steps"]:
        await session.commit()
    return inserted


async def seed_demo_user(session) -> dict:
    """个人侧 demo 用户（张明）——委托通用 seed_user。"""
    return await seed_user(session, DEFAULT_USER, _PROFILE, _SKILLS, _MATCHES, _STEPS)


async def seed_talent_pool(session) -> list[dict]:
    """企业侧人才库种子：8 名独立候选人（user_id 均 ≠ demo_user）。"""
    results = []
    for c in CANDIDATES:
        r = await seed_user(session, c["user_id"], c["profile"], c["skills"], c["matches"])
        results.append({
            "user_id": c["user_id"],
            "name": c["profile"]["name"],
            "target_role": c["profile"]["target_role"],
            "skills": r["skills"],
            "matches": r["matches"],
        })
    return results


async def seed_enterprise_profile(session) -> dict:
    """企业侧「当前登录企业」档案种子（单行，enterprise_id 幂等）。"""
    stmt = (
        select(func.count())
        .select_from(EnterpriseProfile)
        .where(EnterpriseProfile.enterprise_id == _ENTERPRISE["enterprise_id"])
    )
    n = (await session.execute(stmt)).scalar() or 0
    if n == 0:
        session.add(EnterpriseProfile(**_ENTERPRISE))
        await session.commit()
        return {"name": _ENTERPRISE["name"], "inserted": 1}
    return {"name": _ENTERPRISE["name"], "inserted": 0}


async def main() -> None:
    settings = get_settings()
    await init_db(settings)
    try:
        async for session in get_session():
            demo = await seed_demo_user(session)
            print(
                f"demo 用户：档案 {demo['profile']} 条，技能 {demo['skills']} 条，"
                f"匹配 {demo['matches']} 条，学习路径 {demo['steps']} 条（0 = 已有数据，跳过）"
            )
            pool = await seed_talent_pool(session)
            print(f"人才库候选人：{len(pool)} 人")
            for row in pool:
                print(
                    f"  · {row['user_id']} {row['name']}（目标 {row['target_role']}）"
                    f"—— 技能 {row['skills']} 条，匹配 {row['matches']} 条"
                )
            ent = await seed_enterprise_profile(session)
            print(f"企业资料：{ent['name']}（{'新插入' if ent['inserted'] else '已有，跳过'}）")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
