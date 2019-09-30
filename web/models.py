from datetime import datetime, timedelta
from django.db import models
from django.db.models import Q
from django.contrib.postgres.fields import JSONField
from simple_history.models import HistoricalRecords
from web.sns import notify_productcategory_change
from web.managers import ArticleManager
from web.gs1_code_lists import Allergen, FishingZone, Origin, T3780


class Storage():
    TYPE = (
        ("Colonial", "Colonial"),
        ("Refrigerated", "Refrigerated"),
        ("Frozen", "Frozen"),
        ("Unspecified", "Unspecified")
    )


class Article(models.Model):

    TYPES = (
        ("BASE_UNIT_OR_EACH", "BASE_UNIT_OR_EACH"),
        ("CASE", "CASE"),
        ("1/4", "1/4"),
        ("1/2", "1/2"),
        ("PALLET", "PALLET")
    )

    VATS = [6.0, 12.0, 25.0]

    consumer_unit = models.BooleanField(
        default=False, verbose_name="Consumer unit",
        help_text="Should this article be available to consumers?")
    descriptor_code = models.CharField(
        choices=TYPES, max_length=64, verbose_name="Type",
        help_text="What type of article is this?")
    gtin = models.CharField(max_length=14, unique=True,
                            default=0, verbose_name="GTIN")
    child_gtin = models.CharField(
        blank=True, max_length=14, default="",
        verbose_name="Child GTIN",
        help_text="If this is a package, what GTIN does the package contain?")
    quantity_of_lower_layer = models.IntegerField(
        blank=True, default=0, verbose_name="Quantity of Lower Layer",
        help_text="How many of that GTIN does it contain?")
    category = models.CharField(
        max_length=100, verbose_name="Category",
        help_text="Industri category (GS1)")
    weight_g = models.FloatField(default=0, verbose_name="Weight (g)")
    height_mm = models.FloatField(default=0, verbose_name="Height (mm)")
    length_mm = models.FloatField(default=0, verbose_name="Length (mm)")
    width_mm = models.FloatField(default=0, verbose_name="Depth (mm)")
    volume_dm3 = models.FloatField(max_length=10, default=0,
                                   verbose_name="Volume (dm³)")
    net_content = models.FloatField(null=True, verbose_name="Net Content")
    net_content_unit_code = models.CharField(null=True,
                                             max_length=10, verbose_name="Net Content Unit Code", choices=list(T3780.UNIT_CODES.items()))
    creation_date = models.DateTimeField(verbose_name="Creation date")
    name = models.CharField(max_length=100, verbose_name="Name")
    description = models.TextField(blank=True, verbose_name="Description")
    recycle_fee = models.FloatField(default=0.0, verbose_name="Recycle Fee")
    last_modified = models.DateTimeField(
        auto_now=False, verbose_name="Last modified")
    brand_name = models.CharField(max_length=256, verbose_name="Brand")
    source = models.CharField(max_length=40, verbose_name="Source", blank=True)
    vat = models.FloatField(
        default=0, verbose_name="VAT", choices=zip([0.0] + VATS, [0.0] + VATS))
    adult_product = models.BooleanField(
        default=False, verbose_name="Adult Product")
    marketing_message = models.TextField(
        blank=True, verbose_name="Marketing message")
    nutrition_description = models.TextField(
        blank=True, verbose_name="Nutrition Description")
    ingredient_description = models.TextField(
        blank=True, verbose_name="Ingredient Description")
    allergen_statement = models.TextField(
        verbose_name="Allergen Statement", blank=True, default='')
    allergens = JSONField(
        verbose_name="Allergens", blank=True, default=dict)
    origin = models.IntegerField(
        blank=True, verbose_name="Origin", choices=Origin.COUNTRY, default=0)
    fishing_zone = models.IntegerField(
        blank=True, choices=FishingZone.AREA, default=0)
    whitelisted = models.BooleanField(
        default=False, verbose_name="Whitelisted")
    history = HistoricalRecords(
        excluded_fields=['creation_date', 'last_modified'])
    objects = ArticleManager()
    storage_type = models.CharField(
        max_length=64, choices=Storage.TYPE,
        default="Unspecified", verbose_name="Storage Type")
    storage_temperature_range = models.CharField(
        max_length=64, blank=True,
        default="", verbose_name="Storage Temperature Range")

    class Meta:
        indexes = [
            models.Index(fields=['category', 'name', 'gtin', 'source'])
        ]
        ordering = ['-id']

    def is_valid(self):
        if self.whitelisted or not self.consumer_unit:
            return True

        if (self.articleimage_set.count() > 0 and
                self.weight_g > 0 and
                self.height_mm > 0 and
                self.length_mm > 0 and
                self.width_mm > 0 and
                self.volume_dm3 > 0 and
                self.name != '' and
                self.brand_name != '' and
                self.marketing_message != '' and
                self.nutrition_description != '' and
                self.ingredient_description != ''):
            if ((self.consumer_unit and self.vat in Article.VATS) or
                    not self.consumer_unit):
                return True
        return False

    def get_allergens(self):
        allergen_list = []
        for allergen in self.allergens:
            allergen_list.append(
                Allergen.get_text(allergen)
            )
        return ", ".join(allergen_list)

    def save(self, *args, **kwargs):
        super(Article, self).save(*args, **kwargs)

        # Link unlinked images
        images = ArticleImage.objects.filter(
            article=None,
            gtin=self.gtin
        )

        for image in images:
            image.article = self
            image.save()

        # Save products to trigger validation check
        products = Product.objects.filter(article__gtin=self.gtin)
        for product in products:
            product.save_without_historical_record()

    def post_delete(sender, instance, using):
        products = Product.objects.filter(article__gtin=instance.gtin)
        for product in products:
            product.save_without_historical_record()

    def get_image(self):
        if self.descriptor_code == "PALLET":
            return "PALLET"

        if (self.descriptor_code in ["CASE", "1/4", "1/2"] and
                not self.consumer_unit):
            return "CASE"

        return self.articleimage_set.first()

    def get_related(self):
        related = self.get_related_rec()
        related = filter(lambda x: x.id != self.id, related)
        return sorted(related, key=lambda package: package.gtin)

    def get_related_rec(self, packages=[]):
        child = Article.objects.filter(gtin=self.child_gtin).first()
        parents = list(Article.objects.filter(child_gtin=self.gtin))

        if child is not None:
            parents.append(child)

        for p in parents:
            if p not in packages:
                packages.append(p)
                p.get_related_rec(packages)

        return packages


class ArticleImage(models.Model):
    gtin = models.CharField(max_length=14, default=0, verbose_name="GTIN")
    angle = models.CharField(max_length=6, blank=True, verbose_name="Angle")
    filename = models.CharField(max_length=256, verbose_name="Filename")
    creation_date = models.DateTimeField(auto_now_add=True,
                                         verbose_name="Created")
    source = models.CharField(max_length=40, verbose_name="Source", blank=True)
    history = HistoricalRecords(excluded_fields=['creation_date'])
    article = models.ForeignKey(Article, on_delete=models.DO_NOTHING,
                                blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, blank=True,
                                         verbose_name='Last Modified')

    def save(self, *args, **kwargs):
        if (self.article is None and
                Article.objects.filter(gtin=self.gtin).exists()):
            article = Article.objects.get(gtin=self.gtin)
            self.article = article

        super(ArticleImage, self).save(*args, **kwargs)


class ProductCategory(models.Model):
    name = models.CharField(max_length=128,
                            verbose_name='Category Name', unique=True)
    parentcategory = models.ForeignKey("self",
                                       null=True, blank=True,
                                       on_delete=models.DO_NOTHING,
                                       verbose_name='Parent Category')
    url = models.CharField(max_length=256, verbose_name='Category URL')
    is_public = models.BooleanField(verbose_name='Is Public')
    introduction = models.TextField(verbose_name='Intro')
    title = models.CharField(max_length=256, verbose_name='Title')
    metadescription = models.CharField(max_length=1024,
                                       null=True,
                                       blank=True,
                                       verbose_name='Meta Description')
    removed_date = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name='Removed')
    creation_date = models.DateTimeField(auto_now_add=True,
                                         verbose_name='Created')
    last_modified = models.DateTimeField(auto_now=True, blank=True,
                                         verbose_name='Last Modified')

    tags = models.ManyToManyField(
        'Tag', related_name='categories', blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        notify_productcategory_change(self)
        super(ProductCategory, self).save()


class MerchantArticle(models.Model):
    article_gtin = models.CharField(null=True, max_length=14,
                                    verbose_name="Article GTIN")
    article = models.ForeignKey(
        Article, null=True, blank=True, on_delete=models.DO_NOTHING,
        related_name='merchant_articles')
    merchant_name = models.CharField(
        max_length=256, verbose_name='Merchant name')
    external_id = models.CharField(max_length=256, verbose_name='External ID')
    availability_status = models.CharField(
        max_length=100, default='', verbose_name='Availability status')
    listed = models.CharField(max_length=20, blank=True, verbose_name='Listed')
    last_date_to_order = models.CharField(
        max_length=20, blank=True, verbose_name='Last date to order')
    price = models.FloatField(max_length=10, default=0, verbose_name="Price")
    currency = models.CharField(max_length=5, default="SEK", verbose_name="Currency")
    sales_price = models.FloatField(max_length=10, default=0, verbose_name="Sales Price")
    sales_price_valid_from = models.CharField(
        max_length=20, blank=True, verbose_name='Sales Price Valid From')
    sales_price_valid_to = models.CharField(
        max_length=20, blank=True, verbose_name='Sales Price Valid To')

    creation_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Creation date')
    last_modified = models.DateTimeField(
        auto_now=True, verbose_name='Last modified')
    history = HistoricalRecords(excluded_fields=['creation_date',
                                                 'last_modified'])

    class Meta:
        unique_together = (("external_id", "merchant_name"))
        ordering = ['-id']

    def save(self, *args, **kwargs):
        self.article = Article.objects.filter(gtin=self.article_gtin).first()
        super(MerchantArticle, self).save(*args, **kwargs)
        if self.article:
            self.save_related_products()

    def post_delete(sender, instance, using):
        products = Product.objects.filter(article__gtin=instance.article.gtin)
        for product in products:
            product.save_without_historical_record()

    def save_related_products(self):
        products = Product.objects.filter(article__gtin=self.article.gtin)
        for product in products:
            product.save_without_historical_record()

    def __str__(self):
        return self.external_id + " (" + self.merchant_name + ")"


class Product(models.Model):
    TYPES = (
        ("Normal", "Normal"),
        ("Crossdocking", "Crossdocking"),
        ("Nightorder", "Nightorder"),
    )

    marketing_message = models.TextField(blank=True)
    nutrition_description = models.TextField(blank=True)
    ingredient_description = models.TextField(blank=True)
    name = models.CharField(max_length=256, blank=True)
    brand_name = models.CharField(max_length=256, verbose_name="Brand",
                                  blank=True)
    description = models.TextField(blank=True, verbose_name="Description")
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    product_id = models.BigIntegerField(default=0, unique=True)
    article = models.ForeignKey(Article, on_delete=models.DO_NOTHING)
    prefered_merchantarticle = models.ForeignKey(
        MerchantArticle, on_delete=models.DO_NOTHING,
        blank=True, null=True, default=None)
    product_category = models.ForeignKey(
        ProductCategory, on_delete=models.DO_NOTHING, blank=True, null=True)
    tags = models.ManyToManyField(
        'Tag', related_name='products', blank=True)
    adult_product = models.BooleanField(
        default=False, verbose_name="Adult Product")
    origin = models.IntegerField(blank=True,
                                 verbose_name="Origin",
                                 choices=Origin.COUNTRY,
                                 default=0)
    fishing_zone = models.IntegerField(blank=True,
                                       choices=FishingZone.AREA,
                                       default=0)
    allergen_statement = models.TextField(
        verbose_name="Allergen Statement", blank=True, default='')
    allergens = JSONField(
        verbose_name="Allergens", blank=True, default=dict)
    weight_g = models.FloatField(
        blank=True, null=True, verbose_name="Weight (g)")
    height_mm = models.FloatField(
        blank=True, null=True, verbose_name="Height (mm)")
    length_mm = models.FloatField(
        blank=True, null=True, verbose_name="Length (mm)")
    width_mm = models.FloatField(
        blank=True, null=True, verbose_name="Depth (mm)")
    volume_dm3 = models.FloatField(
        max_length=10, blank=True, null=True, verbose_name="Volume (dm³)")
    net_content = models.FloatField(
        blank=True, null=True, verbose_name="Net Content")
    net_content_unit_code = models.CharField(
        blank=True, null=True, max_length=10, verbose_name="Net Content Unit Code", choices=list(T3780.UNIT_CODES.items()))
    recycle_fee = models.FloatField(default=0.0, verbose_name="Recycle Fee")
    vat = models.FloatField(
        default=0, verbose_name="VAT",
        choices=zip([0.0] + Article.VATS, [0.0] + Article.VATS))
    last_receipt_day = models.IntegerField(blank=True, default=0)
    last_sales_day = models.IntegerField(blank=True, default=0)
    product_type = models.CharField(
        max_length=128, blank=True, choices=TYPES,
        default="Normal", verbose_name="Type")
    valid_weight = models.BooleanField(blank=True, default=False)
    valid_volume = models.BooleanField(blank=True, default=False)
    valid_image = models.BooleanField(blank=True, default=False)
    valid_brand = models.BooleanField(blank=True, default=False)
    valid_price = models.BooleanField(blank=True, default=False)
    valid_merchantarticle = models.BooleanField(blank=True, default=False)
    history = HistoricalRecords(
        excluded_fields=['creation_date', 'last_modified'])
    valid_products_query = Q(
        # valid_weight=True,
        # valid_volume=True,
        valid_image=True,
        valid_brand=True,
        valid_price=True,
        # valid_merchantarticle=True,
        article__vat__in=Article.VATS)

    class Meta:
        indexes = [
            models.Index(fields=['product_id', 'name', 'brand_name'])
        ]
        ordering = ['-id']

    def validate_weight(self):
        packages = self.article.get_related()
        case = list(filter(
            lambda package: package.descriptor_code == 'CASE',
            packages
        ))

        if len(case) == 0:
            self.valid_weight = False
            return self.valid_weight
        else:
            case = case[0]

            if int(case.weight_g) == 0:
                self.valid_weight = False
                return self.valid_weight

            weight = self.weight_g or self.article.weight_g
            weight_diff = (
                weight *
                case.quantity_of_lower_layer /
                case.weight_g - 1) * 100

            if abs(weight_diff) >= 20.0:
                self.valid_weight = False
                return self.valid_weight

        self.valid_weight = True
        return self.valid_weight

    def validate_volume(self):
        packages = self.article.get_related()
        case = list(filter(
            lambda package: package.descriptor_code == 'CASE',
            packages
        ))

        if len(case) == 0:
            self.valid_volume = False
            return self.valid_volume
        else:
            case = case[0]

            if int(case.volume_dm3) == 0:
                self.valid_volume = False
                return self.valid_volume

            volume = self.volume_dm3 or self.article.volume_dm3
            volume_diff = (
                volume *
                case.quantity_of_lower_layer /
                case.volume_dm3 - 1) * 100

            if abs(volume_diff) >= 20.0:
                self.valid_volume = False
                return self.valid_volume

        self.valid_volume = True
        return self.valid_volume

    def validate_image(self):
        if self.productimage_set.count() == 0:
            self.valid_image = False
            return self.valid_image

        self.valid_image = True
        return self.valid_image

    def validate_brand(self):
        if self.brand_name == '' and self.article.brand_name == '':
            self.valid_brand = False
            return self.valid_brand

        self.valid_brand = True
        return self.valid_brand

    def validate_price(self):
        store_ids_to_check = {10, 14, 16}
        store_ids_with_price = set(
            self
            .product_detail
            .filter(price__gt=0)
            .values_list('store',  flat=True)
        )

        store_ids_missing_price = store_ids_to_check - store_ids_with_price

        if len(store_ids_missing_price) > 0:
            self.valid_price = False
            return self.valid_price

        self.valid_price = True
        return self.valid_price

    def validate_merchantarticle(self):
        orderable = True
        if self.article.merchant_articles.count() == 0:
            orderable = False
            packages = self.article.get_related()
            for package in packages:
                if package.merchant_articles.count() > 0:
                    orderable = True
                    break

        self.valid_merchantarticle = orderable
        return self.valid_merchantarticle

    def validate_all(self):
        self.validate_weight()
        self.validate_volume()
        self.validate_image()
        self.validate_brand()
        self.validate_price()
        self.validate_merchantarticle()

    def save(self, *args, **kwargs):
        self.validate_all()
        super(Product, self).save(*args, **kwargs)

    def get_allergens(self):
        allergen_list = []
        for allergen in self.allergens:
            allergen_list.append(
                Allergen.get_text(allergen)
            )
        return ", ".join(allergen_list)


class ProductImage(models.Model):
    angle = models.CharField(max_length=6, blank=True, verbose_name="Angle")
    filename = models.CharField(max_length=256, verbose_name="Filename")
    creation_date = models.DateTimeField(auto_now_add=True,
                                         verbose_name="Created")
    source = models.CharField(max_length=40, verbose_name="Source", blank=True)
    history = HistoricalRecords(excluded_fields=['creation_date'])
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True,
                                null=True)
    active = models.BooleanField(default=True)
    main = models.BooleanField(default=False)

    class Meta:
        ordering = ['-main', '-creation_date']

    def save(self, *args, **kwargs):
        super(ProductImage, self).save(*args, **kwargs)

        if self.product is not None:
            self.product.save_without_historical_record()

    def post_delete(sender, instance, using):
        if instance.product is not None:
            instance.product.save_without_historical_record()


class ProductDetail(models.Model):
    STORES = (
        (10, "Stockholm"),
        (14, "Göteborg"),
        (16, "Malmö")
    )

    STATUSES = (
        (1, "Open"),
        (2, "Out of stock"),
        (3, "Replacement"),
        (4, "Missing info"),
        (5, "Sample")
    )

    store = models.IntegerField(choices=STORES)
    price = models.FloatField(max_length=10, default=0)
    enabled = models.BooleanField()
    first_enabled = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(choices=STATUSES, default=4)
    orderfactor = models.BooleanField(
        default=False, verbose_name="Orderfactor")
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING,
                                related_name='product_detail')
    prefered_merchantarticle = models.ForeignKey(
        MerchantArticle, on_delete=models.DO_NOTHING,
        blank=True, null=True, default=None)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        super(ProductDetail, self).save(*args, **kwargs)

        if self.product is not None:
            self.product.save_without_historical_record()

    def post_delete(sender, instance, using):
        if instance.product is not None:
            instance.product.save_without_historical_record()

    def is_tagged_as_new(self):
        if self.first_enabled is None:
            return False

        cutoff_date = datetime.now(
            self.first_enabled.tzinfo) - timedelta(days=30)

        return self.first_enabled > cutoff_date


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Name")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']
