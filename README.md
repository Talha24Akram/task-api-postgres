# Task API — Postgres in Docker (Assignment 3)

Work in progress. Run Postgres by hand:

```bash
docker run --name taskdb -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=tasks \
  -p 5432:5432 -v taskdata:/var/lib/postgresql -d postgres
docker exec -it taskdb psql -U postgres -d tasks
```

> The Postgres 18+ image keeps its data under `/var/lib/postgresql/<version>/`, so the volume is
> mounted one level up from the older `/var/lib/postgresql/data` path.
