
SELECT
TagID,TagName,CreationDate
FROM tag 
WHERE 
RemovedDate IS NULL
AND tagname NOT LIKE 'neo%'
AND tagname NOT LIKE '_auto_%'
AND tagname NOT LIKE '%)';
