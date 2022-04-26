# Demo Dashboard

A simple demo dashboard built with [streamlit](https://docs.streamlit.io/).

## Developing & Debugging

### Installing Dependencies

This project uses python-poetry for dependency management - please install poetry before getting started.

If this is your first time using poetry and you're used to creating your venvs within the project directory, run poetry config virtualenvs.in-project true to configure poetry to do the same.

To bootstrap the project environment run $ poetry install. This will create a new virtual-env for the project and install both the package and dev dependencies.

To execute any python script run $ poetry run python my_script.py

Alternatively you may roll your own virtual-env with either venv, virtualenv, pyenv-virtualenv etc. Poetry will play along an recognize if it is invoked from inside a virtual environment.

### Running The App

To start the app in debug mode, run:

```console
streamlit run frontend/dashboard.py
```

If you're developing locally with local accounts present, you won't need to provide an auth token to inspect your private streams.

Note: Private streams will not be available in the embedded viewer.
