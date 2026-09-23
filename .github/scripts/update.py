#!/usr/bin/env python3
"""Update PKGBUILD from a complete stable upstream release."""

import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request


UPSTREAM = 'https://github.com/ShayanAbbas1/dbdelve'
API = 'https://api.github.com/repos/ShayanAbbas1/dbdelve/releases/latest'
ARCHES = ('x86_64', 'aarch64')


def release_metadata():
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'dbdelve-aur-updater'}
    if token := os.environ.get('GH_TOKEN'):
        headers['Authorization'] = f'Bearer {token}'
    with urllib.request.urlopen(urllib.request.Request(API, headers=headers), timeout=60) as response:
        return json.load(response)


def checksum(url):
    digest = hashlib.sha256()
    # The API token is intentionally only sent to api.github.com.
    with urllib.request.urlopen(url, timeout=120) as response:
        for chunk in iter(lambda: response.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def field(text, name):
    matches = re.findall(rf'^{re.escape(name)}=(.+)$', text, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one {name} assignment')
    return matches[0]


def update(text, release):
    tag = release['tag_name']
    if release.get('draft') or release.get('prerelease') or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError(f'Expected a stable vMAJOR.MINOR.PATCH release, got {tag!r}')
    version = tag[1:]
    current = field(text, 'pkgver')
    if tuple(map(int, version.split('.'))) < tuple(map(int, current.split('.'))):
        raise ValueError(f'Refusing to downgrade {current} to {version}')

    assets = {}
    for arch in ARCHES:
        name = f'dbdelve-{version}-linux-{arch}.tar.gz'
        matches = [asset for asset in release['assets'] if asset['name'] == name]
        if len(matches) != 1 or matches[0].get('state') != 'uploaded':
            raise ValueError(f'Release must contain one uploaded {name}')
        asset = matches[0]
        expected_url = f'{UPSTREAM}/releases/download/{tag}/{name}'
        if asset['browser_download_url'] != expected_url:
            raise ValueError(f'Unexpected download URL for {name}')
        assets[arch] = asset

    hashes = {}
    for arch, asset in assets.items():
        old_hash = field(text, f'sha256sums_{arch}')
        old_digest = old_hash.removeprefix("('").removesuffix("')")
        remote_digest = asset.get('digest')
        if version == current and remote_digest == f'sha256:{old_digest}':
            hashes[arch] = old_hash
            continue
        downloaded = checksum(asset['browser_download_url'])
        if remote_digest and remote_digest != f'sha256:{downloaded}':
            raise ValueError(f'Checksum mismatch for {asset["name"]}')
        hashes[arch] = f"('{downloaded}')"

    if version == current and all(field(text, f'sha256sums_{a}') == hashes[a] for a in ARCHES):
        return text

    replacements = {'pkgver': version, 'pkgrel': '1' if version != current else str(int(field(text, 'pkgrel')) + 1)}
    replacements.update({f'sha256sums_{arch}': value for arch, value in hashes.items()})
    for name, value in replacements.items():
        field(text, name)
        text = re.sub(rf'^{re.escape(name)}=.+$', lambda _: f'{name}={value}', text, flags=re.MULTILINE)
    return text


def main():
    path = Path('PKGBUILD')
    current = path.read_text()
    updated = update(current, release_metadata())
    if updated == current:
        print('Already up to date.')
    else:
        path.write_text(updated)
        print(f'Updated to {field(updated, "pkgver")}-{field(updated, "pkgrel")}')


if __name__ == '__main__':
    main()
