import os
import shutil
import hashlib
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps

class Command(BaseCommand):
    help = "Generates a secure, integrity-hashed database backup snapshot outside static web access."

    def add_arguments(self, parser):
        parser.add_argument(
            '--destination',
            type=str,
            default=os.path.join(settings.BASE_DIR, 'backups'),
            help='Directory to store the backup files (default: project root/backups)'
        )

    def handle(self, *args, **options):
        dest_dir = options['destination']
        os.makedirs(dest_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_conf = settings.DATABASES['default']
        engine = db_conf.get('ENGINE', '')

        self.stdout.write(self.style.NOTICE(f"[START] Commencing database backup at {timestamp}..."))

        backup_filename = f"elara_backup_{timestamp}.sqlite3" if 'sqlite' in engine else f"elara_backup_{timestamp}.json"
        backup_path = os.path.join(dest_dir, backup_filename)

        if 'sqlite' in engine:
            source_db = db_conf['NAME']
            if not os.path.exists(source_db):
                self.stderr.write(self.style.ERROR(f"SQLite database file not found at: {source_db}"))
                return
            shutil.copy2(source_db, backup_path)
        else:
            # For MySQL / PostgreSQL fallback to Django JSON serialized dumpdata
            from django.core.management import call_command
            with open(backup_path, 'w', encoding='utf-8') as f:
                call_command('dumpdata', indent=2, stdout=f)

        # Compute SHA-256 checksum for tamper-evidence
        sha256 = hashlib.sha256()
        with open(backup_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        digest = sha256.hexdigest()

        # Collect record counts
        model_counts = {}
        for app_label in ['accounts', 'rooms', 'bookings', 'services', 'inventory', 'workforce', 'complaints', 'events', 'concierge', 'analytics']:
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    model_counts[model.__name__] = model.objects.count()
            except LookupError:
                pass

        manifest = {
            'timestamp': datetime.now().isoformat(),
            'backup_file': backup_filename,
            'sha256': digest,
            'file_size_bytes': os.path.getsize(backup_path),
            'database_engine': engine,
            'model_counts': model_counts
        }

        manifest_path = os.path.join(dest_dir, f"elara_backup_{timestamp}.manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Backup created successfully!"))
        self.stdout.write(f"  File: {backup_path}")
        self.stdout.write(f"  Size: {manifest['file_size_bytes']:,} bytes")
        self.stdout.write(f"  SHA-256: {digest}")
        self.stdout.write(f"  Manifest: {manifest_path}")
