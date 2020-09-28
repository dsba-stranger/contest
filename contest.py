import argparse
import subprocess
import os
import sys
import enum


class Status(enum.Enum):
    OK = 0
    RUNTIME_ERROR = 1
    WRONG_ANSWER = 2


def read_file(path):
    try:
        with open(path, 'r') as f:
            res = f.read()
            return res
    except:
        return None


def run_test(program, input, output, i):
    res = subprocess.run(['python', program], input=input.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    status = None

    if res.returncode != 0:
        status = Status.RUNTIME_ERROR
    else:
        prog_output = res.stdout.decode('utf-8').strip()
        output = output.strip()
        status = Status.OK if prog_output == output else Status.WRONG_ANSWER

    print(i, end=' ')

    if status == Status.RUNTIME_ERROR:
        print('RE')
    elif status == Status.WRONG_ANSWER:
        print('WA\n\tExpected:\n\t{}\n\tGot:\n\t{}'.format(output, prog_output))
    else:
        print('OK')


def test(args):
    print('[Testing {} | {} test(s)]'.format(args.program, args.n))

    input = os.path.join(args.d if args.d else '', 'i')
    output = os.path.join(args.d if args.d else '', 'o')

    print('[Dir = {} | Input = {}* | Output = {}*]'.format(args.d, input, output))

    for i in range(1, args.n + 1):
        input_cont = read_file(input + str(i))

        if not input_cont:
            print('{} [Cannot open {}]'.format(i, input + str(i)))
            continue

        output_cont = read_file(output + str(i))

        if not output_cont:
            print('{} [Cannot open {}]'.format(i, output + str(i)))
            continue

        run_test(args.program, input_cont, output_cont, i)


def generate(args):
    print('[Generating tests from {}]'.format(args.program))

    input = os.path.join(args.d if args.d else '', 'i')
    output = os.path.join(args.d if args.d else '', 'o')

    print('[Dir = {} | Input = {}* | Output = {}*]'.format(args.d, input, output))

    created_tests = 0

    for i in range(1, args.n + 1):
        res_i = subprocess.run(['python', args.generator], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        if res_i.returncode == 0:
            res_o = subprocess.run(['python', args.program], input=res_i.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

            if res_o.returncode == 0:
                with open(input + str(i), 'w+') as f:
                    f.write(res_i.stdout.decode('utf-8'))
                with open(output + str(i), 'w+') as f:
                    f.write(res_o.stdout.decode('utf-8'))

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