from django.dispatch import receiver
from django.db.models.signals import post_save
from web.models import Product
import web.sqs


@receiver(post_save, sender=Product)
def post_save_product(sender, instance, created, raw, using, update_fields, **kwargs):
    web.sqs.notify_product_change(instance)
