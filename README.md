# dbdelve-bin

AUR packaging for [DBDelve](https://github.com/ShayanAbbas1/dbdelve), a database
client for PostgreSQL, MySQL and SQLite. Packages the upstream Linux release
tarballs for `x86_64` and `aarch64`, including desktop integration and licenses.

## Build and install

On Arch Linux, with `base-devel` installed:

```sh
makepkg -si
```

A working Vulkan or OpenGL driver is required. Install a Secret Service provider
(such as `gnome-keyring` or `kwallet`) to save passwords, and
`xdg-desktop-portal` with the backend for your desktop to use export dialogs.

## Automatic updates

The GitHub Actions workflow runs hourly, on manual dispatch, and when packaging
or automation files change on the default branch. It checks the latest stable
upstream release, verifies both architecture downloads with SHA-256, resets
`pkgrel` for new versions, and regenerates `.SRCINFO` using Arch's `makepkg`.
Replaced assets at the same version increment `pkgrel`. Unchanged assets are
recognized using GitHub's SHA-256 digests without downloading them again.
Incomplete releases and downgrades fail without changing the package.

To enable publishing:

1. Push this directory to a GitHub repository and enable GitHub Actions.
2. Add an SSH public key to your AUR account and save its corresponding private
   key as the repository Actions secret `AUR_SSH_PRIVATE_KEY`.
3. Ensure your AUR account can publish `dbdelve-bin`, then run **aur-auto-update**
   from the Actions tab. The workflow supports an empty AUR repository for the
   first submission.

The workflow needs permission to write repository contents; its YAML requests
`contents: write`. Repository or organization rules must allow the workflow to
push directly to the default branch. Git commits use the same PandaDEV identity
as the neighboring AUR repositories.

Only `PKGBUILD` and `.SRCINFO` are published to AUR. AUR history is preserved,
and every run retries synchronization even if the upstream version is unchanged.
Without the SSH secret, the workflow still updates GitHub and reports that AUR
publishing was skipped.

For a local metadata update:

```sh
python3 .github/scripts/update.py
makepkg --printsrcinfo > .SRCINFO
```
