# Debian Builds for the pydoover library

Mostly used to make pydoover CLI easily accessible, otherwise install with pip in a virtual environment. 

## Release Cycle

An apt package is built and deployed automatically on a Github release, and should match PyPI releases.


## Resources

- [https://wiki.debian.org/Python/LibraryStyleGuide](https://wiki.debian.org/Python/LibraryStyleGuide)
- [https://trstringer.com/creating-python-pkg-ubuntu](https://trstringer.com/creating-python-pkg-ubuntu)
- [https://salsa.debian.org/python-team/packages/black/-/blob/master/pyproject.toml?ref_type=heads#L87](https://salsa.debian.org/python-team/packages/black/-/blob/master/pyproject.toml?ref_type=heads#L87)

Uses pybuild to build a python module.

To add cli to path the following config is added to [pyproject.toml](../pyproject.toml)

```toml
[project.scripts]
pydoover = "pydoover.cli.main:main"
```
