
import boto3
import os
import json


def notify_productcategory_change(productCategory):
    from api.serializers import ExportProductCategorySerializer

    customSerializer = ExportProductCategorySerializer(productCategory)
    data = json.dumps(customSerializer.data)
    topicArn = os.environ.get('product-category-changes-ARN')

    if topicArn is None:
        return

    sns_client = boto3.client('sns')

    response = sns_client.publish(
                        Message=data,
                        TopicArn=topicArn)

    return response
