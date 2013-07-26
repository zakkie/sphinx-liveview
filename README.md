sphinx-liveview
===============

Install
-------

```Shell
pip install tornado
git clone https://github.com/zakkie/sphinx-liveview.git
cd sphinx-liveview/assets/
wget https://github.com/fabien-d/alertify.js/archive/0.3.10.zip
unzip 0.3.10.zip
mv alertify.js-0.3.10 alertify
```

How to Use
----------

```
Usage: server.py [OPTIONS]

server.py options:

  --command=COMMAND                run COMMAND when file or directory is
                                   changed (default [])
  --htdoc                          root directory of HTML documents (default .)
  --port                            (default 8888)
  --watch                          watch file or directory (default .)
````
