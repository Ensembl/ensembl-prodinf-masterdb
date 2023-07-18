CHANGELOG - Ensembl Prodinf MasterDB
====================================
1.2.3
-----
- Reverted  to django-jsonfield, JSON_EXRACT is not supported for mysql

1.2.2
-----
- Fixed filtering on db_types for Biotype and MetaKey

1.2.0
-----
- Removed reference to django-jsonfield, because integrated in main Django now

1.1
---
- Change Attrib Types "Code" field to be read-only
- Enable users to filter on a model specific fields, not only the common ones defined in the parent class


1.0
---
- Moved from initial production services monolithic application (https://github.com/Ensembl/ensembl-production-services)
- Django standard layout / Turned initial source into Portable app.
- Changed namespace to `ensembl.production.masterdb`

