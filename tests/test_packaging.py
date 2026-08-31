"""The package metadata has to stay shippable.

A broken pyproject only shows up at release time, which is the worst moment to
find out.
"""

import os
import re

import aura

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:                                  # 3.11+
    import tomllib
except ModuleNotFoundError:           # pragma: no cover - older interpreters
    tomllib = None

import pytest


def config():
    if tomllib is None:
        pytest.skip('tomllib needs Python 3.11+')
    with open(os.path.join(REPO, 'pyproject.toml'), 'rb') as handle:
        return tomllib.load(handle)


def test_pyproject_parses():
    assert config()['project']['name'] == 'auralang'


def test_the_command_points_at_something_real():
    target = config()['project']['scripts']['aura']
    module, _, attribute = target.partition(':')

    assert module == 'aura'
    assert callable(getattr(aura, attribute)), '%s is not callable' % target


def test_the_shipped_module_is_the_only_one():
    """Shipping a second top-level module would squat a global name."""
    assert config()['tool']['setuptools']['py-modules'] == ['aura']


def test_no_runtime_dependencies():
    """The pitch is 'nothing to install'; keep it true."""
    assert config()['project']['dependencies'] == []


def test_the_version_looks_like_a_version():
    assert re.fullmatch(r'\d+\.\d+\.\d+', config()['project']['version'])


def test_the_declared_python_floor_matches_the_classifiers():
    project = config()['project']
    floor = project['requires-python']
    assert floor.startswith('>=3.')

    lowest = floor.split('>=')[1]
    assert any(c.endswith(lowest) for c in project['classifiers']), \
        'no classifier for the minimum Python %s' % lowest


def test_the_licence_is_an_spdx_expression_not_a_licence_body():
    """PyPI rejects a whole licence text in the License field with a 400.

    `license = { file = "LICENSE" }` inlines the entire file into the
    metadata; under Metadata-Version 2.4 that is invalid and the upload fails
    with an unexplained Bad Request. It has to be a short SPDX expression.
    """
    licence = config()['project']['license']

    assert isinstance(licence, str), 'license must be an SPDX string, not a table'
    assert '\n' not in licence, 'license looks like a licence body, not an expression'
    assert len(licence) < 40, 'license looks like a licence body, not an expression'
    assert licence == 'MIT'


def test_the_licence_file_is_shipped_and_exists():
    assert config()['project']['license-files'] == ['LICENSE']
    assert os.path.exists(os.path.join(REPO, 'LICENSE'))


def test_no_licence_classifier_alongside_the_expression():
    """PEP 639 replaces the classifier; carrying both is rejected."""
    classifiers = config()['project']['classifiers']
    assert not [c for c in classifiers if c.startswith('License ::')], \
        'drop the License :: classifier when using a license expression'


def test_the_readme_referenced_is_the_real_one():
    assert config()['project']['readme'] == 'README.md'
    assert os.path.exists(os.path.join(REPO, 'README.md'))


def test_shell_still_works_as_a_front_door():
    """python shell.py must keep working after the REPL moved into aura."""
    import shell

    assert shell.repl is aura.repl
    assert shell.main is aura.repl


def test_the_readme_has_no_relative_links():
    """PyPI renders the README with relative links resolved against pypi.org.

    `[CONTRIBUTING.md](CONTRIBUTING.md)` becomes
    pypi.org/project/auralang/CONTRIBUTING.md/ and 404s for every visitor.
    Absolute URLs behave identically on GitHub.
    """
    with open(os.path.join(REPO, 'README.md'), encoding='utf-8') as handle:
        readme = handle.read()

    relative = re.findall(r'\]\((?!https?://|#)([^)]+)\)', readme)
    assert not relative, 'relative links break on PyPI: %s' % relative
