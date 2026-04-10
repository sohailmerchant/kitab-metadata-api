"""Load text reuse statistics (n_instances, n_versions) for each text version.

NB: this has now been moved into the load_release_from_yml script."""

from api.models import Version, ReleaseVersion, ReleaseInfo, VersionwiseReuseStats
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Max
import csv


class Command(BaseCommand):
    def handle(self, **options):

        #VersionwiseReuseStats.objects.all().delete()

        #versionwise_stats_fp = "reuse_data/bookwise-stats-v2021.2.5_uni-dir.csv"
        #release_code = "2021.2.5"
        #versionwise_stats_fp = "reuse_data/bookwise-stats-v2022.1.6_uni-dir.csv"
        #release_code = "2022.1.6"
        #versionwise_stats_fp = "reuse_data/bookwise-stats-v2022.2.7_uni-dir.csv"
        #release_code = "2022.2.7"
        #versionwise_stats_fp = "reuse_data/bookwise-stats-v2023.1.8_uni-dir.csv"
        #release_code = "2023.1.8"
        
        release_codes = [
            "2021.2.5", 
            "2022.1.6", 
            "2022.2.7",
            "2023.1.8",
            "2025.1.9",
        ]

        for release_code in release_codes:
            versionwise_stats_fp = f"reuse_data/bookwise-stats-v{release_code}_uni-dir.csv"
            main(versionwise_stats_fp, release_code)


def main(versionwise_stats_fp, release_code):
    release_obj = ReleaseInfo.objects.get(
        release_code = release_code
    );
    print(release_obj)
    n_created = 0
    fieldnames = ['id', 'instances', 'book_cnt']
    with open(versionwise_stats_fp, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
        header = next(reader)
        i=0
        for row in reader:
            i += 1
            if i % 100 == 0:
                print(i, "items processed...")
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
                n_instances = row["instances"],
                n_versions = row["book_cnt"]
            )
            if created:
                n_created += 1
        
        print(f"done uploading reuse stats for {release_code}. Added {n_created} item(s)")

            

