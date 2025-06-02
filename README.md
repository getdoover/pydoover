# PyDoover: The Python Package for Doover

PyDoover is a Python package that provides a simple and easy-to-use interface for using the Doover platform on devices, in tasks and CLIs.

# Getting Started

## Installing
**Python 3.11 or higher is required**

```shell
# Using UV
uv add pydoover

# Using pip
pip install -U pydoover

# to install the development version:
pip install -U git+https://github.com/spaneng/pydoover
```

If you are using `pydoover` and need **grpc** support and **are not** using the `doover_device_base` docker image, install the grpc optional dependencies:

We currently use `grpcio==1.65.1` across all our services, so you need to install this version of `grpcio` to avoid issues.
```bash
uv add pydoover[grpc]
# or
pip install -U pydoover[grpc]
```

### Debian Package
The `pydoover` package (in particular CLI) is also available as a Debian package. You can install it using the following command:

```bash
# add the Doover apt repository:
sudo wget http://apt.u.doover.com/install.sh -O - | sh

# install the package
sudo apt install doover-pydoover
```

## Development

To install all dependencies for development, install all optional dependencies (grpc, reports, test, etc.), run:
```bash
uv sync --all-extras
```

We use pre-commit hooks to ensure code quality and consistency using Ruff. To set up pre-commit hooks, run the following command:

```bash
pre-commit install
```

To run unit tests, use `pytest` in the main directory of the repository:

```bash
uv run pytest
```


## Contributing

For more information, please reach out to the maintainers at hello@doover.com

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
