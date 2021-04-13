[![Build Status](https://travis-ci.com/Ensembl/ensembl-prodinf-masterdb.svg?token=uixv5pZneCqzQNs8zEJr&branch=main)](https://travis-ci.com/Ensembl/ensembl-prodinf-masterdb)
[![codecov](https://codecov.io/gh/Ensembl/ensembl-prodinf-masterdb/branch/main/graph/badge.svg?token=E56NJVCM93)](https://codecov.io/gh/Ensembl/ensembl-prodinf-masterdb)
# ensembl-prodinf-masterdb

This repository is issued from initial https://github.com/Ensembl/ensembl-production-services repo split. 

INSTALL
=======

1. clone the repo
   
    git clone https://github.com/Ensembl/ensembl-prodinf-masterdb

2. Install dependencies in you favorite virtual env

   ```
   cd ensembl-prodinf-masterdb
   pip install -r requirements-dev.txt
   ```

3. Install and run test app

   ```shell
   ./src/manage.py migrate
   ./src/manage.py runserver
   ```
