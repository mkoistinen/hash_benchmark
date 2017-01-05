# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import multiprocessing
import random
import string
import sys
import time

from django import __version__ as django_version
from django.contrib.auth.hashers import PBKDF2PasswordHasher, check_password
try:
    # This won't be available before Django 1.10
    from django.contrib.auth.hashers import Argon2PasswordHasher
except ImportError:
    Argon2PasswordHasher = None
    pass
from django.core.management.base import BaseCommand


def custom_encode(password, salt, algorithm='pbkdf2_sha256', iterations=100000,
                  time_cost=2, memory_cost=512, parallelism=2):
    """
    Hashes a password with the desired specifications.
    """
    hasher = None
    if algorithm.lower().startswith('argon'):
        if Argon2PasswordHasher:
            hasher = Argon2PasswordHasher()
            hasher.time_cost = time_cost
            hasher.memory_cost = memory_cost
            hasher.parallelism = parallelism
            kwargs = {'password': password, 'salt': salt}

    if not hasher:
        hasher = PBKDF2PasswordHasher()
        kwargs = {
            'password': password, 'salt': salt, 'iterations': iterations,
        }

    return hasher.encode(**kwargs)


def password_generator(length=12, chars=None):
    """
    Simple, naive password generator
    """
    if not chars:
        chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


class Command(BaseCommand):
    help = """Benchmarks password hashing useful for selecting hashing
    parameters for a given project on given hardware."""

    def add_arguments(self, parser):
        parser.add_argument(
            '-a', '--algorithm', action='store', type=str,
            required=False, default='pbkdf2_sha256',
            help='hashing algorithm')
        parser.add_argument(
            '-o', '--operations', action='store', type=int,
            required=False, default=20,
            help='number of times to average')
        parser.add_argument(
            '-i', '--iterations', action='store', type=int,
            required=False, default=100000,
            help='number of hashing iterations (PBKDF2 only)')
        parser.add_argument(
            '-t', '--time_cost', action='store', type=int,
            required=False, default=2,
            help='number of times to average (Argon2 only)')
        parser.add_argument(
            '-m', '--memory_cost', action='store', type=int,
            required=False, default=512,
            help='number of times to average (Argon2 only)')
        parser.add_argument(
            '-p', '--parallelism', action='store', type=int,
            required=False, default=0,
            help='number of times to average (Argon2 only)')
        parser.add_argument(
            '-w', '--work_target', action='store', type=float,
            required=False, default=0.0,
            help='number of decimal seconds to spend on password verification')

    def benchmark(self, plain_text, salt, **options):
        algorithm = options['algorithm']
        operations = options['operations']
        iterations = options['iterations']
        time_cost = options['time_cost']
        memory_cost = options['memory_cost']
        parallelism = options['parallelism']

        cipher_text = custom_encode(
            plain_text, salt=salt, iterations=iterations, algorithm=algorithm,
            time_cost=time_cost, memory_cost=memory_cost,
            parallelism=parallelism)
        t1 = time.time()
        for _ in range(0, operations):
            assert check_password(plain_text, cipher_text)
        duration = time.time() - t1

        return cipher_text, duration / operations

    def handle(self, *args, **options):
        algorithm = options['algorithm']
        iterations = options['iterations']
        time_cost = options['time_cost']
        memory_cost = options['memory_cost']
        parallelism = options['parallelism']
        work_target = options['work_target']

        if not parallelism:
            parallelism = options['parallelism'] = multiprocessing.cpu_count() * 2  # noqa

        plain_text = password_generator(length=16)
        salt = password_generator(length=8)

        cipher_text, avg = self.benchmark(plain_text, salt, **options)

        params = cipher_text.split('$')[:-2]
        print('Python: {0}\nDjango: {1}'.format(sys.version, django_version))
        print('Using "{0}" w/parameters ({1}), verification takes, on average, '
              '{2:0.4f}s'.format(params[0], ", ".join(params[1:]), avg))

        if work_target > 0.0:
            if algorithm.lower().startswith('argon'):
                sug_time_cost = int(time_cost * work_target/avg)
                print("\nTo target {0} seconds of work per verification, try "
                      "parameters: --time_cost={1} --memory_cost={2} "
                      "--parallelism={3}".format(work_target, sug_time_cost,
                                                 memory_cost, parallelism))
            else:
                sug_iterations = int(iterations * work_target/avg)
                print("\nTo target {0} seconds of work per verification, "
                      "consider --iterations={1}".format(
                        work_target, sug_iterations))

        if Argon2PasswordHasher and not algorithm.lower().startswith('argon'):
            options['algorithm'] = 'argon2'
            cipher_text, new_avg = self.benchmark(plain_text, salt, **options)

            sug_time_cost = int(time_cost * avg/new_avg)
            print("\nTo target obtain similar work time using Argon2, consider "
                  "parameters: --algorithm=argon2 --time_cost={0} "
                  "--memory_cost={1} --parallelism={2}".format(
                    sug_time_cost, memory_cost, parallelism))
