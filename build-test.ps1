poetry export --without-hashes -f requirements.txt --output requirements.txt
$version=poetry version -s
docker build . -t ajurna/cbwebreader:beta --no-cache
# docker push ajurna/cbwebreader:beta