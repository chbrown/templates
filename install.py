#!/usr/bin/env python
import os
import re
import sys
import argparse

here = os.path.dirname(__file__) or os.curdir
os.chdir(here)


def find_variables(project):
    for dirpath, dirnames, filenames in os.walk(project):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            text = open(filepath).read()
            for variable in re.findall(r'<%(\w+)%>', text):
                yield variable


def interpolate(source_fd, target_fd, variables):
    def repl(match):
        return variables.get(match.group(1), '')

    source = source_fd.read()
    target_fd.write(re.sub(r'<%(\w+)%>', repl, source))


def copy_interpolate(project, destination, variables):
    for dirpath, dirnames, filenames in os.walk(project):
        for filename in filenames:
            source = os.path.join(dirpath, filename)
            target = os.path.join(destination, filename)
            target_directory = os.path.dirname(target)
            if not os.path.exists(target_directory):
                os.mkdir(target_directory)
            if os.path.exists(target):
                print >> sys.stderr, '%s exists; not overwriting' % target
            else:
                with open(source) as source_fd:
                    with open(target, 'w') as target_fd:
                        interpolate(source_fd, target_fd, variables)
                print >> sys.stderr, target


def main():
    # projects = [name for name in os.listdir(here) if os.path.isdir(os.path.join(here, name))]
    projects = [name for name in os.listdir('.') if os.path.isdir(name)]

    parser = argparse.ArgumentParser(
        description='Recursive copy with variable interpolation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('project', choices=projects, help='Type of project')
    parser.add_argument('destination', help='Directory to install to')
    opts, _ = parser.parse_known_args()

    variables = set(find_variables(opts.project))

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
    copy_interpolate(opts.project, opts.destination, values)
    print >> sys.stderr, 'Done'


if __name__ == '__main__':
    main()

# pattern = opts.pattern

# if not sys.stdin.isatty():
#     reader = sys.stdin
# else:
#     reader = (line for path in opts.files for line in open(path))

# if opts.last:
#     cache = []
#     for line in reader:
#         cache.append(line)
#         if pattern in line:
#             cache = []
#     print ''.join(cache),
# else:
#     found = False
#     for line in reader:
#         if found:
#             print line,
#         if pattern in line:
#             found = True
