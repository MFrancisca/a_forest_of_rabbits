"""
Management command: upload_images_to_r2

Uploads all local Wagtail original images to the Cloudflare R2 bucket used by
production/staging, then dumps image metadata to a JSON fixture so the Railway
database can be populated with the correct titles.

Usage
-----
1. Export a fixture of the local image records:

       docker compose exec web python manage.py dumpdata wagtailimages.image \
           --natural-foreign --indent 2 > images_fixture.json

2. Upload the files to R2:

       docker compose exec web python manage.py upload_images_to_r2 \
           --bucket my-bucket \
           --endpoint https://<account-id>.r2.cloudflarestorage.com \
           --access-key KEY \
           --secret-key SECRET

   Or set env vars and omit the flags:
       CLOUDFARE_BUCKET_NAME, CLOUDFARE_ENDPOINT,
       CLOUDFARE_ACCESS_ID, CLOUDFARE_ACCESS_KEY

3. On Railway, load the fixture:

       railway run python manage.py loaddata images_fixture.json

Optional flags
--------------
--dry-run      Print what would be uploaded without actually uploading.
--skip-existing  Skip files that already exist in the bucket (default: True).
--force-overwrite  Re-upload even if the key already exists in R2.
--prefix       Key prefix inside the bucket (default: "original_images/").
"""

import os
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.core.management.base import BaseCommand, CommandError
from wagtail.images import get_image_model

Image = get_image_model()


class Command(BaseCommand):
    help = "Upload local Wagtail original images to Cloudflare R2 (or any S3-compatible store)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--bucket",
            default=os.environ.get("CLOUDFARE_BUCKET_NAME"),
            help="R2/S3 bucket name (default: $CLOUDFARE_BUCKET_NAME)",
        )
        parser.add_argument(
            "--endpoint",
            default=os.environ.get("CLOUDFARE_ENDPOINT"),
            help="S3-compatible endpoint URL (default: $CLOUDFARE_ENDPOINT)",
        )
        parser.add_argument(
            "--access-key",
            default=os.environ.get("CLOUDFARE_ACCESS_ID"),
            help="Access key ID (default: $CLOUDFARE_ACCESS_ID)",
        )
        parser.add_argument(
            "--secret-key",
            default=os.environ.get("CLOUDFARE_ACCESS_KEY"),
            help="Secret access key (default: $CLOUDFARE_ACCESS_KEY)",
        )
        parser.add_argument(
            "--prefix",
            default="original_images/",
            help='Key prefix in the bucket (default: "original_images/")',
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be uploaded without uploading.",
        )
        parser.add_argument(
            "--force-overwrite",
            action="store_true",
            help="Re-upload files that already exist in the bucket.",
        )

    def handle(self, *args, **options):
        bucket = options["bucket"]
        endpoint = options["endpoint"]
        access_key = options["access_key"]
        secret_key = options["secret_key"]
        prefix = options["prefix"]
        dry_run = options["dry_run"]
        force_overwrite = options["force_overwrite"]

        missing = [
            name
            for name, val in [
                ("--bucket / CLOUDFARE_BUCKET_NAME", bucket),
                ("--endpoint / CLOUDFARE_ENDPOINT", endpoint),
                ("--access-key / CLOUDFARE_ACCESS_ID", access_key),
                ("--secret-key / CLOUDFARE_ACCESS_KEY", secret_key),
            ]
            if not val
        ]
        if missing:
            raise CommandError(
                "Missing required configuration:\n  " + "\n  ".join(missing)
            )

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No files will be uploaded."))

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )

        images = Image.objects.all().order_by("pk")
        total = images.count()

        if total == 0:
            self.stdout.write("No images found in the local database.")
            return

        self.stdout.write(f"Found {total} image records in local database.\n")

        uploaded = 0
        skipped = 0
        missing_files = 0
        errors = 0

        for image in images:
            # image.file.name is e.g. "original_images/20170401_123920.jpg"
            local_path = image.file.path  # absolute local filesystem path
            # The key in R2 should match the relative name so Django storages finds it
            r2_key = image.file.name

            if not os.path.exists(local_path):
                self.stderr.write(
                    self.style.ERROR(f"  MISSING local file: {local_path} (title: {image.title!r})")
                )
                missing_files += 1
                continue

            if not force_overwrite:
                try:
                    s3.head_object(Bucket=bucket, Key=r2_key)
                    self.stdout.write(f"  SKIP (exists): {r2_key}")
                    skipped += 1
                    continue
                except ClientError as e:
                    if e.response["Error"]["Code"] != "404":
                        self.stderr.write(self.style.ERROR(f"  ERROR checking {r2_key}: {e}"))
                        errors += 1
                        continue
                    # 404 → does not exist, fall through to upload

            file_size = os.path.getsize(local_path)
            size_kb = file_size / 1024

            if dry_run:
                self.stdout.write(
                    f"  WOULD UPLOAD: {r2_key!r} ({size_kb:.1f} KB) — title: {image.title!r}"
                )
                uploaded += 1
                continue

            try:
                with open(local_path, "rb") as f:
                    s3.upload_fileobj(
                        f,
                        bucket,
                        r2_key,
                        ExtraArgs={"ContentType": self._content_type(local_path)},
                    )
                self.stdout.write(
                    f"  UPLOADED: {r2_key!r} ({size_kb:.1f} KB) — title: {image.title!r}"
                )
                uploaded += 1
            except (BotoCoreError, ClientError) as e:
                self.stderr.write(self.style.ERROR(f"  ERROR uploading {r2_key}: {e}"))
                errors += 1

        verb = "Would upload" if dry_run else "Uploaded"
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done. {verb}: {uploaded}  |  Skipped (already in R2): {skipped}  "
            f"|  Missing locally: {missing_files}  |  Errors: {errors}"
        ))

        if errors or missing_files:
            sys.exit(1)

    @staticmethod
    def _content_type(path: str) -> str:
        ext = path.rsplit(".", 1)[-1].lower()
        return {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "svg": "image/svg+xml",
            "tiff": "image/tiff",
            "tif": "image/tiff",
        }.get(ext, "application/octet-stream")
