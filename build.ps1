$version=poetry version -s
docker build . -t ajurna/cbwebreader -t ajurna/cbwebreader:$version