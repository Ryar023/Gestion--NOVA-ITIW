# Generated migration to fix especialidad field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_add_rol_to_solicitudcuenta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='docente',
            name='especialidad',
            field=models.CharField(max_length=100),
        ),
    ]
