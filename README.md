# Description

With this module has beed loaded, then we can "gain" any module on the fly. Because the python scripts can do almost anything that the C language can do, so with this module's power, we can throw upgrading away from now on.

# Quickstart

1 - Put a python script on the website, I had put one at: http://oeb1qxnpc.bkt.clouddn.com/hello.py, the file's content is:

```python
   #!/usr/bin/env python
   # -*- coding: utf-8 -*-
   # @author: zig(remember1637@gmail.com)

   print("hello, pygain")
```

2 - Load this module from a local test script file "test.py", then "gain" the remote "hello.py":

```python
   import pygain

   pygain.gain("hello", "http://oeb1qxnpc.bkt.clouddn.com", ["py"])

   import hello
```

3 - Execute the test script(tested from python2.6.6 to python3.5.2):

```bash
   > python test.py
```

if everything is fine, then we can see the "hello, pygain" was printed out

# More reality: import zip package

"gain" remote script one by one is inefficient, so we can zip scripts together, let's do it

1 - Put a zip that contains some scripts, I had put one at: http://oeb1qxnpc.bkt.clouddn.com/demo.zip, the zip's content is:

>
> demo.zip
> 
>  /- __init__.py
> 
>  /- hello.py
> 
>  /- hello2.py
>

2 - Load this module from a local test script file "test.py", then "gain" the remote "demo.zip":

```python
     import pygain

     pygain.gain("demo", "http://oeb1qxnpc.bkt.clouddn.com", ["zip", "py"])

     import demo.hello2
```

3 - Execute the test script(tested from python2.6.6 to python3.5.2)

```bash
   > python test.py
```

if everything is fine, then we can see the "hello, pygain" was printed out

4 - But we need only fetch the zip file, the scripts that embeded in the zip will import directly from the zip file.

# Keyword arguments

Because of some special situation, we provider some keyword arguments, we can pass it on as below:

```python
  pygain.gain("demo", "http://zagzig.me/pygain/demo/v1", ["zip", "py"],
    httpheaders={"Referer": "xxx"}, zippw="guesswhat")
```

1. httpheaders: when we fetch the remote file,  we can pass on some http headers

2. zippw: the remote zip file can be encrypted, so pass this password to decrypt&load the remote zip module

# Installation

```bash
   pip install pygain
```

