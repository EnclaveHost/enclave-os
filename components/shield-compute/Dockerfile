FROM alpine@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
RUN apk add --no-cache build-base cmake samurai git ca-certificates python3 openssl-dev patchelf
WORKDIR /build
ENTRYPOINT ["/bin/sh", "/input/build.sh"]
