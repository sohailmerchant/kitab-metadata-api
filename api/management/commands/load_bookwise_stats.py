from api.models import Version, ReleaseVersion, ReleaseInfo, VersionwiseReuseStats
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Max
import csv


class Command(BaseCommand):
    def handle(self, **options):
        #VersionwiseReuseStats.objects.all().delete()
        #versionwise_stats_fp = "reuse_data/bookwise-stats-v7-2022_uni-dir.csv"
        #release_code = "2022.2.7"
        versionwise_stats_fp = "reuse_data/bookwise-stats-v8_uni-dir.csv"
        release_code = "2023.1.8"
        main(versionwise_stats_fp, release_code)


def main(versionwise_stats_fp, release_code):
    release_obj = ReleaseInfo.objects.get(
        release_code = release_code
    );
    print(release_obj)
    fieldnames = ['id', 'instances']
    with open(versionwise_stats_fp, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
        header = next(reader)

        for row in reader:
            try:
                release_version_obj = ReleaseVersion.objects.get(
                    version__version_code = row["id"],
                    release_info = release_obj
                )
            except Exception as e:
                print(e)
                print(row["id"])
                print(release_obj)
                print("No release version found for", row["id"])
                print("skipping...")
                continue
            vrs_obj, created = VersionwiseReuseStats.objects.get_or_create(
                release_version = release_version_obj,
                n_instances = row["instances"]
            )
        print("done")
            

