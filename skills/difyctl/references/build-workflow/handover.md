# Hand-over phase

Start when every slice in `plan.md` is ticked. In the commands below, `<mode>` is `workflow` for a Workflow app and `advanced_chat` for a Chatflow app.

1. Run the final acceptance run: every case in the spec, on the draft. Report pass or fail per requirement and per case. Show your reasoning for each `judged` case.
2. Stop at the human gate. Show the human the results, the "Changes during build" list from `plan.md`, and anything still open. Nothing goes live without a yes.
3. Publish, then confirm the new version is live:

   ```bash
   difyctl publish console_app --app-id <app_id> --json
   difyctl get console_app version --app-id <app_id> --json
   ```

   The new version must show `current: true`.

4. Turn on access. Ask about each item separately. Nothing is on by default.
   - Web app. Give the human the `url` from the result.

     ```bash
     difyctl set webapp <mode> --app-id <app_id> --enabled --json
     ```

   - Service API (needs an admin):

     ```bash
     difyctl set service_api <mode> --app-id <app_id> --enabled --json
     ```

   - Who may open the web app (Enterprise). Find the members or groups, then set the list:

     ```bash
     difyctl get access_subject --keyword <name> --json
     difyctl set webapp_access <mode> --app-id <app_id> --access-mode private \
       --subjects '[{"id":"<id>","type":"group"}]' --json
     ```

     `--subjects` replaces the whole list. `type` is `account` or `group`.
5. Smoke test the live app with one acceptance case:

   ```bash
   difyctl run console_app workflow --app-id <app_id> --inputs '{"<var>": "<value>"}' --json
   difyctl run console_app advanced_chat --app-id <app_id> --query "<message>" --inputs '{}' --json
   ```

6. Close. Mark `plan.md` as published with the version id, the date and the url. Give the human a short summary.
