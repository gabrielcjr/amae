"""
WSGI config for amae project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "amae.settings")

# OpenTelemetry Tracing Initialization
otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
if otel_endpoint:
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = os.getenv("OTEL_SERVICE_NAME", "amae-web")
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        target_endpoint = (
            otel_endpoint
            if otel_endpoint.endswith("/v1/traces")
            else f"{otel_endpoint}/v1/traces"
        )
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=target_endpoint))
        )
        trace.set_tracer_provider(provider)

        DjangoInstrumentor().instrument()
        PsycopgInstrumentor().instrument()
        RedisInstrumentor().instrument()
        print(f"[OpenTelemetry] AMAE Tracing initialized -> {target_endpoint}")
    except Exception as e:
        print(f"[OpenTelemetry] Failed to initialize tracing for AMAE: {e}")

application = get_wsgi_application()
