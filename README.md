# Find in Files

"Find in Files" is a cross-platform Python program that provides a user-friendly GUI interface to search text within multiple files on your system.


## Features

- **GUI Interface:** "Find in Files" uses the wxPython library to create a cross-platform program.
- **RegEx Support:** Use Python's regex library for advanced text searching capabilities.
- **Search in Files:** Recursively search through folders and files, displaying all results and context in the window.
- **Search Setting:** Support filename matching, support match case, whole word, and regular expression.
- **Command Line Support:** Execute the command line with specified folders and files as arguments to start a new search.
- **Windows System Integration:**
  - **Context Menu:** Integrate with context menus, right-click on a folder and search directly within it.
  - **SendTo Menu:** Integrate with the "Send To" menu, multi-select files and use "Send To" to quick access.


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
- __License:__ MIT License. Copyright (c) 2023-2025 Shixian Li (znsoooo). All Rights Reserved.
