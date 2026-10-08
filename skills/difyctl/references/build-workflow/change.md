# Change an existing app

Use this path when the app already exists. It reuses the four phases.

1. Find the app and confirm with the human that it is the right one:

   ```bash
   difyctl get console_app --name <name> --json
   ```

2. Export first. Save the live DSL as the starting `difyctl/<app-slug>/app.yml`. Note the current version id: the version with `current: true`.

   ```bash
   difyctl export console_app dsl --app-id <app_id> --json
   difyctl get console_app version --app-id <app_id> --json
   ```

   Publishing replaces the live version, so that id is the one to go back to. `difyctl export console_app dsl --app-id <app_id> --workflow-id <version_id>` exports it again.

3. If `difyctl/<app-slug>/` has no `spec.md`, the app was built elsewhere. Rebuild a baseline spec from the export: the graph, the requirements you can infer, the inputs and outputs. The human confirms it.
4. Write the change as a "Change" section in the spec: new, changed and removed requirements and cases. Existing cases become regression cases.
5. Plan only the nodes that change, in slices as usual.
6. At the end, run every old case again. Then hand over as usual.
