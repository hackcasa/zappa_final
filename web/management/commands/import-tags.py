import csv
from django.core.management.base import BaseCommand
from tqdm import tqdm
from web.models import Tag


class Command(BaseCommand):
    help = 'Import tags using CSV file from Core'

    def add_arguments(self, parser):
        parser.add_argument('file to import', type=str,
                            help='Specifies which file to import')

    def get_item_count(self, filename):
        counter_file = open(filename, encoding="utf8")
        counter = csv.DictReader(counter_file)
        line_count = len(list(counter))
        counter_file.close()
        return line_count

    def handle(self, *args, **options):
        filename = options['file to import']
        created = 0
        existing = 0
        line_count = self.get_item_count(filename)

        with open(filename, encoding="utf8") as csvfile:
            reader = csv.DictReader(csvfile)
            existing_tag_names = set(Tag.objects.all().values_list(
                'name', flat=True))

            for item in tqdm(reader, total=line_count):
                if item['TagName'] in existing_tag_names:
                    existing += 1
                else:
                    new_tag = Tag(
                        name=item['TagName']
                    )
                    new_tag.save()
                    existing_tag_names.add(new_tag.name)
                    created += 1

        print("*** REPORT ***")
        print(f"Items: {line_count}")
        print(f"Created tags: {created}")
        print(f"Already existing tags: {existing}")
        print(f"Current no of tags: {Tag.objects.all().count()}")
