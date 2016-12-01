#!/usr/bin/env bash

# This script allows TravisCI to generate the API documentation for each
# commit on master branch and to deploy it to the vulk-api repository.
# API_USER and API_PASS are travis secure variable

git clone https://$API_USER:$API_PASS@github.com/realitix/vulk-api.git vulk-api > /dev/null 2>&1
rm -rf vulk-api/*
python setup.py api
git --git-dir=vulk-api/.git --work-tree=vulk-api config user.name "realitix Travis User"
git --git-dir=vulk-api/.git --work-tree=vulk-api config user.email "realitix@gmail.com"
git --git-dir=vulk-api/.git --work-tree=vulk-api add -A
git --git-dir=vulk-api/.git --work-tree=vulk-api commit -m "$TRAVIS_COMMIT"
git --git-dir=vulk-api/.git --work-tree=vulk-api push origin master > /dev/null 2>&1
