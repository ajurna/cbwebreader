$version=uvx --from=toml-cli toml get --toml-path=pyproject.toml project.version
docker build .  -t ajurna/cbwebreader -t ajurna/cbwebreader:$version
docker push ajurna/cbwebreader --all-tags
