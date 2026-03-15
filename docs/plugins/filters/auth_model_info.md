# Auth Model Info Filter

A specialized filter for OpenWebUI that displays real-time metadata (display name, token capacity, and remaining quota) for models managed via the Antigravity Auth API.

## Features

- **Automatic Metadata Injection**: Displays model details in the status bar of the chat interface.
- **Quota Tracking**: Shows remaining quota percentage for the current model.
- **Dynamic Matching**: Fetches authorized models from the API and matches them against the current session.
- **Caching**: Efficiently caches model info to minimize API overhead.

## Configuration (Valves)

- `BASE_URL`: The endpoint of your model management service.
- `TOKEN`: Bearer token for authentication.
- `PROJECT_ID`: The project identifier on the management service.
- `AUTH_INDEX`: The authentication index required by the service.
- `ENABLE_CACHE`: Toggle caching of model data (default: `True`).

## Installation

This plugin is designed to be local-only and is excluded from Git by default.

1. Ensure the directory `plugins/filters/auth_model_info/` exists.
2. The main logic resides in `auth_model_info.py`.
