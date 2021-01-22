# Pàgines amb plantilla Autoritat amb entrades de Wikidata i sense recursos d'autoritat
select t.article from ( select distinct(i.id) from (select d.article, d.id from ( select b.article from bios b left join (select * from whatlinks where against='Plantilla:Autoritat') as   w on b.article=w.article where w.against is null ) as l left join wikidata d on d.article=l.article order by d.id ) as i left join ( select distinct(id) from authorities order by id ) as a on i.id=a.id where a.id is null ) as f, wikidata t where f.id=t.id order by t.article ASC;