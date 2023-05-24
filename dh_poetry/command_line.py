"""Shim between dh_virtualenv and poetry

When -r is used for pip to install dependencies use poetry instead and remove
incompatible arguments.
"""
import os
import subprocess
import sys


def _remove_kwarg(args, kwarg):
    """Remove kwarg and its value from args.

    If both are in one arg (--log=hi), remove that element, but if they are
    split between two args ['--log', 'hi'] remove both.

    Args:
        args ([str, ...]): List of strings
        kwarg (str): Usually of the form '--<name>' ie) '--log'
    """
    args = [arg for arg in args if '%s=' % kwarg not in arg]
    # If kwarg is by self, remove it and its value
    try:
        index = args.index(kwarg)
    except ValueError:
        pass
    else:
        args = args[:index] + args[index + 2:]
    return args


def convert_pip_args_to_poetry_args(pip_args):
    """Remove non poetry compatible args from arg list meant for pip_args.
    """
    # Remove -r requirements.txt
    try:
        r_index = pip_args.index('-r')
    except ValueError:
        # Unsupported behavior, but if you want to use this outside of this
        # package, go for it and "good luck"
        pass
    else:
        pip_args = pip_args[:r_index] + pip_args[r_index + 2:]
    for kwarg in [
            '--index-url',
            '--extra-index-url',
            '--log']:
        pip_args = _remove_kwarg(pip_args, kwarg)
    # Add additional args
    # Can't be specified by --extra-pip-arg in debian/rules because used by pip
    # when installing preinstall packages ie) poetry
    return pip_args


def main():
    dh_poetry = sys.argv[0]
    # Get path of dh_poetry poetry
    assert os.path.isfile(dh_poetry), "We should have a full path to dh_poetry"
    bin_dir = os.path.dirname(dh_poetry)
    pip_path = os.path.join(bin_dir, 'pip')
    if not os.path.isfile(pip_path):
        pip_path = os.path.join(bin_dir, 'pip3')

    poetry_path = os.path.join(bin_dir, 'poetry')
    assert os.path.isfile(pip_path), "Can't find pip: %s" % pip_path
    assert os.path.isfile(poetry_path), "Can't find poetry: %s" % poetry_path
    # Setup environment variables
    environment = os.environ.copy()
    # Fallback to pip if requirements.txt not specified
    pip_args = sys.argv[1:]
    if '-r' not in pip_args:
        cmd_args = [pip_path] + pip_args
    else:
        # Ensure pyproject.lock or poetry.lock exists
        lockfile_exists = any(
            os.path.isfile(os.path.join(os.getcwd(), filename))
            for filename in ('poetry.lock', 'pyproject.lock')
        )
        assert lockfile_exists, "poetry.lock doesn't exist"
        # Get args
        poetry_args = convert_pip_args_to_poetry_args(sys.argv[1:])
        cmd_args = [poetry_path] + poetry_args
        # Set VIRTUAL_ENV only for `poetry`, to make sure it installs files in
        # the right location.
        venv_dir = os.path.dirname(bin_dir)
        environment['VIRTUAL_ENV'] = environment.get('VIRTUAL_ENV', venv_dir)
    print("Executing", cmd_args, "with environment", environment)
    subprocess.check_call(cmd_args, env=environment)


if __name__ == '__main__':
    main()
