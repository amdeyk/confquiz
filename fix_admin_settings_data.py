#!/usr/bin/env python3
"""
Fix script to insert missing admin_settings data
Run this if the admin_settings table exists but has no/incomplete data
"""
import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models import AdminSettings

async def fix_admin_settings():
    """Insert or update default admin settings"""
    print("=" * 60)
    print("Fixing Admin Settings Data")
    print("=" * 60)
    print()

    async with AsyncSessionLocal() as session:
        try:
            # Check existing settings
            result = await session.execute(select(AdminSettings))
            existing_settings = result.scalars().all()

            print(f"Current admin_settings count: {len(existing_settings)}")
            if existing_settings:
                print("\nExisting settings:")
                for setting in existing_settings:
                    print(f"  - {setting.setting_key} = {setting.setting_value}")
            print()

            # Define required settings
            required_settings = {
                "display_mode": "png_slides",
                "screen_share_fps": "10",
                "screen_share_quality": "0.7"
            }

            # Check which settings are missing
            existing_keys = {s.setting_key for s in existing_settings}
            missing_keys = set(required_settings.keys()) - existing_keys

            if not missing_keys:
                print("✓ All required settings exist!")
                print()
                return

            print(f"Missing settings: {', '.join(missing_keys)}")
            print()

            # Insert missing settings
            inserted_count = 0
            for key in missing_keys:
                value = required_settings[key]
                new_setting = AdminSettings(
                    setting_key=key,
                    setting_value=value
                )
                session.add(new_setting)
                print(f"✓ Inserting: {key} = {value}")
                inserted_count += 1

            await session.commit()

            print()
            print("=" * 60)
            print(f"✓ Successfully inserted {inserted_count} settings!")
            print("=" * 60)
            print()

            # Verify final state
            result = await session.execute(select(AdminSettings))
            all_settings = result.scalars().all()

            print("Final admin_settings:")
            for setting in all_settings:
                print(f"  - {setting.setting_key} = {setting.setting_value}")
            print()

        except Exception as e:
            await session.rollback()
            print(f"✗ Error: {e}")
            raise

if __name__ == "__main__":
    print()
    asyncio.run(fix_admin_settings())
    print("Done!")
    print()
