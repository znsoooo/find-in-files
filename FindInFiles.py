import os
import re
import sys
import pathlib
import traceback

import wx
import wx.stc as stc
import wx.lib.mixins.listctrl as listmix

__ver__ = 'v1.1.1'
__title__ = 'Find in Files ' + __ver__


def AddEntry():
    try:
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
            value2 = f'"{sys.executable}" "{__file__}"'
            if hasattr(sys, '_MEIPASS'):  # if build by pyinstaller
                value2 = f'"{sys.executable}"'
            if i < 2:  # if find in one file or folder
                value2 += ' "%1"'
            winreg.SetValueEx(key2, '', 0, winreg.REG_SZ, value2)

            winreg.CloseKey(key1)
            winreg.CloseKey(key2)

    except Exception:
        traceback.print_exc()


def ReadFile(path):
    for encoding in ['u8', 'u16', None]:
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
    for ln, line in enumerate(text.split('\n')):
        if pattern.search(line):
            yield file, ln, line, [m.span() for m in pattern.finditer(line)]


class MyListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, size=(20, 20), style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.InsertColumn(0, 'Text', width=900)
        self.InsertColumn(1, 'File', width=200, format=wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(2, 'Ln',   width=50)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def OnChar(self, evt):
        code = evt.GetKeyCode()
        if code not in [wx.WXK_UP, wx.WXK_DOWN]:
            evt.Skip()
        else:
            cnt = self.GetItemCount()
            idx = self.GetFirstSelected()
            idx = (idx + 1 if code == wx.WXK_DOWN else -1 if idx == -1 else idx - 1) % cnt
            self.Select(idx)
            self.EnsureVisible(idx)


class MyTextCtrl(stc.StyledTextCtrl):
    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent, size=(20, 20))

        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'face:Courier New,size:11')
        self.StyleSetSpec(1, 'back:#00FFFF')

        self.SetAdditionalSelectionTyping(True)
        self.SetEOLMode(stc.STC_EOL_LF)  # fix save file '\r\n' translate to '\r\r\n'
        self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(1, 50)
        self.SetMargins(5, -5)
        self.SetMultipleSelection(True)
        self.SetTabWidth(4)
        self.SetViewWhiteSpace(True)

        self.Bind(stc.EVT_STC_CHANGE, self.OnText)

    def OnText(self, evt):
        lines = self.GetLineCount()
        width = len(str(lines)) * 9 + 24
        self.SetMarginWidth(1, width)

    def SetUnicodeHighlights(self, spans):
        text = self.GetValue()
        self.StartStyling(0)
        self.SetStyling(len(text.encode()), 0)
        if spans and len(spans) < 10000:
            idxs = [0]
            for c in text:
                idxs.append(idxs[-1] + len(c.encode()))  # unicode index -> bytes index
            for i, (p1, p2) in enumerate(spans):
                p1, p2 = idxs[p1], idxs[p2]
                self.StartStyling(p1)
                self.SetStyling(p2 - p1, 1)

    def SetUnicodeSelection(self, p1, p2):
        text = self.GetValue()
        p1, p2 = (len(text[:p].encode()) for p in (p1, p2))  # unicode index -> bytes index
        self.ShowPosition(p1)
        self.SetSelection(p1, p2)

    def StartStyling(self, start):
        try:
            super().StartStyling(start)
        except TypeError:  # compatible for old version of wxPython
            super().StartStyling(start, 0xFFFF)


class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.status = parent.status

        self.serial = 0
        self.matches = []
        self.history = sys.argv[0] + '/../history.txt'

        self.input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.filter = wx.TextCtrl(self, -1, '*.*', style=wx.TE_PROCESS_ENTER)
        self.btn1 = wx.ToggleButton(self, size=(30, 10), label='Cc')
        self.btn2 = wx.ToggleButton(self, size=(30, 10), label='W')
        self.btn3 = wx.ToggleButton(self, size=(30, 10), label='.*')

        self.results = MyListCtrl(self)

        self.path = wx.StaticText(self, label='fullpath')
        self.btn4 = wx.Button(self, label='Open in Explorer')

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
        self.input.Bind(wx.EVT_TEXT, self.OnFind)
        self.input.Bind(wx.EVT_TEXT_ENTER, self.OnFind)
        self.filter.Bind(wx.EVT_TEXT, self.OnFind)
        self.filter.Bind(wx.EVT_TEXT_ENTER, self.OnFind)
        self.btn1.Bind(wx.EVT_TOGGLEBUTTON, self.OnFind)
        self.btn2.Bind(wx.EVT_TOGGLEBUTTON, self.OnFind)
        self.btn3.Bind(wx.EVT_TOGGLEBUTTON, self.OnFind)

        self.input.Bind(wx.EVT_CHAR, self.results.OnChar)

        self.results.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect)
        self.results.Bind(wx.EVT_LIST_ITEM_DESELECTED, lambda e: self.path.SetLabel(os.getcwd() + os.sep))
        self.btn4.Bind(wx.EVT_BUTTON, self.OnOpenPath)

        self.parent.Bind(wx.EVT_CHAR_HOOK, self.OnChar)
        self.parent.Bind(wx.EVT_CLOSE, self.OnClose)

    def GetPattern(self):
        return GetPattern(self.input.GetValue(), self.btn1.GetValue(), self.btn2.GetValue(), self.btn3.GetValue())

    def UpdateUI(self, serial):
        wx.Yield()
        return serial != self.serial

    def OnFind(self, evt):
        serial = self.serial = self.serial + 1
        self.matches.clear()
        self.results.DeleteAllItems()
        self.text.ClearAll()
        self.text.EmptyUndoBuffer()
        self.path.SetLabel(os.getcwd() + os.sep)

        input = self.input.GetValue()
        if not input:
            self.parent.SetTitle(__title__)
        else:
            self.parent.SetTitle(f'{input.strip()} - {__title__}')

        pattern = self.GetPattern()
        if not pattern:
            self.status.SetStatusText('')
            return

        cnt1 = cnt2 = 0
        filter = self.filter.GetValue()
        for file in GetFiles(filter):
            cnt1 += 1
            if self.UpdateUI(serial):
                return
            for item in GetMatches(file, pattern):
                cnt2 += 1
                if self.UpdateUI(serial):
                    return
                file, ln, line, spans = item
                self.matches.append(item)
                ln = '-' if ln < 0 else str(ln + 1)  # ln is -1 while match on path name
                self.results.Append([line.strip(), os.path.basename(file), ln])
                if self.results.GetItemCount() == 1:
                    self.results.Select(0)
                self.status.SetStatusText(f' Found {cnt2} results in {cnt1} files')
            self.status.SetStatusText(f' Found {cnt2} results in {cnt1} files')

    def OnOpenPath(self, evt):
        idx = self.results.GetFirstSelected()
        if idx == -1:
            os.popen('explorer "%s"' % os.getcwd())
        else:
            os.popen('explorer /select, "%s"' % os.path.abspath(self.matches[idx][0]))

    def OnSelect(self, evt):
        idx = evt.GetIndex()
        file, ln, line, spans = self.matches[idx]
        self.path.SetLabel(file)
        self.text.SetValue(ReadFile(file))
        self.text.EmptyUndoBuffer()
        self.text.ScrollToLine(ln - 12)
        self.text.MarkerDefine(1, stc.STC_MARK_SHORTARROW)
        self.text.MarkerAdd(ln, 1)

        text = self.text.GetValue()
        pattern = self.GetPattern()
        spans = [m.span() for m in pattern.finditer(text)]
        self.text.SetUnicodeHighlights(spans)

    def OnChar(self, evt):
        if wx.WXK_ESCAPE == evt.GetKeyCode():
            self.parent.Close()
        else:
            evt.Skip()

    def OnOpen(self):
        if not os.path.isfile(self.history):
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
        input = self.input.GetValue()
        filter = self.filter.GetValue()
        mask = '%d%d%d' % (self.btn1.GetValue(), self.btn2.GetValue(), self.btn3.GetValue())
        if input:
            with open(self.history, 'w', encoding='u8') as f:
                f.write('\n'.join([input, filter, mask]))
        evt.Skip()


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title=__title__, size=(1200, 800))
        self.status = self.CreateStatusBar()  # must be initialized here
        self.panel = MyPanel(self)
        self.Layout()
        self.Centre()
        self.Show()


if __name__ == '__main__':
    AddEntry()
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()
