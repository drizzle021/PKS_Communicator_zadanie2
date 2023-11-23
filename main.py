import threading
import tkinter.font

from Server import Server
from Client import Client

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

        self.font = tkinter.font.Font(family="Calibri Light", size=11, weight="normal")


        self.chatBox = tk.Text(self,state="disabled",font=self.font)
        self.chatBox.pack()


        self.inputControl = ttk.Frame(self)

        self.inputControlTopSpace = ttk.Label(self.inputControl,text="\n")
        self.inputControlTopSpace.grid(row=0,column=0,rowspan=1)

        self.inputField = ttk.Entry(self.inputControl,width=30 ,font=tkinter.font.Font(family="Arial",size=13))
        self.inputField.grid(row=3,column=0,columnspan=3,padx=5)

        self.sendButtonIcon = tk.PhotoImage(file="img/send-01.png")
        self.sendButton = tk.Button(self.inputControl, image=self.sendButtonIcon, borderwidth=0, command=self.sendMessage)
        self.sendButton.grid(row=3,column=3)

        self.addFileButtonIcon = tk.PhotoImage(file="img/file-01.png")
        self.addFileButton = tk.Button(self.inputControl, image=self.addFileButtonIcon, borderwidth=0, command=self.openFile)
        self.addFileButton.grid(row=4,column=0,padx=5)

        self.makeMistakeBool = tk.BooleanVar()
        self.makeMistakeBool.set(False)
        self.makeMistakeCheckBox = ttk.Checkbutton(self.inputControl,variable=self.makeMistakeBool,text="-Make Mistake Toggle-")
        self.makeMistakeCheckBox.grid(row=4,column=2)

        self.inputControl.place(x=0,y=420,anchor="nw",width=330,height=130)

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
        master.geometry("330x250")
        about = tk.Text(master,state="normal")
        about.insert(tk.END,"abcdefghijk PKS")
        about.config(state="disabled")
        about.pack()
        print("rohadt kurva anyad.. ez meg nincs meg")


    def openHelp(self):
        wbopen("https://www.youtube.com/watch?v=o80rtKdziKU")

    def increaseFontSize(self):
        self.font.config(size=self.font.cget("size") + 1)

    def decreaseFontSize(self):
        if self.font.cget("size") == 11:
            return
        self.font.config(size=self.font.cget("size") - 1)

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

        self.selected = tk.StringVar()
        self.selectClient = ttk.Radiobutton(self,variable=self.selected,value=1,text="Client")
        self.selectServer = ttk.Radiobutton(self,variable=self.selected,value=0,text="Server")
        self.selectClient.pack()
        self.selectServer.pack()

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

        global ip,port,mode
        ip = ipIN
        port = portIN
        mode = int(self.selected.get())
        self.destroy()

def start(ip, port):
    gui = GUI(ip,port)
    gui.start()


mode = None
ip = ""
port = 0
login = Login()
login.start()
print(f"{mode}:{ip}:{port}")
if mode == 1:
    user = Client((ip,port))
elif mode == 0:
    user = Server(ip,port)

t2 = threading.Thread(target=lambda: start(ip,port))
t2.start()
