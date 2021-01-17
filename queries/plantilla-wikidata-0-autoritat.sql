# Pàgines amb plantilla Autoritat amb entrades de Wikidata i sense recursos d'autoritat
select distinct( i.article ), i.id from (select d.article, d.id from ( select b.article from bios b left join (select * from whatlinks where
against='Plantilla:Autoritat') as   w on b.article=w.article where w.against is not null ) as l left join wikidata d on d.article=l.article ) as i
where i.id not in ( select distinct(id) from authorities ) order by i.article ASC;

