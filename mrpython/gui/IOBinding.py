import os
import types
import shlex
import sys
import codecs
import tempfile
import tkinter.filedialog as tkFileDialog
import tkinter.messagebox as tkMessageBox
import re
from tkinter import *
from tkinter.simpledialog import askstring

from mrpython.configHandler import MrPythonConf

from codecs import BOM_UTF8

# Try setting the locale, so that we can find out
# what encoding to use
try:
    import locale
    locale.setlocale(locale.LC_CTYPE, "")
except (ImportError, locale.Error):
    pass

# Encoding for file names
filesystemencoding = sys.getfilesystemencoding()  ### currently unused

locale_encoding = 'ascii'
if sys.platform == 'win32':
    # On Windows, we could use "mbcs". However, to give the user
    # a portable encoding name, we need to find the code page
    try:
        locale_encoding = locale.getdefaultlocale()[1]
        codecs.lookup(locale_encoding)
    except LookupError:
        pass
else:
    try:
        # Different things can fail here: the locale module may not be
        # loaded, it may not offer nl_langinfo, or CODESET, or the
        # resulting codeset may be unknown to Python. We ignore all
        # these problems, falling back to ASCII
        locale_encoding = locale.nl_langinfo(locale.CODESET)
        if locale_encoding is None or locale_encoding == '':
            # situation occurs on Mac OS X
            locale_encoding = 'ascii'
        codecs.lookup(locale_encoding)
    except (NameError, AttributeError, LookupError):
        # Try getdefaultlocale: it parses environment variables,
        # which may give a clue. Unfortunately, getdefaultlocale has
        # bugs that can cause ValueError.
        try:
            locale_encoding = locale.getdefaultlocale()[1]
            if locale_encoding is None or locale_encoding == '':
                # situation occurs on Mac OS X
                locale_encoding = 'ascii'
            codecs.lookup(locale_encoding)
        except (ValueError, LookupError):
            pass

locale_encoding = locale_encoding.lower()

encoding = locale_encoding  ### KBK 07Sep07  This is used all over MRPYTHON, check!
                            ### 'encoding' is used below in encode(), check!

coding_re = re.compile(r'^[ \t\f]*#.*coding[:=][ \t]*([-\w.]+)', re.ASCII)
blank_re = re.compile(r'^[ \t\f]*(?:[#\r\n]|$)', re.ASCII)

def coding_spec(data):
    """Return the encoding declaration according to PEP 263.

    When checking encoded data, only the first two lines should be passed
    in to avoid a UnicodeDecodeError if the rest of the data is not unicode.
    The first two lines would contain the encoding specification.

    Raise a LookupError if the encoding is declared but unknown.
    """
    if isinstance(data, bytes):
        # This encoding might be wrong. However, the coding
        # spec must be ASCII-only, so any non-ASCII characters
        # around here will be ignored. Decoding to Latin-1 should
        # never fail (except for memory outage)
        lines = data.decode('iso-8859-1')
    else:
        lines = data
    # consider only the first two lines
    if '\n' in lines:
        lst = lines.split('\n', 2)[:2]
    elif '\r' in lines:
        lst = lines.split('\r', 2)[:2]
    else:
        lst = [lines]
    for line in lst:
        match = coding_re.match(line)
        if match is not None:
            break
        if not blank_re.match(line):
            return None
    else:
        return None
    name = match.group(1)
    try:
        codecs.lookup(name)
    except LookupError:
        # The standard encoding error does not indicate the encoding
        raise LookupError("Unknown encoding: "+name)
    return name


class IOBinding:

    def __init__(self, editwin):
        self.editwin=editwin
        self.fileencoding = None
        

    def close(self):
        # Break cycles
        self.editwin = None
        self.filename_change_hook = None

    def get_saved(self):
        return self.editwin.get_saved()

    def set_saved(self, flag):
        self.editwin.set_saved(flag)

    def reset_undo(self):
        self.editwin.reset_undo()

    filename_change_hook = None

    def set_filename_change_hook(self, hook):
        self.filename_change_hook = hook

    filename = None
    dirname = None

    def set_filename(self, filename):
        if filename and os.path.isdir(filename):
            self.filename = None
            self.dirname = filename
        else:
            self.filename = filename
            self.dirname = None
            self.set_saved(1)
            if self.filename_change_hook:
                self.filename_change_hook()

    def open(self, event=None, editFile=None):
        #flist = self.editwin.flist
        # Save in case parent window is closed (ie, during askopenfile()).
        #if flist:
        if not editFile:
            filename = self.askopenfile()
        else:
            filename=editFile
        if filename:
                # If editFile is valid and already open, flist.open will
                # shift focus to its existing window.
                # If the current window exists and is a fresh unnamed,
                # unmodified editor window (not an interpreter shell),
                # pass self.loadfile to flist.open so it will load the file
                # in the current window (if the file is not already open)
                # instead of a new window.
            #if (self.editwin and
            #            not getattr(self.editwin, 'interp', None) and
            #            not self.filename and
            #            self.get_saved()):
            self.editwin.open(filename, self.loadfile)
            return True
        return False
           

    eol = r"(\r\n)|\n|\r"  # \r\n (Windows), \n (UNIX), or \r (Mac)
    eol_re = re.compile(eol)
    eol_convention = os.linesep  # default

    def loadfile(self, filename):
        try:
            # open the file in binary mode so that we can handle
            # end-of-line convention ourselves.
            with open(filename, 'rb') as f:
                two_lines = f.readline() + f.readline()
                f.seek(0)
                bytes = f.read()
        except OSError as msg:
            tkMessageBox.showerror("I/O Error", str(msg), master=self.editwin)
            return False
        chars, converted = self._decode(two_lines, bytes)
        if chars is None:
            tkMessageBox.showerror("Decoding Error",
                                   "File %s\nFailed to Decode" % filename,
                                   parent=self.editwin)
            return False
        # We now convert all end-of-lines to '\n's
        firsteol = self.eol_re.search(chars)
        if firsteol:
            self.eol_convention = firsteol.group(0)
            chars = self.eol_re.sub(r"\n", chars)
        self.editwin.delete("1.0", "end")
        self.set_filename(None)
        self.editwin.insert("1.0", chars)
        self.reset_undo()
        self.set_filename(filename)
        if converted:
            # We need to save the conversion results first
            # before being able to execute the code
            self.set_saved(False)
        self.editwin.mark_set("insert", "1.0")
        self.editwin.yview("insert")
        self.updaterecentfileslist(filename)
        return True

    def _decode(self, two_lines, bytes):
        "Create a Unicode string."
        chars = None
        # Check presence of a UTF-8 signature first
        if bytes.startswith(BOM_UTF8):
            try:
                chars = bytes[3:].decode("utf-8")
            except UnicodeDecodeError:
                # has UTF-8 signature, but fails to decode...
                return None, False
            else:
                # Indicates that this file originally had a BOM
                self.fileencoding = 'BOM'
                return chars, False
        # Next look for coding specification
        try:
            enc = coding_spec(two_lines)
        except LookupError as name:
            tkMessageBox.showerror(
                title="Error loading the file",
                message="The encoding '%s' is not known to this Python "\
                "installation. The file may not display correctly" % name,
                master = self.editwin)
            enc = None
        except UnicodeDecodeError:
            return None, False
        if enc:
            try:
                chars = str(bytes, enc)
                self.fileencoding = enc
                return chars, False
            except UnicodeDecodeError:
                pass
        # Try ascii:
        try:
            chars = str(bytes, 'ascii')
            self.fileencoding = None
            return chars, False
        except UnicodeDecodeError:
            pass
        # Try utf-8:
        try:
            chars = str(bytes, 'utf-8')
            self.fileencoding = 'utf-8'
            return chars, False
        except UnicodeDecodeError:
            pass
        # Finally, try the locale's encoding. This is deprecated;
        # the user should declare a non-ASCII encoding
        try:
            # Wait for the editor window to appear
            #self.editwin.text.update()
            self.editwin.update()
            enc = askstring(
                "Specify file encoding",
                "The file's encoding is invalid for Python 3.x.\n"
                "MRPYTHON will convert it to UTF-8.\n"
                "What is the current encoding of the file?",
                initialvalue = locale_encoding,
                parent = self.editwin)

            if enc:
                chars = str(bytes, enc)
                self.fileencoding = None
            return chars, True
        except (UnicodeDecodeError, LookupError):
            pass
        return None, False  # None on failure

    def maybesave(self):
        if self.get_saved():
            return "yes"
        message = "Do you want to save %s before closing?" % (
            self.filename or "this untitled document")
        confirm = tkMessageBox.askyesnocancel(
                  title="Save On Close",
                  message=message,
                  default=tkMessageBox.YES,
                  master=self.editwin)
        if confirm:
            reply = "yes"
            self.save(None)
            if not self.get_saved():
                reply = "cancel"
        elif confirm is None:
            reply = "cancel"
        else:
            reply = "no"
        self.editwin.focus_set()
        return reply

    def maybesave_run(self):
        if self.get_saved():
            return "yes"
        msg = "Source Must Be Saved\n" + 5*' ' + "OK to Save?"
        confirm = tkMessageBox.askokcancel(title="Save Before Run or Check",
                                           message=msg,
                                           default=tkMessageBox.OK,
                                           master=self.editwin)
        if confirm:
            reply = "yes"
            self.save(None)
            if not self.get_saved():
                reply = "cancel"
        else:
            reply = "cancel"
        return reply
        
    def save(self, event):
        if not self.filename:
            self.save_as(event)
        else:
            if self.writefile(self.filename):
                self.set_saved(True)
                try:
                    self.editwin.store_file_breaks()
                except AttributeError:  # may be a PyShell
                    pass
        self.editwin.focus_set()
        if not self.filename:
            return None
        else:
            return self.filename
        ### return "break"

    def save_as(self, event):
        filename = self.asksavefile()
        if filename:
            if self.writefile(filename):
                #self.opened=TRUE
                self.set_filename(filename)
                self.set_saved(1)
                try:
                    self.editwin.store_file_breaks()
                except AttributeError:
                    pass
        self.editwin.focus_set()
        self.updaterecentfileslist(filename)
        return "break"

    def save_a_copy(self, event):
        filename = self.asksavefile()
        if filename:
            self.writefile(filename)
        self.editwin.focus_set()
        self.updaterecentfileslist(filename)
        return "break"

    def writefile(self, filename):
        self.fixlastline()
        text = self.editwin.get("1.0", "end-1c")
        if self.eol_convention != "\n":
            text = text.replace("\n", self.eol_convention)
        chars = self.encode(text)
        try:
            with open(filename, "wb") as f:
                f.write(chars)
            return True
        except OSError as msg:
            tkMessageBox.showerror("I/O Error", str(msg),
                                   master=self.editwin)
            return False

    def encode(self, chars):
        if isinstance(chars, bytes):
            # This is either plain ASCII, or Tk was returning mixed-encoding
            # text to us. Don't try to guess further.
            return chars
        # Preserve a BOM that might have been present on opening
        if self.fileencoding == 'BOM':
            return BOM_UTF8 + chars.encode("utf-8")
        # See whether there is anything non-ASCII in it.
        # If not, no need to figure out the encoding.
        try:
            return chars.encode('ascii')
        except UnicodeError:
            pass
        # Check if there is an encoding declared
        try:
            # a string, let coding_spec slice it to the first two lines
            enc = coding_spec(chars)
            failed = None
        except LookupError as msg:
            failed = msg
            enc = None
        else:
            if not enc:
                # PEP 3120: default source encoding is UTF-8
                enc = 'utf-8'
        if enc:
            try:
                return chars.encode(enc)
            except UnicodeError:
                failed = "Invalid encoding '%s'" % enc
        tkMessageBox.showerror(
            "I/O Error",
            "%s.\nSaving as UTF-8" % failed,
            master = self.editwin)
        # Fallback: save as UTF-8, with BOM - ignoring the incorrect
        # declared encoding
        return BOM_UTF8 + chars.encode("utf-8")

    def fixlastline(self):
        c = self.editwin.get("end-2c")
        if c != '\n':
            self.editwin.insert("end-1c", "\n")

    def print_window(self, event):
        confirm = tkMessageBox.askokcancel(
                  title="Print",
                  message="Print to Default Printer",
                  default=tkMessageBox.OK,
                  master=self.editwin)
        if not confirm:
            self.editwin.focus_set()
            return "break"
        tempfilename = None
        saved = self.get_saved()
        if saved:
            filename = self.filename
        # shell undo is reset after every prompt, looks saved, probably isn't
        if not saved or filename is None:
            (tfd, tempfilename) = tempfile.mkstemp(prefix='MRPYTHON_tmp_')
            filename = tempfilename
            os.close(tfd)
            if not self.writefile(tempfilename):
                os.unlink(tempfilename)
                return "break"
        platform = os.name
        printPlatform = True
        if platform == 'posix': #posix platform
            command = MrPythonConf.GetOption('main','General',
                                         'print-command-posix')
            command = command + " 2>&1"
        elif platform == 'nt': #win32 platform
            command = MrPythonConf.GetOption('main','General','print-command-win')
        else: #no printing for this platform
            printPlatform = False
        if printPlatform:  #we can try to print for this platform
            command = command % shlex.quote(filename)
            pipe = os.popen(command, "r")
            # things can get ugly on NT if there is no printer available.
            output = pipe.read().strip()
            status = pipe.close()
            if status:
                output = "Printing failed (exit status 0x%x)\n" % \
                         status + output
            if output:
                output = "Printing command: %s\n" % repr(command) + output
                tkMessageBox.showerror("Print status", output, master=self.editwin)
        else:  #no printing for this platform
            message = "Printing is not enabled for this platform: %s" % platform
            tkMessageBox.showinfo("Print status", message, master=self.editwin)
        if tempfilename:
            os.unlink(tempfilename)
        return "break"

    opendialog = None
    savedialog = None

    filetypes = [
        ("Python files", "*.py *.pyw", "TEXT"),
        ("Text files", "*.txt", "TEXT"),
        ("All files", "*"),
        ]

    defaultextension = '.py' if sys.platform == 'darwin' else ''

    def askopenfile(self):
        dir, base = self.defaultfilename("open")
        if not self.opendialog:
            self.opendialog = tkFileDialog.Open(master=self.editwin,
                                                filetypes=self.filetypes)
        filename = self.opendialog.show(initialdir=dir, initialfile=base)
        return filename

    def defaultfilename(self, mode="open"):
        if self.filename:
            return os.path.split(self.filename)
        elif self.dirname:
            return self.dirname, ""
        else:
            try:
                pwd = os.getcwd()
            except OSError:
                pwd = ""
            return pwd, ""

    def asksavefile(self):
        dir, base = self.defaultfilename("save")
        if not self.savedialog:
            self.savedialog = tkFileDialog.SaveAs(
                    master=self.editwin,
                    filetypes=self.filetypes,
                    defaultextension=self.defaultextension)
        filename = self.savedialog.show(initialdir=dir, initialfile=base)
        return filename

    def updaterecentfileslist(self,filename):
        "Update recent file list on all editor windows"
        if self.editwin:
            self.editwin.update_recent_files_list(filename)

def _io_binding(parent):
    root = Tk()
    root.title("Test IOBinding")
    width, height, x, y = list(map(int, re.split('[x+]', parent.geometry())))
    root.geometry("+%d+%d"%(x, y + 150))
    class MyEditWin:
        def __init__(self, text):
            self.text = text
            self.flist = None
            self.text.bind("<Control-o>", self.open)
            self.text.bind("<Control-s>", self.save)
        def get_saved(self): return 0
        def set_saved(self, flag): pass
        def reset_undo(self): pass
        def open(self, event):
            self.text.event_generate("<<open-window-from-file>>")
        def save(self, event):
            self.text.event_generate("<<save-window>>")

    text = Text(root)
    text.pack()
    text.focus_set()
    editwin = MyEditWin(text)
    io = IOBinding(editwin)

