"""Reads and writes shared by the per-mode app-settings routes."""

from __future__ import annotations

from dataclasses import asdict
from enum import StrEnum

from flask import request
from pydantic import BaseModel
from werkzeug.exceptions import NotFound, ServiceUnavailable

from configs import dify_config
from controllers.common.rbac.locators import agent_binding
from controllers.openapi._errors import AccessSubjectsInvalid
from controllers.openapi._models import (
    AccessSubjectListResponse,
    AccessSubjectQuery,
    AccessSubjectRow,
    WebAppAccess,
    WebAppAccessPayload,
    WebAppToken,
)
from controllers.openapi.auth.context import Context
from enums import WebAppAccessMode
from extensions.ext_application_services import application_services
from libs.url_utils import normalize_api_base_url
from machinery.context import RequestContext
from services.app_site_service import AppSiteAppNotFoundError, AppSiteChanges, AppSiteNotFoundError
from services.entities.app_entities import AppRecord, UpdateAppParams
from services.webapp_access_query_service import WebAppAccessUnavailableError

WEBAPP_ACCESS_UNAVAILABLE = "webapp_access_unavailable"


class AccessSubjectType(StrEnum):
    ACCOUNT = "account"
    GROUP = "group"


def request_context(ctx: Context) -> RequestContext:
    return ctx.request_context


def app_base_url() -> str:
    return dify_config.APP_WEB_URL or request.url_root.rstrip("/")


def _info_from_record[T: BaseModel](ctx: Context, record: AppRecord, model: type[T], role: str | None) -> T:
    data = asdict(record)
    if "role" in model.model_fields:
        if role is None:
            agent = agent_binding(ctx.workspace.id, ctx.app.id)
            role = agent.role if agent is not None else ""
        data["role"] = role
    return model.model_validate(data)


def app_info[T: BaseModel](ctx: Context, model: type[T]) -> T:
    record = application_services().apps.console.get(request_context(ctx), ctx.app.id)
    return _info_from_record(ctx, record, model, None)


def update_app_info[T: BaseModel](ctx: Context, patch: BaseModel, model: type[T]) -> T:
    console = application_services().apps.console
    current = console.get(request_context(ctx), ctx.app.id)
    changes = patch.model_dump(exclude_unset=True, exclude_none=True)
    record = console.update(
        request_context(ctx),
        ctx.app.id,
        UpdateAppParams(
            name=changes.get("name", current.name),
            description=changes.get("description", current.description or ""),
            icon_type=changes.get("icon_type", current.icon_type),
            icon=changes.get("icon", current.icon or ""),
            icon_background=changes.get("icon_background", current.icon_background or ""),
            use_icon_as_answer_icon=changes.get("use_icon_as_answer_icon", current.use_icon_as_answer_icon),
            max_active_requests=changes.get("max_active_requests", current.max_active_requests or 0),
            role=changes.get("role"),
        ),
    )
    return _info_from_record(ctx, record, model, changes.get("role"))


def service_api[T: BaseModel](ctx: Context, model: type[T]) -> T:
    base_url = normalize_api_base_url(dify_config.SERVICE_API_URL or request.host_url.rstrip("/"))
    data: dict[str, object] = {"enabled": ctx.app.enable_api, "base_url": base_url}
    if "api_rpm" in model.model_fields:
        data |= {"api_rpm": ctx.app.api_rpm or 0, "api_rph": ctx.app.api_rph or 0}
    return model.model_validate(data)


def update_service_api[T: BaseModel](ctx: Context, enabled: bool, model: type[T]) -> T:
    record = application_services().apps.console.set_api_enabled(request_context(ctx), ctx.app.id, enabled)
    return model.model_validate({**service_api(ctx, model).model_dump(), "enabled": record.enable_api})


def webapp[T: BaseModel](ctx: Context, model: type[T]) -> T:
    app = application_services().apps.console.get(request_context(ctx), ctx.app.id)
    site = app.site or {}
    return model.model_validate(
        {**site, "enabled": app.enable_site, "access_token": site.get("code"), "app_base_url": app_base_url()}
    )


def update_webapp[T: BaseModel](ctx: Context, patch: BaseModel, model: type[T]) -> T:
    changes = patch.model_dump(exclude_unset=True, exclude_none=True)
    enabled = changes.pop("enabled", None)
    try:
        if changes:
            application_services().app_sites.update(request_context(ctx), ctx.app.id, AppSiteChanges(**changes))
    except (AppSiteNotFoundError, AppSiteAppNotFoundError) as error:
        raise NotFound(str(error)) from error
    if enabled is not None:
        application_services().apps.console.set_site_enabled(request_context(ctx), ctx.app.id, enabled)
    return webapp(ctx, model)


def reset_webapp(ctx: Context) -> WebAppToken:
    try:
        site = application_services().app_sites.reset_access_token(request_context(ctx), ctx.app.id)
    except (AppSiteNotFoundError, AppSiteAppNotFoundError) as error:
        raise NotFound(str(error)) from error
    return WebAppToken(access_token=site.code, app_base_url=app_base_url())


def webapp_access(ctx: Context) -> WebAppAccess:
    console = application_services().apps.console
    access_mode = console.get(request_context(ctx), ctx.app.id).access_mode
    if access_mode is None:
        raise ServiceUnavailable(WEBAPP_ACCESS_UNAVAILABLE)
    try:
        subjects = console.access_subjects(ctx.app.id)
    except WebAppAccessUnavailableError as error:
        raise ServiceUnavailable(WEBAPP_ACCESS_UNAVAILABLE) from error
    return WebAppAccess(access_mode=access_mode, groups=subjects["groups"], members=subjects["members"])


def update_webapp_access(ctx: Context, body: WebAppAccessPayload) -> WebAppAccess:
    private = body.access_mode == WebAppAccessMode.PRIVATE
    well_formed = all(subject.get("id") and subject.get("type") in AccessSubjectType for subject in body.subjects)
    if private != bool(body.subjects) or not well_formed:
        raise AccessSubjectsInvalid()
    try:
        application_services().apps.console.update_access(
            ctx.app.id,
            body.access_mode,
            [{"subjectId": subject["id"], "subjectType": subject["type"]} for subject in body.subjects],
        )
    except WebAppAccessUnavailableError as error:
        raise ServiceUnavailable(WEBAPP_ACCESS_UNAVAILABLE) from error
    return webapp_access(ctx)


def access_subjects(query: AccessSubjectQuery) -> AccessSubjectListResponse:
    try:
        result = application_services().apps.console.search_access_subjects(
            keyword=query.keyword, page=query.page, limit=query.limit, group_id=query.group_id
        )
    except WebAppAccessUnavailableError as error:
        raise ServiceUnavailable(WEBAPP_ACCESS_UNAVAILABLE) from error
    rows = []
    for subject in result["subjects"]:
        group = subject.get("groupData") or {}
        account = subject.get("accountData") or {}
        rows.append(
            AccessSubjectRow(
                id=subject["subjectId"],
                type=subject["subjectType"],
                name=group.get("name") or account.get("name") or "",
                email=account.get("email"),
                member_count=group.get("groupSize"),
            )
        )
    return AccessSubjectListResponse(
        page=query.page, limit=query.limit, has_more=bool(result.get("hasMore")), data=rows
    )
