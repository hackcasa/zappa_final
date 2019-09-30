SELECT
categoryid,
categoryname,
parentcategoryid,
categoryurl,
ispublic,
categoryintroduction,
title,
metadescription
FROM category c
WHERE  removeddate is null