from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lga', '0007_lga_tier_licencetype_bylaw_reference_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=40, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(blank=True, max_length=30)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['order', 'name'],
                'verbose_name_plural': 'business activities',
            },
        ),
        migrations.AddField(
            model_name='licencetype',
            name='activity',
            field=models.ForeignKey(
                blank=True,
                help_text='Business activity this licence covers (BUSINESS-category licences).',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='licence_types',
                to='lga.businessactivity',
            ),
        ),
    ]
