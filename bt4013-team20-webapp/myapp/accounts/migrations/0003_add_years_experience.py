from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_add_notifications_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='years_experience',
            field=models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True),
        ),
    ]
