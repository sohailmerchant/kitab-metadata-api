from api.models import Version, ReleaseVersion, ReleaseInfo, VersionwiseReuseStats
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Max
import csv


class Command(BaseCommand):
    def handle(self, **options):
        versionwise_stats_fp = "reuse_data/bookwise-stats-v7-2022_uni-dir.csv"
        release_code = "2022.2.7"
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
            version_obj = Version.objects.filter(
                version_code = row["id"]
            ).first()
            try:
                release_version_obj = ReleaseVersion.objects.get(
                    version = version_obj,
                    release_info = release_obj
                )
            except:
                print("No release version found for", version_obj)
                print("skipping...")
                continue
            #print(release_version_obj)
            vrs_obj, created = VersionwiseReuseStats.objects.get_or_create(
                release_version = release_version_obj,
                n_instances = row["instances"]
            )
        print("done")
            

