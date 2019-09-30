
SELECT DISTINCT t.TagID,t.TagName,p.productname,p.productid,p.EanCode
FROM tag t
INNER JOIN producttag pt
ON pt.TagId = t.tagid
INNER JOIN product p
ON p.productid = pt.productid 
WHERE t.removeddate IS NULL
AND p.RemovedDate IS NULL
AND t.tagname NOT LIKE 'neo%'
AND t.tagname NOT LIKE '_auto_%'
AND t.tagname NOT LIKE '%)'
