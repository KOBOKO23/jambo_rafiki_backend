from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sponsorships', '0002_sponsorshipinterest_delete_progressreport_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='sponsorship',
            constraint=models.UniqueConstraint(fields=('child', 'sponsor'), name='uniq_child_sponsor_pair'),
        ),
    ]
