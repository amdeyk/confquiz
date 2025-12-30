#!/usr/bin/env python3
"""
Test Data Generator for Quiz System
Creates sample teams, sessions, and a quiz master account for testing
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal, init_db
from models import User, Team, Session, Round, TeamSession, Score
from auth import get_password_hash
from config import settings


async def create_test_data():
    """Create test data for the quiz system"""

    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        print("\n1. Creating Quiz Master account...")

        # Check if quiz master already exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == "quizmaster"))
        if result.scalar_one_or_none():
            print("   ⚠️  Quiz Master 'quizmaster' already exists")
        else:
            qm = User(
                username="quizmaster",
                password_hash=get_password_hash("qm123"),
                role="quiz_master"
            )
            db.add(qm)
            print("   ✓ Created: quizmaster / qm123")

        await db.commit()

        print("\n2. Creating test teams...")

        teams_data = [
            {"name": "Team Alpha", "code": "ALPHA", "seat_order": 1},
            {"name": "Team Beta", "code": "BETA", "seat_order": 2},
            {"name": "Team Gamma", "code": "GAMMA", "seat_order": 3},
            {"name": "Team Delta", "code": "DELTA", "seat_order": 4},
            {"name": "Team Epsilon", "code": "EPSILON", "seat_order": 5},
        ]

        for team_data in teams_data:
            result = await db.execute(select(Team).where(Team.code == team_data["code"]))
            if result.scalar_one_or_none():
                print(f"   ⚠️  Team {team_data['code']} already exists")
            else:
                team = Team(**team_data)
                db.add(team)
                print(f"   ✓ Created: {team_data['name']} (Code: {team_data['code']})")

        await db.commit()

        print("\n3. Creating test session...")

        session_name = f"{settings.conference_name} - Quiz Competition" if settings.conference_name else "Test Quiz Session"

        result = await db.execute(select(Session).where(Session.name == session_name))
        if result.scalar_one_or_none():
            print(f"   ⚠️  Session '{session_name}' already exists")
        else:
            session = Session(
                name=session_name,
                banner_text=settings.conference_name or "Quiz Competition",
                status="live"
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            print("   ✓ Created: Test Quiz Session (ID: {})".format(session.id))

            print("\n4. Creating test rounds...")

            rounds_data = [
                {
                    "name": "Round 1: General Knowledge",
                    "type": "normal",
                    "timer_default_ms": 30000,
                    "scoring_presets": {"positive": [10, 5], "negative": [-5]},
                    "order_index": 1
                },
                {
                    "name": "Round 2: Fastest Finger",
                    "type": "fastest",
                    "timer_default_ms": 20000,
                    "scoring_presets": {"positive": [15, 10, 5], "negative": []},
                    "order_index": 2
                },
                {
                    "name": "Round 3: Bonus Round",
                    "type": "bonus",
                    "timer_default_ms": 45000,
                    "scoring_presets": {"positive": [20, 10], "negative": [-10]},
                    "order_index": 3
                }
            ]

            for round_data in rounds_data:
                round_obj = Round(session_id=session.id, **round_data)
                db.add(round_obj)
                print(f"   ✓ Created: {round_data['name']}")

            await db.commit()

            print("\n5. Assigning teams to session...")

            # Get all teams
            result = await db.execute(select(Team))
            teams = result.scalars().all()

            for team in teams:
                team_session = TeamSession(
                    session_id=session.id,
                    team_id=team.id,
                    starting_score=0
                )
                db.add(team_session)
                await db.flush()

                # Create score entry
                score = Score(
                    team_session_id=team_session.id,
                    total=0
                )
                db.add(score)
                print(f"   ✓ Assigned: {team.name}")

            await db.commit()

        print("\n" + "=" * 50)
        print("Test Data Creation Complete!")
        print("=" * 50)
        print("\nAccounts created:")
        print("  Admin:")
        print("    Username: admin")
        print("    Password: admin123")
        print()
        print("  Quiz Master:")
        print("    Username: quizmaster")
        print("    Password: qm123")
        print()
        print("Teams created:")
        print("  - Team Alpha   (Code: ALPHA)")
        print("  - Team Beta    (Code: BETA)")
        print("  - Team Gamma   (Code: GAMMA)")
        print("  - Team Delta   (Code: DELTA)")
        print("  - Team Epsilon (Code: EPSILON)")
        print()
        print("Session created:")
        print(f"  - {session_name} (Status: live)")
        print("  - 3 Rounds configured")
        print("  - All teams assigned")
        print()
        print("You can now start the server and test!")
        print("  python main.py")


if __name__ == "__main__":
    asyncio.run(create_test_data())
