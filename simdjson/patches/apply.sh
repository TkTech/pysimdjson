#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/../.."
cp simdjson/simdjson_source/simdjson.{h,cpp} simdjson/
patch -ruN -p0 < simdjson/patches/float-aware-minify.patch
