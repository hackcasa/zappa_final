
SELECT DISTINCT t.TagID,t.TagName,c.categoryname,c.categoryid
FROM tag t
INNER JOIN categorytag ct
ON ct.TagId = t.tagid
INNER JOIN category c
ON c.categoryid = ct.categoryid 
WHERE t.removeddate IS NULL
AND c.RemovedDate IS NULL
AND t.tagname NOT LIKE 'neo%'
AND t.tagname NOT LIKE '_auto_%'
AND t.tagname NOT LIKE '%)'