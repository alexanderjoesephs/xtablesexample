# Generated by Django 5.0 on 2023-12-17 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timestablesapp', '0018_remove_student_classes_delete_times_table_assigned_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='classes',
        ),
        migrations.AddField(
            model_name='student',
            name='classes',
            field=models.ManyToManyField(null=True, to='timestablesapp.teacher'),
        ),
    ]