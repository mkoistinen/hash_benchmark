# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import base64
import hashlib
import random
import string
import sys
import time

from django import __version__ as django_version
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.auth.hashers import check_password
from django.core.management.base import BaseCommand
from django.utils.crypto import pbkdf2


def custom_encode(password, salt,
                  algorithm='pbkdf2_sha256',
                  digest=None,
                  iterations=100000):
    """
    Builds the password with the specs we want.
    """
    assert password is not None
    assert salt and '$' not in salt
    if not digest:
        digest = hashlib.sha256
    hash = pbkdf2(password, salt, iterations, digest=digest)
    hash = base64.b64encode(hash).decode('ascii').strip()
    return "%s$%d$%s$%s" % (algorithm, iterations, salt, hash)


def password_generator(length=12, chars=None):
    """
    Naive password generator
    """
    if not chars:
        chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


class Command(BaseCommand):
    help = """Benchmarks password hashing."""

    def add_arguments(self, parser):
        parser.add_argument(
            '-o', '--operations', action='store', type=int,
            required=False, default=20,
            help='number of times to average')

        parser.add_argument(
            '-i', '--iterations', action='store', type=int,
            required=False, default=30000,
            help='number of hashing iterations')

    def handle(self, *args, **options):
        operations = options['operations']
        iterations = options['iterations']

        plaintext = password_generator(length=16)
        salt = password_generator(length=8)
        ciphertext = custom_encode(plaintext, salt=salt, iterations=iterations)

        t1 = time.time()
        for _ in range(0, operations):
            assert check_password(plaintext, ciphertext)
        duration = time.time() - t1

        avg = duration / operations
        cipher, iterations = ciphertext.split('$')[:2]

        print('Python: {0}\nDjango: {1}'.format(sys.version, django_version))
        print('Using cipher: "{0}" with {1} iterations, verification takes, '
              'on average, {2:0.4f}s'.format(
                cipher, intcomma(iterations, False), avg))
