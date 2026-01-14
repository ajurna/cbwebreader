$version=uv version --short
docker build .  -t ajurna/cbwebreader -t ajurna/cbwebreader:$version
docker push ajurna/cbwebreader --all-tags
