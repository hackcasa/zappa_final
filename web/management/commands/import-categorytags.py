import csv
from django.core.management.base import BaseCommand
from tqdm import tqdm
from web.models import Tag, ProductCategory


class Command(BaseCommand):
    help = 'Import product-tag connections using CSV file from Core'

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
        mismatched = 0
        line_count = self.get_item_count(filename)

        with open(filename, encoding="utf8") as csvfile:
            reader = csv.DictReader(csvfile)
            existing_tag_names = set(Tag.objects.all().values_list(
                'name', flat=True))
            existing_categories = set(ProductCategory.objects
                                      .all()
                                      .values_list('id', flat=True))

            for item in tqdm(reader, total=line_count):
                casted_id = int(item['categoryid'])
                if item['TagName'] in existing_tag_names and \
                        casted_id in existing_categories:
                        created += 1
                        category = ProductCategory.objects.get(id=casted_id)
                        tag = Tag.objects.get(name=item['TagName'])
                        if tag not in category.tags.all():
                            category.tags.add(tag)
                            category.save()
                        else:
                            existing += 1

                else:
                    mismatched += 1

        print("*** REPORT ***")
        print(f"Items: {line_count}")
        print(f"Created category-tag connections: {created}")
        print(f"Mismatched category-tag connections: {mismatched}")
        print(f"Already existing category-tag connections: {existing}")
