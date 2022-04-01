$version=poetry version -s
docker build . --no-cache -t ajurna/cbwebreader -t ajurna/cbwebreader:$version
docker push ajurna/cbwebreader:$version
docker push ajurna/cbwebreader