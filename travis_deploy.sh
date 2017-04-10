#!/usr/bin/env bash

# This script allows TravisCI to generate the API documentation for each
# commit on master branch and to deploy it to the vulk-api repository.
# API_USER and API_PASS are travis secure variable
git clone https://$API_USER:$API_PASS@github.com/realitix/vulk-api.git vulk-api > /dev/null 2>&1
rm -rf vulk-api/docs
sphinx-apidoc -f -o vulk-api vulk
LD_LIBRARY_PATH=VulkanSDK/1.0.46.0/x86_64/lib make -C vulk-api html
mv vulk-api/_build/html vulk-api/docs
rm -rf vulk-api/_build
git --git-dir=vulk-api/.git --work-tree=vulk-api config user.name "realitix Travis User"
git --git-dir=vulk-api/.git --work-tree=vulk-api config user.email "realitix@fake.com"
git --git-dir=vulk-api/.git --work-tree=vulk-api add -A
git --git-dir=vulk-api/.git --work-tree=vulk-api commit -m "$TRAVIS_COMMIT_MSG" > /dev/null 2>&1
git --git-dir=vulk-api/.git --work-tree=vulk-api push origin master > /dev/null 2>&1

# Deploy documentation in vulk-doc
git clone https://$API_USER:$API_PASS@github.com/realitix/vulk-doc.git vulk-doc > /dev/null 2>&1
rm -rf vulk-doc/*
python setup.py doc
git --git-dir=vulk-doc/.git --work-tree=vulk-doc config user.name "realitix Travis User"
git --git-dir=vulk-doc/.git --work-tree=vulk-doc config user.email "realitix@fake.com"
git --git-dir=vulk-doc/.git --work-tree=vulk-doc add -A
git --git-dir=vulk-doc/.git --work-tree=vulk-doc commit -m "$TRAVIS_COMMIT_MSG" > /dev/null 2>&1
git --git-dir=vulk-doc/.git --work-tree=vulk-doc push origin master > /dev/null 2>&1

