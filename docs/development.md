# Development

Create an environment with Home Assistant development dependencies, then run:

```sh
python3 /home/alves-dev/.codex/skills/home-assistant-integration-standards/scripts/validate_integration_structure.py .
python3 -m compileall custom_components
```

`dev/start-ha.sh` and `dev/stop-ha.sh` manage the shared local Home Assistant instance. `dev/copy-to-core.sh` deploys this integration to its local configuration before starting that instance.
