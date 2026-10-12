#!/usr/bin/env bash
# Applies the Axon Framework 4 -> 5 OpenRewrite recipe to the current working
# directory. The CWD must be the target project root (where pom.xml or
# build.gradle[.kts] lives). Self-locates so it can be invoked by absolute path.
#
# Usage:  migrate.sh [axon|axoniq] [recipe-version]
# Default framework: axoniq
#
# Recipe artifact version defaults to ../references/recipe-version.

set -euo pipefail

if [ "$#" -gt 2 ]; then
  echo "ERR: usage: migrate.sh [axon|axoniq] [recipe-version]" >&2
  exit 2
fi

framework="${1:-axoniq}"
case "$framework" in
  axon)
    recipe="org.axonframework.migration.UpgradeAxon4ToAxon5"
    ;;
  axoniq)
    recipe="io.axoniq.framework.migration.UpgradeAxon4ToAxoniq5"
    ;;
  *)
    echo "ERR: framework must be 'axon' or 'axoniq' (got: '$framework')" >&2
    exit 2
    ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$#" -eq 2 ]; then
  version="$2"
else
  version_file="$(cd "$script_dir/../references" && pwd)/recipe-version"
  if [ ! -f "$version_file" ]; then
    echo "ERR: recipe-version file missing at $version_file" >&2
    exit 6
  fi
  version="$(tr -d '[:space:]' < "$version_file")"
  if [ -z "$version" ]; then
    echo "ERR: recipe-version file is empty: $version_file" >&2
    exit 6
  fi
fi
if [[ ! "$version" =~ ^[0-9][A-Za-z0-9._-]*$ ]]; then
  echo "ERR: recipe version must start with a digit and contain only letters, digits, '.', '_', or '-'" >&2
  exit 2
fi
init_gradle="$(cd "$script_dir/../assets" && pwd)/init.gradle"

if [ ! -f "$init_gradle" ]; then
  echo "ERR: bundled init.gradle missing at $init_gradle" >&2
  exit 4
fi

if [ -f pom.xml ]; then
  echo "Using org.axonframework:axon-migration:${version} (${recipe})" >&2
  exec mvn -U org.openrewrite.maven:rewrite-maven-plugin:6.46.1:run \
    "-Drewrite.recipeArtifactCoordinates=org.axonframework:axon-migration:${version}" \
    "-Drewrite.activeRecipes=${recipe}"
fi

if [ -f build.gradle ] || [ -f build.gradle.kts ]; then
  gradle_cmd=""
  if [ -x ./gradlew ]; then
    gradle_cmd="./gradlew"
  elif command -v gradle >/dev/null 2>&1; then
    gradle_cmd="gradle"
  else
    echo "ERR: no ./gradlew and no 'gradle' on PATH" >&2
    exit 5
  fi
  echo "Using org.axonframework:axon-migration:${version} (${recipe})" >&2
  exec "$gradle_cmd" rewriteRun \
    --init-script "$init_gradle" \
    "-Drewrite.activeRecipe=${recipe}" \
    "-Drewrite.axonMigrationVersion=${version}"
fi

echo "ERR: no pom.xml or build.gradle[.kts] in $(pwd)" >&2
exit 3
