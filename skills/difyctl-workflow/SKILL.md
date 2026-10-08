---
name: difyctl-workflow
description: Build, test, fix and publish a Dify workflow or advanced-chat app with difyctl, from a blank app to a live version. Use when asked to create or change a Dify workflow or chatflow.
---

# Build a workflow app with difyctl

Read `../difyctl/SKILL.md` first. It explains how to find and run any operation.

Work on one app per goal. Change it by overwriting its draft; never make copies. Always pass `--json`.

## The loop

1. Create the app once: `difyctl create console_app workflow --name "<name>"` (or `create console_app advanced_chat`). Note the `app_id`. A new app starts with an empty draft.
2. Export the draft: `difyctl export console_app dsl --app-id <app_id>`. Save the `data` field as `app.yml`. Keep `draft_hash` from the result.
3. Look up each node you need: `difyctl get node_type`, then `difyctl describe node_type --node-type <type>`. The `schema` is the node's `data`; `default_config` is a good starting point. Set each node's `data.version` to the `version` that `describe node_type` returns.
4. Edit `app.yml`. See `references/dsl.md` for where nodes and edges go and for a minimal valid workflow.
5. Import it over the draft: `difyctl import console_app dsl --app-id <app_id> --mode yaml-content --yaml-content "$(cat app.yml)" --draft-hash <draft_hash>`. The import also copies the YAML's `app.name` and icon onto the app. A hash mismatch means someone else changed the draft: export again and redo your edit. Export again after each import to get the new hash.
6. Test the whole draft: `difyctl test console_app workflow --app-id <app_id> --inputs '{...}'`. For an advanced-chat app use `test console_app advanced_chat --query "<message>"`.
7. If it failed, list the runs with `difyctl get run --app-id <app_id>`, then find the node: `difyctl get run node --app-id <app_id> --run-id <run_id>`.
8. Fix that node, import again, then test just it: `difyctl test node workflow --app-id <app_id> --node-id <node_id>` (`test node advanced_chat` for a chatflow, with `--query`). It reuses the values the last full test run saved. Override one with `--inputs '{"#<node_id>.<var>#": ...}'`.
9. When a full test passes, publish: `difyctl publish console_app --app-id <app_id>`.
10. Confirm: `difyctl get console_app version --app-id <app_id>` shows your version with `current: true`.

## Hand it over

- Turn on the web app: `difyctl set webapp workflow --app-id <app_id> --enabled` (`set webapp advanced_chat` for a chatflow).
- Turn on the Service API (admin): `difyctl set service_api workflow --app-id <app_id> --enabled`.
- On Enterprise, choose who may open it: `difyctl get access_subject --keyword <name>`, then `difyctl set webapp_access workflow --app-id <app_id> --access-mode private --subjects '[{"id":"<id>","type":"group"}]'`.

## Limits

- A draft test that pauses on a human-input node can't be resumed over difyctl.
- Trigger-started workflows (webhook, schedule, plugin) can't be draft-tested.
- Loop and iteration nodes can't be tested alone; use a full draft test.
- `test node` can't take file inputs.
- Import rejects nodes a mode doesn't allow: no `answer` in a workflow, no `end` or triggers in an advanced-chat app. Don't use `datasource` or `knowledge-index`; they belong to knowledge pipelines.
- LLM nodes need a model that's set up in the workspace. If you don't know one, ask the user.
