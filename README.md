# ensembl-prodinf-masterdb

This repository is issued from initial https://github.com/Ensembl/ensembl-production-services repo split. 

INSTALL
=======

1. clone the repo
   
    git clone https://github.com/Ensembl/ensembl-prodinf-masterdb

2. cd ensembl-prodinf-masterdb

3. Install dependencies in you favorite virtual env

   ```
   pip install -r requirements.txt
   ```

4. Install and run test app

   ```shell
   ./src/manage.py migrate
   ./src/manage.py runserver
   ```
