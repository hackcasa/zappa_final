import os
import sys
import boto3
import json
import logging
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)


def notify_product_change(product):
    if sys.argv[0] == 'manage.py':
        return False
    queue_url = os.environ.get('product-core-sync-queue-url')
    if not queue_url:
        logger.warning(
            'Cannot sync product to core: env product-core-sync-queue-url not set')
        return False
    from api.serializers import CoreSyncSerializer
    serializer = CoreSyncSerializer(instance=product)
    errors = []
    if not serializer.can_sync_to_core(errors):
        logger.error('Cannot sync product ' + str(product.id) +
                     ' to core: ' + ', '.join(errors))
        return False
    data = json.dumps(serializer.data, cls=DjangoJSONEncoder)
    sqs = boto3.client('sqs', 'eu-west-1')
    logger.info('Sending core update for product:' + str(product.product_id))
    return sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=data
    )
