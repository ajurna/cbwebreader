poetry export -f requirements.txt --output requirements.txt
$version=poetry version -s
docker build . --no-cache -t ajurna/cbwebreader:beta
docker push ajurna/cbwebreader@beta