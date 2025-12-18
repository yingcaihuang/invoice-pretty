"""
Celery configuration for task queue processing
"""
import logging
from celery import Celery
from celery.signals import task_failure, task_success, task_retry
from .config import settings

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "web_invoice_processor",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.services.tasks"]
)

# Configure Celery
celery_app.conf.update(
    # Serialization settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600 * 48,  # Results expire after 48 hours
    
    # Timezone settings
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker crashes
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    worker_disable_rate_limits=False,
    
    # Retry settings
    task_default_retry_delay=60,  # Wait 60 seconds before retry
    task_max_retries=3,  # Maximum 3 retries
    
    # Result backend settings
    result_backend_transport_options={
        'master_name': 'mymaster',
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPIDLE': 60,
            'TCP_KEEPINTVL': 10,
            'TCP_KEEPCNT': 3
        }
    },
    
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Beat scheduler settings for periodic tasks
    beat_schedule={
        'cleanup-expired-tasks': {
            'task': 'cleanup_expired_tasks',
            'schedule': 3600.0,  # Run every hour (3600 seconds)
            'args': (settings.redis_url, settings.storage_path),
            'options': {
                'expires': 1800,  # Task expires after 30 minutes if not executed
            }
        },
        'cleanup-old-files': {
            'task': 'cleanup_old_files',
            'schedule': 6 * 3600.0,  # Run every 6 hours
            'args': (settings.storage_path, 24),  # Clean files older than 24 hours
            'options': {
                'expires': 3600,  # Task expires after 1 hour if not executed
            }
        },
        'update-expired-task-status': {
            'task': 'update_expired_task_status',
            'schedule': 6 * 3600.0 + 300,  # Run 5 minutes after file cleanup
            'args': (settings.redis_url, settings.storage_path),
            'options': {
                'expires': 1800,  # Task expires after 30 minutes if not executed
            }
        },
        'storage-usage-monitoring': {
            'task': 'monitor_storage_usage',
            'schedule': 12 * 3600.0,  # Run every 12 hours
            'args': (settings.storage_path,),
            'options': {
                'expires': 1800,  # Task expires after 30 minutes if not executed
            }
        }
    },
    beat_schedule_filename='celerybeat-schedule',
)


# Signal handlers for logging and monitoring
@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """Handle task failures."""
    logger.error(f"Task {task_id} failed: {exception}")
    logger.debug(f"Task args: {args}, kwargs: {kwargs}")
    logger.debug(f"Traceback: {traceback}")


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Handle task success."""
    logger.info(f"Task {sender.request.id} completed successfully")


@task_retry.connect
def task_retry_handler(sender=None, reason=None, **kwargs):
    """Handle task retries."""
    logger.warning(f"Task {sender.request.id} retrying: {reason}")