from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest

from controllers.openapi import _app_settings
from controllers.openapi._errors import AccessSubjectsInvalid
from controllers.openapi._models import (
    AgentAppInfo,
    AgentAppInfoPatch,
    AppInfoPatch,
    AppSettingsInfo,
    WebApp,
    WebAppAccessPayload,
    WebAppPatch,
)
from controllers.openapi.auth.context import Context
from services.entities.app_entities import AppRecord


def _record() -> AppRecord:
    return AppRecord(
        id="app-1",
        name="Old",
        mode_compatible_with_agent="workflow",
        description="keep me",
        icon_type="emoji",
        icon="🤖",
        icon_background="#fff",
        max_active_requests=3,
    )


@pytest.fixture
def console(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    console = MagicMock()
    console.get.return_value = _record()
    console.update.return_value = _record()
    monkeypatch.setattr(
        _app_settings, "application_services", lambda: SimpleNamespace(apps=SimpleNamespace(console=console))
    )
    monkeypatch.setattr(_app_settings, "request_context", lambda _ctx: "rc")
    monkeypatch.setattr(_app_settings, "agent_binding", lambda *_: SimpleNamespace(role="writer"))
    return console


_CTX = cast(Context, SimpleNamespace(app=SimpleNamespace(id="app-1"), workspace=SimpleNamespace(id="ws-1")))


@pytest.mark.parametrize(
    ("patch", "description", "name"),
    [
        (AppInfoPatch(name="New"), "keep me", "New"),
        (AppInfoPatch(description=""), "", "Old"),
        (AppInfoPatch(description=None), "keep me", "Old"),
    ],
)
def test_set_app_info_changes_only_passed_fields(
    console: MagicMock, patch: AppInfoPatch, description: str, name: str
) -> None:
    _app_settings.update_app_info(_CTX, patch, AppSettingsInfo)
    params = console.update.call_args.args[2]
    assert (params.name, params.description, params.icon, params.max_active_requests) == (name, description, "🤖", 3)


def test_set_app_info_without_role_keeps_the_agent_role(console: MagicMock) -> None:
    _app_settings.update_app_info(_CTX, AgentAppInfoPatch(name="New"), AgentAppInfo)
    assert console.update.call_args.args[2].role is None


@pytest.mark.parametrize(
    "body",
    [
        WebAppAccessPayload(access_mode="private", subjects=[]),
        WebAppAccessPayload(access_mode="public", subjects=[{"id": "u1", "type": "account"}]),
        WebAppAccessPayload(access_mode="private", subjects=[{"id": "u1", "type": "member"}]),
        WebAppAccessPayload(access_mode="private", subjects=[{"type": "group"}]),
    ],
)
def test_set_webapp_access_refuses_bad_subjects(monkeypatch: pytest.MonkeyPatch, body: WebAppAccessPayload) -> None:
    console = MagicMock()
    monkeypatch.setattr(
        _app_settings, "application_services", lambda: SimpleNamespace(apps=SimpleNamespace(console=console))
    )
    with pytest.raises(AccessSubjectsInvalid):
        _app_settings.update_webapp_access(_CTX, body)
    console.update_access.assert_not_called()


@pytest.mark.parametrize(
    ("patch", "site_called", "toggle_called"),
    [(WebAppPatch(enabled=True), False, True), (WebAppPatch(title="Hi"), True, False)],
)
def test_set_webapp_calls_only_what_changed(
    monkeypatch: pytest.MonkeyPatch, console: MagicMock, patch: WebAppPatch, site_called: bool, toggle_called: bool
) -> None:
    sites = MagicMock()
    monkeypatch.setattr(
        _app_settings,
        "application_services",
        lambda: SimpleNamespace(apps=SimpleNamespace(console=console), app_sites=sites),
    )
    monkeypatch.setattr(_app_settings, "webapp", lambda _ctx, _model: None)
    _app_settings.update_webapp(_CTX, patch, WebApp)
    assert sites.update.called is site_called
    assert console.set_site_enabled.called is toggle_called
