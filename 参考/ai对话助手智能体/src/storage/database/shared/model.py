from coze_coding_dev_sdk.database import Base

from typing import Optional
import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Double, Index, Integer, Numeric, PrimaryKeyConstraint, String, Table, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, OID
from sqlalchemy.orm import Mapped, mapped_column

class Conversations(Base):
    __tablename__ = 'conversations'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='conversations_pkey'),
        Index('idx_conversations_created_at', 'created_at'),
        Index('idx_conversations_user_id', 'user_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class Evaluations(Base):
    __tablename__ = 'evaluations'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='evaluations_pkey'),
        Index('idx_evaluations_created_at', 'created_at'),
        Index('idx_evaluations_user_id', 'user_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    evaluation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    evaluation_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    score: Mapped[Optional[float]] = mapped_column(Double(53))
    feedback: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class HealthCheck(Base):
    __tablename__ = 'health_check'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='health_check_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))


class LearningContents(Base):
    __tablename__ = 'learning_contents'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='learning_contents_pkey'),
        Index('idx_learning_contents_subject', 'subject')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class LearningPaths(Base):
    __tablename__ = 'learning_paths'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='learning_paths_pkey'),
        Index('idx_learning_paths_user_id', 'user_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    path_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class MultiAgentContext(Base):
    __tablename__ = 'multi_agent_context'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='multi_agent_context_pkey'),
        UniqueConstraint('category', 'entity_id', name='multi_agent_context_category_entity_id_key'),
        Index('idx_context_category', 'category'),
        Index('idx_context_entity_id', 'entity_id'),
        Index('idx_context_updated_at', 'updated_at'),
        {'comment': '多智能体上下文持久化表'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, comment='上下文类别（user_profiles/learning_progress等）')
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False, comment='实体ID（用户ID等）')
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, comment='上下文数据')
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))


class MultiAgentMessages(Base):
    __tablename__ = 'multi_agent_messages'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='multi_agent_messages_pkey'),
        Index('idx_messages_correlation_id', 'correlation_id'),
        Index('idx_messages_created_at', 'created_at'),
        Index('idx_messages_sender', 'sender'),
        Index('idx_messages_session_id', 'session_id'),
        {'comment': '多智能体消息持久化表'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, comment='会话ID')
    sender: Mapped[str] = mapped_column(String(100), nullable=False, comment='发送者Agent')
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    receiver: Mapped[Optional[str]] = mapped_column(String(100), comment='接收者Agent')
    correlation_id: Mapped[Optional[str]] = mapped_column(String(255))
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    priority: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))


t_pg_stat_statements = Table(
    'pg_stat_statements', Base.metadata,
    Column('userid', OID),
    Column('dbid', OID),
    Column('toplevel', Boolean),
    Column('queryid', BigInteger),
    Column('query', Text),
    Column('plans', BigInteger),
    Column('total_plan_time', Double(53)),
    Column('min_plan_time', Double(53)),
    Column('max_plan_time', Double(53)),
    Column('mean_plan_time', Double(53)),
    Column('stddev_plan_time', Double(53)),
    Column('calls', BigInteger),
    Column('total_exec_time', Double(53)),
    Column('min_exec_time', Double(53)),
    Column('max_exec_time', Double(53)),
    Column('mean_exec_time', Double(53)),
    Column('stddev_exec_time', Double(53)),
    Column('rows', BigInteger),
    Column('shared_blks_hit', BigInteger),
    Column('shared_blks_read', BigInteger),
    Column('shared_blks_dirtied', BigInteger),
    Column('shared_blks_written', BigInteger),
    Column('local_blks_hit', BigInteger),
    Column('local_blks_read', BigInteger),
    Column('local_blks_dirtied', BigInteger),
    Column('local_blks_written', BigInteger),
    Column('temp_blks_read', BigInteger),
    Column('temp_blks_written', BigInteger),
    Column('shared_blk_read_time', Double(53)),
    Column('shared_blk_write_time', Double(53)),
    Column('local_blk_read_time', Double(53)),
    Column('local_blk_write_time', Double(53)),
    Column('temp_blk_read_time', Double(53)),
    Column('temp_blk_write_time', Double(53)),
    Column('wal_records', BigInteger),
    Column('wal_fpi', BigInteger),
    Column('wal_bytes', Numeric),
    Column('jit_functions', BigInteger),
    Column('jit_generation_time', Double(53)),
    Column('jit_inlining_count', BigInteger),
    Column('jit_inlining_time', Double(53)),
    Column('jit_optimization_count', BigInteger),
    Column('jit_optimization_time', Double(53)),
    Column('jit_emission_count', BigInteger),
    Column('jit_emission_time', Double(53)),
    Column('jit_deform_count', BigInteger),
    Column('jit_deform_time', Double(53)),
    Column('stats_since', DateTime(True)),
    Column('minmax_stats_since', DateTime(True))
)


t_pg_stat_statements_info = Table(
    'pg_stat_statements_info', Base.metadata,
    Column('dealloc', BigInteger),
    Column('stats_reset', DateTime(True))
)


class PushRecords(Base):
    __tablename__ = 'push_records'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='push_records_pkey'),
        Index('idx_push_records_created_at', 'created_at'),
        Index('idx_push_records_user_id', 'user_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    push_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class Questions(Base):
    __tablename__ = 'questions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='questions_pkey'),
        Index('idx_questions_difficulty', 'difficulty'),
        Index('idx_questions_subject', 'subject'),
        Index('idx_questions_topic', 'topic')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    question_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    answer_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class UserProfiles(Base):
    __tablename__ = 'user_profiles'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='user_profiles_pkey'),
        UniqueConstraint('user_id', name='user_profiles_user_id_key'),
        Index('idx_user_profiles_user_id', 'user_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    learning_style: Mapped[Optional[str]] = mapped_column(Text)
    knowledge_level: Mapped[Optional[str]] = mapped_column(Text)
    learning_goal: Mapped[Optional[str]] = mapped_column(Text)
    learning_speed: Mapped[Optional[str]] = mapped_column(Text)
    learning_preference: Mapped[Optional[dict]] = mapped_column(JSONB)
    learning_progress: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class VectorStore(Base):
    __tablename__ = 'vector_store'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='vector_store_pkey'),
        UniqueConstraint('content_id', name='vector_store_content_id_key'),
        Index('idx_vector_store_content_id', 'content_id'),
        Index('idx_vector_store_created_at', 'created_at'),
        {'comment': '向量存储表 - 存储学习内容的向量表示'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_id: Mapped[str] = mapped_column(String(255), nullable=False, comment='内容唯一标识符')
    text_: Mapped[str] = mapped_column('text', Text, nullable=False, comment='原始文本内容')
    embedding: Mapped[dict] = mapped_column(JSONB, nullable=False, comment='向量嵌入 (JSONB数组)')
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"), comment='元数据 (主题、标签等)')
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
