"""The README promises Python 3.9+, and CI runs it there. Keep that honest."""

import ast
import glob
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ['aura.py', 'shell.py'] + sorted(
    os.path.relpath(path, REPO) for path in glob.glob(os.path.join(REPO, 'tests', '*.py'))
)


def test_every_source_file_parses_as_python_39():
    problems = []

    for name in SOURCES:
        path = os.path.join(REPO, name)
        with open(path, encoding='utf-8') as handle:
            source = handle.read()
        try:
            ast.parse(source, filename=name, feature_version=(3, 9))
        except SyntaxError as exc:
            problems.append(f'{name}:{exc.lineno}: {exc.msg}')

    assert not problems, '\n'.join(problems)


def test_no_runtime_dependencies_are_imported():
    """aura.py must run on a bare interpreter - stdlib only."""
    with open(os.path.join(REPO, 'aura.py'), encoding='utf-8') as handle:
        tree = ast.parse(handle.read())

    stdlib = {'sys', 'os', 'math'}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split('.')[0])

    assert imported <= stdlib | {'shell'}, f'unexpected imports: {imported - stdlib}'
