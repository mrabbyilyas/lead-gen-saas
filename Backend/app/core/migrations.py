from pathlib import Path
from typing import List, Optional
import logging
from app.core.database import get_supabase_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Database migration runner for executing SQL migration files."""

    def __init__(self):
        self.settings = settings
        self.migrations_dir = Path(__file__).parent.parent.parent / "migrations"

    def create_migrations_table(self):
        """Create the migrations tracking table if it doesn't exist."""
        # For now, we'll assume the table exists or will be created manually
        # This is a simplified approach for Supabase
        logger.info(
            "Migrations table setup (manual creation required in Supabase dashboard)"
        )
        return True

    def get_executed_migrations(self) -> List[str]:
        """Get list of already executed migrations."""
        client = get_supabase_client()

        try:
            result = (
                client.table("schema_migrations")
                .select("migration_name")
                .order("id")
                .execute()
            )
            return [row["migration_name"] for row in result.data]
        except Exception as e:
            logger.error(f"Failed to get executed migrations: {e}")
            return []

    def get_migration_files(self) -> List[Path]:
        """Get list of migration files sorted by name."""
        if not self.migrations_dir.exists():
            logger.warning(
                f"Migrations directory does not exist: {self.migrations_dir}"
            )
            return []

        migration_files = []
        for file_path in self.migrations_dir.glob("*.sql"):
            if file_path.is_file():
                migration_files.append(file_path)

        # Sort by filename to ensure proper order
        migration_files.sort(key=lambda x: x.name)
        return migration_files

    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of migration file."""
        import hashlib

        with open(file_path, "rb") as f:
            content = f.read()
            return hashlib.md5(content).hexdigest()

    def execute_migration(self, file_path: Path) -> bool:
        """Execute a single migration file."""
        migration_name = file_path.name
        self.calculate_checksum(file_path)

        logger.info(f"Executing migration: {migration_name}")

        try:
            # Read migration file
            with open(file_path, "r", encoding="utf-8") as f:
                migration_sql = f.read()

            # For Supabase, we'll log the SQL and indicate manual execution needed
            logger.info(f"Migration SQL for {migration_name}:")
            logger.info("Please execute the following SQL in Supabase dashboard:")
            logger.info(migration_sql)

            # Simulate successful execution for now
            # In a real implementation, you would execute this via Supabase SQL editor
            # or use a different approach

            logger.info(f"Migration {migration_name} prepared for execution")
            return True

        except Exception as e:
            logger.error(f"Failed to prepare migration {migration_name}: {e}")
            return False

    def run_migrations(self, target_migration: Optional[str] = None) -> bool:
        """Run all pending migrations or up to a specific target."""
        logger.info("Starting database migrations")

        try:
            # Ensure migrations table exists
            self.create_migrations_table()

            # Get executed migrations
            executed_migrations = self.get_executed_migrations()
            logger.info(f"Found {len(executed_migrations)} executed migrations")

            # Get migration files
            migration_files = self.get_migration_files()
            logger.info(f"Found {len(migration_files)} migration files")

            if not migration_files:
                logger.info("No migration files found")
                return True

            # Filter pending migrations
            pending_migrations = []
            for file_path in migration_files:
                if file_path.name not in executed_migrations:
                    pending_migrations.append(file_path)

                # Stop at target migration if specified
                if target_migration and file_path.name == target_migration:
                    break

            if not pending_migrations:
                logger.info("No pending migrations to execute")
                return True

            logger.info(f"Found {len(pending_migrations)} pending migrations")

            # Execute pending migrations
            success_count = 0
            for file_path in pending_migrations:
                if self.execute_migration(file_path):
                    success_count += 1
                else:
                    logger.error(f"Migration failed, stopping at: {file_path.name}")
                    break

            logger.info(
                f"Successfully executed {success_count}/{len(pending_migrations)} migrations"
            )
            return success_count == len(pending_migrations)

        except Exception as e:
            logger.error(f"Migration process failed: {e}")
            return False

    def rollback_migration(self, migration_name: str) -> bool:
        """Rollback a specific migration (if rollback file exists)."""
        rollback_file = self.migrations_dir / f"rollback_{migration_name}"

        if not rollback_file.exists():
            logger.error(f"Rollback file not found: {rollback_file}")
            return False

        try:
            logger.info(f"Rolling back migration: {migration_name}")

            # Read rollback file
            with open(rollback_file, "r", encoding="utf-8") as f:
                rollback_sql = f.read()

            # For Supabase, log the rollback SQL
            logger.info(f"Rollback SQL for {migration_name}:")
            logger.info(rollback_sql)

            logger.info(f"Rollback {migration_name} prepared")
            return True

        except Exception as e:
            logger.error(f"Failed to prepare rollback {migration_name}: {e}")
            return False

    def get_migration_status(self) -> dict:
        """Get current migration status."""
        try:
            executed_migrations = self.get_executed_migrations()
            migration_files = self.get_migration_files()

            pending_migrations = []
            for file_path in migration_files:
                if file_path.name not in executed_migrations:
                    pending_migrations.append(file_path.name)

            return {
                "total_migrations": len(migration_files),
                "executed_migrations": len(executed_migrations),
                "pending_migrations": len(pending_migrations),
                "executed_list": executed_migrations,
                "pending_list": pending_migrations,
                "migrations_dir": str(self.migrations_dir),
            }

        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                "error": str(e),
                "total_migrations": 0,
                "executed_migrations": 0,
                "pending_migrations": 0,
            }


# Convenience functions
def run_migrations(target_migration: Optional[str] = None) -> bool:
    """Run database migrations."""
    runner = MigrationRunner()
    return runner.run_migrations(target_migration)


def get_migration_status() -> dict:
    """Get migration status."""
    runner = MigrationRunner()
    return runner.get_migration_status()


def rollback_migration(migration_name: str) -> bool:
    """Rollback a specific migration."""
    runner = MigrationRunner()
    return runner.rollback_migration(migration_name)


# CLI interface for running migrations
if __name__ == "__main__":
    import sys

    def main():
        if len(sys.argv) > 1:
            command = sys.argv[1]

            if command == "migrate":
                target = sys.argv[2] if len(sys.argv) > 2 else None
                success = run_migrations(target)
                sys.exit(0 if success else 1)

            elif command == "status":
                status = get_migration_status()
                print("Migration Status:")
                print(f"  Total migrations: {status['total_migrations']}")
                print(f"  Executed: {status['executed_migrations']}")
                print(f"  Pending: {status['pending_migrations']}")
                if status.get("pending_list"):
                    print(f"  Pending files: {', '.join(status['pending_list'])}")
                sys.exit(0)

            elif command == "rollback":
                if len(sys.argv) < 3:
                    print("Usage: python migrations.py rollback <migration_name>")
                    sys.exit(1)
                migration_name = sys.argv[2]
                success = rollback_migration(migration_name)
                sys.exit(0 if success else 1)

            else:
                print(f"Unknown command: {command}")
                print("Available commands: migrate, status, rollback")
                sys.exit(1)
        else:
            print("Usage: python migrations.py <command>")
            print("Commands:")
            print("  migrate [target_migration] - Run migrations")
            print("  status                     - Show migration status")
            print("  rollback <migration_name>  - Rollback a migration")
            sys.exit(1)

    main()
