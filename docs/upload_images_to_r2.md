# `upload_images_to_r2` — Bulk Image Upload to Cloudflare R2

Management command for exporting all local Wagtail images to the Cloudflare R2
bucket used by production/staging, together with a DB fixture that preserves
human-readable titles.

Located at: `core/management/commands/upload_images_to_r2.py`

---

## When to use this

- You have images in your local dev database that don't exist in production/staging yet.
- You want to avoid re-uploading through the Wagtail admin one by one.
- You need production's database to have the same titles as your local records.

---

## Prerequisites

- Docker is running (`docker compose up -d`).
- The Docker image is up to date — rebuild if needed:
  ```bash
  docker compose build
  ```
  *(Required if the image was built before `django-storages[s3]` was added to
  `requirements/base.txt`, since that package provides boto3.)*
- You have R2 API credentials (bucket name, endpoint URL, access key, secret key).
  These can be created in the Cloudflare dashboard under **R2 → Manage API tokens**.

---

## Full workflow

### 1. Dump image records from local database

```bash
docker compose exec web python manage.py dumpdata wagtailimages.image \
    --natural-foreign --indent 2 > images_fixture.json
```

This creates `images_fixture.json` in the project root containing every image
record: title, file path, width, height, focal point, and tags.

### 2. Upload image files to R2

**Using flags:**
```bash
docker compose exec web python manage.py upload_images_to_r2 \
    --bucket YOUR_BUCKET_NAME \
    --endpoint https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com \
    --access-key YOUR_R2_ACCESS_KEY \
    --secret-key YOUR_R2_SECRET_KEY
```

**Using environment variables** (recommended — avoids credentials in shell history):

Set the variables in `.env` (already present — just fill in `CLOUDFARE_BUCKET_NAME`):
```
CLOUDFARE_BUCKET_NAME=your-bucket
CLOUDFARE_ENDPOINT=https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
CLOUDFARE_ACCESS_ID=your-access-key-id
CLOUDFARE_ACCESS_KEY=your-secret-access-key
```

Then run without flags:
```bash
docker compose exec web python manage.py upload_images_to_r2
```

### 3. Load the fixture into the Railway database

```bash
railway run python manage.py loaddata images_fixture.json
```

This creates the image records in Railway's PostgreSQL with the correct titles,
pointing at the files now stored in R2.

---

## Command flags

| Flag | Default | Description |
|------|---------|-------------|
| `--bucket` | `$CLOUDFARE_BUCKET_NAME` | R2/S3 bucket name |
| `--endpoint` | `$CLOUDFARE_ENDPOINT` | S3-compatible endpoint URL |
| `--access-key` | `$CLOUDFARE_ACCESS_ID` | R2 access key ID |
| `--secret-key` | `$CLOUDFARE_ACCESS_KEY` | R2 secret access key |
| `--prefix` | `original_images/` | Key prefix inside the bucket |
| `--dry-run` | off | Print what would be uploaded without uploading |
| `--force-overwrite` | off | Re-upload files that already exist in R2 |

---

## Behaviour

- **Skip by default**: files already present in R2 are skipped. Use
  `--force-overwrite` to re-upload them.
- **Original images only**: only files from `media/original_images/` are
  uploaded. Wagtail renditions (in `media/images/`) are regenerated on demand
  and do not need to be transferred.
- **Key paths**: each file is stored in R2 under the same relative path that
  Wagtail records in the database (e.g. `original_images/20170401_123920.jpg`),
  so Django Storages finds them without any reconfiguration.
- **Exit code**: the command exits with code 1 if any files were missing locally
  or failed to upload, so it is safe to use in scripts.

---

## Output example

```
Found 160 image records in local database.

  SKIP (exists): original_images/20170401_123920.jpg
  UPLOADED: original_images/20170402_192522.jpg (2341.8 KB) — title: 'Smalt on parchment'
  UPLOADED: original_images/20170403_200248.jpg (1876.4 KB) — title: 'Lead White dry pigment'
  ...

Done. Uploaded: 142  |  Skipped (already in R2): 18  |  Missing locally: 0  |  Errors: 0
```

---

## Troubleshooting

**`No module named 'boto3'`**
The Docker image is stale. Run `docker compose build` and retry.

**`Missing required configuration`**
One or more credentials were not provided as flags or environment variables.

**`403 Forbidden` from R2**
The API token does not have write permission on the bucket. Create a token with
**Object Read & Write** scope for the specific bucket in the Cloudflare dashboard.

**`Missing local file` warnings**
The database has a record pointing to a file that no longer exists on disk.
These images will not be uploaded; you may need to re-add them through the
Wagtail admin.

**`loaddata` errors on Railway**
If the fixture references image IDs that conflict with existing records, delete
the conflicting records in the Railway admin first, or use
`python manage.py loaddata --ignorenonexistent`.
