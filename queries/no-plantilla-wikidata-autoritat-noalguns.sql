# Pàgines sense plantilla Autoritat amb entrades de Wikidata amb només certs recursos i no d'altres (p. ex., VIAF i ORCID)
select distinct( i.article ) from (select d.article, d.id from ( select b.article from bios b left join (select * from whatlinks where against='Plantilla:Autoritat') as   w on b.article=w.article where w.against is null ) as l left join wikidata d on d.article=l.article ) as i left join (
  select a.id, a.authority from authorities a where a.id not in  ( select distinct( s.id ) from  ( (
  select distinct(id), group_concat(distinct(authority) order by authority asc) as groups from authorities group by id having groups = "P214,P496"
  UNION
  select distinct(id), group_concat(distinct(authority)) as groups from authorities group by id having count(id) = 1 and groups in ("P214", "P496")  ) as s ) order by s.id asc )
) p on i.id=p.id where p.authority is not null  order by i.article asc;
