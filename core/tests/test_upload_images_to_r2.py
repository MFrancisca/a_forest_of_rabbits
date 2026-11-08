from io import StringIO
from unittest import mock

import pytest
import wagtail_factories
from botocore.exceptions import ClientError
from django.core.management import call_command
from django.core.management.base import CommandError

from core.management.commands.upload_images_to_r2 import Command

CREDS = dict(bucket='b', endpoint='https://r2.example', access_key='k', secret_key='s')


def _client_error(code):
    return ClientError({'Error': {'Code': code, 'Message': code}}, 'HeadObject')


@pytest.fixture
def s3():
    with mock.patch('core.management.commands.upload_images_to_r2.boto3.client') as factory:
        client = factory.return_value
        client.head_object.side_effect = _client_error('404')  # nothing in the bucket yet
        yield client


def _run(**options):
    out, err = StringIO(), StringIO()
    call_command('upload_images_to_r2', stdout=out, stderr=err, **{**CREDS, **options})
    return out.getvalue(), err.getvalue()


@pytest.mark.django_db
def test_missing_configuration_lists_every_missing_setting(monkeypatch):
    for var in ('CLOUDFARE_BUCKET_NAME', 'CLOUDFARE_ENDPOINT', 'CLOUDFARE_ACCESS_ID', 'CLOUDFARE_ACCESS_KEY'):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(CommandError) as exc:
        call_command('upload_images_to_r2', bucket=None, endpoint=None, access_key=None, secret_key=None)
    for flag in ('--bucket', '--endpoint', '--access-key', '--secret-key'):
        assert flag in str(exc.value)


@pytest.mark.django_db
def test_no_images(s3):
    out, _ = _run()
    assert 'No images found' in out
    s3.upload_fileobj.assert_not_called()


@pytest.mark.django_db
def test_uploads_new_image_under_its_storage_name(s3):
    image = wagtail_factories.ImageFactory()

    out, _ = _run()

    s3.upload_fileobj.assert_called_once()
    _, bucket, key = s3.upload_fileobj.call_args.args
    assert (bucket, key) == ('b', image.file.name)
    assert s3.upload_fileobj.call_args.kwargs['ExtraArgs'] == {'ContentType': 'image/jpeg'}
    assert 'Uploaded: 1' in out


@pytest.mark.django_db
def test_skips_image_already_in_bucket(s3):
    wagtail_factories.ImageFactory()
    s3.head_object.side_effect = None

    out, _ = _run()

    s3.upload_fileobj.assert_not_called()
    assert 'SKIP (exists)' in out and 'Skipped (already in R2): 1' in out


@pytest.mark.django_db
def test_force_overwrite_does_not_check_bucket(s3):
    wagtail_factories.ImageFactory()
    s3.head_object.side_effect = None

    _run(force_overwrite=True)

    s3.head_object.assert_not_called()
    s3.upload_fileobj.assert_called_once()


@pytest.mark.django_db
def test_dry_run_uploads_nothing(s3):
    wagtail_factories.ImageFactory()

    out, _ = _run(dry_run=True)

    s3.upload_fileobj.assert_not_called()
    assert 'WOULD UPLOAD' in out and 'Would upload: 1' in out


@pytest.mark.django_db
def test_head_error_other_than_404_counts_as_error_and_exits_nonzero(s3):
    wagtail_factories.ImageFactory()
    s3.head_object.side_effect = _client_error('403')

    with pytest.raises(SystemExit) as exc:
        _run()

    assert exc.value.code == 1
    s3.upload_fileobj.assert_not_called()


@pytest.mark.django_db
def test_upload_failure_exits_nonzero(s3):
    wagtail_factories.ImageFactory()
    s3.upload_fileobj.side_effect = _client_error('500')

    with pytest.raises(SystemExit):
        _run()


@pytest.mark.django_db
def test_missing_local_file_is_reported_and_exits_nonzero(s3):
    image = wagtail_factories.ImageFactory()
    image.file.storage.delete(image.file.name)

    with pytest.raises(SystemExit):
        _run()

    s3.upload_fileobj.assert_not_called()


@pytest.mark.parametrize('path, expected', [
    ('a/b.JPG', 'image/jpeg'),
    ('x.jpeg', 'image/jpeg'),
    ('x.png', 'image/png'),
    ('x.webp', 'image/webp'),
    ('x.tif', 'image/tiff'),
    ('x.unknown', 'application/octet-stream'),
    ('noext', 'application/octet-stream'),
])
def test_content_type(path, expected):
    assert Command._content_type(path) == expected
