Hash Benchmark
##############

Provides a managment command that times the current Django project's
password hashing settings.

This is useful for comparing and optimizing hash settings for the
running environment.


How to install
==============

* Install the package: ``pip install hash_benchmark``;
* Add ``'hash_benchmark',`` to your INSTALLED_APPS in settings.py;

Optional but **strongly** recommended:

* ``pip install argon2_cffi``.


How to use
==========

Install this package as per the above instructions in your project on
hardware typical for your project's production environment.

Run the management command with your current password hashing settings
and take a note of the performance: ::

    # Tests hashing performance of your installations pbkdf2_sha256
    # algorithm with 100,000 iterations
    > python manage.py hash_password -i 100000

    Python: 2.7.10 (default, Jul 13 2015, 12:05:58) 
    [GCC 4.2.1 Compatible Apple LLVM 6.1.0 (clang-602.0.53)]
    Django: 1.9.7
    Using "pbkdf2_sha256" w/parameters (100000), verification takes, on average, 0.0821s

Now, decide if this "work factor" (average password verification
duration) is appropriate for your project's needs. Your goal is to spend
as much time hashing as possible and still have acceptable performance
for your users during password verification.

Important considerations for choosing the right work-level are:

* Considerations for a higher work-factor:

  *  Stronger protection of your hashed passwords against brute-
     force attacks, possibly requiring less frequent forced password
     change policies for your users

* Considerations for a lower work-factor:

  *  Faster log-ins for users;
  *  Better site performance when many users are logging-in
     simultaneously;
  *  Large work-factors can be exploited remotely to cause DDoS
     attacks on your site

Armed with this management command, you can now make informed decisions
about the settings to use for PBKDF2_SHA256 and its
iterations parameter.


Switching to Argon2
===================

Argon2 is a newer password hashing algorithm that is supported in
Django 1.10 when the 3rd-party library `argon2_cffi` is installed
(see above). Argon2 is designed to be more resilient to GPU-based
brute-force attacks.

The argon2_cffi implementation is already very fast due to the fact that
it is implemented as a compile C-library and is multi-threaded. This
already makes it significantly faster than anything written in Python.

Casual anecdotal evidence from the internet collated by this author in
Jan 2017 suggests that for the same duration of work (in seconds), a
Django installation configured to run Argon2 is estimated to be about
1,500X more resilient than a SHA256-based algorithm against GPU-based
brute-force attacks.

    :Notice:
    
    Please do not make important decisions based on these figures, do
    your own research!

If Argon2 is right for your project, it is suggested that the
parallelism parameter should be set to 2X the number of CPUs in your
system. The memory_cost should be adapted to your environment. The
default value is 1,536K bytes, which is reasonably small and should be
a safe value for almost any environment. A higher memory_cost value may
provide even better resilience against GPUs. The time_cost remains to
be set according to how long your project is willing to spend verifying
a password.

For more information read: https://argon2-cffi.readthedocs.io/en/stable/parameters.html
