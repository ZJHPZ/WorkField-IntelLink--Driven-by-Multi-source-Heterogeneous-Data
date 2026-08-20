"""
Multi-Agent System
多智能体系统 - 各Agent实现
"""

from .conversation_agent import ConversationAgent
from .document_agent import DocumentAgent
from .question_agent import QuestionAgent
from .multimedia_generation_agent import MultimediaAgent
from .multimodal_understanding_agent import MultimodalUnderstandingAgent
from .qa_agent import QAAgent
from .learning_path_agent import LearningPathAgent
from .evaluation_agent import EvaluationAgent
from .recommendation_agent import RecommendationAgent
from .email_agent import EmailAgent
from .bigdata_learning_agent import BigDataLearningAgent
from .learning_engine_agent import LearningEngineAgent
from .resource_agent import ResourceAgent
from .diagnosis_agent import DiagnosisAgent

__all__ = [
    "ConversationAgent",
    "DocumentAgent",
    "QuestionAgent",
    "MultimediaAgent",
    "MultimodalUnderstandingAgent",
    "QAAgent",
    "LearningPathAgent",
    "EvaluationAgent",
    "RecommendationAgent",
    "EmailAgent",
    "BigDataLearningAgent",
    "LearningEngineAgent",
    "ResourceAgent",
    "DiagnosisAgent",
]
