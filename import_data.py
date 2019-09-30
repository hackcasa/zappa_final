#!/usr/bin/env python

# import json to db
import os
import django

print("I am running.")
# sys.path.append("/Users/cjl7/repos/restful_pim")  #here store is root folder(means parent).

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pim.settings")
django.setup()

from web.models import Article, MerchantArticle

all_articles = Article.objects.all()

print(all_articles)


for line in open('temp/ArticleData2', encoding='utf-8').readlines():
    _t = eval(line)

    try:
        _t_listed = _t['Listed']['s']
    except Exception as e:
        _t_listed = '1999-01-01'
    try:
        _t_delisted = _t['DeListed']['s']
    except Exception as e:
        _t_delisted = '1999-01-01'

    try:
        _brand_name = _t['BrandName']['s']
    except Exception as e:
        _brand_name = 'Nope'

    try:
        _category = _t['Category']['s']
    except Exception as e:
        _category = 'Nope'

    _a = Article(
        gtin=int(_t['Gtin']['s']),
        category=_category,
        version=_t['Version']['s'],
        weight_g=int(_t['Dimensions']['m']['WeightG']['n']),
        height_mm=int(_t['Dimensions']['m']['HeightMM']['n'].split('.')[0]),
        length_mm=int(_t['Dimensions']['m']['LengthMM']['n'].split('.')[0]),
        volume_dm2=float(_t['Dimensions']['m']['VolumeDM2']['n']),
        width_mm=int(_t['Dimensions']['m']['WidthMM']['n'].split('.')[0]),
        creation_date=_t['CreationDate']['s'],
        product_name=_t['ProductName']['s'],
        last_modified=_t['LastModifiedDate']['s'],
        brand_name=_brand_name)

    _merchant = MerchantArticle(
        external_id=_t['ExternalIds']['m']['Bergendahls']['s'],
        merchant_name=_t['MerchantName']['s'],
        availability_status=_t['AvailabilityStatus']['s'])

    try:
        _a.save()
        _merchant.article = _a
        _merchant.save()
    except Exception as e:
        print(e)
        pass
