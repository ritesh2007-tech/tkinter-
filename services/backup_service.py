"""
Backup and Restore Service.
Creates full backups of the SQLite database and optimized images directory into a single timestamped ZIP archive.
Provides verified restore capability with emergency pre-restore snapshot.
"""
import os
import shutil
import zipfile
from datetime import datetime
from config import DB_PATH, IMAGES_DIR, BACKUP_DIR, DATA_DIR
from database.models import AuditDAO

class BackupService:
    @classmethod
    def create_backup(cls, custom_destination=None):
        """
        Creates a complete backup archive containing:
        - jewelry_mortgage.db
        - all stored images (customers, id_proofs, jewels, connections)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"SwarnaRatna_Backup_{timestamp}.zip"
            
            if custom_destination and os.path.isdir(custom_destination):
                dest_zip = os.path.join(custom_destination, backup_filename)
            elif custom_destination and custom_destination.lower().endswith(".zip"):
                dest_zip = custom_destination
            else:
                dest_zip = os.path.join(BACKUP_DIR, backup_filename)

            with zipfile.ZipFile(dest_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                # Add database
                if os.path.exists(DB_PATH):
                    z.write(DB_PATH, arcname="jewelry_mortgage.db")

                # Add all image directories
                for root, dirs, files in os.walk(IMAGES_DIR):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, DATA_DIR)
                        z.write(full_path, arcname=rel_path)

            file_size_mb = os.path.getsize(dest_zip) / (1024 * 1024)
            AuditDAO.log("BACKUP_CREATED", os.path.basename(dest_zip), f"Backup created successfully ({file_size_mb:.2f} MB)")
            return True, dest_zip, f"Backup created successfully ({file_size_mb:.2f} MB)"
        except Exception as e:
            return False, "", f"Backup failed: {str(e)}"

    @classmethod
    def restore_backup(cls, zip_path):
        """
        Restores database and images from backup ZIP.
        First takes an emergency snapshot of current state before applying.
        """
        if not os.path.exists(zip_path) or not zipfile.is_zipfile(zip_path):
            return False, "Selected file is not a valid zip archive."

        try:
            # 1. Create emergency pre-restore snapshot
            emergency_dir = os.path.join(BACKUP_DIR, "pre_restore_snapshot")
            os.makedirs(emergency_dir, exist_ok=True)
            if os.path.exists(DB_PATH):
                shutil.copy2(DB_PATH, os.path.join(emergency_dir, "emergency_mortgage.db"))

            # 2. Extract into DATA_DIR
            with zipfile.ZipFile(zip_path, 'r') as z:
                # Check required files
                namelist = z.namelist()
                if "jewelry_mortgage.db" not in namelist:
                    return False, "Archive does not contain a valid jewelry_mortgage.db database!"

                # Extract database
                z.extract("jewelry_mortgage.db", path=DATA_DIR)

                # Extract images
                for name in namelist:
                    if name.startswith("images/"):
                        z.extract(name, path=DATA_DIR)

            AuditDAO.log("BACKUP_RESTORED", os.path.basename(zip_path), "Database and images restored successfully")
            return True, "Database and images successfully restored from backup."
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
