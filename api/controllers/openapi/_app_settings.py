"""Reads and writes shared by the per-mode app-settings routes."""

from __future__ import annotations

from dataclasses import asdict

from flask import request
from pydantic import BaseModel

from configs import dify_config
from controllers.common.rbac.locators import agent_binding
from controllers.openapi._models import AgentServiceApi
from controllers.openapi.auth.context import Context
from extensions.ext_application_services import application_services
from libs.url_utils import normalize_api_base_url
from machinery.context import RequestContext
from services.entities.app_entities import UpdateAppParams


def request_context(ctx: Context) -> RequestContext:
    return ctx.request_context


def app_base_url() -> str:
    return dify_config.APP_WEB_URL or request.url_root.rstrip("/")


def app_info[T: BaseModel](ctx: Context, model: type[T]) -> T:
    data = asdict(application_services().apps.console.get(request_context(ctx), ctx.app.id))
    if "role" in model.model_fields:
        agent = agent_binding(ctx.workspace.id, ctx.app.id)
        data["role"] = agent.role if agent is not None else ""
    return model.model_validate(data)


def update_app_info[T: BaseModel](ctx: Context, patch: BaseModel, model: type[T]) -> T:
    console = application_services().apps.console
    current = console.get(request_context(ctx), ctx.app.id)
    changes = patch.model_dump(exclude_unset=True)
    console.update(
        request_context(ctx),
        ctx.app.id,
        UpdateAppParams(
            name=changes.get("name") or current.name,
            description=changes.get("description", current.description or ""),
            icon_type=changes.get("icon_type", current.icon_type),
            icon=changes.get("icon", current.icon or ""),
            icon_background=changes.get("icon_background", current.icon_background or ""),
            use_icon_as_answer_icon=changes.get("use_icon_as_answer_icon", current.use_icon_as_answer_icon),
            max_active_requests=changes.get("max_active_requests", current.max_active_requests or 0),
            role=changes.get("role"),
        ),
    )
    return app_info(ctx, model)


def service_api[T: BaseModel](ctx: Context, model: type[T]) -> T:
    base_url = normalize_api_base_url(dify_config.SERVICE_API_URL or request.host_url.rstrip("/"))
    data: dict[str, object] = {"enabled": ctx.app.enable_api, "base_url": base_url}
    if model is AgentServiceApi:
        data |= {"api_rpm": ctx.app.api_rpm or 0, "api_rph": ctx.app.api_rph or 0}
    return model.model_validate(data)


def update_service_api[T: BaseModel](ctx: Context, enabled: bool, model: type[T]) -> T:
    record = application_services().apps.console.set_api_enabled(request_context(ctx), ctx.app.id, enabled)
    return model.model_validate({**service_api(ctx, model).model_dump(), "enabled": record.enable_api})
