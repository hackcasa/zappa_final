import csv
from django.core.management.base import BaseCommand
from tqdm import tqdm
from web.models import Tag, Product


class Command(BaseCommand):
    help = 'Import productcategory-tag connections using CSV file from Core'

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
            existing_products = set(Product.objects
                                    .all()
                                    .values_list(
                                                 'article__gtin',
                                                 flat=True
                                                 ))

            for item in tqdm(reader, total=line_count):
                if item['TagName'] in existing_tag_names and \
                        item['EanCode'] in existing_products:
                    gtin = item['EanCode']
                    product = Product.objects.get(article__gtin=gtin)
                    tag = Tag.objects.get(name=item['TagName'])
                    if tag not in product.tags.all():
                        created += 1
                        product.tags.add(tag)

                    else:
                        existing += 1

                else:
                    mismatched += 1

        print("*** REPORT ***")
        print(f"Items: {line_count}")
        print(f"Created product-tag connections: {created}")
        print(f"Mismatched product-tag connections: {mismatched}")
        print(f"Already existing product-tag connections: {existing}")
