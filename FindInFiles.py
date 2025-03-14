"""
Find in Files
=============

Input text and find keywords in multiple files, list all results in the table, and quick preview in the application.
Search mode supports match-case, whole-word, and regular-expression.


Usage on cross-platform
-----------------------

Search in current working directory:
    $ cd /path/you/need
    $ python FindInFiles.py

Search in multiple locations:
    $ python FindInFiles.py DIR1 DIR2 .. FILE1 FILE2 ..


Usage on Windows
----------------

There is two way to start the program:
    1. Select ONE file or folder, or right-click in the background of explorer, and choose the "Find in Files" option.
    2. Select multiple files or folders, and choose the "Find in Files" option from the "Send to" menu.


License
-------

Author:
    Shixian Li

E-mail:
    lsx7@sina.com

Website:
    https://github.com/znsoooo/find-in-files

License:
    MIT License. Copyright (c) 2023-2025 Shixian Li (znsoooo).

"""


import os
import os.path as osp
import re
import sys
import pathlib
import traceback

import wx
import wx.stc as stc
import wx.lib.mixins.listctrl as listmix

__version__ = 'v1.5.2'
__title__ = 'Find in Files ' + __version__


ID_RUNNING = 0
ID_STOPPED = 1
ID_RESTART = 2

IS_BARE_RUN = not sys.argv[1:] and osp.realpath(os.getcwd()) == osp.realpath(osp.dirname(sys.argv[0]))


def SetupOnWindows():
    prefix = f'"{sys.executable}" "{__file__}"'
    if hasattr(sys, '_MEIPASS'):  # if build by pyinstaller
        prefix = f'"{sys.executable}"'
    try:
        SetContextMenu(prefix)
        SetSendTo(prefix)
    except Exception:
        traceback.print_exc()


def SetContextMenu(prefix):
    import winreg

    paths = [
        r'SOFTWARE\Classes\*\shell\FindInFiles',
        r'SOFTWARE\Classes\Directory\shell\FindInFiles',
        r'SOFTWARE\Classes\Directory\Background\shell\FindInFiles',
    ]

    for i, path in enumerate(paths):
        key1 = winreg.CreateKey(winreg.HKEY_CURRENT_USER, path)
        winreg.SetValueEx(key1, '', 0, winreg.REG_SZ, 'Find in Files')
        winreg.SetValueEx(key1, 'Icon', 0, winreg.REG_SZ, 'Magnify.exe')

        key2 = winreg.CreateKey(key1, 'command')
        value2 = prefix + ' "%1"' if i < 2 else prefix  # open with one args or not
        winreg.SetValueEx(key2, '', 0, winreg.REG_SZ, value2)

        winreg.CloseKey(key1)
        winreg.CloseKey(key2)


def SetSendTo(prefix):
    import winreg

    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders')
    path = osp.expandvars(winreg.QueryValueEx(key, 'SendTo')[0])
    winreg.CloseKey(key)

    text = (
        'args = "%s"\n'
        'For i = 0 To WScript.Arguments.Count - 1\n'
        '    args = args & " """ & WScript.Arguments(i) & """"\n'
        'Next\n'
        'WScript.CreateObject("WScript.Shell").Run args\n'
    ) % prefix.replace('"', '""')

    with open(f'{path}/Find in Files.vbs', 'w') as f:
        f.write(text)


def ReadFile(path):
    for encoding in ['u8', 'u16', 'gbk', None]:
        try:
            with open(path, encoding=encoding) as f:
                return f.read(1000) + f.read()  # raise an error in first 1000 chars while file is very big
        except UnicodeError:
            pass
    return ''


def GetPattern(pattern, is_case, is_word, is_re):
    if not pattern:
        return
    if not is_re:
        pattern = re.escape(pattern)
    if is_word:
        pattern = r'\b%s\b' % pattern
    try:
        return re.compile(pattern, flags=re.M if is_case else re.M | re.I)
    except re.error:
        return


def GetFiles(filter):
    filter = re.sub(r'\*+', '*', filter.lstrip('/\\')) or '*'  # convert illegal path pattern
    paths = sys.argv[1:] or [os.getcwd()]  # use cwd if args not exist
    for path in paths:
        root = pathlib.Path(path)
        files = root.rglob(filter) if root.is_dir() else [root] if root.match(filter) else []
        for file in files:
            if file.is_file():
                yield str(file)


def GetMatches(file, pattern):
    if pattern.search(file):
        yield file, -1, file, [m.span() for m in pattern.finditer(file)]
    text = ReadFile(file)
    lines = text.split('\n')
    line_sts = [m.start() for m in re.finditer(r'^', text, re.M)] + [len(text) + 1]
    line_st = line_sts.pop(0)
    ln = -1
    for m in pattern.finditer(text):
        match_st = m.start()
        if match_st < line_st:
            continue
        while match_st >= line_st:
            line_st = line_sts.pop(0)
            ln += 1
        yield file, ln, lines[ln], [m.span() for m in pattern.finditer(lines[ln])]


class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, window, callback):
        wx.FileDropTarget.__init__(self)
        window.SetDropTarget(self)
        self.callback = callback

    def OnDropFiles(self, x, y, filenames):
        self.callback(filenames)
        return False


class MyTextDialog(wx.TextEntryDialog):
    def __init__(self, title, prompt, text, size):
        wx.TextEntryDialog.__init__(self, None, prompt, title, text, style=wx.TE_MULTILINE | wx.OK)
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.GetChildren()[1].SetFont(font)
        self.SetSize(size)
        self.Center()
        self.ShowModal()
        self.Destroy()


class MyListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, size=(20, 20), style=wx.LC_REPORT)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        self.parent = parent
        self.last_sel = 0
        self.selected_changed = False

        self.InsertColumn(0, 'Text', width=900)
        self.InsertColumn(1, 'File', width=200, format=wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(2, 'Ln',   width=50)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelect)

    def GetAllSelected(self):
        idx = self.GetFirstSelected()
        idxs = []
        while idx != -1:
            idxs.append(idx)
            idx = self.GetNextSelected(idx)
        return idxs

    def OnSelect(self, evt):
        if not self.selected_changed:
            # call it only once time
            self.selected_changed = True
            wx.CallAfter(self.AfterSelect)

    def AfterSelect(self):
        self.selected_changed = False
        self.parent.AfterSelect()

    def OnView(self, direction, shift=False):
        cnt = self.GetItemCount()
        idx = self.GetFocusedItem()
        idx2 = (idx if idx == -1 and direction < 0 else idx + direction) % (cnt or 1)
        self.Focus(idx2)
        self.EnsureVisible(idx2)

        self.last_sel = self.last_sel if shift else idx2
        idx_st, idx_ed = sorted((idx2, self.last_sel))
        [self.Select(i, idx_st <= i <= idx_ed) for i in range(self.GetItemCount())]

    def OnKeyDown(self, evt):
        key = evt.GetKeyCode()
        shift = evt.ShiftDown()
        if key == wx.WXK_UP:
            self.OnView(-1, shift)
        elif key == wx.WXK_DOWN:
            self.OnView(1, shift)
        elif evt.ControlDown() and key == ord('A'):
            self.Select(-1, True)
        else:
            evt.Skip()


class MyTextCtrl(stc.StyledTextCtrl):
    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent, size=(20, 20))

        self.text = None
        self.patt_search = self.patt_select = re.compile('$0')  # impossible pattern

        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'face:Courier New,size:11')
        self.StyleSetSpec(1, 'back:#00FFFF')
        self.StyleSetSpec(2, 'back:#7FFF7F')
        self.MarkerDefine(1, stc.STC_MARK_SHORTARROW)

        self.SetAdditionalSelectionTyping(True)
        self.SetEOLMode(stc.STC_EOL_LF)  # fix save file '\r\n' translate to '\r\r\n'
        self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(1, 50)
        self.SetMargins(5, -5)
        self.SetMultipleSelection(True)
        self.SetTabWidth(4)
        self.SetViewWhiteSpace(True)

        self.Bind(stc.EVT_STC_CHANGE, self.SetMargin)
        self.Bind(stc.EVT_STC_UPDATEUI, lambda e: self.SetHighlightPattern())

    def GetSelectedPattern(self):
        selected = self.GetSelectedText()
        if re.fullmatch(r'\w+', selected):
            return GetPattern(selected, False, True, False)
        else:
            return re.compile('$0')

    def SetMargin(self, evt):
        lines = self.GetLineCount()
        width = len(str(lines)) * 9 + 24
        self.SetMarginWidth(1, width)

    def ResetText(self, text=''):
        if text == self.text:
            return

        self.text = text
        self.patt_search = self.patt_select = re.compile('$0')  # impossible pattern

        self.SetEditable(True)
        self.SetValue(text)
        self.EmptyUndoBuffer()
        self.SetEditable(False)

        # convert unicode index to bytes index
        self.idxs = [0]
        for c in self.text:
            self.idxs.append(self.idxs[-1] + len(c.encode()))

    def SetHighlightLine(self, line):
        self.ScrollToLine(line - 12)
        self.MarkerDeleteAll(1)
        self.MarkerAdd(line, 1)
        self.ScrollToColumn(0)

    def SetHighlightPattern(self, pattern=None):
        patt_search = pattern or self.patt_search
        patt_select = self.GetSelectedPattern()

        if (patt_search, patt_select) == (self.patt_search, self.patt_select):
            return  # nothing changed

        self.patt_search = patt_search
        self.patt_select = patt_select
        self.SetStyleRange(0, 0, -1)
        for style, patt in enumerate([self.patt_search, self.patt_select], 1):
            for i, m in enumerate(patt.finditer(self.text)):
                self.SetStyleRange(style, *m.span())

    def SetStyleRange(self, style, start, end):
        start = self.idxs[start]
        end = self.idxs[end]
        try:
            self.StartStyling(start)
        except TypeError:  # compatible for old version of wxPython
            self.StartStyling(start, 0xFFFF)
        self.SetStyling(end - start, style)


class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.status = parent.status

        self.flag = ID_STOPPED
        self.matches = []
        self.history = osp.splitext(sys.argv[0])[0] + '.log'

        self.input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.filter = wx.TextCtrl(self, -1, '*.*', style=wx.TE_PROCESS_ENTER)
        self.btn1 = wx.ToggleButton(self, size=(30, 10), label='Cc')
        self.btn2 = wx.ToggleButton(self, size=(30, 10), label='W')
        self.btn3 = wx.ToggleButton(self, size=(30, 10), label='.*')

        self.results = MyListCtrl(self)

        self.path = wx.TextCtrl(self, -1, 'fullpath', style=wx.TE_READONLY | wx.TE_NOHIDESEL | wx.NO_BORDER)
        self.btn4 = wx.Button(self, -1, 'Open in Explorer')

        self.text = MyTextCtrl(self)

        self.SetLayout()

        self.OnOpen()  # load history text before binding `wx.EVT_TEXT`
        self.SetBinding()
        wx.CallAfter(self.OnFind, -1)

    def SetLayout(self):
        border = 4

        box1 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.TOP | wx.BOTTOM | wx.RIGHT
        box1.Add(self.input,  1, wx.ALL, border)
        box1.Add(self.filter, 0, flags, border)
        box1.Add(self.btn1,   0, flags | wx.EXPAND, border)
        box1.Add(self.btn2,   0, flags | wx.EXPAND, border)
        box1.Add(self.btn3,   0, flags | wx.EXPAND, border)

        box3 = wx.BoxSizer(wx.HORIZONTAL)
        box3.Add(self.path, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, border)
        box3.Add(self.btn4, 0, wx.ALL, border)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(box1,         0, wx.EXPAND)
        box.Add(self.results, 1, wx.EXPAND)
        box.Add(box3,         0, wx.EXPAND)
        box.Add(self.text,    2, wx.EXPAND)

        self.SetSizer(box)

    def SetBinding(self):
        for widget in [self.input, self.filter]:
            widget.Bind(wx.EVT_TEXT, self.OnFind)
            widget.Bind(wx.EVT_TEXT_ENTER, self.OnFind)
            widget.Bind(wx.EVT_CHAR, self.results.OnKeyDown)
            widget.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)

        self.btn1.Bind(wx.EVT_TOGGLEBUTTON, self.OnFind)
        self.btn2.Bind(wx.EVT_TOGGLEBUTTON, self.OnFind)
        self.btn3.Bind(wx.EVT_TOGGLEBUTTON, self.OnFind)
        self.btn4.Bind(wx.EVT_BUTTON, self.OnOpenPath)

        self.parent.Bind(wx.EVT_CHAR_HOOK, self.OnChar)
        self.parent.Bind(wx.EVT_CLOSE, self.OnClose)

    def GetPattern(self):
        return GetPattern(self.input.GetValue(), self.btn1.GetValue(), self.btn2.GetValue(), self.btn3.GetValue())

    def KeepGoing(self, iter, cnt1=0, cnt2=0):
        for item in iter:
            wx.Yield()
            if self.flag != ID_RUNNING:
                return
            self.cnt1 += cnt1
            self.cnt2 += cnt2
            self.status.SetStatusText(f' Found {self.cnt2} results in {self.cnt1} files')
            yield item

    def OnFind(self, evt):
        if self.flag == ID_STOPPED:
            try:
                self.FindResults()
            except Exception:
                traceback.print_exc()
            finally:
                self.flag = ID_STOPPED
        else:
            self.flag = ID_RESTART

    def FindResults(self):
        self.flag = ID_RUNNING

        self.SaveHistory()
        self.matches.clear()
        self.results.DeleteAllItems()
        self.path.SetValue(os.getcwd() + os.sep)
        self.text.ResetText()

        input = self.input.GetValue()
        title = f'{input.strip()} - {__title__}' if input else __title__
        self.parent.SetTitle(title)

        if not input:
            if IS_BARE_RUN:
                self.text.ResetText(__doc__.lstrip())
                return self.status.SetStatusText(' Tutorial')
            return self.status.SetStatusText(' Input pattern')

        pattern = self.GetPattern()
        if not pattern:
            return self.status.SetStatusText(' Bad pattern')

        self.cnt1 = self.cnt2 = 0
        self.status.SetStatusText(f' Found {self.cnt2} results in {self.cnt1} files')

        for file in self.KeepGoing(GetFiles(self.filter.GetValue()), 1):
            for item in self.KeepGoing(GetMatches(file, pattern), 0, 1):
                file, ln, line, spans = item
                self.matches.append(item)
                ln = '-' if ln < 0 else str(ln + 1)  # ln is -1 while match on path name
                self.results.Append([line.strip(), osp.basename(file), ln])
                if self.results.GetItemCount() == 1:
                    self.results.Select(0)
                    self.results.Focus(0)
                    self.results.last_sel = 0

        if self.flag == ID_RESTART:
            self.FindResults()

    def SaveHistory(self):
        input = self.input.GetValue()
        filter = self.filter.GetValue()
        mask = '%d%d%d' % (self.btn1.GetValue(), self.btn2.GetValue(), self.btn3.GetValue())
        try:
            with open(self.history, 'w', encoding='u8') as f:
                f.write('\n'.join([input, filter, mask]))
        except Exception:
            traceback.print_exc()

    def OnDragOpen(self, paths):
        sys.argv[1:] = paths
        self.OnFind(None)

    def OnOpenPath(self, evt):
        path = self.path.GetStringSelection()
        if not osp.exists(path):
            path = self.path.GetValue()
        path = osp.abspath(path)
        os.popen(f'explorer /select, "{path}"')

    def AfterSelect(self):
        # called in `MyListCtrl` object
        idxs = self.results.GetAllSelected()
        if len(idxs) == 0:
            self.path.SetValue(os.getcwd() + os.sep)
            self.text.ResetText()
        elif len(idxs) == 1:
            file, ln, line, spans = self.matches[idxs[0]]
            pattern = self.GetPattern()
            self.path.SetValue(file)
            self.text.ResetText(ReadFile(file))
            self.text.SetHighlightLine(ln)
            self.text.SetHighlightPattern(pattern)
        else:
            idx = self.results.GetFocusedItem()
            lines = [self.matches[idx][2] for idx in idxs]
            pattern = self.GetPattern()
            self.path.SetValue(self.matches[idx][0])
            self.text.ResetText('\n'.join(lines) + '\n')
            self.text.SetHighlightPattern(pattern)

    def OnMouseWheel(self, evt):
        direction = 1 if evt.GetWheelRotation() < 0 else -1
        shift = evt.ShiftDown()
        self.results.OnView(direction, shift)

    def OnChar(self, evt):
        key = evt.GetKeyCode()
        if key == wx.WXK_ESCAPE:
            self.parent.Close()
        elif key == wx.WXK_F1:
            text = re.__doc__.strip() + '\n'
            MyTextDialog('Regex Syntax', 'Help on module re:', text, (800, 600))
        elif key == wx.WXK_F12:
            text = __doc__[__doc__.find('License'):].strip() + '\n'
            MyTextDialog('About Find-in-Files', 'License:', text, (600, 400))
        else:
            evt.Skip()

    def OnOpen(self):
        if not osp.isfile(self.history):
            return
        try:
            input, filter, mask = ReadFile(self.history).splitlines()
            self.input.SetValue(input)
            self.filter.SetValue(filter)
            self.btn1.SetValue(int(mask[0]))
            self.btn2.SetValue(int(mask[1]))
            self.btn3.SetValue(int(mask[2]))
            self.input.SetInsertionPointEnd()
        except Exception:
            traceback.print_exc()

    def OnClose(self, evt):
        self.flag = ID_STOPPED
        self.SaveHistory()
        evt.Skip()


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title=__title__, size=(1200, 800))

        self.status = self.CreateStatusBar()  # must be initialized here
        self.panel = MyPanel(self)

        MyFileDropTarget(self, self.panel.OnDragOpen)  # multi window bind to one dt object cause error exit code
        MyFileDropTarget(self.panel.text, self.panel.OnDragOpen)

        icon_path = osp.realpath(__file__ + '/../icon.ico')
        if osp.isfile(icon_path):
            self.SetIcons(wx.IconBundle(icon_path))

        self.Layout()
        self.Centre()
        self.Show()


if __name__ == '__main__':
    SetupOnWindows()
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()
