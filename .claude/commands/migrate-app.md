Migrate a pydoover device application to the doover-2 API. The app to migrate is at: $ARGUMENTS

Follow the migration guide at `../docs/migration-guide.md` (relative to the pydoover repo root) exactly. Read that file first, then:

1. Read ALL source files in the app's `src/` directory
2. Read tests, pyproject.toml, Dockerfile, and .github/workflows/
3. Apply each migration step from the guide
4. Run `uv run pytest tests -v` to verify
5. Run `uv run python -c "from <package>.application import <AppClass>"` to verify imports
6. Run `uv run export-config` if the script exists
7. If a remote device IP is provided, deploy with `doover app run <DEVICE_IP>`, then check logs via `ssh doovit@<DEVICE_IP> "docker logs --tail 50 <CONTAINER_ID>"` to confirm the app starts correctly

Not every app will have all components (tags, UI, sensors). Only migrate what exists. For example, an app with no UI doesn't need `app_ui.py` or `ui_cls`. An app with no `set_tags_async` calls doesn't need `app_tags.py` or `tags_cls`.

Cast any config integer values passed to platform interface methods with `int()` as JSON delivers them as floats.
