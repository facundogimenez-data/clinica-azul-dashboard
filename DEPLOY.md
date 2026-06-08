# Deploying Clínica Azul Dashboard to EasyPanel

This guide covers deploying the live demo to [EasyPanel](https://easypanel.io). The repo ships
`docker-compose.prod.yml` — a self-contained stack (MySQL + dashboard) that seeds itself from
`db/schema.sql` on first boot, so the deployed demo shows realistic data with zero manual setup.

## Prerequisites

- An EasyPanel project with this GitHub repo connected: `facundogimenez-data/clinica-azul-dashboard`
- Strong values generated for the database credentials below — **do not reuse** the values from
  `.env.example` (those are for local development only)

## Required environment variables

Set these in EasyPanel before the first deploy:

| Variable | Purpose | Notes |
|---|---|---|
| `DB_NAME` | MySQL database name | e.g. `clinica_azul_demo` |
| `DB_USER` | MySQL app user | e.g. `dashboard_user` |
| `DB_PASSWORD` | MySQL app user password | generate a strong random value |
| `DB_ROOT_PASSWORD` | MySQL root password | generate a strong random value, different from `DB_PASSWORD` |

`DB_HOST` (`mysql`) and `DB_PORT` (`3306`) are already set inside `docker-compose.prod.yml` —
no need to add them in EasyPanel.

`docker-compose.prod.yml` has no fallback values for these — if any are missing, `docker compose`
will fail to start rather than silently running with demo credentials.

## Route A — deploy as a single Compose service (recommended)

1. In EasyPanel, create a new service of type **App from Docker Compose** (or "Compose"),
   pointing at this repo and `docker-compose.prod.yml`.
2. Add the four environment variables above to the service.
3. Deploy. EasyPanel will build the `dashboard` image from the `Dockerfile`, start `mysql`,
   wait for its healthcheck, seed it from `db/schema.sql`, then start `dashboard`.
4. Attach a domain/subdomain to the `dashboard` service's internal port `8501`.

## Route B — separate App + Database services

Use this if you'd rather run MySQL as an EasyPanel-managed database service (consistent with
how other stacks — e.g. budget2026 — are run):

1. Create an EasyPanel **MySQL** database service, with `DB_NAME` / `DB_USER` / `DB_PASSWORD` /
   `DB_ROOT_PASSWORD` matching the table above.
2. Load `db/schema.sql` into it once via EasyPanel's database console / import feature
   (this is the step `docker-entrypoint-initdb.d` automates in Route A — here it's manual
   because the managed service doesn't run your compose file).
3. Create an EasyPanel **App** service from this repo's `Dockerfile`.
4. Set `DB_HOST` / `DB_PORT` to point at the managed MySQL service's internal address, plus
   `DB_USER` / `DB_PASSWORD` / `DB_NAME`.
5. Attach a domain/subdomain to internal port `8501`.

## Networking

- The dashboard listens on `8501` inside the container (`--server.address=0.0.0.0`,
  set in the `Dockerfile`'s `CMD`).
- MySQL is **not** published to the host in `docker-compose.prod.yml` — only the `dashboard`
  service needs to be publicly reachable.

## Post-deploy verification checklist

- [ ] Container health is green (`HEALTHCHECK` hits `/_stcore/health`)
- [ ] Dashboard loads at the assigned domain
- [ ] All three tabs render data — *Gestión de citas*, *Recursos médicos*, *Satisfacción*
      (confirms `db/schema.sql` seeded correctly)
- [ ] `https://<your-domain>/_stcore/health` returns `ok`

## Redeploys

Push to `main` — if auto-deploy is enabled on the EasyPanel service, it rebuilds automatically.
Otherwise trigger a manual **Rebuild** from the EasyPanel dashboard.

> Note: MySQL only runs `db/schema.sql` on a *fresh* volume (first boot). Schema changes after
> the initial deploy require a manual migration — they won't be picked up by simply rebuilding.
