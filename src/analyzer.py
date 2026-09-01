#!/usr/bin/env python3

from sqlalchemy import func

from src.app import app, db, WikipediaEdit


def analyze_edits():
    """Analyze Wikipedia edits stored in the database."""

    with app.app_context():

        total_edits = WikipediaEdit.query.count()

        if total_edits == 0:
            print("No Wikipedia edits are stored in the database.")
            return

        # Number of distinct Wikipedia pages
        unique_pages = (
            db.session.query(
                func.count(func.distinct(WikipediaEdit.title))
            )
            .scalar()
        )

        # Human vs bot edits
        bot_edits = (
            WikipediaEdit.query
            .filter(WikipediaEdit.bot.is_(True))
            .count()
        )

        human_edits = total_edits - bot_edits

        bot_percentage = (bot_edits / total_edits) * 100

        # Simple average
        average_edits_per_page = total_edits / unique_pages

        # Most edited pages
        top_pages = (
            db.session.query(
                WikipediaEdit.title,
                func.count(WikipediaEdit.id).label("edit_count")
            )
            .group_by(WikipediaEdit.title)
            .order_by(func.count(WikipediaEdit.id).desc())
            .limit(5)
            .all()
        )

        # Most active editors
        top_editors = (
            db.session.query(
                WikipediaEdit.user,
                func.count(WikipediaEdit.id).label("edit_count")
            )
            .filter(WikipediaEdit.user.isnot(None))
            .group_by(WikipediaEdit.user)
            .order_by(func.count(WikipediaEdit.id).desc())
            .limit(5)
            .all()
        )

        print("\nWIKIPEDIA PULSE ANALYSIS")
        print("=" * 40)

        print(f"\nTotal edits: {total_edits}")
        print(f"Unique pages: {unique_pages}")
        print(f"Average edits per page: {average_edits_per_page:.2f}")

        print(f"\nHuman edits: {human_edits}")
        print(f"Bot edits: {bot_edits}")
        print(f"Bot percentage: {bot_percentage:.1f}%")

        print("\nTop 5 most edited pages:")

        for number, (title, count) in enumerate(top_pages, start=1):
            print(f"{number}. {title}: {count} edits")

        print("\nTop 5 most active editors:")

        for number, (user, count) in enumerate(top_editors, start=1):
            print(f"{number}. {user}: {count} edits")


if __name__ == "__main__":
    analyze_edits()