import tkinter.ttk as ttk
import tkinter as tk
from tkinter.messagebox import showerror
from tkinter import filedialog as fd
import re

class GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("PKS - Communicator")
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

        self.inputControl.pack()

    def sendMessage(self):
        message = self.inputField.get()
        self.inputField.delete(0, tk.END)
        if message.strip() != "":
            print(f"message sent... \n{message} {self.makeMistakeBool.get()}")

    def openFile(self):
        print(fd.askopenfilename())

    def start(self):
        self.mainloop()

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

        self.bind("<Return>",self.checkInput)

    def start(self):
        self.mainloop()

    def checkInput(self,event=""):
        portIN = self.portInput.get()
        ipIN = self.ipaddressInput.get()
        if portIN == "" or ipIN == "":
            showerror(title='Error',message=f"IP or PORT field is empty")
            return -1
        if re.match("^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$",ipIN) is None:
            showerror(title='Error', message=f"Wrong IP address format")
            return -1

        global ip,port
        ip = ipIN
        port = portIN
        self.destroy()


ip = ""
port = 0
login = Login()
login.start()
print(f"{ip}\t{port}")

gui = GUI()
#print(gui.style.theme_names())
gui.start()