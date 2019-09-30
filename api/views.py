
from web.models import *
from api.serializers import *
from datetime import datetime

from django.db.models import Q
from django.http import Http404

from rest_framework import generics, status
from rest_framework.request import clone_request
from rest_framework.response import Response


class AllowPUTAsCreateMixin(object):
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object_or_none()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if instance is None:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_object_or_none(self):
        try:
            return self.get_object()
        except Http404:
            if self.request.method == 'PUT':
                self.check_permissions(clone_request(self.request, 'POST'))
            else:
                raise


class PreferValidooAndNewerDataMixin(object):
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object_or_none()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if instance is None:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        last_modified = datetime.strptime(request.data['last_modified'],
                                          '%Y-%m-%d %H:%M:%S').astimezone()

        # Only save data if it's newer
        # We do however prefer Validoo data over any other, even if it's older
        if instance.last_modified < last_modified:
            if request.data['source'] == 'validoo':
                serializer.save()
            elif not instance.source == 'validoo':
                serializer.save()
        else:
            if (not instance.source == 'validoo' and
                    request.data['source'] == 'validoo'):
                serializer.save()

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_object_or_none(self):
        try:
            return self.get_object()
        except Http404:
            if self.request.method == 'PUT':
                self.check_permissions(clone_request(self.request, 'POST'))
            else:
                raise


class ProductList(generics.ListAPIView):
    queryset = Product.objects.filter(
        Product.valid_products_query
    )[:10]
    serializer_class = ProductSerializer


class ProductGtin(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        gtin = self.kwargs['gtin']
        queryset = Product.objects.filter(
            Product.valid_products_query
        ).filter(article__gtin=gtin)
        return queryset


class ProductId(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'product_id'
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ArticleList(generics.ListCreateAPIView):
    queryset = Article.objects.all()[:10]
    serializer_class = ArticleSerializer


class ArticleGtin(generics.ListAPIView):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        gtin = self.kwargs['gtin']
        queryset = Article.objects.filter(gtin=gtin)
        return queryset


class ArticleProductName(generics.RetrieveAPIView):
    lookup_field = 'product_name'
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer


class ArticleExternalId(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'external_id'
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer


class ArticleAdd(PreferValidooAndNewerDataMixin, generics.UpdateAPIView):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        queryset = Article.objects.filter(gtin=self.request.data['gtin'])
        return queryset

    def get_object(self):
        obj = Article.objects.filter(gtin=self.request.data['gtin']).first()
        return obj


class ArticleImageAdd(generics.CreateAPIView):
    serializer_class = ArticleImageSerializer

    def create(self, request, *args, **kwargs):
        if request.data.get('angle'):
            existing = ArticleImage.objects.filter(
                gtin=request.data.get('gtin'),
                angle__iexact=request.data.get('angle')).first()

            if existing:
                existing.filename = request.data.get('filename')
                serializer = ArticleImageSerializer(
                    existing, data=request.data)
                serializer.is_valid(raise_exception=True)
                existing.save()
                headers = self.get_success_headers(serializer.data)

                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK,
                    headers=headers)
            else:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers)


class ArticleImageGtin(generics.ListAPIView):
    serializer_class = ArticleImageSerializer

    def get_queryset(self):
        gtin = self.kwargs['gtin']
        queryset = ArticleImage.objects.filter(gtin=gtin)
        return queryset


class MerchantArticleAdd(AllowPUTAsCreateMixin, generics.UpdateAPIView):
    serializer_class = MerchantArticleSerializer

    def get_queryset(self):
        queryset = MerchantArticle.objects.filter(
            external_id=self.request.data['external_id'],
            merchant_name=self.request.data['merchant_name'])
        return queryset

    def get_object(self):
        obj = MerchantArticle.objects.filter(
            external_id=self.request.data['external_id'],
            merchant_name=self.request.data['merchant_name']).first()
        return obj


class MerchantArticleList(generics.ListAPIView):
    queryset = MerchantArticle.objects.all()
    serializer_class = MerchantArticleSerializer


class MerchantArticleGet(generics.RetrieveAPIView):
    serializer_class = MerchantArticleSerializer

    def get_object(self):
        obj = MerchantArticle.objects.filter(
            external_id=self.kwargs['external_id'],
            merchant_name=self.kwargs['merchant_name']).first()

        return obj


class MerchantArticleByGtin(generics.ListAPIView):
    serializer_class = MerchantArticleSerializer

    def get_queryset(self):
        obj = MerchantArticle.objects.filter(
            article_gtin=self.kwargs['gtin'])

        return obj


class MerchantArticleNameAndGtin(generics.ListAPIView):
    serializer_class = MerchantArticleSerializer

    def get_queryset(self):
        obj = MerchantArticle.objects.filter(
            article_gtin=self.kwargs['gtin'],
            merchant_name=self.kwargs['merchant_name'])

        return obj


class TagList(generics.ListAPIView):
    serializer_class = TagSerializer

    def get_queryset(self):
        tagtypeId = self.kwargs.get('tagtypeid')
        tagtypename = self.kwargs.get('tagtypename')

        if tagtypeId is None and tagtypename is None:
            queryset = Tag.objects.all()
            return queryset
        else:
            if tagtypename:
                queryset = Tag.objects.filter(
                    tagtype__name__icontains=tagtypename
                    )
            if tagtypeId:
                queryset = Tag.objects.filter(
                    tagtype=tagtypeId
                    )
            return queryset
