#!/bin/sh
# L6 repo hygiene. Run from a site's root, before the build.
#   sh vendor/site-ui/tests/check_repo.sh
# With SITE_UI_DIR set (a local clone for development) only the folder check runs.
dir="${SITE_UI_DIR:-vendor/site-ui}"
if [ ! -f "$dir/tokens.css" ]; then
  echo "FAIL L6 $dir/tokens.css not found: run 'git submodule update --init'"
  exit 1
fi
if [ -z "$SITE_UI_DIR" ]; then
  if ! tag=$(git -C vendor/site-ui describe --exact-match --tags 2>/dev/null); then
    echo "FAIL L6 vendor/site-ui is not on a tag: check out a release tag and commit the pointer"
    exit 1
  fi
  echo "check_repo: site-ui $tag"
else
  echo "check_repo: using SITE_UI_DIR=$SITE_UI_DIR"
fi
