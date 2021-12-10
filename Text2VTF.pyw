from PIL import Image, ImageFont, ImageDraw, ImageTk
import subprocess
import os
import tempfile
import math
import tkinter as tk
from tkinter import filedialog
from configparser import ConfigParser
import matplotlib.font_manager as fm




class TextVTF():
    def __init__(self):
        self.W = 256
        self.H = 256
        self.resized = False
        self.tempPath = tempfile.gettempdir()
        config = ConfigParser()
        config.read('config.ini')
        self.fontPath = config.get('main', 'fontpath')
        # fontPath = 'C:\\Users\\Robse\\Desktop\\roundo-semibold\\Roundo-SemiBold.otf'
        self.fnt = ImageFont.truetype(self.fontPath, size=128)
        self.createUI()

    def createUI(self):
        self.root = tk.Tk()
        self.root.title('Text2VTF')

        self.SettingsButton = tk.Button(self.root, text='Settings',command=self.Command_SettingsButton)
        self.SettingsButton.pack()
        self.saveAsButton = tk.Button(self.root, text='SaveAs',command=self.Command_saveAsButton)
        self.saveAsButton.pack()

        self.textField = tk.Text(self.root)
        self.textField.pack()

    def Command_saveAsButton(self):
        inputText = self.textField.get('1.0','end')
        inputText = inputText[0:len(inputText)-1] #cut off unnecessary \n
        outputPath = filedialog.asksaveasfilename(defaultextension=".vtf", filetypes=(("VTF File", "*.vtf"),))
        i = outputPath.rindex('/')
        j = outputPath.rindex('.')
        name = outputPath[i+1:j]
        outputPath = outputPath[0:i+1]
        self.createTempImage(inputText, name)
        self.createVtf(outputPath, name)

    def Command_SettingsButton(self):
        settingsWindow = tk.Toplevel(self.root)
        settingsWindow.title('Change settings')

        changeFontButton = tk.Button(settingsWindow, text='Font', command= self.Command_ChangeFontButton)
        changeFontButton.pack()
        
        VTFCMDPathButton = tk.Button(settingsWindow, text='VTFCmd', command= self.Command_VTFCMDPathButton)
        VTFCMDPathButton.pack()

    def Command_VTFCMDPathButton(self):
        appPath = filedialog.askopenfilename()
        self.updateConfig('main', 'vtfcmdpath', appPath)



    def Command_ChangeFontButton(self):
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
        if self.fontPath in fontnames:
            i = fontnames.index(self.fontPath)
            fontList.select_set(i)
            fontList.see(i)
            # fontList.selection_anchor(i)
            fontWindow.update()
            fontList.event_generate('<<ListboxSelect>>')
        fontList.bind('<<ListboxSelect>>', self.OnFontListSelection)
        fontList.bind('<Double-Button>', self.OnListboxEnter)
        previewLabel = tk.Label(fontWindow, name = 'previewLabel')
        previewLabel.pack()


    def OnListboxEnter(self, event):
        listbox = event.widget
        font = listbox.get(listbox.curselection())
        self.updateConfig('main', 'fontpath', font)
        self.fnt = ImageFont.truetype(font, size=128)
        listbox.master.destroy() #close the list window



    def OnFontListSelection(self, event):
        listbox = event.widget
        font = listbox.get(listbox.curselection())
        # font = fm.findfont(fm.FontProperties(family=fontfam))
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


    def updateConfig(self, section, key, value):
        config = ConfigParser()
        config.read('config.ini')
        config.set(section, key, value)
        with open('config.ini', 'w') as f:
            config.write(f)

    def createTempImage(self, txt, name):
        tmpImg = Image.new("RGBA",(self.W,self.H), (255,255,255,0))
        draw = ImageDraw.Draw(tmpImg)
        w, h = draw.textsize(text=txt,font=self.fnt)
        if w > 256:
            exp = math.ceil(math.log2(w)) #next highest power of 2
            self.W = int(math.pow(2, exp))
            self.resized = True

        if h > 256:
            exp = math.ceil(math.log2(h)) #next highest power of 2
            self.H = int(math.pow(2, exp))
            self.resized = True

        if self.resized:
            tmpImg = tmpImg.resize((self.W,self.H))
            draw = ImageDraw.Draw(tmpImg)


        midW = round((self.W-w)/2)
        midH = round((self.H-h)/2)
        draw.text((midW, midH), text=txt, font=self.fnt, fill='white',align='center') ##draw the text in the center of the image

        self.tmpimgPath = self.tempPath+'/'+name+'.png'
        tmpImg.save(self.tmpimgPath)

    def createVtf(self, path, name):
        inputPath = f'{self.tempPath}\\{name}.png' #path to the temp image
        config = ConfigParser()
        config.read('config.ini')
        appPath = config.get('main', 'vtfcmdpath')
        app = 'VTFCmd.exe'
        # appPath = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Counter-Strike Source\\bin\\VTFCmd.exe"
        command = [app,'-file', inputPath,'-output',path, '-resize', '-rmethod','NEAREST','-shader', 'UnlitGeneric','-recurse']
        vtfcmdProcess = subprocess.Popen(command, executable = appPath)

        vtfcmdProcess.wait() #wait for vtfcmd to create the file(s)

        #figure out destination folder: folder: <game>/materials/destination
        lastSlash = path.rindex("/")
        dest = path[0:lastSlash]
        lastSlash2 = dest.rindex("/")
        destination = dest[lastSlash2+1:lastSlash]

        vmtFile = open(path+f'{name}.vmt', 'w')

        os.remove(inputPath) 

        vmttext = f'"UnlitGeneric"\n \
        {{\n\
            "$basetexture" "{destination}\\{name}"\n\
            "$translucent" 1\n\
        }}'

        vmt = vmttext.splitlines(keepends=True)
        vmtFile.writelines(vmt)

    def run(self):
        self.root.mainloop()

# def createConfig(): 
#     config = ConfigParser()
#     config.read('config.ini')
#     config.add_section('main')
#     config.set('main', 'fontPath', 'C:\\Users\\Robse\\Desktop\\roundo-semibold\\Roundo-SemiBold.otf')
#     config.set('main', 'vtfCmdPath', 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Counter-Strike Source\\bin\\VTFCmd.exe')
#     with open('config.ini', 'w') as f:
#         config.write(f)
def main():
    app = TextVTF()
    app.run()

if __name__ == '__main__':
    main()