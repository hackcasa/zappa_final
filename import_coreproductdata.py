#!/usr/bin/env python

import sys
import os
import django
import pytz
from datetime import datetime


print("I am alive!.")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pim.settings")
django.setup()

from web.models import ProductData

#Some mappings for readability
EanCode=0
ProductDescription=1
NutritionDescription=2
IngredientsDescription=3
ProductName=4
CreationDate=5
LastmodifiedDate=6

tz = pytz.timezone("Europe/Stockholm")


testy = datetime.strptime("2007-10-27 12:24:12", "%Y-%m-%d %H:%M:%S")
print(testy)


lineset = open('temp/CoreProductData_stage180915.csv',encoding='utf-8').readlines()
headerrow =lineset.pop(0)
for line in lineset:
    print('')
    print(line)

    csv_row = line.split(';')
       
    _pd = ProductData(
        gtin=csv_row[EanCode],
        marketing_message=csv_row[ProductDescription].strip('"'),
        nutrition_description=csv_row[NutritionDescription].strip('"'),
        ingredient_description=csv_row[IngredientsDescription].strip('"'),
        name=csv_row[ProductName],
        creation_date=tz.localize(datetime.strptime(csv_row[CreationDate].strip('"'), "%Y-%m-%d %H:%M:%S")),
        last_modified=tz.localize(datetime.strptime(csv_row[LastmodifiedDate].strip('\n').strip('"'), "%Y-%m-%d %H:%M:%S"))
        )

    if _pd.marketing_message == "NULL":
        _pd.marketing_message = str()

    if _pd.nutrition_description == "NULL":
        _pd.nutrition_description = str()

    if _pd.ingredient_description == "NULL":
        _pd.ingredient_description = str()       
    
    try:
        _pd.save()
    except Exception as e:
        print(e)
        pass
