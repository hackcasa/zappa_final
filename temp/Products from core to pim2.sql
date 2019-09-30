SELECT DISTINCT
p.productid,
p.EanCode,
pdv_volume.PropertyValue as Volume,
pdv_weight.PropertyValue as Weight,
pdv_height.PropertyValue as Height,
pdv_length.PropertyValue as Length,
pdv_width.PropertyValue as Width,
ps.calculatedcustomerprice as price10,
ps14.calculatedcustomerprice as price14,
ps16.calculatedcustomerprice as price16,
Replace(Replace(Replace(p.ProductDescription,'\r\n',' '),'\n',' '),';',',') AS ProductDescription ,
Replace(Replace(Replace(p.NutritionDescription,'\r\n',' '),'\n',' '),';',',') AS NutritionDescription,
Replace(Replace(Replace(p.IngredientsDescription,'\r\n',' '),'\n',' '),';',',') AS IngredientsDescription,
p.ProductName,
p.ImageUrl,
p.VatRate,
p.CreationDate,
p.LastmodifiedDate,
s.suppliername,
IF(pattribute.removeddate < now() OR pattribute.ToDate < now(), 0, 1) AS NewProduct,
p.OriginID as Origin,
p.IsAdultProduct AS AdultProduct,
p.StoreVarmColdFrozen as StorageType,
p.RecycleFee,
pdv_season.PropertyValue as Season,
pdv_orderfactor.PropertyValue as Orderfactor,
pdv_lastrecday.PropertyValue as LastReceiptDay,
pdv_lastsaleday.PropertyValue as LastSalesDay,
pdv_truckrouteopt.PropertyValue as TruckRouteOpt
FROM prefilledautomaten.product p
INNER JOIN prefilledautomaten.productstore ps ON p.productid = ps.productid
INNER JOIN prefilledautomaten.productstore ps14 ON p.productid = ps14.productid
INNER JOIN prefilledautomaten.productstore ps16 ON p.productid = ps16.productid
INNER JOIN prefilledautomaten.supplier s ON s.supplierid = p.supplierid
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_volume ON pdv_volume.ProductId = p.productid AND pdv_volume.PropertyId = 1
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_weight ON pdv_weight.ProductId = p.productid AND pdv_weight.PropertyId = 2
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_height ON pdv_height.ProductId = p.productid AND pdv_height.PropertyId = 21
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_length ON pdv_length.ProductId = p.productid AND pdv_length.PropertyId = 22
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_width ON pdv_width.ProductId = p.productid AND pdv_width.PropertyId = 23
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_season ON pdv_season.ProductId = p.productid AND pdv_season.PropertyId = 10
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_orderfactor ON pdv_orderfactor.ProductId = p.productid AND pdv_orderfactor.PropertyId = 11
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_lastrecday ON pdv_lastrecday.ProductId = p.productid AND pdv_lastrecday.PropertyId = 5
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_lastsaleday ON pdv_lastsaleday.ProductId = p.productid AND pdv_lastsaleday.PropertyId = 4
LEFT JOIN prefilledautomaten.productdynamicvalue pdv_truckrouteopt ON pdv_truckrouteopt.ProductId = p.productid AND pdv_truckrouteopt.PropertyId = 20
LEFT JOIN prefilledautomaten.productattribute pattribute ON pattribute.productid = p.productid AND pattribute.attributeid = 2173
WHERE p.RemovedDate IS NULL
AND ps.RemovedDate IS NULL
AND ps.storeid = 10
AND ps14.storeid = 14
AND ps16.storeid = 16
AND ps.IsReplacementProduct = 0
AND p.PossibleToBuy = 1
AND IsWine = 0
AND p.supplierid NOT IN
(#These Ids are children of Clas Ohlsson
14344,
14563,
14566,
14569,
14572,
14575,
14578,
14941,
14944,
14947
);
