poetry export --without-hashes -f requirements.txt --output requirements.txt
$version=poetry version -s
docker build .  -t ajurna/cbwebreader -t ajurna/cbwebreader:$version
docker push ajurna/cbwebreader --all-tags
