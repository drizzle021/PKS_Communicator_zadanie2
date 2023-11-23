import tkinter.ttk as ttk
import tkinter as tk
from webbrowser import open as wbopen
from tkinter.messagebox import showerror
from tkinter import filedialog as fd
import re

class GUI(tk.Tk):
    def __init__(self, ip, port):
        super().__init__()

        self.ip = ip
        self.port = port
        self.file = None

        self.title(f"PKS - Communicator -- {ip}:{port}")
        self.geometry("330x550")
        self.resizable(False,False)
        self.style = ttk.Style(self)
        self.style.theme_use("clam")


        self.chatBox = tk.Text(self,state="disabled")
        self.chatBox.pack()

        self.inputControl = ttk.Frame(self)
        self.inputField = ttk.Entry(self.inputControl)
        self.inputField.pack(side="left")

        self.sendButtonIcon = tk.PhotoImage(file="img/send-01.png")
        self.sendButton = tk.Button(self.inputControl, image=self.sendButtonIcon, borderwidth=0, command=self.sendMessage)


        self.addFileButtonIcon = tk.PhotoImage(file="img/file-01.png")
        self.addFileButton = tk.Button(self.inputControl, image=self.addFileButtonIcon, borderwidth=0, command=self.openFile)
        self.addFileButton.pack()

        self.makeMistakeBool = tk.BooleanVar()
        self.makeMistakeBool.set(False)
        self.makeMistakeCheckBox = ttk.Checkbutton(self.inputControl,variable=self.makeMistakeBool)
        self.makeMistakeCheckBox.pack(side="right")


        self.sendButton.pack(side="right", padx=5)

        self.inputControl.place(x=0,y=400,anchor="nw",width=330)

        self.menuBar = tk.Menu(self, tearoff=False)
        self.config(menu=self.menuBar)

        self.fileOptionMenu = tk.Menu(self.menuBar, tearoff=False)
        self.fileOptionMenu.add_command(label="Open", command=self.openFile)
        self.fileOptionMenu.add_command(label="Exit", command=self.stop)
        self.viewOptionMenu = tk.Menu(self.menuBar, tearoff=False)
        self.viewOptionMenu.add_command(label="Increase Font Size", command=self.increaseFontSize)
        self.viewOptionMenu.add_command(label="Decrease Font Size", command=self.decreaseFontSize)
        self.helpOptionMenu = tk.Menu(self.menuBar, tearoff=False)
        self.helpOptionMenu.add_command(label="About..", command=self.openAbout)
        self.helpOptionMenu.add_command(label="Help", command=self.openHelp)

        self.menuBar.add_cascade(label="File", menu=self.fileOptionMenu)
        self.menuBar.add_cascade(label="View", menu=self.viewOptionMenu)
        self.menuBar.add_cascade(label="Help", menu=self.helpOptionMenu)

        self.bind("<Return>",self.sendMessage)


    def sendMessage(self, *args):
        message = self.inputField.get()
        self.inputField.delete(0, tk.END)
        if self.file is not None:
            self.chatBox.config(state="normal")
            self.chatBox.insert(tk.END,f"{ip}:{port}\nFile at destination: {self.file}\n\n")
            self.file = None
            self.chatBox.config(state="disabled")
        elif message.strip() != "":
            self.chatBox.config(state="normal")
            self.chatBox.insert(tk.END,f"{ip}:{port}\n{message}\n\n")
            # print(f"{ip}:{port}\n{message}\n")
            self.chatBox.config(state="disabled")

    def openFile(self):
        self.file = fd.askopenfilename()

    def openAbout(self):
        master = tk.Tk()
        master.title("About")
        master.resizable(False,False)
        about = tk.Text(master)
        print("rohadt kurva anyad.. ez meg nincs meg")


    def openHelp(self):
        wbopen("https://www.youtube.com/watch?v=o80rtKdziKU")

    def increaseFontSize(self):
        pass

    def decreaseFontSize(self):
        pass

    def start(self):
        self.mainloop()

    def stop(self):
        self.destroy()

class Login(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PKS - Communicator")
        self.geometry("300x300")


        self.ipaddressLabel = ttk.Label(text="IP ADDRESS: ")
        self.ipaddressLabel.pack()
        self.ipaddressInput = ttk.Entry(self)
        self.ipaddressInput.pack(side="top")

        self.portLabel = ttk.Label(text="PORT: ")
        self.portLabel.pack()
        self.portInput = ttk.Entry(self)
        self.portInput.pack()

        self.loginButton = ttk.Button(self,text="LOGIN", command=self.checkInput)
        self.loginButton.pack(side="bottom")

        self.isClientBool = tk.BooleanVar()
        self.isClientBool.set(False)
        self.checkbox = ttk.Checkbutton(self,variable=self.isClientBool)
        self.checkbox.pack()

        self.menuBar = tk.Menu(self,tearoff=False)
        self.config(menu=self.menuBar)

        self.fileOptionMenu = tk.Menu(self.menuBar,tearoff=False)
        self.fileOptionMenu.add_command(label="Exit",command=self.stop)

        self.menuBar.add_cascade(label="File",menu=self.fileOptionMenu)

        self.bind("<Return>",self.checkInput)

    def start(self):
        self.mainloop()

    def stop(self):
        self.destroy()

    def checkInput(self,*args):
        portIN = self.portInput.get()
        ipIN = self.ipaddressInput.get()
        if portIN == "" or ipIN == "":
            showerror(title='Error',message=f"IP or PORT field is empty")
            return -1
        if re.match("^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$",ipIN) is None:
            showerror(title='Error', message=f"Wrong IP address format")
            return -1

        global ip,port,type
        ip = ipIN
        port = portIN
        type = 1 if self.isClientBool else 0
        self.destroy()

if __name__ == '__main__':
    type = None
    ip = ""
    port = 0
    login = Login()
    login.start()
    print(f"{ip}\t{port}")

    gui = GUI(ip, port)
    print(gui.style.theme_names())
    gui.start()

