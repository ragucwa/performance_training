# TimescaleDB And Grafana

This workspace can run Locust with TimescaleDB-backed Grafana dashboards.

## Prerequisites

- Docker Desktop or another Docker engine with `docker compose`
- The Python dependencies from `requirements.txt`

## Quick Start

1. Start the monitoring stack:
   `just monitor-up`
2. Initialize the Grafana datasource and import the Locust dashboards:
   `just monitor-init`
3. Run Locust and write metrics to TimescaleDB:
   `just run-timescale 5 2 5m`

Grafana will be available at `http://localhost:3000/d/qjIIww4Zz?from=now-15m&to=now`.

## Useful Recipes

- `just test-timescale`
- `just monitor-down`
- `just monitor-reset`

## Notes

- TimescaleDB is exposed only on `127.0.0.1:5432`.
- Grafana is exposed only on `127.0.0.1:3000`.
- The default local credentials used for initialization are `admin/admin` for Grafana and `postgres/password` for TimescaleDB.