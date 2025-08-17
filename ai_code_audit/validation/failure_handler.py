"""
Failure handling and graceful degradation system for AI Code Audit System.

This module provides comprehensive failure handling including:
- Graceful degradation strategies
- Recovery actions and fallback mechanisms
- Error classification and handling
- System stability maintenance
"""

import traceback
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures that can occur."""
    LLM_API_ERROR = "llm_api_error"
    NETWORK_ERROR = "network_error"
    PARSING_ERROR = "parsing_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class FailureSeverity(Enum):
    """Severity levels for failures."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FailureStrategy(Enum):
    """Strategies for handling failures."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    DEGRADE = "degrade"


class RecoveryAction(Enum):
    """Recovery actions to take."""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    SWITCH_MODEL = "switch_model"
    REDUCE_COMPLEXITY = "reduce_complexity"
    USE_CACHE = "use_cache"
    PARTIAL_ANALYSIS = "partial_analysis"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class FailureContext:
    """Context information for a failure."""
    failure_type: FailureType
    severity: FailureSeverity
    error_message: str
    stack_trace: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryPlan:
    """Plan for recovering from a failure."""
    strategy: FailureStrategy
    actions: List[RecoveryAction] = field(default_factory=list)
    fallback_options: List[str] = field(default_factory=list)
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureRecord:
    """Record of a failure and its handling."""
    failure_id: str
    context: FailureContext
    recovery_plan: RecoveryPlan
    attempts: List[Dict[str, Any]] = field(default_factory=list)
    final_outcome: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class FailureHandler:
    """Comprehensive failure handling and recovery system."""
    
    def __init__(self):
        """Initialize failure handler."""
        self.failure_records: Dict[str, FailureRecord] = {}
        self.failure_patterns: Dict[str, int] = {}  # Pattern -> count
        self.recovery_strategies: Dict[FailureType, RecoveryPlan] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        
        # Initialize default strategies
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Initialize default recovery strategies."""
        
        # LLM API errors
        self.recovery_strategies[FailureType.LLM_API_ERROR] = RecoveryPlan(
            strategy=FailureStrategy.RETRY,
            actions=[RecoveryAction.RETRY_WITH_BACKOFF, RecoveryAction.SWITCH_MODEL],
            max_retries=3,
            retry_delay=2.0,
            timeout=30.0
        )
        
        # Network errors
        self.recovery_strategies[FailureType.NETWORK_ERROR] = RecoveryPlan(
            strategy=FailureStrategy.RETRY,
            actions=[RecoveryAction.RETRY_WITH_BACKOFF, RecoveryAction.USE_CACHE],
            max_retries=5,
            retry_delay=1.0,
            timeout=60.0
        )
        
        # Parsing errors
        self.recovery_strategies[FailureType.PARSING_ERROR] = RecoveryPlan(
            strategy=FailureStrategy.DEGRADE,
            actions=[RecoveryAction.REDUCE_COMPLEXITY, RecoveryAction.PARTIAL_ANALYSIS],
            max_retries=2,
            retry_delay=0.5
        )
        
        # Validation errors
        self.recovery_strategies[FailureType.VALIDATION_ERROR] = RecoveryPlan(
            strategy=FailureStrategy.FALLBACK,
            actions=[RecoveryAction.PARTIAL_ANALYSIS, RecoveryAction.MANUAL_INTERVENTION],
            max_retries=1,
            retry_delay=0.0
        )
        
        # Timeout errors
        self.recovery_strategies[FailureType.TIMEOUT_ERROR] = RecoveryPlan(
            strategy=FailureStrategy.RETRY,
            actions=[RecoveryAction.REDUCE_COMPLEXITY, RecoveryAction.RETRY_WITH_BACKOFF],
            max_retries=2,
            retry_delay=5.0,
            timeout=120.0
        )
        
        # Resource errors
        self.recovery_strategies[FailureType.RESOURCE_ERROR] = RecoveryPlan(
            strategy=FailureStrategy.DEGRADE,
            actions=[RecoveryAction.REDUCE_COMPLEXITY, RecoveryAction.USE_CACHE],
            max_retries=1,
            retry_delay=10.0
        )
        
        # Configuration errors
        self.recovery_strategies[FailureType.CONFIGURATION_ERROR] = RecoveryPlan(
            strategy=FailureStrategy.ABORT,
            actions=[RecoveryAction.MANUAL_INTERVENTION],
            max_retries=0
        )
        
        # Unknown errors
        self.recovery_strategies[FailureType.UNKNOWN_ERROR] = RecoveryPlan(
            strategy=FailureStrategy.RETRY,
            actions=[RecoveryAction.RETRY_WITH_BACKOFF],
            max_retries=1,
            retry_delay=1.0
        )
    
    def handle_failure(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """Handle a failure and attempt recovery.
        
        Args:
            error: The exception that occurred
            context: Context information about the failure
            
        Returns:
            Recovery result if successful, None if failed
        """
        # Classify the failure
        failure_context = self._classify_failure(error, context)
        
        # Generate failure ID
        failure_id = f"{failure_context.component}_{failure_context.operation}_{int(datetime.now().timestamp())}"
        
        # Get recovery plan
        recovery_plan = self._get_recovery_plan(failure_context)
        
        # Create failure record
        failure_record = FailureRecord(
            failure_id=failure_id,
            context=failure_context,
            recovery_plan=recovery_plan
        )
        
        self.failure_records[failure_id] = failure_record
        
        # Log failure
        logger.warning(f"Handling failure {failure_id}: {failure_context.error_message}")
        
        # Execute recovery plan
        result = self._execute_recovery_plan(failure_record, context)
        
        # Update failure record
        if result is not None:
            failure_record.resolved = True
            failure_record.resolution_time = datetime.now()
            failure_record.final_outcome = "recovered"
            logger.info(f"Failure {failure_id} recovered successfully")
        else:
            failure_record.final_outcome = "failed"
            logger.error(f"Failure {failure_id} could not be recovered")
        
        # Update failure patterns
        self._update_failure_patterns(failure_context)
        
        return result
    
    def _classify_failure(self, error: Exception, context: Dict[str, Any]) -> FailureContext:
        """Classify the type and severity of a failure."""
        error_message = str(error)
        error_type = type(error).__name__
        
        # Determine failure type
        failure_type = FailureType.UNKNOWN_ERROR
        severity = FailureSeverity.MEDIUM
        
        if "timeout" in error_message.lower() or "TimeoutError" in error_type:
            failure_type = FailureType.TIMEOUT_ERROR
            severity = FailureSeverity.HIGH
        elif "network" in error_message.lower() or "ConnectionError" in error_type:
            failure_type = FailureType.NETWORK_ERROR
            severity = FailureSeverity.HIGH
        elif "api" in error_message.lower() or "HTTPError" in error_type:
            failure_type = FailureType.LLM_API_ERROR
            severity = FailureSeverity.HIGH
        elif "parse" in error_message.lower() or "SyntaxError" in error_type:
            failure_type = FailureType.PARSING_ERROR
            severity = FailureSeverity.MEDIUM
        elif "validation" in error_message.lower() or "ValidationError" in error_type:
            failure_type = FailureType.VALIDATION_ERROR
            severity = FailureSeverity.LOW
        elif "memory" in error_message.lower() or "MemoryError" in error_type:
            failure_type = FailureType.RESOURCE_ERROR
            severity = FailureSeverity.CRITICAL
        elif "config" in error_message.lower() or "ConfigurationError" in error_type:
            failure_type = FailureType.CONFIGURATION_ERROR
            severity = FailureSeverity.CRITICAL
        
        return FailureContext(
            failure_type=failure_type,
            severity=severity,
            error_message=error_message,
            stack_trace=traceback.format_exc(),
            component=context.get('component', 'unknown'),
            operation=context.get('operation', 'unknown'),
            metadata=context
        )
    
    def _get_recovery_plan(self, failure_context: FailureContext) -> RecoveryPlan:
        """Get recovery plan for a failure type."""
        base_plan = self.recovery_strategies.get(
            failure_context.failure_type,
            self.recovery_strategies[FailureType.UNKNOWN_ERROR]
        )
        
        # Adjust plan based on severity
        if failure_context.severity == FailureSeverity.CRITICAL:
            # More aggressive recovery for critical failures
            base_plan.max_retries = min(base_plan.max_retries + 2, 5)
            base_plan.retry_delay *= 2
        elif failure_context.severity == FailureSeverity.LOW:
            # Less aggressive recovery for low severity
            base_plan.max_retries = max(base_plan.max_retries - 1, 1)
            base_plan.retry_delay *= 0.5
        
        return base_plan
    
    def _execute_recovery_plan(self, failure_record: FailureRecord, context: Dict[str, Any]) -> Optional[Any]:
        """Execute the recovery plan for a failure."""
        plan = failure_record.recovery_plan
        
        for attempt in range(plan.max_retries + 1):
            attempt_info = {
                'attempt': attempt + 1,
                'timestamp': datetime.now(),
                'actions_taken': [],
                'result': None
            }
            
            try:
                # Execute recovery actions
                for action in plan.actions:
                    action_result = self._execute_recovery_action(action, context, attempt)
                    attempt_info['actions_taken'].append({
                        'action': action.value,
                        'result': action_result
                    })
                    
                    if action_result and action_result.get('success'):
                        attempt_info['result'] = 'success'
                        failure_record.attempts.append(attempt_info)
                        return action_result.get('data')
                
                # If no action succeeded, try the original operation again
                if 'retry_function' in context:
                    result = context['retry_function']()
                    attempt_info['result'] = 'success'
                    failure_record.attempts.append(attempt_info)
                    return result
                
            except Exception as e:
                attempt_info['result'] = f'failed: {str(e)}'
                logger.warning(f"Recovery attempt {attempt + 1} failed: {str(e)}")
            
            failure_record.attempts.append(attempt_info)
            
            # Wait before next attempt
            if attempt < plan.max_retries:
                import time
                time.sleep(plan.retry_delay * (2 ** attempt))  # Exponential backoff
        
        return None
    
    def _execute_recovery_action(self, action: RecoveryAction, context: Dict[str, Any], attempt: int) -> Optional[Dict[str, Any]]:
        """Execute a specific recovery action."""
        try:
            if action == RecoveryAction.RETRY_WITH_BACKOFF:
                # Already handled by the retry loop
                return {'success': False, 'message': 'Handled by retry loop'}
            
            elif action == RecoveryAction.SWITCH_MODEL:
                if 'model_switcher' in context:
                    new_model = context['model_switcher']()
                    return {'success': True, 'data': new_model, 'message': 'Switched to fallback model'}
            
            elif action == RecoveryAction.REDUCE_COMPLEXITY:
                if 'complexity_reducer' in context:
                    reduced_input = context['complexity_reducer'](context.get('input_data'))
                    return {'success': True, 'data': reduced_input, 'message': 'Reduced input complexity'}
            
            elif action == RecoveryAction.USE_CACHE:
                if 'cache_lookup' in context:
                    cached_result = context['cache_lookup'](context.get('cache_key'))
                    if cached_result:
                        return {'success': True, 'data': cached_result, 'message': 'Used cached result'}
            
            elif action == RecoveryAction.PARTIAL_ANALYSIS:
                if 'partial_analyzer' in context:
                    partial_result = context['partial_analyzer'](context.get('input_data'))
                    return {'success': True, 'data': partial_result, 'message': 'Performed partial analysis'}
            
            elif action == RecoveryAction.MANUAL_INTERVENTION:
                # Log for manual intervention
                logger.critical(f"Manual intervention required for: {context.get('operation', 'unknown operation')}")
                return {'success': False, 'message': 'Manual intervention required'}
            
        except Exception as e:
            logger.error(f"Recovery action {action.value} failed: {str(e)}")
        
        return {'success': False, 'message': f'Action {action.value} not available or failed'}
    
    def _update_failure_patterns(self, failure_context: FailureContext):
        """Update failure pattern tracking."""
        pattern = f"{failure_context.failure_type.value}:{failure_context.component}:{failure_context.operation}"
        self.failure_patterns[pattern] = self.failure_patterns.get(pattern, 0) + 1
        
        # Alert if pattern is becoming frequent
        if self.failure_patterns[pattern] > 5:
            logger.warning(f"Frequent failure pattern detected: {pattern} ({self.failure_patterns[pattern]} occurrences)")
    
    def register_fallback_handler(self, operation: str, handler: Callable):
        """Register a fallback handler for an operation."""
        self.fallback_handlers[operation] = handler
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """Get failure handling statistics."""
        total_failures = len(self.failure_records)
        resolved_failures = len([r for r in self.failure_records.values() if r.resolved])
        
        # Group by failure type
        type_stats = {}
        for record in self.failure_records.values():
            failure_type = record.context.failure_type.value
            if failure_type not in type_stats:
                type_stats[failure_type] = {'total': 0, 'resolved': 0}
            
            type_stats[failure_type]['total'] += 1
            if record.resolved:
                type_stats[failure_type]['resolved'] += 1
        
        # Group by severity
        severity_stats = {}
        for record in self.failure_records.values():
            severity = record.context.severity.value
            if severity not in severity_stats:
                severity_stats[severity] = {'total': 0, 'resolved': 0}
            
            severity_stats[severity]['total'] += 1
            if record.resolved:
                severity_stats[severity]['resolved'] += 1
        
        return {
            'total_failures': total_failures,
            'resolved_failures': resolved_failures,
            'resolution_rate': (resolved_failures / total_failures * 100) if total_failures > 0 else 0,
            'by_type': type_stats,
            'by_severity': severity_stats,
            'frequent_patterns': dict(sorted(self.failure_patterns.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def clear_old_records(self, older_than_hours: int = 24):
        """Clear old failure records to free memory."""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        to_remove = []
        for failure_id, record in self.failure_records.items():
            if record.context.timestamp < cutoff_time:
                to_remove.append(failure_id)
        
        for failure_id in to_remove:
            del self.failure_records[failure_id]
        
        logger.info(f"Cleared {len(to_remove)} old failure records")
