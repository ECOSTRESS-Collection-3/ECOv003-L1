Introduction
------------

This has some notes I've made as writing this. We'll perhaps move this into some  documentation

Formating/Linting
-----------------

We use [ruff](https://docs.astral.sh/ruff/) for formatting and as a
linter. This is just a convenience, there are other formatting tools
and linters. But ruff is fast, and at least for now that is the tool
we use.

Note we use these tools where useful - it isn't generally considered
an error for "ruff check" to find something, and a file might not have
been formatted with "ruff format". But we generally use these. 

As a convention, we tend to put in directives for ruff to skip a check
where it gets it wrong. This is put in the pyproject.toml file (e.g. 
"muses_observation_test.py" = ["E712"]) to silence an incorrect warning).

This isn't because we consider the failing the ruff checking as an
error (i.e., some projects have a git precommit hook to reject code
that doesn't pass linters - we don't do that). Rather we silence the
warnings just so we can see possibly real problems without a lot of
noise cluttering the "ruff check" report.

Typing
------

There has been some recent moves to push optional static typing into
python, through the use of typehints along with extra tools like
Mypy. I looked into this a bit, and it looks like this is *not*
something we should be doing.

1. The tools don't really fully work - they don't catch all typing
   mistakes. A tool that "sort of works" is actually worse than no
   tool.
   
2. People who have done this for particular projects spend a *lot* of
   time getting this right.  For C++ sort of static typing, this only
   works if *everything* including library calls are typed.
   
3. It tends to be fragile.

4. Typing errors tend to be of the "obvious" sort - any kind of a unit
   test is likely to catch a problem of say passing a float to something
   expecting a str. There can be subtle errors that crop up with the wrong
   types, but honestly in more than 20 years of using python I can't think
   of an example where I ran into this.
   
So putting this in fully is a whole lot of work, with actually no real
pay off. This isn't shocking, python was designed from the beginning
to be dynamically duck typed and shoe horning C++ style static typing
doesn't really work so well. 

Python also tends to have more complicated types - so the typing is
more like Haskell typing than C++. Haskell is very good at type
inference, which none of the python tools have. And C++ has some level
of type inference with the "auto" keyword - there is no equivalent
"auto" typing in python.

All that said, type *hints* are actually pretty useful to document
what a function expects without needing to read the code in detail to
see what it does with argument.

So in this code we have typehints where these might be
useful - as an additional way to document functions. These should be
read as exactly that, a "hint" at what type we want. We don't have
these everywhere, make no attempt to make them consistent (e.g., a
function with a particular type hint for an argument might pass that
to another function with a different type hint). 

It is not in general an error if an value passed as an argument
doesn't match a type - it just need to have the proper duck typing to
supply whatever that function is expecting. 

But as a documentation of what we generally expect, typehints are
useful.

We do have mypy running cleanly with python 3.11.10 and mypy 1.14.1.
The information mypy supplies is useful, and it is nice not to have
spurious errors in the output. So we have this in place at this point
in time. We may or may not maintain this, it is useful as long as this
isn't too much work.  But static analysis does find some useful things
(are the type hints wrong?  Are we handling "None" for an argument
that can set to "None"?).

