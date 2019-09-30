from django.test import TestCase
from unittest.mock import patch
from web.models import Article, Product
import web.sqs


@patch("web.sqs.notify_product_change", autospec=True)
class ProductCoreSyncTriggerTestCase(TestCase):
    """ Tests if the core sync trigger works for all relations, doesn not test the validation stuff"""

    def setUp(self):
        date = "2000-01-01 00:00Z"
        article = Article.objects.create(
            gtin="00000001", creation_date=date, last_modified=date)
        Product.objects.create(
            product_id=1, article=article, creation_date=date, last_modified=date)

    def test_product_save(self, mock):
        """Product save triggers core update"""
        product = Product.objects.get(product_id=1)
        product.weight_g = 100
        product.save()
        mock.assert_called()

    def test_article_save(self, mock):
        """Article save triggers core update"""
        article = Article.objects.get(gtin="00000001")
        article.weight_g = 100
        article.save()
        self.assertTrue(mock.called)
