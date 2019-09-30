from web.models import *
from rest_framework import serializers
from api.core_convert import *


class MerchantArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantArticle
        fields = '__all__'

    def create(self, validated_data):
        article = Article.objects.filter(
            gtin=validated_data['article_gtin']).first()

        if article is not None:
            validated_data['article'] = article

        return super(MerchantArticleSerializer, self).create(validated_data)


class ArticleSerializer(serializers.ModelSerializer):
    merchant_articles = MerchantArticleSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = '__all__'


class ProductArticleSerializer(ArticleSerializer):
    related_articles = serializers.SerializerMethodField()

    def get_related_articles(self, obj):
        related_articles = obj.get_related()
        return ArticleSerializer(related_articles, many=True, read_only=True).data


class ProductDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductDetail
        exclude = ('id', 'product', 'enabled')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('__all__')


class ProductSerializer(serializers.ModelSerializer):
    product_detail = ProductDetailSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()
    marketing_message = serializers.SerializerMethodField()
    nutrition_description = serializers.SerializerMethodField()
    ingredient_description = serializers.SerializerMethodField()
    net_content = serializers.SerializerMethodField()
    net_content_unit_code = serializers.SerializerMethodField()
    article = ProductArticleSerializer(read_only=True)

    class Meta:
        depth = 1
        model = Product
        exclude = ('id',)

    def get_images(self, obj):
        productimage_set = obj.productimage_set.filter(active=True)
        return ProductImageSerializer(productimage_set, many=True).data

    def get_name(self, obj):
        if obj.name:
            return obj.name
        else:
            return obj.article.name

    def get_brand_name(self, obj):
        if obj.brand_name:
            return obj.brand_name
        else:
            return obj.article.brand_name

    def get_marketing_message(self, obj):
        if obj.marketing_message:
            return obj.marketing_message
        else:
            return obj.article.marketing_message

    def get_nutrition_description(self, obj):
        if obj.nutrition_description:
            return obj.nutrition_description
        else:
            return obj.article.nutrition_description

    def get_ingredient_description(self, obj):
        if obj.ingredient_description:
            return obj.ingredient_description
        else:
            return obj.article.ingredient_description

    def get_net_content(self, obj):
        if obj.net_content:
            return obj.net_content
        return obj.article.net_content

    def get_net_content_unit_code(self, obj):
        if obj.net_content_unit_code:
            return obj.net_content_unit_code
        return obj.article.net_content_unit_code


class ArticleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleImage
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class ProductCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductCategory
        fields = '__all__'


# This serializer renames fields to fit the form of current sns
# data to service int-tagtaxonomy
class ExportProductCategorySerializer(serializers.ModelSerializer):

    Id = serializers.IntegerField(source='id')
    ParentId = serializers.SerializerMethodField(method_name='get_parent_id')
    Url = serializers.CharField(source='url')
    IsPublic = serializers.BooleanField(source='is_public')
    CategoryIntroduction = serializers.CharField(source='introduction')
    Title = serializers.CharField(source='title')
    MetaDescription = serializers.CharField(source='metadescription')
    ParentCategory = \
        serializers.SerializerMethodField(method_name='get_parent')

    class Meta:
        model = ProductCategory
        fields = ('Id', 'ParentId', 'Title', 'Url', 'IsPublic',
                  'CategoryIntroduction', 'Title', 'MetaDescription',
                  'ParentCategory')

    def get_parent(self, obj):
        if obj.parentcategory is not None:
            return ExportProductCategorySerializer(obj.parentcategory).data
        else:
            return None

    def get_parent_id(self, obj):
        if obj.parentcategory is not None:
            return obj.parentcategory.id
        else:
            return None


class CoreSyncSerializer(serializers.ModelSerializer):
    Product = serializers.SerializerMethodField()
    ProductStores = serializers.SerializerMethodField()
    Attributes = serializers.SerializerMethodField()
    DynamicProperties = serializers.SerializerMethodField()
    Tags = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('Product', 'ProductStores',
                  'Attributes', 'DynamicProperties', 'Tags')

    def get_Product(self, obj):
        return convert_product(obj)

    def get_ProductStores(self, obj):
        return convert_product_stores(obj)

    def get_Attributes(self, obj):
        return convert_attributes(obj)

    def get_DynamicProperties(self, obj):
        return convert_dynamic_properties(obj)

    def get_Tags(self, obj):
        return convert_tags(obj)

    def can_sync_to_core(self, errors=[]):
        required_product = [
            "UnitId",
            "DisplayUnitId",
            "CategoryId",
            "OriginId",
        ]
        data = self.data
        for key in required_product:
            if key not in data['Product'] or data['Product'][key] == None or data['Product'][key] == 0:
                errors.append('Key ' + key + ' can not be empty')
        return len(errors) == 0
