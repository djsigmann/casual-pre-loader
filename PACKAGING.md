# Stable Releases
All stable releases MUST be versioned under a subset of [semver 2.0](https://semver.org/spec/v2.0.0.html), and MAY NOT contain pre-release information nor build metadata.

A stable release's version is respective to the tag it was built from, which MUST be equivalent to the version string appended to the letter 'v'. E.g. version `1.0.0` is cognate to the tag `v1.0.0`.

## Examples
### The following are valid and in ascending order of recency:
- `1.0.0`
- `1.0.1`
- `1.1.0`
- `1.2.0`
- `2.0.0`

### The following are invalid:
- `1.0.0-post1`
- `1.0.0-dev33+gbadbeef`

# Other Releases
Internal tooling and testing MUST additionally append revision data similar to [semver 2.0](https://semver.org/spec/v2.0.0.html) notation denoting how many commits have been made since the latest tag and the commit hash the release was built from.

These could be considered pre-releases of the next tag (which may be unknown at the time, hence why we use the revision notation instead of release candidate notation).

Such releases MUST NOT be published to package registries and SHOULD NOT be packaged by third-party packagers. These SHOULD be considered ephemeral and MAY BE deleted, renamed, or replaced at any time.

## Examples
### A version string of `1.0.0-r3+gfacaded` denotes that the respective release:
- Is built from the `3rd` revision of the `1.0.0` tag, i.e. `3` commits have been made since then.
- The commit the release was built off of has a unique abbreviated commit hash of `facaded`.
