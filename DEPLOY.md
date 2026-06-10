   # Deploying Signa to Production

   This guide walks through taking Signa from a local development project to a live, publicly accessible service. It covers hosting options, free tier limits, and step by step configuration.

   ## Architecture in Production

   ```
   Browser / CLI
         |
         v
   FastAPI (Render or Railway)
         |
         v
   PostgreSQL (Neon)
         |
         v
   MalwareBazaar Feed (seed on deploy)
   ```

   The web UI and API are served from the same FastAPI application. A production grade database replaces the local SQLite file. The seed script runs once to populate the database with threat indicators.

   ---

   ## Hosting Options

   ### Option A: Render (Recommended for Simplicity)

   - Web service: Free tier (512 MB RAM, shared CPU, sleeps after 15 minutes of inactivity)
   - PostgreSQL: Not natively free on Render (starts at USD 7/month)
   - Pair Render (FastAPI) + Neon (PostgreSQL) for the best free combination

   | Service | Free Tier Limits | Cost |
   |---------|-----------------|------|
   | Render Web Service | 512 MB RAM, 100 GB bandwidth/month, sleeps on idle | Free |
   | Neon PostgreSQL | 0.5 GB storage, 100 hours compute/month, 1 project | Free |

   ### Option B: Railway

   - Web service: Free tier (500 MB RAM, shared CPU, 500 hours/month)
   - PostgreSQL: Free tier (1 GB storage, shared)
   - Simpler all in one setup, but the free tier hours are limited

   | Service | Free Tier Limits | Cost |
   |---------|-----------------|------|
   | Railway Web Service | 500 MB RAM, 500 hours/month | Free |
   | Railway PostgreSQL | 1 GB storage, shared | Free |

   500 hours per month equals about 16 hours of uptime per day. If you need 24/7 availability, a paid plan is required (starts at USD 5/month).

   ### Option C: Self Hosted (VPS)

   - Any VPS provider (DigitalOcean, Hetzner, AWS EC2)
   - Full control, no idle sleep
   - Starts at approximately USD 4-6/month
   - Requires manual setup of PostgreSQL, reverse proxy, and SSL

   ---

   ## Free Tier Analysis

   | Requirement | Neon Free | Render Free | Railway Free |
   |-------------|-----------|-------------|--------------|
   | Database storage | 0.5 GB | Not available | 1 GB |
   | Compute | 100 hours/month | Always on (sleeps on idle) | 500 hours/month |
   | Custom domain | No (subdomain only) | Yes | Yes |
   | SSL/TLS | Yes | Yes | Yes |
   | Bandwidth | 5 GB/month | 100 GB/month | 1 GB/month |
   | Good for | Database | API hosting | All in one |

   For a personal project with light usage, the Neon + Render combination is the most practical. The database has enough storage for hundreds of thousands of malware hashes. The API sleeps after 15 minutes of inactivity but wakes up on the next request (takes 30-60 seconds).

   ---

   ## Step by Step Deployment Guide

### Step 1: Set Up Neon PostgreSQL

1. Go to https://neon.tech and create a free account.
2. Create a new project. Choose a region close to your users.
3. From the project dashboard, copy the connection string. It looks like:
   ```
   postgresql://user:password@ep-example-123456.us-east-2.aws.neon.tech/signa?sslmode=require
   ```
4. Save this string. You will need it in Step 3.

### Step 2: Prepare the Codebase

1. Remove the SQLite specific fallback in `api/database.py`. Replace it to always use the environment variable:

   ```python
   DATABASE_URL = os.environ["SIGN_DB_URL"]
   ```

   This ensures SQLite is never used in production by accident.

2. Add a `start.sh` script at the project root:

   ```bash
   #!/usr/bin/env bash
   # Run database migrations (creates tables if they do not exist)
   python -c "from db.schema import Base; from api.database import engine; Base.metadata.create_all(bind=engine)"
   # Start the server
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```

   Render and Railway both set the `$PORT` environment variable automatically.

3. Ensure `requirements.txt` includes `python-multipart` (already present) and `psycopg2-binary` (already present) for PostgreSQL support.

### Step 3: Deploy to Render

1. Push your code to a GitHub repository.
2. Log in to https://render.com.
3. Click "New" and select "Web Service".
4. Connect your GitHub repository.
5. Configure the service:

   | Setting | Value |
   |---------|-------|
   | Name | signa |
   | Environment | Python |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `sh start.sh` |
   | Plan | Free |

6. Add the environment variable:

   | Key | Value |
   |-----|-------|
   | `SIGN_DB_URL` | Your Neon connection string |

7. Click "Create Web Service". Render will build and deploy your application.
8. Once deployed, open the provided URL (e.g. `https://signa.onrender.com`).

### Step 4: Run the Seed Script on the Server

After deployment, you need to populate the database with threat indicators.

1. Open the Render shell (or use SSH).
2. Run:

   ```bash
   python -m db.seed --limit 1000
   ```

   This fetches the latest malware hashes from MalwareBazaar and stores them in your Neon database.

### Step 5: Set Up Automatic Database Seeding (Optional)

To keep your database up to date, schedule a cron job or use Render's Cron Jobs feature (paid) to run the seed script periodically.

Alternatively, set up a GitHub Action that runs the seed script against your Neon database on a schedule:

```yaml
name: Daily Seed
on:
  schedule:
    - cron: "0 6 * * *"
jobs:
  seed:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -r requirements.txt
      - run: python -m db.seed --limit 500
        env:
          SIGN_DB_URL: ${{ secrets.SIGN_DB_URL }}
```

---

## Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Neon PostgreSQL project created and connection string saved
- [ ] `start.sh` script added to repository
- [ ] Render web service created with environment variable `SIGN_DB_URL`
- [ ] Build succeeds and service starts
- [ ] Seed script run on deployed server
- [ ] Web UI accessible via public URL
- [ ] CLI can reach the API (update `cli/client.py` `API_BASE_URL`)

---

## Updating the CLI to Point to Production

In `cli/client.py`, change the `API_BASE_URL` to your deployed URL:

```python
API_BASE_URL = "https://signa.onrender.com"
```

Users can then scan files against your live database:

```bash
python -m cli.main scan document.pdf
```

---

## Cost Summary (Free Tier)

| Service | Monthly Cost |
|---------|-------------|
| Neon PostgreSQL (free tier) | USD 0 |
| Render Web Service (free tier) | USD 0 |
| GitHub (free tier) | USD 0 |
| **Total** | **USD 0** |

The free tier limits are sufficient for a personal project or portfolio. If the project gains significant traffic, upgrading to a paid plan (approximately USD 7-15/month total) provides more compute hours, no idle sleep, and higher bandwidth limits.
