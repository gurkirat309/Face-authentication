# Generated by Django 5.2 on 2025-04-20 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userimages",
            name="face_encoding",
            field=models.BinaryField(null=True),
        ),
    ]
