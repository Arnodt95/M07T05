from django.db import migrations


def seed_publishers(apps, schema_editor):
    """
    Seed a default set of publishers.

    This ensures that journalists always see a populated list of publishers
    in the article submission form. If a publisher already exists, we do not
    create duplicates.
    """
    Publisher = apps.get_model("news_app", "Publisher")

    defaults = [
        ("Daily Sentinel", "National and international coverage."),
        ("Cape Chronicle", "Local news and community reporting."),
        ("Tech Dispatch", "Technology and startup journalism."),
        ("Global Brief", "World affairs and geopolitics."),
        ("Finance Gazette", "Markets, business, and economy."),
    ]

    for name, description in defaults:
        Publisher.objects.get_or_create(
            name=name,
            defaults={"description": description},
        )


def unseed_publishers(apps, schema_editor):
    """
    Reverse the seed operation by deleting only the seeded publishers.
    """
    Publisher = apps.get_model("news_app", "Publisher")
    names = [
        "Daily Sentinel",
        "Cape Chronicle",
        "Tech Dispatch",
        "Global Brief",
        "Finance Gazette",
    ]
    Publisher.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("news_app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_publishers, reverse_code=unseed_publishers),
    ]
