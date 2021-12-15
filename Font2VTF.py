from configparser import ConfigParser
import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk
import matplotlib.font_manager as fm



class Font2VTF:
    def __init__(self):
        self.folderPath = ''
        self.fnt = None
        self.root = tk.Tk()
        self.root.title('Font2VTF')
        self.SettingsButton = tk.Button(self.root, text='Font', command=self.Command_FontButton)
        self.SettingsButton.pack()
        self.saveAsButton = tk.Button(self.root, text='Save As', command=self.Command_saveAsButton)
        self.saveAsButton.pack()
        self.statusLabel = tk.Label(text='Status:')
        self.statusLabel.pack()


    def Command_FontButton(self):
        fontWindow = tk.Toplevel(self.root)
        fontWindow.focus_set()
        fontnames = fm.findSystemFonts()
        fontnames.sort()
        fontList = tk.Listbox(fontWindow)
        for font in fontnames:
            fontList.insert('end',font)
        
        longest = max(fontnames, key = len)
        fontList.configure(width = len(longest))

        fontList.pack()
        fontList.bind('<<ListboxSelect>>', self.OnFontListSelection)
        fontList.bind('<Double-Button>', self.OnListboxEnter)
        previewLabel = tk.Label(fontWindow, name = 'previewLabel')
        previewLabel.pack()

    def OnListboxEnter(self, event):
        listbox = event.widget
        font = listbox.get(listbox.curselection())
        self.fnt = ImageFont.truetype(font, size=128)
        self.statusLabel.config(text=f'Status: Set font to {font}')
        listbox.master.destroy() #close the list window

    def OnFontListSelection(self,event):
            listbox = event.widget
            font = listbox.get(listbox.curselection())
            fnt = ImageFont.truetype(font, 60)

            tmpImg = Image.new("RGBA",(512, 128), (255,255,255,0))
            draw = ImageDraw.Draw(tmpImg)
            w,h = draw.textsize('ABCabc123', font= fnt)
            draw.text(((512-w)/2, (128-h)/2), text = 'ABCabc123', font = fnt, fill='black')
            photo = ImageTk.PhotoImage(tmpImg)

            master = event.widget.master
            widgets = master.winfo_children()
            
            previewLabel = None
            for w in widgets:
                if w.winfo_name() == 'previewLabel':
                    previewLabel = w

            previewLabel.config(image = photo)
            previewLabel.image = photo

    def Command_saveAsButton(self):
        self.folderPath = filedialog.askdirectory()
        self.folderPath = self.folderPath.replace('/', '\\')+'\\' #vtfcmd doesnt like / in paths
        self.createVTFs()
        self.statusLabel.config(text=f'Status: Saved to {self.folderPath}')

    def createVTFs(self):
        texturenames = []
        for i in range(33,127): #ascii values from "!" to "~"
            txt = Image.new("RGBA",(256,256), (255,255,255,0))
            draw = ImageDraw.Draw(txt)
            w, h = draw.textsize(chr(i), font=self.fnt)
            draw.text(((256-w)/2, (256-h)/2), chr(i), font=self.fnt, fill='white',align='center')
            txt.save(self.folderPath+f"/{(i)}.png")
            texturenames.append(self.folderPath+f"/{(i)}.png")


        config = ConfigParser()
        config.read('config.ini')
        appPath = config.get('main', 'vtfcmdpath')
        app = 'VTFCmd.exe'
        command = [app,
        '-folder', self.folderPath,
        '-output',self.folderPath,
        '-resize', '-rmethod',
        'NEAREST','-shader', 
        'UnlitGeneric',
        '-param','$translucent','1',
        '-recurse']
        vtfcmdProcess = subprocess.Popen(command, executable = appPath)

        vtfcmdProcess.wait() #wait for vtfcmd to create the file(s)
        for t in texturenames:
            os.remove(t) 

    def run(self):
        self.root.mainloop()

def main():
    app = Font2VTF()
    app.run()

if __name__ == '__main__':
    main()