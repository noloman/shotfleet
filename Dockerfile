# shotfleet `check` for Linux and CI: ghcr.io/noloman/shotfleet-check:<version>. Only `check` (and doctor, init) work in it:
# no simulators, emulators or Maestro, and no macOS text recognition, so Tesseract reads the screenshots.
# The image holds the compiled program (PyInstaller one-folder build), never shotfleet.py.
#   docker buildx build --platform linux/amd64,linux/arm64 --build-arg VERSION=0.1.4 -t ghcr.io/noloman/shotfleet-check:0.1.4 .
# packaging/docker-check.sh builds and pushes it for a release.

# Build: the same pinned, hash-checked inputs as the macOS build (packaging/requirements-build.txt), with the recorded Python 3.14.2.
FROM python:3.14.2-slim-trixie@sha256:1a3c6dbfd2173971abba880c3cc2ec4643690901f6ad6742d0827bae6cefc925 AS build
RUN apt-get update && apt-get install -y --no-install-recommends binutils && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY packaging/requirements-build.txt packaging/
RUN python -m venv /venv && /venv/bin/pip install --quiet --disable-pip-version-check --only-binary=:all: \
    --require-hashes -r packaging/requirements-build.txt
COPY shotfleet.py ./
COPY skill skill
# the release date (shotfleet.py baked_release_date), frozen into the program like packaging/build.sh does: the build day, in UTC
RUN mkdir build && printf 'RELEASE_DATE = "%s"\n' "$(date -u +%Y-%m-%d)" > build/_release.py
RUN /venv/bin/pyinstaller --onedir --name shotfleet --add-data "/src/skill:skill" --paths /src/build --hidden-import _release --distpath /dist --workpath /tmp/pyi \
    --specpath /tmp --noconfirm --log-level WARN shotfleet.py \
 && /dist/shotfleet/shotfleet --version \
 && ! find /dist -name '*.py' | grep .

# Runtime: Debian slim (the same Debian as the build image, so the same glibc), Tesseract with the common store languages,
# aapt2 for --app app.apk, jq for CI scripts.
FROM debian:trixie-slim@sha256:a29215f6a35e51e22adffa17f89e9d2ef06214e64a2bad10d765c46aea49f11f
ARG VERSION=dev
# Tesseract language data (Debian package suffixes). More languages: FROM this image, USER root, apt-get install tesseract-ocr-<code>.
ARG LANGS="eng deu fra spa ita por nld swe dan nor fin pol ces ron tur rus ukr ara jpn kor chi-sim chi-tra tha vie hin ind msa ell heb hun slk hrv cat bul"
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr $(for l in $LANGS; do printf 'tesseract-ocr-%s ' "$l"; done) aapt jq \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 1000 shotfleet
COPY --from=build /dist/shotfleet /opt/shotfleet
LABEL org.opencontainers.image.title="shotfleet-check" \
      org.opencontainers.image.description="shotfleet check: localized App Store and Google Play screenshots, checked on Linux with Tesseract" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.url="https://shotfleet.com" \
      org.opencontainers.image.source="https://shotfleet.com" \
      org.opencontainers.image.documentation="https://shotfleet.com/docs.html#linux"
# tells the program it is the check-only image, so `run` and `export` stop with one clear line
ENV SHOTFLEET_IMAGE=check
USER shotfleet
WORKDIR /work
ENTRYPOINT ["/opt/shotfleet/shotfleet"]
CMD ["--help"]
