import os
import shutil
import hashlib
import json
import glob
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = "Safely restores the database from an integrity-verified snapshot."

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to specific backup file (e.g. backups/elara_backup_20261027_120000.sqlite3)'
        )
        parser.add_argument(
            '--latest',
            action='store_true',
            help='Automatically restore the latest backup found in the backups/ directory.'
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Bypass confirmation prompt (for non-interactive disaster recovery).'
        )

    def handle(self, *args, **options):
        dest_dir = os.path.join(settings.BASE_DIR, 'backups')
        target_file = options.get('file')

        if options.get('latest'):
            backups = sorted(glob.glob(os.path.join(dest_dir, "elara_backup_*.sqlite3")) +
                             glob.glob(os.path.join(dest_dir, "elara_backup_*.json")))
            if not backups:
                self.stderr.write(self.style.ERROR("[ERROR] No backup files found in backups/ directory."))
                return
            target_file = backups[-1]

        if not target_file or not os.path.exists(target_file):
            self.stderr.write(self.style.ERROR(f"[ERROR] Backup file not found: {target_file}"))
            return

        # Look for corresponding manifest to verify integrity
        base_name = os.path.splitext(target_file)[0]
        manifest_path = f"{base_name}.manifest.json"
        
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            expected_hash = manifest.get('sha256')

            sha256 = hashlib.sha256()
            with open(target_file, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    sha256.update(chunk)
            actual_hash = sha256.hexdigest()

            if expected_hash != actual_hash:
                self.stderr.write(self.style.ERROR("[INTEGRITY FAILURE] SHA-256 hash mismatch! Backup file may have been altered or corrupted."))
                self.stderr.write(f"  Expected: {expected_hash}")
                self.stderr.write(f"  Actual:   {actual_hash}")
                return
            self.stdout.write(self.style.SUCCESS("[INTEGRITY VERIFIED] SHA-256 hash matches the signed manifest."))

        if not options.get('no_input'):
            confirm = input(f"Are you sure you want to restore database from {target_file}? This will overwrite active data! (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING("Restoration cancelled by operator."))
                return

        db_conf = settings.DATABASES['default']
        engine = db_conf.get('ENGINE', '')

        if 'sqlite' in engine:
            target_db = db_conf['NAME']
            # Create a safety pre-restore backup first
            safety_copy = f"{target_db}.pre_restore.bak"
            if os.path.exists(target_db):
                shutil.copy2(target_db, safety_copy)
            shutil.copy2(target_file, target_db)
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Database successfully restored from {target_file}!"))
        else:
            from django.core.management import call_command
            call_command('loaddata', target_file)
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] JSON snapshot loaded successfully into database!"))
