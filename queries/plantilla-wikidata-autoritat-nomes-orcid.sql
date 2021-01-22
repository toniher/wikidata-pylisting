# Pàgines només amb ORCID
select d.article, d.id from  wikidata d inner join ( select distinct(id), group_concat(distinct(authority)) as groups from authorities group by id having count(id) = 1 and groups in ("P496") order by id asc ) as a on a.id=d.id ;
