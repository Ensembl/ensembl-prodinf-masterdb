# ensembl-prodinf-masterdb

This repository is issued from initial https://github.com/Ensembl/ensembl-production-services repo split. 

INSTALL
=======

1. clone the repo
   
    git clone https://github.com/Ensembl/ensembl-prodinf-masterdb

2. cd ensembl-prodinf-masterdb
   
3. setup.py sdist 
    ```
    python3 -m venv .venv
    source .venv/bin/activate
    setup.py sdist
    pip install sdist/[package_name].tar.gz
    ```
   
    pip install -e https://github.com/Ensembl/ensembl-prodinf-masterdb#egg=ensembl-prodinf-masterdb

