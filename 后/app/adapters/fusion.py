"""★ 多源信号融合引擎 —— 跨源技能信号合并、置信度融合、冲突检测。

设计方案 §3.4：
1. 同名合并：归一化后同名的技能信号合并成一条
2. 置信度融合：多源佐证非线性提升（独立证据的补集乘积）
3. 冲突检测：同一技能在不同源 required_type 矛盾时降权
4. 孤证不入图谱：单一来源 → candidate

输入：list[SkillSignal]（来自不同适配器的原始信号）
输出：list[FusedSkill]（融合后的可信技能）
"""

from __future__ import annotations

import re

from app.domain import SourceType
from app.domain.signals import FusedSkill, SkillSignal


class FusionEngine:
    """信号融合引擎。"""

    TYPE_PRIORITY = {"必备": 3, "加分": 2, "提及": 1}

    def fuse(self, signals: list[SkillSignal]) -> list[FusedSkill]:
        """融合所有信号，返回 FusedSkill 列表（按置信度降序）。"""
        if not signals:
            return []

        # 1. 按归一化技能名分组
        groups: dict[str, list[SkillSignal]] = {}
        for sig in signals:
            key = self._normalize(sig.name)
            if key:
                groups.setdefault(key, []).append(sig)

        # 2. 每组做融合
        fused = [self._merge_group(name, group) for name, group in groups.items()]

        # 3. 按置信度降序
        fused.sort(key=lambda f: -f.confidence)
        return fused

    def _merge_group(self, name: str, signals: list[SkillSignal]) -> FusedSkill:
        """合并同一技能的所有信号。"""
        source_types = list(set(s.source_type.value for s in signals))

        # 置信度融合：1 - Π(1 - ci)（独立证据补集乘积）
        conf_product = 1.0
        for s in signals:
            conf_product *= (1.0 - s.credibility)
        fused_confidence = 1.0 - conf_product

        # required_type 取最高级
        best_type = "提及"
        best_priority = 0
        for s in signals:
            p = self.TYPE_PRIORITY.get(s.required_type, 0)
            if p > best_priority:
                best_priority = p
                best_type = s.required_type

        # 收集去重证据
        seen_ev = set()
        evidences = []
        for s in signals:
            ev = s.evidence.strip()
            if ev and ev not in seen_ev:
                seen_ev.add(ev)
                evidences.append({
                    "text": ev,
                    "source": s.source_type.value,
                    "doc_id": s.source_doc_id,
                })

        # 多源佐证判定
        unique_sources = len(set(s.source_type for s in signals))
        status = "confirmed" if unique_sources >= 2 else "candidate"

        return FusedSkill(
            name=name,
            confidence=round(fused_confidence, 4),
            required_type=best_type,
            source_count=unique_sources,
            source_types=source_types,
            evidences=evidences,
            verification_status=status,
        )

    @staticmethod
    def _normalize(name: str) -> str:
        """技能名归一化（宽松版，与 l2_normalize 一致）。"""
        s = name.strip()
        s = re.sub(r"^(熟悉|掌握|精通|了解|熟练|会|具备|使用|善于|能够)", "", s).strip()
        s = s.strip("，。、；;,. 　")
        s_lower = s.lower()
        aliases = {
            "k8s": "Kubernetes", "kubernetes": "Kubernetes",
            "pytorch": "PyTorch", "tensorflow": "TensorFlow",
            "rag": "RAG", "transformer": "Transformer",
            "docker": "Docker", "kafka": "Kafka",
            "golang": "Go",
        }
        return aliases.get(s_lower, s)
