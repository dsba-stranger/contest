# Contest
Generate tests and check them against your solution.

## Generating
If you have a valid solution, you can generate some tests in order to test your other, probably, more complicated program.

Suppose you have the following code that returns a sum of two numbers.
##### main.py
```
a = int(input())
b = int(input())
print(a + b)
```

In order to generate tests you need a **generator**, basically, a script that returns random input.

##### generator.py
```
import random
print(random.randint(0, 100))
print(random.randint(0, 100))
```

Eventually, generate 100 tests in **tests** directory.

`python contest.py generate main.py generator.py -d tests -n 100`

For each test this command creates two files which start with **i** and **o**, for instance, i1, o1, i2, o2 and so on.

## Testing

Having some tests in a directory: i1, o1, i2, o2, e.t.c, one can test his program with the following command.

`python contest.py test YOUR_PROGRAM.py -d DIRECTORY_WITH_TESTS -n NUMBER_OF_TESTS`

