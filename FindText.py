import os
import re

import wx
import wx.stc as stc
import wx.lib.mixins.listctrl as listmix


def ReadFile(path):
    try:
        with open(path) as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, encoding='u8') as f:
                return f.read()
        except UnicodeDecodeError:
            return ''


def GetPattern(pattern, is_case, is_word, is_re):
    if not is_re:
        pattern = re.escape(pattern)
    if is_word:
        pattern = r'\b%s\b' % pattern
    return re.compile(pattern, flags=0 if is_case else re.IGNORECASE)


def GetFiles(path):
    files = []
    exts = {'.*'}
    for root, _, files2 in os.walk(path):
        for file in files2:
            files.append(os.path.join(root, file))
            exts.add(os.path.splitext(file)[1].lower())
    return files, ['*' + ext for ext in exts]


def GetMatches(files, pattern):
    for file in files:
        text = ReadFile(file)
        for ln, line in enumerate(text.split('\n')):
            match = pattern.search(line)
            if match:
                yield file, ln, line, match.span()


class MyListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.InsertColumn(0, 'Text', width=900)
        self.InsertColumn(1, 'File', width=200, format=wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(2, 'Ln')


class MyTextCtrl(stc.StyledTextCtrl):
    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent)

        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'face:Courier New,size:11')
        self.SetAdditionalSelectionTyping(True)
        self.SetEOLMode(stc.STC_EOL_LF)  # fix save file '\r\n' translate to '\r\r\n'
        self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(1, 30)
        self.SetMargins(5, -5)
        self.SetMultipleSelection(True)
        self.SetTabWidth(4)
        self.SetViewWhiteSpace(True)


class MyPanel(wx.Panel):
    def __init__(self, parent, root):
        wx.Panel.__init__(self, parent)

        self.root = root
        self.matches = []

        self.input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.filter = wx.Choice(self, size=(60, -1))
        self.btn1 = wx.ToggleButton(self, size=(30, -1), label='Cc')
        self.btn2 = wx.ToggleButton(self, size=(30, -1), label='W')
        self.btn3 = wx.ToggleButton(self, size=(30, -1), label='.*')

        self.results = MyListCtrl(self)

        self.path = wx.StaticText(self, label='fullpath')
        self.btn4 = wx.Button(self, label='Open in Explorer')

        self.text = MyTextCtrl(self)

        self.SetLayout()

        self.input.Bind(wx.EVT_TEXT, self.OnFind)
        self.btn1.Bind(wx.EVT_TOGGLEBUTTON, self.OnFind)
        self.btn2.Bind(wx.EVT_TOGGLEBUTTON, self.OnFind)
        self.btn3.Bind(wx.EVT_TOGGLEBUTTON, self.OnFind)

        self.results.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect)
        self.btn4.Bind(wx.EVT_BUTTON, self.OnOpenPath)

        self.files, self.exts = GetFiles(root)

        self.filter.SetItems(self.exts)

    def SetLayout(self):
        border = 5

        box1 = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.TOP | wx.BOTTOM | wx.RIGHT
        box1.Add(self.input,  1, wx.ALL | wx.EXPAND, border)
        box1.Add(self.filter, 0, flags, border)
        box1.Add(self.btn1,   0, flags, border)
        box1.Add(self.btn2,   0, flags, border)
        box1.Add(self.btn3,   0, flags, border)

        box3 = wx.BoxSizer(wx.HORIZONTAL)
        box3.Add(self.path, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, border)
        box3.Add(self.btn4, 0, wx.ALL, border)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(box1,         0, wx.EXPAND)
        box.Add(self.results, 1, wx.EXPAND)
        box.Add(box3,         0, wx.EXPAND)
        box.Add(self.text,    2, wx.EXPAND)

        self.SetSizer(box)

    def OnFind(self, evt):
        pattern = GetPattern(self.input.GetValue(), self.btn1.GetValue(), self.btn2.GetValue(), self.btn3.GetValue())
        self.matches = list(GetMatches(self.files, pattern))
        self.results.DeleteAllItems()
        for file, ln, line, span in self.matches:
            self.results.Append([line.strip(), os.path.basename(file), ln + 1])

    def OnOpenPath(self, evt):
        idx = self.results.GetFirstSelected()
        path = self.root if idx == -1 else self.matches[idx][0]
        os.popen('explorer /select, "%s"' % os.path.abspath(path))

    def OnSelect(self, evt):
        idx = evt.GetIndex()
        file, ln, line, span = self.matches[idx]
        self.path.SetLabel(file)
        self.text.LoadFile(file)
        self.text.ScrollToLine(ln)
        pos = self.text.PositionFromLine(ln)
        self.text.SetSelection(pos + span[0], pos + span[1])


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title='Find in Files', size=(1200, 800))
        self.panel = MyPanel(self, '.')
        self.Centre()
        self.Show()


if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()
