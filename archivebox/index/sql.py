__package__ = 'archivebox.index'

from io import StringIO
from typing import List, Tuple, Iterator

from .schema import Link
from ..util import enforce_types
from ..config import setup_django, OUTPUT_DIR


### Main Links Index

@enforce_types
def parse_sql_main_index(out_dir: str=OUTPUT_DIR) -> Iterator[Link]:
    setup_django(out_dir, check_db=True)
    from core.models import Snapshot

    return (
        Link.from_json(page.as_json(*Snapshot.keys))
        for page in Snapshot.objects.all()
    )

@enforce_types
def write_sql_main_index(links: List[Link], out_dir: str=OUTPUT_DIR) -> None:
    setup_django(out_dir, check_db=True)
    from core.models import Snapshot
    from django.db import transaction

    all_urls = {link.url: link for link in links}
    all_ts = {link.timestamp: link for link in links}

    with transaction.atomic():
        for snapshot in Snapshot.objects.all():
            if snapshot.timestamp in all_ts:
                info = {k: v for k, v in all_urls.pop(snapshot.url)._asdict().items() if k in Snapshot.keys}
                snapshot.delete()
                Snapshot.objects.create(**info)
            if snapshot.url in all_urls:
                info = {k: v for k, v in all_urls.pop(snapshot.url)._asdict().items() if k in Snapshot.keys}
                snapshot.delete()
                Snapshot.objects.create(**info)
            else:
                snapshot.delete()

        for url, link in all_urls.items():
            info = {k: v for k, v in link._asdict().items() if k in Snapshot.keys}
            Snapshot.objects.update_or_create(url=url, defaults=info)



@enforce_types
def list_migrations(out_dir: str=OUTPUT_DIR) -> List[Tuple[bool, str]]:
    setup_django(out_dir, check_db=False)
    from django.core.management import call_command
    out = StringIO()
    call_command("showmigrations", list=True, stdout=out)
    out.seek(0)
    migrations = []
    for line in out.readlines():
        if line.strip() and ']' in line:
            status_str, name_str = line.strip().split(']', 1)
            is_applied = 'X' in status_str
            migration_name = name_str.strip()
            migrations.append((is_applied, migration_name))

    return migrations

@enforce_types
def apply_migrations(out_dir: str=OUTPUT_DIR) -> List[str]:
    setup_django(out_dir, check_db=False)
    from django.core.management import call_command
    null, out = StringIO(), StringIO()
    call_command("makemigrations", interactive=False, stdout=null)
    call_command("migrate", interactive=False, stdout=out)
    out.seek(0)

    return [line.strip() for line in out.readlines() if line.strip()]

@enforce_types
def get_admins(out_dir: str=OUTPUT_DIR) -> List[str]:
    setup_django(out_dir, check_db=False)
    from django.contrib.auth.models import User
    return User.objects.filter(is_superuser=True)
