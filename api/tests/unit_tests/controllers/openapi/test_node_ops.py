from collections.abc import Callable
from types import SimpleNamespace
from typing import Protocol, cast
from unittest.mock import MagicMock

import pytest
from flask import Flask
from werkzeug.exceptions import BadRequest

from controllers.openapi import _errors, app_workflow, node_types
from controllers.openapi._models import NodeTypeDetailResponse
from controllers.openapi.auth.context import Context
from services.workflow_service import WorkflowService


class _EndpointView(Protocol):
    __handler__: Callable[..., object]


def test_describe_node_type_has_a_schema_without_default_config(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    """`WorkflowService()` needs a live db.engine; its default-config lookup itself uses no instance state."""
    stand_in = SimpleNamespace(
        get_default_block_config=lambda node_type: WorkflowService.get_default_block_config(None, node_type)  # pyrefly: ignore[bad-argument-type]
    )
    monkeypatch.setattr(node_types, "WorkflowService", lambda: stand_in)
    api = node_types.NodeTypeDetailApi()
    with app.test_request_context("/openapi/v1/node-types/if-else"):
        response = cast(
            NodeTypeDetailResponse,
            cast(_EndpointView, api.get).__handler__(api, cast(Context, SimpleNamespace()), "if-else"),
        )
    assert (response.type, response.version) == ("if-else", "1")
    assert response.schema_["properties"]
    assert response.default_config == {}


def test_describe_node_type_refuses_an_unknown_type(app: Flask) -> None:
    api = node_types.NodeTypeDetailApi()
    with app.test_request_context("/openapi/v1/node-types/nope"), pytest.raises(_errors.NodeTypeNotFound):
        cast(_EndpointView, api.get).__handler__(api, cast(Context, SimpleNamespace()), "nope")


def _draft(nodes: list[dict[str, object]]) -> SimpleNamespace:
    return SimpleNamespace(graph_dict={"nodes": nodes})


@pytest.mark.parametrize(
    ("draft", "node_id", "error"),
    [
        (None, "n1", _errors.DraftNotFound),
        (_draft([{"id": "n1", "data": {"type": "llm"}}]), "missing", _errors.NodeNotFound),
        (_draft([{"id": "loop1", "data": {"type": "loop"}}]), "loop1", BadRequest),
        (_draft([{"id": "it1", "data": {"type": "iteration"}}]), "it1", BadRequest),
    ],
)
def test_node_run_refuses_what_cannot_run(
    monkeypatch: pytest.MonkeyPatch, draft: SimpleNamespace | None, node_id: str, error: type[Exception]
) -> None:
    service = MagicMock()
    service.get_draft_workflow.return_value = draft
    monkeypatch.setattr(app_workflow, "WorkflowService", lambda: service)
    ctx = cast(Context, SimpleNamespace(app=SimpleNamespace(id="app-1"), session=MagicMock(), account=MagicMock()))
    with pytest.raises(error):
        app_workflow.run_draft_node(ctx, node_id, inputs={}, query="")
    service.run_draft_workflow_node.assert_not_called()
