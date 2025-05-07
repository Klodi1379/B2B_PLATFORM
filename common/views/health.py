from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import redis
import json
import os
import datetime

def health_check(request):
    """
    Health check endpoint for Docker/Kubernetes
    Returns status of database, redis, and application
    """
    # Check database connection
    db_status = "ok"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        db_status = str(e)
    
    # Check Redis connection
    redis_status = "ok"
    try:
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
    except Exception as e:
        redis_status = str(e)
    
    # Application info
    app_info = {
        "name": "B2B Platform",
        "version": "1.0.0",
        "environment": "production" if not settings.DEBUG else "development",
        "time": datetime.datetime.now().isoformat(),
    }
    
    # System info
    system_info = {
        "python_version": os.sys.version,
        "django_version": settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else "unknown",
    }
    
    # Construct response
    response = {
        "status": "ok" if db_status == "ok" and redis_status == "ok" else "error",
        "database": db_status,
        "redis": redis_status,
        "application": app_info,
        "system": system_info,
    }
    
    return JsonResponse(response)
