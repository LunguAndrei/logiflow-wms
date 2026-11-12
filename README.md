# LogiFlow WMS

A warehouse management system built as a hands-on DevOps learning project.

The system will track products from inbound receiving and storage through order fulfillment and outbound shipping.

## Run with Docker Compose

Requirements: Docker Desktop.

Pull the latest application image and start the service:

```bash
docker compose pull
docker compose up -d
```

Open the API documentation at <http://127.0.0.1:8000/docs>.

Check the application and database:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
docker compose ps
```

`/health` confirms that the API responds. `/ready` also checks that the SQLite database is available. Compose reports the container as `healthy` when its readiness check succeeds.

The SQLite database is stored in the named Docker volume `logiflow-data`, so it persists when the container is stopped or recreated.

View service logs with:

```bash
docker compose logs --tail 50 api
```

Stop the service with:

```bash
docker compose down
```

## CI/CD

GitHub Actions runs the test suite, builds and scans the Docker image, and publishes the multi-platform image to GitHub Container Registry after changes are merged into `main`.