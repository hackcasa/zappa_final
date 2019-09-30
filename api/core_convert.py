from datetime import timedelta, datetime


def filter_dict(obj, val=None):
    # TODO: We should not always remove all None items (maybe!?)
    return dict(filter(lambda item: item[1] is not val, obj.items()))


def get_season_tag_name(key):
    table = {
        "Clas Ohlson": "COB",
        "Matkasse": "MK",
        "Grillartiklar": "G",
        "Halloweenartiklar": "H",
        "Julartiklar": "J",
        "Artiklar som säljs året runt, men mest runt jul": "JB",
        "Midsommarartiklar": "M",
        "Artiklar som säljs året runt, men mest runt midsommar": "MB",
        "Nyårsartiklar": "N",
        "Artiklar som säljs året runt, men mest runt nyår": "NB",
        "Påskartiklar": "P",
        "Artiklar som säljs året runt, men mest runt påsk": "PB",
        "Sommarartiklar": "S",
        "Sommartorget": "ST",
    }
    return table[key] if key in table else None


def convert_season_tags(product):
    tags = map(lambda x: get_season_tag_name(x), product.tags.all())
    return list(filter(lambda x: x is not None, tags))


def convert_order_route_from_product_type(key):
    table = {
        "Crossdocking": "X",
        "Nightorder": "A",
    }
    return table[key] if key in table else None


def get_attribute_id(key):
    # data from prefilledautomaten.attribute
    table = {
        'Ekonomipack': 1,
        'Nyckelhålsmärkt': 1736,
        'Ekologisk': 2167,
        'Glutenfri': 2168,
        'Laktosfri': 2169,
        'Låglaktos': 2170,
        'Premiumkvalité': 2171,
        'Mjölkproteinfri': 2172,
        # 'Nyhet': 2173,
        '18Åldersgräns': 2174,
        'Fairtrade': 2175,
        'Svanenmärkt': 2176,
        'Kravmärkt': 2177,
        'Video': 2178,
        'Äkta vara': 2181,
        'Astma- och Allergiförbundet': 2184,
        'test': 2187,
        'Rosa bandet': 2190,
        'Svenskt sigill': 2191,
        '3+ dagar': 2194,
        '5+ dagar': 2197,
        '7+ dagar': 2200,
        '10+ dagar': 2203,
        '30+ dagar': 2206,
        'Svenskt ursprung': 2209,
        'Svensk fågel': 2212,
        '4+ dagar': 2215,
        'Vegansk': 2218,
        'MSC': 2219,
        'Strategisk produkt': 2222,
        'Svenskt sigill klimatcertifierad': 2224,
        'ASC': 2227,
        'Från Sverige': 2230,
        'Kött från Sverige': 2233,
        'Mjölk från Sverige': 2236,
        'Faroklass brandfarligt': 2239,
        'Faroklass miljöfarligt': 2242,
        'Faroklass skadligt': 2245,
        'Faroklass Warning': 2248,
        'Energiklass A+': 2251,
        'Energiklass C': 2254,
        'Energiklass D': 2257,
        'Energiklass E': 2260,
        'Energiklass A++': 2263,
        'Energiklass A': 2266,
        'Energiklass B': 2269,
    }
    return table[key] if key in table else None


def get_dynamic_property_id(key):
    table = {
        'Volume': 1,
        'Weight': 2,
        'KfpDfp': 3,
        'LastSalesDay': 4,
        'LastReceiptDay': 5,
        'OldPz1': 6,
        'OldPz2': 7,
        'OldPz3': 8,
        'MaxStock': 9,
        'Season': 10,
        'OrderFactor': 11,
        'MinStock': 12,
        'DfpLengthMM': 13,
        'DfpWidthMM': 14,
        'DfpHeightMM': 15,
        'DfpWeightG': 16,
        'DfpType': 17,
        'SupplierArticleNumber': 18,
        'AxfoodArticleId': 19,
        'TruckrouteOptimizationProd3': 20,
        'KfpHeightMM': 21,
        'KfpLengthtMM': 22,
        'KfpWidthMM': 23,
        'IsFakeStockBalance': 24,
        'ExternalImageUrl': 25,
        'ProductSupplier': 26,
        'ValdioDFPWidthMM': 27,
        'ValdioDFPHeightMM': 28,
        'ValidoDFPLengthtMM': 29,
        'ValdioDFPWeightG': 30,
        'DFPEANCode': 31,
        'SafetyStock': 33,
        'KfpDfpPurchaseOrder': 36,
        'NoNutritionsNeeded': 38,
        'NoIngredientsNeeded': 41,
        'NoAllergensNeeded': 44,
        'DeliveredUnitConversionFactor': 45,
        'HandlingUnitQuantity': 46,
        'BDMaterialNumber': 49,
        'ProductSegment': 55,
        'StandardUnitKfp': 56,
        'StandardUnitGtin': 59,
        'LimitedOfferProduct': 61,
        'QLPricing': 64,
        'QLMatching': 67,
        'FirstSalesDate': 70,
        'CategoryManager': 73,
    }
    return table[key] if key in table else None


def get_origin_id(key):
    table = {
        752: 1,  # Svensk
        249: 2,  # Fransk
        # TODO: MAP THIS ?: 3, # Afrika
        # TODO: MAP THIS ?: 4, # Grekiskt
        # TODO: MAP THIS ?: 5, # Indien
        # TODO: MAP THIS ?: 6, # Nordamerika
        # TODO: MAP THIS ?: 7, # Latinamerika
        # TODO: MAP THIS ?: 8, # Orienten
        # TODO: MAP THIS ?: 9, # Japan
        # TODO: MAP THIS ?: 10, # Italienskt
        # TODO: MAP THIS ?: 11, # Sydostasien
        # TODO: MAP THIS ?: 12, # Spansk
        # TODO: MAP THIS ?: 13, # Tyskland
        # TODO: MAP THIS ?: 14, # "Ryssland och Östeuropa"
        # TODO: MAP THIS ?: 15, # Internationellt
        # TODO: MAP THIS ?: 16, # Övriga
        # TODO: MAP THIS ?: 73, # Sverige
        # TODO: MAP THIS ?: 74, # Norge
        # TODO: MAP THIS ?: 75, # Kanada
        # TODO: MAP THIS ?: 76, # Frankrike
        # TODO: MAP THIS ?: 77, # Grekland
        # TODO: MAP THIS ?: 78, # Portugal
        # TODO: MAP THIS ?: 79, # Danmark
        # TODO: MAP THIS ?: 80, # Italien
        # TODO: MAP THIS ?: 81, # Finland
        # TODO: MAP THIS ?: 82, # Kalifornien
        # TODO: MAP THIS ?: 83, # Thailand
        # TODO: MAP THIS ?: 84, # Kina
        # TODO: MAP THIS ?: 85, # Belgien
        # TODO: MAP THIS ?: 86, # Europa
        # TODO: MAP THIS ?: 87, # Turkiet
        # TODO: MAP THIS ?: 88, # Holland
        # TODO: MAP THIS ?: 89, # England
        # TODO: MAP THIS ?: 90, # Spanien
        # TODO: MAP THIS ?: 91, # Nederländerna
        # TODO: MAP THIS ?: 92, # Polen
        # TODO: MAP THIS ?: 93, # "Blandat: EG och icke EG"
        # TODO: MAP THIS ?: 94, # Ungern
        # TODO: MAP THIS ?: 95, # Bulgarien
        # TODO: MAP THIS ?: 96, # Kroatien
        # TODO: MAP THIS ?: 98, # India
        # TODO: MAP THIS ?: 99, # Uruguay
        # TODO: MAP THIS ?: 100, # Irland
        # TODO: MAP THIS ?: 101, # "Nya Zeeland"
        # TODO: MAP THIS ?: 102, # Sverige/England
        # TODO: MAP THIS ?: 103, # Sverige/Danmark
        # TODO: MAP THIS ?: 104, # China
        # TODO: MAP THIS ?: 105, # Holland/Frankrike
        # TODO: MAP THIS ?: 106, # "Costa Rica"
        # TODO: MAP THIS ?: 107, # Zaire
        # TODO: MAP THIS ?: 108, # Israel/USA
        # TODO: MAP THIS ?: 109, # Mexico
        # TODO: MAP THIS ?: 110, # Holland/Belgien
        # TODO: MAP THIS ?: 111, # Frankrike/Italien
        # TODO: MAP THIS ?: 112, # Sverge
        # TODO: MAP THIS ?: 113, # Centralamerika
        # TODO: MAP THIS ?: 114, # Brasilien
        # TODO: MAP THIS ?: 115, # Israel/Indien
        # TODO: MAP THIS ?: 116, # "Italien/Nya Zeeland"
        # TODO: MAP THIS ?: 117, # Sydafrika
        # TODO: MAP THIS ?: 118, # Argentina
        # TODO: MAP THIS ?: 119, # China/Thailand
        # TODO: MAP THIS ?: 120, # USA
        # TODO: MAP THIS ?: 121, # Kenya
        # TODO: MAP THIS ?: 122, # Israel
        # TODO: MAP THIS ?: 123, # Malaysia
        # TODO: MAP THIS ?: 124, # Nordostatlanten
        # TODO: MAP THIS ?: 125, # Vietnam
        # TODO: MAP THIS ?: 126, # Norden
        # TODO: MAP THIS ?: 127, # Litauen
        # TODO: MAP THIS ?: 131, # Roslagen
        # TODO: MAP THIS ?: 135, # U.S.A.
        # TODO: MAP THIS ?: 136, # DK
        # TODO: MAP THIS ?: 137, # Egypten
        # TODO: MAP THIS ?: 138, # Marocko
        # TODO: MAP THIS ?: 139, # Chile
        # TODO: MAP THIS ?: 140, # "Dominikanska Republiken"
        # TODO: MAP THIS ?: 141, # Iran
        # TODO: MAP THIS ?: 142, # Colombia
        # TODO: MAP THIS ?: 143, # Peru
        # TODO: MAP THIS ?: 144, # Zimbabwe
    }
    return table[key] if key in table else None


def convert_attributes(product, detail=None):
    result = []

    for tag in product.tags.all():
        id = get_attribute_id(tag.name)
        if id is not None:
            result.append({
                'AttributeId': id
            })

    # Special case for "Nyhet"
    if not detail and product.product_detail:
        detail = product.product_detail.filter(store=10).first()

        if detail is None:
            detail = product.product_detail.first()

    if detail:
        first_enabled = detail.first_enabled if detail.first_enabled else datetime.now() - \
            timedelta(days=60)
        result.append({
            'AttributeId': 2173,
            'FromDate': first_enabled,
            'ToDate': first_enabled + timedelta(days=30),
        })

    return result


def create_dynamic_property(key, value, store=None):
    prop = {
        'PropertyId': get_dynamic_property_id(key),
        'PropertyName': key,
        'PropertyValue': value,
    }
    if store is not None:
        prop['StoreId'] = store
    return prop


def convert_dynamic_properties(product):
    result = [
        create_dynamic_property('Volume', product.volume_dm3),
        create_dynamic_property('Weight', product.weight_g),
        create_dynamic_property('KfpHeightMM', product.height_mm),
        create_dynamic_property('KfpLengthtMM', product.length_mm),
        create_dynamic_property('KfpWidthMM', product.width_mm),
        create_dynamic_property('Season', '.'.join(
            convert_season_tags(product))),
        create_dynamic_property('LastReceiptDay', product.last_receipt_day),
        create_dynamic_property('LastSalesDay', product.last_sales_day),
        create_dynamic_property('TruckrouteOptimizationProd3',
                                convert_order_route_from_product_type(product.product_type)),
        create_dynamic_property('BDMaterialNumber',
                                product.prefered_merchantarticle.external_id if product.prefered_merchantarticle else None),
        create_dynamic_property('SupplierArticleNumber',
                                product.prefered_merchantarticle.external_id if product.prefered_merchantarticle else None),
    ]

    base_unit_quantity = get_base_unit_quantity(product, product.article.gtin)

    if base_unit_quantity is not None:
        create_dynamic_property('KfpDfp', base_unit_quantity)

    for detail in product.product_detail.all():
        result.append(create_dynamic_property(
            'OrderFactor', 1 if detail.orderfactor else 0, detail.store))
        result.append(create_dynamic_property(
            'BDMaterialNumber', detail.prefered_merchantarticle.external_id if detail.prefered_merchantarticle else None, detail.store))
        result.append(create_dynamic_property(
            'SupplierArticleNumber', detail.prefered_merchantarticle.external_id if detail.prefered_merchantarticle else None, detail.store))

        base_unit_quantity = get_base_unit_quantity(
            detail, product.article.gtin)

        if base_unit_quantity is not None:
            create_dynamic_property('KfpDfp', base_unit_quantity, detail.store)

    return result


def get_base_unit_quantity(product, base_unit_gtin):
    if product.prefered_merchantarticle is not None:
        if product.prefered_merchantarticle.article.child_gtin == base_unit_gtin:
            return product.prefered_merchantarticle.article.quantity_of_lower_layer
        else:
            upper_quantity = product.prefered_merchantarticle.article.quantity_of_lower_layer
            next_lower_article = Article.objects.filter(
                gtin=product.prefered_merchantarticle.article.child_gtin).first()

            if next_lower_article is not None:
                if next_lower_article.child_gtin == product.article.gtin:
                    return next_lower_article.quantity_of_lower_layer * upper_quantity

    return None


def convert_unit(validoo_unit):
    # data from prefilledautomaten.unit
    unit_table = {
        "H87": 1,  # st, PIECES
        "GRM": 2,  # g, WEIGHT
        "KGM": 3,  # kg, WEIGHT
        "DLT": 6,  # dl, VOLUME
        "LTR": 7,  # L, VOLUME
        "MLT": 10,  # ml, VOLUME
        "CLT": 11,  # cl, VOLUME
        "HGM": 12,  # hg, WEIGHT
        "G24": 13,  # msk, VOLUME
        "G25": 14,  # tsk, VOLUME
        # "???": 16,  # st tekoppar, VOLUME
        # "???": 17,  # st kaffekoppar, VOLUME
        # "???": 18,  # glas, VOLUME
        "MGM": 25,  # mg, WEIGHT,
        # "???": 26,  # krm, VOLUME
        # "???": 27,  # st klyftor, PARTS,
        # "???": 28,  # st krukor, PIECES
        # "???": 29,  # st tärningar, PIECES
        # "???": 30,  # knippe, PIECES
    }
    if(validoo_unit in unit_table):
        return unit_table[validoo_unit]
    return None


def convert_tags(product):
    tags = filter(lambda tag: get_season_tag_name(tag.name) is
                  None and get_attribute_id(tag.name) is None, product.tags.all())
    return list(map(lambda tag: tag.id, tags))


def convert_product(product):
    from api.serializers import ProductSerializer
    serializer = ProductSerializer(product)
    article = product.article
    image = product.productimage_set.first()
    unit_id = convert_unit(serializer.data['net_content_unit_code'])
    return filter_dict({
        "ProductId": product.product_id,  # int
        "ProductName": serializer.data['name'],  # string
        "Quantity": serializer.data['net_content'],  # float
        # int
        "UnitId": unit_id,
        "DisplayUnitId": unit_id,  # int
        "CategoryId": product.product_category.id if product.product_category else None,  # int
        # "ProductGroupId": ???,  # int
        # "CalculatedWeight": ???,  # float
        # "RecommendedPrice": ???,  # float
        "VatRate": article.vat,  # float
        "EanCode": article.gtin,  # string
        # string
        "ImageUrl": image.filename if image else None,
        # "ProductUrl": ???,  # string
        # "SupplierId": ???,  # int
        # "MaximumOrder": ???,  # float
        "ProductDescription": serializer.data['description'],  # string
        # "UsageDescription": ???,  # string
        # string
        "IngredientsDescription": serializer.data['ingredient_description'],
        # string
        "NutritionDescription": serializer.data['nutrition_description'],
        # "StorageDescription": ???,  # string
        # "StoreVarmColdFrozen": ???,  # string
        # "PossibleToBuy": ???,  # bool
        # "IsOffer": ???,  # bool
        "RecycleFee": product.recycle_fee,  # double
        # "AmountInPackage": ???,  # int
        # "TempMostBought": ???,  # int
        # "ExternalComment": ???,  # string
        # "InternalComment": ???,  # string
        # "IsPickingCostIncluded": ???,  # bool
        # "IsDeliveryCostIncluded": ???,  # bool
        # "RatesSum": ???,  # int
        # "RatesCount": ???,  # int
        "OriginId": get_origin_id(product.origin),  # int?
        # "IsWine": ???,  # bool
        # "AxfoodSAPId": ???,  # string
        # "IsEcological": ???,  # bool
        # "RelatedProductIDs": ???,  # string
        "IsAdultProduct": product.adult_product,  # bool
        # "AutomaticSubscription": ???,  # bool
        # "IsAlreadyRenamed": ???,  # bool
        # "OriginalAfterRenameFileSize": ???,  # string
        # "OriginalCurrentFileSize": ???,  # string
        # "CreationDate": ???,  # DateTime?
        # "LastModifiedDate": ???,  # DateTime?
        # "LastUpdatedByUserId": ???,  # int
        # "RemovedDate": ???,  # DateTime?
    })


def convert_product_store(detail, product):
    return filter_dict({
        # "ProductStoreId": ???,  # int
        "ProductId": product.product_id,  # int
        "StoreId": detail.store,  # int
        # "LocalEancode": ???,  # string
        "CalculatedCustomerPrice": detail.price,  # decimal
        # "CalculatedCustomerPrice_Per_Unit": ???,  # decimal
        "IsOutOfStock": detail.status == 2,  # bool
        # "OutOfStockDate": ???,  # DateTime
        # "StockBackDate": ???,  # DateTime
        "IsReplacementProduct": detail.status == 3  # bool
        # "IsApproximateWeight": ???,  # bool
        # "IsShowPricePerUnit": ???,  # bool
        # "PriceValidFrom": ???,  # DateTime
        # "PriceValidTo": ???,  # DateTime
        # "PriceIn": ???,  # decimal
        # "PercentageAddon": ???,  # decimal
        # "FixedAddon": ???,  # decimal
        # "PickingZone1": ???,  # string
        # "PickingZone2": ???,  # string
        # "PickingZone3": ???,  # string
        # "SoldCount": ???,  # int
        # "IsForeCastPriorityProduct": ???,  # bool
        # "DontShowAsMissedProduct": ???,  # bool
        # "StoreLevelOriginId": ???,  # int?
        # "PickingNote": ???,  # string
        # "AdvanceDeliveryMinimumOrder": ???,  # int
        # "MinimumRequiredDeliveryDays": ???,  # byte
        # "DeliverableWeekDays": ???,  # string
        # "DeliveryDaysAhead": ???,  # int
        # "CancelDaysBefore": ???,  # int
        # "StorePriceIn": ???,  # decimal
        # "CreationDate": ???,  # DateTime?
        # "LastModifiedDate": ???,  # DateTime?
        # "RemovedDate": ???,  # DateTime?
        # "CanSendAdvanceDeliveryEmail": ???,  # bool
        # "OldCalculatedCustomerPrice": ???,  # decimal
    })


def convert_product_stores(product):
    return list(map(lambda x: convert_product_store(x, product), product.product_detail.all()))
