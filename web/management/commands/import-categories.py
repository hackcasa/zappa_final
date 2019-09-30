import csv
from django.core.management.base import BaseCommand
from tqdm import tqdm
from web.models import ProductCategory


class Command(BaseCommand):
    help = 'Import categories using CSV file from Core'

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
            existing_category_names = set(
                ProductCategory.objects.all().values_list('name', flat=True))

            print("Importing...")
            for item in tqdm(reader, total=line_count):
                if item['categoryname'] in existing_category_names:
                    existing += 1
                else:
                    new_category = ProductCategory(
                        name=item['categoryname'],
                        url=item['categoryurl'],
                        is_public=item['ispublic'],
                        introduction=item['categoryintroduction'],
                        title=item['title'],
                        metadescription=item['metadescription'],
                    )
                    new_category.id = item['categoryid']
                    new_category.save()
                    existing_category_names.add(new_category.name)
                    created += 1

            csvfile.seek(0)
            reader = csv.DictReader(csvfile)

            print("Linking...")
            created_links = 0
            categories = ProductCategory.objects.all()
            for item in tqdm(reader, total=line_count):
                if item['parentcategoryid'] and \
                        item['parentcategoryid'] != "NULL":
                    category = categories.filter(
                        pk=int(item['categoryid'])).first()
                    parent_category = categories.filter(
                        pk=int(item['parentcategoryid'])).first()

                    if category is not None and parent_category is not None:
                        category.parentcategory = parent_category
                        category.save()
                        created_links += 1

        category_count = ProductCategory.objects.all().count()

        print("*** REPORT ***")
        print(f"Items: {line_count}")
        print(f"Created categories: {created}")
        print(f"Already existing categories: {existing}")
        print(f"Current no of categories: {category_count}")
        print(f"Created category links: {created_links}")
