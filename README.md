# Find in Files

`Find in Files` is a Python application that provides a simple and efficient way to search for text within files on your system. It offers a user-friendly graphical interface, making it easy for users to execute complex searches using regular expressions.


## Features

- __GUI Interface:__ "Find in Files" uses the wxPython library to create a cross-platform graphical interface.
- __RegEx Support:__ Use Python's regex library for advanced text matching capabilities.
- __System Wide Search:__ Recursively search through directories and files, displays the context in the results.
- __Command Line Support:__ Execute searches from the command line with specified files and folders as arguments.
- __Windows system support:__
  - __Context Menu Integration:__ Integration with context menu, allowing right-click on a file or directory and search within them directly.
  - __Send To Menu Integration:__ Offers integration with the "Send To" menu for quick access.


## Installation

This program require `python>=3.6` and `wxpython>=4.0.0`

Install requirement and run on Windows / OSX:

```bash
pip install wxpython
python FindInFiles.py
```

Install on Linux, you may need to find `*.whl` here and install:

<https://extras.wxpython.org/wxPython4/extras/linux>


## Usage

- Run without arguments to search the current working directory:

    ```bash
    $ cd /path/you/need
    $ python FindInFiles.py
    ```

- Provide FILE or DIR paths as arguments to search in multiple locations:

    ```bash
    $ python FindInFiles.py DIR1 DIR2 .. FILE1 FILE2 ..
    ```


## License

- __Author:__ Shixian Li
- __QQ:__ 11313213
- __Email:__ <lsx7@sina.com>
- __GitHub:__ <https://github.com/znsoooo/find-in-files>
- __License:__ MIT License. Copyright (c) 2023-2024 Shixian Li (znsoooo). All Rights Reserved.
