import wx
import wx.stc as stc
import wx.lib.mixins.listctrl as listmix


class MyListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.InsertColumn(0, 'Text', width=900)
        self.InsertColumn(1, 'File', width=200)
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
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.filter = wx.ComboBox(self, size=(60, -1))
        self.btn1 = wx.ToggleButton(self, size=(30, -1), label='Cc')
        self.btn2 = wx.ToggleButton(self, size=(30, -1), label='W')
        self.btn3 = wx.ToggleButton(self, size=(30, -1), label='.*')

        self.results = MyListCtrl(self)

        self.path = wx.StaticText(self, label='fullpath')
        self.btn4 = wx.Button(self, label='Open in Explorer')

        self.text = MyTextCtrl(self)

        self.SetLayout()

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


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title='Find in Files', size=(1200, 800))
        self.panel = MyPanel(self)
        self.Centre()
        self.Show()


if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()
