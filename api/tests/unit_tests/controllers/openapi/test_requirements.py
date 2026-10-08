from collections.abc import Callable
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from werkzeug.exceptions import UnprocessableEntity

from controllers.openapi import _errors
from controllers.openapi.auth import requirements
from controllers.openapi.auth.context import Context
from controllers.openapi.auth.requirements import CheckAppMode, CheckWebAppAuthEnterprise
from controllers.openapi.auth.subjects import Subject
from enums import DeploymentEdition
from models import AppMode

_SUBJECT = cast(Subject, SimpleNamespace())
_SESSION = cast(Session, MagicMock())


def test_app_mode_refuses_another_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(requirements, "load_app", lambda _ctx: SimpleNamespace(mode=AppMode.CHAT))
    with pytest.raises(UnprocessableEntity, match="app_mode_mismatch"):
        CheckAppMode(AppMode.WORKFLOW).run(_SUBJECT, cast(Context, SimpleNamespace()), _SESSION)


@pytest.mark.parametrize(
    ("edition", "webapp_auth"),
    [
        (DeploymentEdition.COMMUNITY, True),
        (DeploymentEdition.CLOUD, True),
        (DeploymentEdition.ENTERPRISE, False),
    ],
)
def test_webapp_access_needs_ee_with_webapp_auth(
    monkeypatch: pytest.MonkeyPatch,
    config_overrides: Callable[..., None],
    edition: DeploymentEdition,
    webapp_auth: bool,
) -> None:
    config_overrides(DEPLOYMENT_EDITION=edition)
    features = SimpleNamespace(webapp_auth=SimpleNamespace(enabled=webapp_auth))
    monkeypatch.setattr(requirements.SystemFeatureService, "get_public_system_features", lambda: features)
    with pytest.raises(_errors.WebAppAccessRequiresEE):
        CheckWebAppAuthEnterprise().run(_SUBJECT, cast(Context, SimpleNamespace()), _SESSION)
