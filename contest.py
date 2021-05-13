import argparse
import subprocess
import os
import sys
import enum
from abc import abstractmethod, ABCMeta
#import resource
import datetime
import time
from tabulate import tabulate
from hurry.filesize import size
import logging


class Status(enum.Enum):
    OK = 0
    RUNTIME_ERROR = 1
    WRONG_ANSWER = 2


class Test:

    def __init__(self, directory, input_file, output_file):
        self._in = Test._join(directory, input_file)
        self._out = Test._join(directory, output_file)
        self.status = None
        self.answer = ''
        self.output = ''
        self.time = None
        self.memory = None

    @staticmethod
    def _join(directory, file):
        return os.path.join(directory if directory else '', file)

    def read_input(self):
        return read_file(self._in)

    def read_answer(self):
        return read_file(self._out).strip()


class Program(metaclass=ABCMeta):

    def __init__(self, path):
        self._path = path

    @abstractmethod
    def run_test(self, test):
        pass

    @abstractmethod
    def generate_test(self, generator):
        pass

    def _test(self, args, test):
        then = time.time()

        # TODO: Handle timeouts
        proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = proc.communicate(input=test.read_input().encode('utf-8'))

        err = res[1].decode('utf-8').strip()

        now = time.time()

        if len(err) > 0:
            test.status = Status.RUNTIME_ERROR
            logging.info('RE {}\n{}'.format(test._in, err))
        else:
            test.answer = test.read_answer()
            test.output = res[0].decode('utf-8').strip()
            test.status = Status.OK if test.answer == test.output else Status.WRONG_ANSWER

        if test.status == Status.WRONG_ANSWER:
            logging.info('WA {}\nExpected:\n{}\nGot:\n{}\n'.format(test._in, test.answer, test.output))

        test.time = datetime.timedelta(seconds=now - then)

        # TODO: Fix memory usage
        test.memory = 0
        #test.memory = usage_end.ru_maxrss - usage_start.ru_maxrss'''

    def _gen(self, args, generator, test):
        #TODO: Handle RE
        res_i = subprocess.run(['python', generator], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if res_i.returncode == 0:
            # TODO: Handle RE
            res_o = subprocess.run(args, input=res_i.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if res_o.returncode == 0:
                with open(test._in, 'w+') as f:
                    f.write(res_i.stdout.decode('utf-8'))
                with open(test._out, 'w+') as f:
                    f.write(res_o.stdout.decode('utf-8'))
                return True
            return False
        return False

class CompiledProgram(Program):

    def __init__(self, path):
        super().__init__(path)

    @abstractmethod
    def compile(self):
        pass


class PythonProgram(Program):

    def __init__(self, path):
        super().__init__(path)

    def _args(self):
        return ['python', self._path]

    def run_test(self, test):
        self._test(self._args(), test)

    def generate_test(self, generator, test):
        return self._gen(self._args(), generator, test)

class BinaryProgram(Program):
    def __init__(self, path):
        super().__init__(path)

    def _args(self):
        return [self._path]

    def run_test(self, test):
        self._test(self._args(), test)

    def generate_test(self, generator, test):
        return self._gen(self._args(), generator, test)


def create_program(program_path):
    file, ext = os.path.splitext(program_path)

    if ext == '.py':
        return PythonProgram(program_path)
    elif len(ext) == 0:
        return BinaryProgram(program_path)
    else:
        raise ValueError('Unknown program extension {}'.format(ext))


def read_file(path):
    try:
        with open(path, 'r') as f:
            res = f.read()
            return res
    except:
        return None


def test(args):
    logging.basicConfig(filename=args.l, filemode='w', level=logging.INFO)

    tests = [Test(args.d, 'i%s' % i, 'o%s' % i) for i in range(1, args.n + 1)]
    program = create_program(args.program)

    print(tabulate([(args.program, args.d, args.n)], headers=['Program', 'Directory', 'Number of tests']), end='\n\n')

    for test in tests:
        program.run_test(test)

    tests_data = [None] * len(tests)

    for i, test in enumerate(tests):
        status = None

        if test.status == Status.RUNTIME_ERROR:
            status = 'RE'
        elif test.status == Status.WRONG_ANSWER:
            status = 'WA'
        elif test.status == Status.OK:
            status = 'OK'

        tests_data[i] = (i + 1, status, '{:.2f}s'.format(test.time.total_seconds()), size(test.memory))

    print(tabulate(tests_data, headers=['Index', 'Status', 'Time', 'Memory']))


def generate(args):
    print(tabulate([(args.program, args.d, args.n)], headers=['Program', 'Directory', 'Number of tests']), end='\n\n')

    input = os.path.join(args.d if args.d else '', 'i')
    output = os.path.join(args.d if args.d else '', 'o')

    created_tests = 0
    program = create_program(args.program)

    for i in range(1, args.n + 1):
        if program.generate_test(args.generator, Test(args.d, 'i%s' % i, 'o%s' % i)):
            created_tests += 1

    print('[%s test(s) has been created]' % created_tests)


class FileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values and not os.path.exists(values):
            raise ValueError('{} doesn\'t exist'.format(values))
        setattr(namespace, self.dest, values)


def main():
    parser = argparse.ArgumentParser(prog='contest')

    subparser = parser.add_subparsers()

    test_parser = subparser.add_parser('test', help='Test your program')
    test_parser.add_argument('program', nargs='?', action=FileAction, help='Path to program')
    test_parser.add_argument('-d', action=FileAction, help='Tests directory')
    test_parser.add_argument('-n', type=int, default=1, help='Number of tests')
    test_parser.add_argument('-l', default='contest.log', help='Path to log file')
    test_parser.set_defaults(func=test)

    gen_parser = subparser.add_parser('generate', help='Generate tests')
    gen_parser.add_argument('program', action=FileAction, help='Path to program')
    gen_parser.add_argument('generator', action=FileAction, help='Path to generator')
    gen_parser.add_argument('-d', action=FileAction, help='Tests directory')
    gen_parser.add_argument('-n', type=int, default=1, help='Number of tests')
    gen_parser.set_defaults(func=generate)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('contest failed: {}'.format(exc), file=sys.stderr)