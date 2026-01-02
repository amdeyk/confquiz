"""
Migration: Add AdminSettings table and insert default values
Created: 2026-01-02

This migration:
1. Creates admin_settings table (via Base.metadata.create_all)
2. Inserts default settings for display mode
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal, init_db
from models import AdminSettings


async def run_migration():
    """Run migration to add admin settings"""

    # Create tables (including new admin_settings table)
    print("Creating tables...")
    await init_db()

    # Insert default settings
    print("Inserting default admin settings...")
    async with AsyncSessionLocal() as session:
        try:
            # Check if settings already exist
            result = await session.execute(select(AdminSettings))
            existing = result.scalars().all()

            if existing:
                print(f"Admin settings already exist ({len(existing)} rows). Skipping insertion.")
                return

            # Insert default settings
            default_settings = [
                AdminSettings(
                    setting_key="display_mode",
                    setting_value="png_slides"
                ),
                AdminSettings(
                    setting_key="screen_share_fps",
                    setting_value="10"
                ),
                AdminSettings(
                    setting_key="screen_share_quality",
                    setting_value="0.7"
                )
            ]

            for setting in default_settings:
                session.add(setting)

            await session.commit()
            print(f"Inserted {len(default_settings)} default admin settings:")
            for setting in default_settings:
                print(f"  - {setting.setting_key} = {setting.setting_value}")

        except Exception as e:
            await session.rollback()
            print(f"Error during migration: {e}")
            raise


if __name__ == "__main__":
    print("Running migration: 001_add_admin_settings")
    asyncio.run(run_migration())
    print("Migration completed successfully!")
