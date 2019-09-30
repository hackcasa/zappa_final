import os
import re
import csv
import boto3
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
from django.core.management.base import BaseCommand
from tqdm import tqdm
from web.models import Article, ArticleImage, \
    Product, ProductImage, ProductDetail, Tag


class Command(BaseCommand):
    help = 'Import products using CSV file from Core'

    def add_arguments(self, parser):
        parser.add_argument('file to import', type=str,
                            help='Specifies which file to import')

        parser.add_argument(
            '-a',
            '--access-key-id',
            type=str,
            help='Access key to AWS Prod',
        )

        parser.add_argument(
            '-s',
            '--secret-access-key',
            type=str,
            help='Secret Access Key to AWS Prod',
        )

    def __init__(self):
        self.report = defaultdict(list)
        self.datetime_format = '%Y-%m-%d %H:%M:%S'

    def get_item_count(self, filename):
        counter_file = open(filename, encoding="utf-8")
        counter = csv.DictReader(counter_file)
        line_count = len(list(counter))
        counter_file.close()
        return line_count

    def handle(self, *args, **options):
        filename = options['file to import']

        if options['access_key_id']:
            self.prod_s3_client = boto3.client(
                's3',
                aws_access_key_id=options['access_key_id'],
                aws_secret_access_key=options['secret_access_key']
            )
        else:
            self.prod_s3_client = boto3.client('s3')

        self.s3_client = boto3.client('s3')

        line_count = self.get_item_count(filename)

        with open(filename, encoding="utf-8") as csvfile:
            season_tags = self.get_or_create_season_tags()
            reader = csv.DictReader(csvfile)
            for csv_article in tqdm(reader, total=line_count):
                #try:
                    gtin = csv_article['EanCode'].zfill(14)

                    # Get article
                    article = Article.objects.filter(gtin=gtin).first()

                    if article is None:
                        self.report[gtin].append("Creating article")
                        article = self.create_article(
                            csv_article, gtin)

                    # Get or create product
                    product = (Product.objects
                               .filter(article__gtin=gtin).first())

                    if product is None:
                        self.report[gtin].append("Creating product")
                        product = Product()
                        product.article = article
                        product.source = "mathem"
                        product.product_id = csv_article['productid']
                    else:
                        self.report[gtin].append("Product already exists")

                    if csv_article['LastReceiptDay']:
                        product.last_receipt_day = int(
                            csv_article['LastReceiptDay'])

                    if csv_article['LastSalesDay']:
                        product.last_sales_day = int(
                            csv_article['LastSalesDay'])

                    product.product_type = 'Normal'
                    if csv_article['TruckRouteOpt'] == 'A':
                        product.product_type = 'Nightorder'
                    if csv_article['TruckRouteOpt'] == 'X':
                        product.product_type = 'Crossdocking'

                    if csv_article['Season']:
                        seasons = csv_article['Season'].split('.')

                        for season in seasons:
                            if season in season_tags:
                                product.tags.add(season_tags[season])

                    # Overwrite fields if it's not the data we already have
                    clean_productdesc = self.clean(
                        csv_article['ProductDescription'])
                    clean_nutdesc = self.clean(
                        csv_article['NutritionDescription'])
                    clean_ingdesc = self.clean(
                        csv_article['IngredientsDescription'])

                    if (product.description != clean_productdesc and
                            product.article.description != clean_productdesc):
                        product.description = clean_productdesc
                        self.report[gtin].append("Updated description")

                    if (product.nutrition_description != clean_nutdesc and
                            product.article.nutrition_description !=
                            clean_nutdesc):
                        product.nutrition_description = clean_nutdesc
                        self.report[gtin].append(
                            "Updated nutrition_description")

                    if (product.ingredient_description != clean_ingdesc and
                            product.article.ingredient_description !=
                            clean_ingdesc):
                        product.article.ingredient_description = clean_ingdesc
                        self.report[gtin].append(
                            "Updated ingredient_description")

                    if (product.name != csv_article['ProductName'] and
                            product.article.name !=
                            csv_article['ProductName']):
                        product.name = csv_article['ProductName']
                        self.report[gtin].append("Updated name")

                    if product.article.brand_name != csv_article[
                            'suppliername']:
                        product.brand_name = csv_article[
                            'suppliername']
                        self.report[gtin].append("Updated brand_name")

                    # Save product
                    product.save()

                    # Get images from article (if any)
                    product_images = (ProductImage.objects
                                      .values_list('filename', flat=True)
                                      .filter(product__article__gtin=gtin))

                    for image in ArticleImage.objects.filter(gtin=gtin):
                        if image.filename not in product_images:
                            new_image = ProductImage(
                                angle=image.angle,
                                source=image.source,
                                product=product,
                                filename=image.filename
                            )
                            new_image.save()
                            self.report[gtin].append(
                                "Importing image from article (" +
                                image.filename +
                                ')')

                    for store_id, name in ProductDetail.STORES:
                        storeItem = ProductDetail.objects.filter(
                            store=store_id,
                            product=product).first()

                        if storeItem is None:
                            storeItem = ProductDetail(store=store_id)
                            self.report[gtin].append(
                                "ProductDetails for store " +
                                str(store_id) +
                                " created")
                        else:
                            self.report[gtin].append(
                                "ProductDetails for store " +
                                str(store_id) +
                                " found")

                        csv_price = round(
                            float(csv_article['price'+str(store_id)]),
                            13)
                        if storeItem.price != csv_price:
                            self.report[gtin].append(
                                "Price updated for " +
                                str(store_id) +
                                " (" +
                                str(storeItem.price) +
                                " => " +
                                str(csv_price) +
                                ")")
                            storeItem.price = csv_price

                        if(bool(csv_article['NewProduct'])):
                            storeItem.first_enabled = timezone.now()
                        else:
                            storeItem.first_enabled = (timezone.now()
                                                       - timedelta(days=31))
                        storeItem.enabled = 1
                        storeItem.orderfactor = bool(
                            csv_article['Orderfactor'])
                        storeItem.product = product
                        storeItem.save()

                #except Exception as e:
                #    print("Exception")
                #    print(e)
                #    pass

        print("*** REPORT ***")
        for gtin, gtin_report in dict(self.report).items():
            print(gtin)
            if (gtin_report == [
                    'Product already exists',
                    'ProductDetails for store 10 found',
                    'ProductDetails for store 14 found',
                    'ProductDetails for store 16 found']):
                print(' - Product exists. No changes')
            else:
                for gtin_report_item in gtin_report:
                    print(' -', gtin_report_item)
            print('')

    def get_or_create_season_tags(self):
        tag_names = {
            'COB': 'Clas Ohlson',
            'MK': 'Matkasse',
            'G': 'Grillartiklar',
            'H': 'Halloweenartiklar',
            'J': 'Julartiklar',
            'JB': 'Artiklar som säljs året runt, men mest runt jul',
            'M': 'Midsommarartiklar',
            'MB': 'Artiklar som säljs året runt, men mest runt midsommar',
            'N': 'Nyårsartiklar',
            'NB': 'Artiklar som säljs året runt, men mest runt nyår',
            'P': 'Påskartiklar',
            'PB': 'Artiklar som säljs året runt, men mest runt påsk',
            'S': 'Sommarartiklar',
            'ST': 'Sommartorget'
        }

        tag_dict = {}

        for season, tag_name in tag_names.items():
            tag = Tag.objects.filter(name=tag_name).first()
            if tag is not None:
                tag_dict[season] = tag

        return tag_dict

    def create_article(
            self, csv_item, gtin):
        self.datetime_format = '%Y-%m-%d %H:%M:%S'

        storage_type = 'Unspecified'
        if csv_item['StorageType'] == 'FROZEN':
            storage_type = 'Frozen'

        article = Article(
            consumer_unit=True,
            descriptor_code='BASE_UNIT_OR_EACH',
            gtin=gtin,
            creation_date=datetime
            .strptime(
                csv_item['CreationDate'],
                self.datetime_format)
            .astimezone(),
            name=csv_item['ProductName'],
            description=self.clean(csv_item[
                'ProductDescription']),
            last_modified=datetime
            .strptime(
                csv_item['LastmodifiedDate'],
                self.datetime_format)
            .astimezone(),
            brand_name=csv_item['suppliername'],
            source='mathem',
            vat=csv_item['VatRate'],
            nutrition_description=self.clean(csv_item[
                'NutritionDescription']),
            ingredient_description=self.clean(csv_item[
                'IngredientsDescription']),

            storage_type=storage_type,
        )

        if csv_item['Volume']:
            article.volume_dm3 = float(csv_item['Volume'])
        if csv_item['Weight']:
            article.weight_g = float(csv_item['Weight']) * 1000
        if csv_item['Height']:
            article.height_mm = float(csv_item['Height'])
        if csv_item['Length']:
            article.length_mm = float(csv_item['Length'])
        if csv_item['Width']:
            article.width_mm = float(csv_item['Width'])
        if csv_item['AdultProduct']:
            article.adult_product = bool(csv_item['AdultProduct'])
        if csv_item['Origin']:
            article.origin = int(csv_item['Origin'])
        if csv_item['RecycleFee']:
            article.recycle_fee = float(csv_item['RecycleFee'])

        # Save Article
        article.save()

        # If ImageUrl is set, get from prod bucket
        if csv_item['ImageUrl']:
            self.report[gtin].append(
                "Fetching image (" +
                csv_item['ImageUrl'] +
                ") from prod bucket")
            try:
                prod_image_response = self.prod_s3_client.get_object(
                    Bucket='env-static-files-s3bucket-1wlxbug76hqfd',
                    Key='shared/images/products/original/' +
                        csv_item['ImageUrl']
                )

                # Put image in pim bucket
                image_dest_filename = article.gtin + ".jpg"

                if (re.match(
                        r"^[0-9]{14}(_[a-zA-Z][0-9][a-zA-Z][0-9])?.",
                        csv_item['ImageUrl'])):
                    image_dest_filename = csv_item['ImageUrl']

                self.s3_client.put_object(
                    Bucket=os.environ['pim-validoo-item-BucketName'],
                    Key='in/' + image_dest_filename,
                    Body=prod_image_response['Body'].read()
                )

                self.report[gtin].append(
                    "Saving image as " +
                    image_dest_filename)

                # Create new ArtileImage
                article_image = ArticleImage(
                    gtin=article.gtin,
                    filename=image_dest_filename,
                    source='mathem',
                    article=article
                )

                # Save ArticleImage
                article_image.save()
                self.report[gtin].append('Image saved')
            except Exception as e:
                self.report[gtin].append('Failed: ' + type(e).__name__)
                pass

        return article

    def clean(self, dirty):
        cleaned = re.sub('<[^<]+?>', ' ', dirty)
        cleaned = re.sub(' {2,}', ' ', cleaned)
        if cleaned == 'NULL':
            cleaned = ''
        return cleaned
