from django.db import models
from django.db.models import Q
from django.db.models import Count


class ArticleQuerySet(models.QuerySet):

    def valid_query(self):
        return Q(
            Q(
                consumer_unit=True,
                image_count__gt=0,
                weight_g__gt=0,
                height_mm__gt=0,
                length_mm__gt=0,
                width_mm__gt=0,
                volume_dm3__gt=0,
                vat__in=self.model.VATS,
                name__gt='',
                brand_name__gt='',
                # marketing_message__gt='',
                # nutrition_description__gt='',
                # ingredient_description__gt=''
            ) |
            Q(consumer_unit=False) |
            Q(whitelisted=True)
        )

    def valid(self):
        query = self.annotate(image_count=Count('articleimage'))
        return query.filter(self.valid_query())

    def invalid(self):
        query = self.annotate(image_count=Count('articleimage'))
        return query.exclude(self.valid_query())


class ArticleManager(models.Manager):
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)

    def valid(self):
        return self.get_queryset().valid()

    def invalid(self):
        return self.get_queryset().invalid()
