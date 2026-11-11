# Development

Create an environment with Home Assistant development dependencies, then run:

```sh
python3 /home/alves-dev/.codex/skills/home-assistant-integration-standards/scripts/validate_integration_structure.py .
python3 -m compileall custom_components
```

`dev/start-ha.sh` and `dev/stop-ha.sh` manage the shared Docker Home Assistant instance.
`dev/deploy-to-ha.sh` stages this integration into the mounted configuration and restarts
the shared container. See [the local Home Assistant reference](local-home-assistant.md)
for the container, configuration, authentication, and test-environment details.
