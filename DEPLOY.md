# Deploying Nyhetsradar

One small Linux VM runs everything. Four containers, one command.

```
internet ──▶ Caddy (TLS + login)  ──▶ web   Next.js
                                       │
                                       └──▶ api   Flask ◀── pipeline (every 4h)
                                                    │
                                                 news.db
```

Only Caddy is exposed. Flask is never reachable from the internet.

---

## 1. Get a machine

Any VM with 1 GB RAM and 10 GB disk is plenty — the database grows about
90 MB per year at current volume.

**Free options:**

| Host | Region | Notes |
|---|---|---|
| Oracle Cloud Always Free | Stockholm, Frankfurt, Amsterdam | Permanently free. Card required at signup, and ARM instances are often "out of capacity" — retry, or pick an AMD micro shape. |
| Google Cloud free tier | us-west1 / us-central1 / us-east1 only | Easier signup, but US-only. Fine for testing; wrong for real Selvaag data. |

Pick Ubuntu 24.04 LTS. Open ports **22, 80 and 443** in the provider's firewall —
on Oracle this is a Security List rule and is the step people forget.

---

## 2. Point a domain at it

Create an **A record** for the hostname you want, pointing at the VM's public IP.
Caddy needs this working *before* first start, or the certificate request fails.

Check it resolves before continuing:

```bash
dig +short radar.dittdomene.no
```

No domain? Use a free subdomain from DuckDNS or similar. Caddy will still get a
real certificate.

---

## 3. Install Docker on the VM

```bash
ssh ubuntu@<ip>
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit    # log out and back in for the group to apply
```

---

## 4. Get the code and configure

```bash
ssh ubuntu@<ip>
git clone https://github.com/Nahom101-1/NewsFeedSelvaagEiendom.git
cd NewsFeedSelvaagEiendom
cp .env.example .env
```

Generate a password hash:

```bash
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'velg-et-passord'
```

Edit `.env`:

```bash
DOMAIN=radar.dittdomene.no
BASIC_AUTH_USER=radar
BASIC_AUTH_HASH=$2a$14$...        # paste the hash from above
SCORE_THRESHOLD=50

# Optional — turns on Norwegian summaries and "why this matters".
# ANTHROPIC_API_KEY=sk-ant-...
# SCORE_ARGS=--llm
```

The hash contains `$` characters. Keep it in single quotes if you export it by
hand; inside `.env` it is read literally and needs no escaping.

---

## 5. Start

```bash
docker compose -f compose.prod.yaml up -d --build
```

First build takes a few minutes. Then:

```bash
docker compose -f compose.prod.yaml ps
docker compose -f compose.prod.yaml logs -f caddy
```

Caddy fetches a certificate on first start. Once the log settles, open
`https://radar.dittdomene.no` and log in with the username and password from
step 4.

**The first page will be empty** — nothing has been collected yet. Either wait
for the pipeline's first cycle, or trigger one now:

```bash
docker compose -f compose.prod.yaml exec pipeline python -m nyhetsradar.collect
docker compose -f compose.prod.yaml exec pipeline python -m nyhetsradar.dedup
docker compose -f compose.prod.yaml exec pipeline python -m nyhetsradar.score
```

---

## 6. Day to day

```bash
# update to the latest code
git pull && docker compose -f compose.prod.yaml up -d --build

# watch the collector
docker compose -f compose.prod.yaml logs -f pipeline

# change what gets surfaced: edit config/, then
docker compose -f compose.prod.yaml restart pipeline

# stop everything
docker compose -f compose.prod.yaml down
```

`config/` is mounted read-only into the pipeline, so tuning `profile.md` or the
keyword lists is an edit plus a restart — not a rebuild.

---

## 7. Back up the judgements

The news is re-fetchable. **The feedback labels are not** — they are hand-made,
and they are what a trained model would later learn from.

```bash
docker compose -f compose.prod.yaml exec api \
  sqlite3 /data/news.db ".backup '/data/backup.db'"
docker compose -f compose.prod.yaml cp api:/data/backup.db ./backup-$(date +%F).db
```

Worth doing before any upgrade.

---

## 8. When it goes wrong

| Symptom | Cause |
|---|---|
| Certificate never issues | DNS not pointing at the VM yet, or port 80 closed in the provider firewall |
| Page loads but says *"Får ikke kontakt med serveren"* | `api` container is down — `docker compose -f compose.prod.yaml logs api` |
| Empty page, no stories | Pipeline hasn't run yet, or everything scored below the threshold. Check `/admin`. |
| `502` from Caddy | `web` container still starting, or crashed |
| Out of disk | `docker system prune -a` |

Health check, from on the VM:

```bash
docker compose -f compose.prod.yaml exec api curl -s localhost:8000/healthz
```

---

## Not covered

This runs one shared login for a handful of testers. Real user accounts, rate
limiting, log retention and monitoring are all absent by design — add them when
this stops being a test.
