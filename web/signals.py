from django.dispatch import receiver
from django.db.models.signals import post_save
from web.models import Product
from web.sqs import notify_product_change


@receiver(post_save, sender=Product)
def post_save_product(sender, instance, created, raw, using, update_fields, **kwargs):
    ignore_keys = ["_state", "creation_date", "last_modified",
                   "history", "id", "skip_history_when_saving"]
    notify_product_change(instance)
    return
    for field in update_fields:
        if field in ignore_keys:
            continue
        notify_product_change(instance)
        break
