#!/usr/bin/env python
import os
import re
import argparse

import logging
logger = logging.getLogger(__name__)


here = os.path.dirname(__file__) or os.curdir


def mkdir_p(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def walk(root):
    # yield lists of filepaths that are as relative as `root` is.
    # does not yield directories. thus, empty directories will be totally ignored.
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def find_variables(project):
    for filepath in walk(project):
        text = open(filepath).read()
        for variable in re.findall(r'<%(\w+)%>', text):
            yield variable


def interpolate(string, variables):
    def repl(match):
        return variables.get(match.group(1), '')

    return re.sub(r'<%(\w+)%>', repl, string)


def copy_interpolate(project, destination, variables):
    for source_filename in walk(project):
        target_filename = interpolate(source_filename, variables)
        target_filepath = os.path.join(destination, target_filename)
        target_directory = os.path.dirname(target_filepath)
        # make sure we can write to where target_filepath needs to be
        mkdir_p(target_directory)
        # ignore if it already exists
        if os.path.exists(target_filepath):
            logger.debug('%s exists; not overwriting', target_filepath)
        else:
            source_contents = open(source_filename, 'rb').read()
            target_contents = interpolate(source_contents, variables)
            open(target_filepath, 'wb').write(target_contents)
            logger.info('%s -> %s', source_filename, target_filepath)


def main():
    # projects = [name for name in os.listdir(here) if os.path.isdir(os.path.join(here, name))]
    projects = [name for name in os.listdir('.') if os.path.isdir(name)]

    parser = argparse.ArgumentParser(
        description='Recursive copy with variable interpolation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('project', choices=projects, help='Type of project')
    parser.add_argument('destination', help='Directory to install to')
    parser.add_argument('--verbose', action='store_true', help='Log extra information')
    opts, _ = parser.parse_known_args()

    level = logging.DEBUG if opts.verbose else logging.INFO
    logging.basicConfig(level=level)

    os.chdir(os.path.join(here, opts.project))
    logger.info('current working directory: %s', os.getcwd())

    variables = set(find_variables('.'))

    for variable in variables:
        default = os.getenv(variable)
        kw = dict(help='Template variable')
        if default is not None:
            kw['default'] = default
        else:
            kw['required'] = True
        parser.add_argument('--' + variable, **kw)

    opts = parser.parse_args()

    # last key wins conflicts in the dict constructor
    values = dict(os.environ.items() + vars(opts).items())
    copy_interpolate('.', opts.destination, values)
    logger.debug('Done')


if __name__ == '__main__':
    main()
