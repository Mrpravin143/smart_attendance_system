# Generated by Django 5.2.3 on 2025-06-24 04:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0007_attendance_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='timestamp',
            field=models.DateTimeField(),
        ),
    ]
