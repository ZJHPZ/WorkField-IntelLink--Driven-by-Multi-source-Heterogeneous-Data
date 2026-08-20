"""
Multi-Agent System - 监控指标模块
用于追踪多智能体系统的运行状态和性能指标
"""
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """单个Agent的指标"""
    agent_id: str
    call_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    last_call_time: Optional[datetime] = None
    last_error: Optional[str] = None
    
    @property
    def avg_latency_ms(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.total_latency_ms / self.call_count
    
    @property
    def success_rate(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.success_count / self.call_count
    
    @property
    def error_rate(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.error_count / self.call_count


@dataclass
class SystemMetrics:
    """系统级指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    intent_distribution: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_distribution: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    @property
    def uptime_seconds(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()


class MultiAgentMonitor:
    """
    多智能体系统监控器
    
    提供以下监控能力：
    1. 请求级指标：追踪总请求数、成功/失败数
    2. Agent级指标：追踪每个Agent的调用次数、延迟、错误率
    3. 意图分布：追踪各类意图的调用频率
    4. 错误追踪：记录各类错误的发生次数
    
    使用示例：
        monitor = MultiAgentMonitor()
        
        # 记录请求开始
        request_id = monitor.record_request_start()
        
        # 记录Agent调用
        monitor.record_agent_call("conversation", latency_ms=50.0, success=True)
        
        # 记录意图
        monitor.record_intent("question")
        
        # 获取指标
        metrics = monitor.get_metrics()
    """
    
    # 单例模式
    _instance: Optional['MultiAgentMonitor'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._system_metrics = SystemMetrics()
        self._request_timings: Dict[str, float] = {}  # request_id -> start_time
        self._lock = threading.Lock()
        self._initialized = True
        
        logger.info("[Monitor] MultiAgentMonitor initialized")
    
    def start_monitoring(self):
        """启动监控（预留方法，用于未来启动定期报告等）"""
        logger.info("[Monitor] MultiAgent monitoring started")
        return self
    
    @classmethod
    def get_instance(cls) -> 'MultiAgentMonitor':
        """获取监控器单例"""
        return cls()
    
    def record_request_start(self, request_id: Optional[str] = None) -> str:
        """记录请求开始"""
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"
        
        with self._lock:
            self._request_timings[request_id] = time.time()
            self._system_metrics.total_requests += 1
        
        return request_id
    
    def start_request(self, user_id: str, intent: str) -> str:
        """开始请求追踪（start_request的别名）"""
        request_id = f"{user_id}_{intent}_{int(time.time() * 1000)}"
        return self.record_request_start(request_id)
    
    def end_request(self, request_id: str, success: bool = True) -> bool:
        """结束请求追踪（end_request的别名）"""
        self.record_request_end(request_id, success=success)
        return success
    
    def record_request_end(self, request_id: str, success: bool = True, error: Optional[str] = None) -> bool:
        """记录请求结束"""
        with self._lock:
            if request_id in self._request_timings:
                latency = (time.time() - self._request_timings[request_id]) * 1000
                del self._request_timings[request_id]
                
                if success:
                    self._system_metrics.successful_requests += 1
                else:
                    self._system_metrics.failed_requests += 1
                    if error:
                        self._system_metrics.error_distribution[error] += 1
                
                logger.debug(f"[Monitor] Request {request_id} completed in {latency:.2f}ms, success={success}")
        
        return success
    
    def start_request(self, user_id: str, intent: str) -> str:
        """
        开始请求追踪（start_request 别名）
        
        Args:
            user_id: 用户ID
            intent: 意图类型
        
        Returns:
            请求ID
        """
        return self.record_request_start()
    
    def end_request(self, request_id: str, success: bool = True, error: Optional[str] = None) -> bool:
        """
        结束请求追踪（end_request 别名）
        
        Args:
            request_id: 请求ID
            success: 是否成功
            error: 错误类型
        
        Returns:
            是否成功
        """
        return self.record_request_end(request_id, success, error)
    
    def record_agent_call(self, agent_id: str, latency_ms: float, success: bool = True, error: Optional[str] = None):
        """记录Agent调用"""
        with self._lock:
            if agent_id not in self._agent_metrics:
                self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
            
            metrics = self._agent_metrics[agent_id]
            metrics.call_count += 1
            metrics.total_latency_ms += latency_ms
            metrics.min_latency_ms = min(metrics.min_latency_ms, latency_ms)
            metrics.max_latency_ms = max(metrics.max_latency_ms, latency_ms)
            metrics.last_call_time = datetime.now()
            
            if success:
                metrics.success_count += 1
            else:
                metrics.error_count += 1
                if error:
                    metrics.last_error = error
        
        logger.debug(f"[Monitor] Agent {agent_id} call recorded: latency={latency_ms:.2f}ms, success={success}")
    
    def record_intent(self, intent: str):
        """记录意图类型"""
        with self._lock:
            self._system_metrics.intent_distribution[intent] += 1
    
    def record_error(self, error_type: str, error_message: str):
        """记录错误"""
        with self._lock:
            self._system_metrics.error_distribution[error_type] += 1
            logger.warning(f"[Monitor] Error recorded: type={error_type}, message={error_message}")
    
    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取指定Agent的指标"""
        with self._lock:
            if agent_id not in self._agent_metrics:
                return None
            
            metrics = self._agent_metrics[agent_id]
            return {
                "agent_id": metrics.agent_id,
                "call_count": metrics.call_count,
                "success_count": metrics.success_count,
                "error_count": metrics.error_count,
                "success_rate": metrics.success_rate,
                "error_rate": metrics.error_rate,
                "avg_latency_ms": metrics.avg_latency_ms,
                "min_latency_ms": metrics.min_latency_ms if metrics.min_latency_ms != float('inf') else 0,
                "max_latency_ms": metrics.max_latency_ms,
                "last_call_time": metrics.last_call_time.isoformat() if metrics.last_call_time else None,
                "last_error": metrics.last_error,
            }
    
    def get_all_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Agent的指标"""
        with self._lock:
            return {
                agent_id: self.get_agent_metrics(agent_id)
                for agent_id in self._agent_metrics
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取系统级指标"""
        with self._lock:
            return {
                "system": {
                    "total_requests": self._system_metrics.total_requests,
                    "successful_requests": self._system_metrics.successful_requests,
                    "failed_requests": self._system_metrics.failed_requests,
                    "success_rate": self._system_metrics.success_rate,
                    "error_rate": self._system_metrics.error_rate,
                    "uptime_seconds": self._system_metrics.uptime_seconds,
                    "uptime_hours": self._system_metrics.uptime_seconds / 3600,
                },
                "intent_distribution": dict(self._system_metrics.intent_distribution),
                "error_distribution": dict(self._system_metrics.error_distribution),
                "agents": self.get_all_agent_metrics(),
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态
        
        告警条件：
        - 系统错误率 > 5%
        - 任意Agent错误率 > 10%
        - 任意Agent平均延迟 > 5000ms
        """
        health = {
            "healthy": True,
            "warnings": [],
            "alerts": [],
        }
        
        # 检查系统错误率
        if self._system_metrics.error_rate > 0.05:
            health["healthy"] = False
            health["alerts"].append(f"System error rate too high: {self._system_metrics.error_rate * 100:.2f}%")
        
        # 检查Agent指标
        for agent_id, metrics in self._agent_metrics.items():
            if metrics.call_count > 0:
                if metrics.error_rate > 0.10:
                    health["healthy"] = False
                    health["alerts"].append(f"Agent {agent_id} error rate too high: {metrics.error_rate * 100:.2f}%")
                elif metrics.error_rate > 0.05:
                    health["warnings"].append(f"Agent {agent_id} error rate elevated: {metrics.error_rate * 100:.2f}%")
                
                if metrics.avg_latency_ms > 5000:
                    health["healthy"] = False
                    health["alerts"].append(f"Agent {agent_id} latency too high: {metrics.avg_latency_ms:.2f}ms")
                elif metrics.avg_latency_ms > 3000:
                    health["warnings"].append(f"Agent {agent_id} latency elevated: {metrics.avg_latency_ms:.2f}ms")
        
        return health
    
    def reset_metrics(self):
        """重置所有指标"""
        with self._lock:
            self._agent_metrics.clear()
            self._system_metrics = SystemMetrics()
            self._request_timings.clear()
        
        logger.info("[Monitor] All metrics reset")
    
    def should_fallback(self) -> bool:
        """
        判断是否应该回退到单智能体架构
        
        回退条件：
        - 系统错误率 > 10%
        - 或失败请求数 > 50（短时间内大量失败）
        """
        with self._lock:
            # 如果错误率超过10%，建议回退
            if self._system_metrics.error_rate > 0.10:
                logger.warning(f"[Monitor] High error rate detected: {self._system_metrics.error_rate * 100:.2f}%, suggesting fallback")
                return True
            
            # 如果失败请求超过50个，建议回退
            if self._system_metrics.failed_requests > 50:
                logger.warning(f"[Monitor] Too many failed requests: {self._system_metrics.failed_requests}, suggesting fallback")
                return True
            
            return False


# 全局监控器实例
_monitor: Optional[MultiAgentMonitor] = None


def get_multi_agent_monitor() -> MultiAgentMonitor:
    """获取多智能体监控器"""
    global _monitor
    if _monitor is None:
        _monitor = MultiAgentMonitor.get_instance()
    return _monitor


# 装饰器：自动监控Agent调用
def monitored_agent_call(agent_id: str):
    """装饰器：自动记录Agent调用的延迟和结果"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_multi_agent_monitor()
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                monitor.record_agent_call(agent_id, latency_ms, success, error)
        
        return wrapper
    return decorator
