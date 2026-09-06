import customtkinter as c
import tutor
import json
import os 
from customtkinter import filedialog
import PyPDF2 
from tkinter import messagebox
import tkinter as tk
import pymupdf
from PIL import Image, ImageTk, ImageGrab
import threading
import sys
import platform


if platform.system() == "Windows":
    speicher_ordner = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "UniTutor")
else:
    speicher_ordner = os.path.join(os.path.expanduser("~"), ".config", "UniTutor")
if not os.path.exists(speicher_ordner):
    os.makedirs(speicher_ordner)
os.chdir(speicher_ordner)



aktuellesfach = ""
aktuelles_pdf_dokument = None
aktuelle_pdf_seite = 0
aktueller_zoom = 0.5

aktuelle_bilder = []
gespeicherte_pdfs = {}

app = c.CTk()
app.title("LearnTut")


app.iconname("LearnTut") 


if platform.system() == "Windows":
    import ctypes
    try:
        myappid = 'learntut.desktop.app.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass





c.set_appearance_mode("dark")
app.configure(fg_color="#313338")


def hole_ressourcen_pfad(dateiname):
    try:
        basis_pfad = sys._MEIPASS
    except Exception:
        basis_pfad = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basis_pfad, dateiname)

try:
    logo_pfad = hole_ressourcen_pfad("logo.png")
    icon_bild = ImageTk.PhotoImage(Image.open(logo_pfad))
    app.wm_iconphoto(True, icon_bild)
except Exception as e:
    pass 

def nachricht_senden():
    text = eingabefeld.get("1.0", "end-1c")
    if text.strip() == "" and len(aktuelle_bilder) == 0:
        return
   
    chatfenster.configure(state="normal") 
    chatfenster.insert("end", "\n👤 Du:\n" + text + "\n\n")
    chatfenster.see("end") 
    chatfenster.configure(state="disabled") 

    def worker():
        antwort = tutor.generiere_antwort(text, aktuelle_bilder)
        app.after(1000, lambda: antwort_anzeigen(antwort))
    threading.Thread(target=worker).start()


    eingabefeld.delete("1.0", "end")
    eingabefeld.configure(state="disabled")
    button.configure(state="disabled", text="Tippt...")



def enter_senden(event):
    nachricht_senden()
    return "break"


def antwort_anzeigen(antwort):
    eingabefeld.configure(state="normal")
    button.configure(state="normal", text="Senden")
    aktuelle_bilder.clear()
    update_bild_vorschau()
    chatfenster.configure(state="normal")
    chatfenster.insert("end", "🎓 Tutor:\n", "bold")
    
    render_markdown(chatfenster, antwort)
    
    chatfenster.insert("end", "\n━━━━━━━━━━━━━━━━━━━━━━━━\n")
    chatfenster.see("end")
    chatfenster.configure(state="disabled")



#layout
app.geometry("1400x800")
if platform.system() == "Windows": 
    app.state("zoomed")



else:
    app.attributes('-zoomed', True)


#slidebar
menu_offen = False
def toggle_menu(): 
    global menu_offen
    #print("Knopf wurde gedrückt!", menu_offen)
    if menu_offen == False:
        menu_frame.place(x=0, y=0, relheight=1)
        menu_frame.lift()
        menu_button.lift()
        menu_offen = True
    else:
        menu_frame.place_forget()
        menu_offen = False

menu_button = c.CTkButton(app, text="=", width=40, command=toggle_menu,  fg_color="#4e5058")
menu_button.pack(anchor="nw", padx=10, pady=10)


def fachadd():
    alle_faecher = []
    if os.path.exists("faecher.json"):
        with open ("faecher.json", "r") as f:
            alle_faecher = json.load(f)
        
    dialog = c.CTkInputDialog(text="Neues fach: ", title="Neues Fach")
    fach_name = dialog.get_input()

    if fach_name in alle_faecher:
        messagebox.showerror("Fehler", "Dieses Fach existiert bereits!")
        return 

    

    if fach_name:
        

        alle_faecher.append(fach_name)
        with open ("faecher.json", "w") as w:
            json.dump(alle_faecher, w)

        for widget in menu_frame.winfo_children():
            if widget != fachadd_button:
                 widget.destroy()
        fachladen()
        fachwechsel(fach_name)


menu_frame = c.CTkFrame(app,width=200, fg_color="#202124")
fachadd_button = c.CTkButton(menu_frame, text="+", command=fachadd, fg_color="#4e5058", hover_color="#6d6f78", corner_radius=4)
fachadd_button.pack(pady=(60, 20), padx=10, fill="x")

def fachladen():
    if os.path.exists("faecher.json"):
        with open("faecher.json", "r") as f:
            geladene_facher = json.load(f)
        
        for fach in sorted(geladene_facher, key=str.lower):
            fach_reihe = c.CTkFrame(menu_frame, fg_color="transparent")
            fach_reihe.pack(pady=5, padx=10, fill="x")
            fachbutton_del = c.CTkButton(fach_reihe, text="X", width=30, command=lambda f=fach, r=fach_reihe: gui_fach_loeschen(f, r), fg_color="transparent", text_color="grey", hover_color="#ed4245", text_color_disabled="white")
            fachbutton_del.pack(side="right")
            fachbutton = c.CTkButton(fach_reihe, text=fach, command=lambda f=fach: fachwechsel(f),  fg_color="#4e5058", hover_color="#6d6f78", corner_radius=4)
            fachbutton.pack(fill="both", expand=True)



def fachwechsel(gewealtesfach):
    welcome_frame.pack_forget()
    leftframe.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    centerframe.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    rightframe.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    docpfad_stoff = gewealtesfach + "_stoff.json"
    docpfad_aufgaben = gewealtesfach + "_aufgaben.json"
    pdf_canvas.delete("all")
    tutor.setze_aufgabe("")

    einstellungen = {}
    global aktuellesfach
    aktuellesfach = gewealtesfach


    chatfenster.configure(state="normal")
    chatfenster.delete("1.0", "end")
    verlauf = tutor.ladefach(gewealtesfach)
    for nachricht in verlauf:
        if nachricht["role"] == "user":
            if isinstance(nachricht["content"], list):
                text_inhalt = nachricht["content"][0]["text"]
                chatfenster.insert("end", "Du: [Bild] " + text_inhalt + "\n")
            else:
                chatfenster.insert("end", "\n👤 Du:\n" + nachricht["content"] + "\n\n")
        if nachricht["role"] == "assistant":
            chatfenster.insert("end", "🎓 Tutor:\n", "bold")
            render_markdown(chatfenster, nachricht["content"])
            chatfenster.insert("end", "\n━━━━━━━━━━━━━━━━━━━━━━━━\n")
    chatfenster.insert("end", "--- Workspace: " + aktuellesfach + " geladen ---\n")
    chatfenster.see("end")
    chatfenster.configure(state="disabled")

    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            einstellungen = json.load(f)
    einstellungen["letztes_fach"] = gewealtesfach
    with open("config.json", "w") as w:
                json.dump(einstellungen, w, indent=4)


    for widget in box_stoff.winfo_children():
        if widget == upload_stoff:
            continue
        else:
            widget.destroy()

    

    for widget in box_Aufgaben.winfo_children():
        if widget == upload_Aufgaben:
            continue
        else:
            widget.destroy()



    if gewealtesfach in gespeicherte_pdfs:
        aufgabeladen(gespeicherte_pdfs[gewealtesfach])

    if os.path.exists(docpfad_stoff):
        with open(docpfad_stoff, "r") as f:
            sammlung = json.load(f)
        for dateiname in sorted(sammlung):
            kurzname = dateiname if len(dateiname) < 25 else dateiname[:22] + "..."
            doku_reihe = c.CTkFrame(box_stoff, fg_color="#383a40", corner_radius=6)
            doku_reihe.pack(fill="x", pady=2)
            doku_del = c.CTkButton(doku_reihe, text="X", width=30, fg_color="transparent", text_color="#B5BAC1", hover_color="#ed4245", command=lambda d=dateiname:gui_dokument_loeschen(d, "stoff"))
            doku_del.pack(side="right", padx=5, pady=5)

            doku_label = c.CTkLabel(doku_reihe, text=kurzname)
            doku_label.pack(pady=5, padx=5, side="left")


    if os.path.exists(docpfad_aufgaben):
        with open(docpfad_aufgaben, "r") as f:
            sammlung = json.load(f)
        for dateiname in sorted(sammlung):
            kurzname = dateiname if len(dateiname) < 25 else dateiname[:22] + "..."
            doku_reihe = c.CTkFrame(box_Aufgaben, fg_color="#383a40", corner_radius=6)
            doku_reihe.pack(fill="x", pady=2)

            doku_del = c.CTkButton(doku_reihe, text="X", width=30, fg_color="transparent", text_color="#B5BAC1", hover_color="#ed4245", command=lambda d=dateiname:gui_dokument_loeschen(d, "aufgaben"))
            doku_del.pack(side="right", padx=5, pady=5)
            doku_label = c.CTkLabel(doku_reihe, text=kurzname)
            doku_label.pack(pady=5, padx=5, side="left")


def gui_dokument_loeschen(dateiname, art):
    global aktuellesfach
    löschen = messagebox.askyesno("Löschen", "Willst du das wirklich löschen?")
    if löschen == True:
        tutor.dokument_loeschen(dateiname, art)
        fachwechsel(aktuellesfach)


def chat_leeren():
    value = messagebox.askyesno("Chat leeren", "Willst du den aktuellen Chat wirklich löschen?")

    if value == True:
        tutor.chat_leeren()
        chatfenster.delete("1.0", "end")
    global aktuellesfach
    fachwechsel(aktuellesfach)
    


    



def dokumente_laden(art):
    files = filedialog.askopenfilenames()
    print(files)
    global aktuellesfach
    



    for pfad in files:  
        gesamter_doc_text = ""
        anzeigename = os.path.basename(pfad)
        with open(pfad, "rb") as f:
            pdf_leser = PyPDF2.PdfReader(f)
            for seite in pdf_leser.pages:
                gesamter_doc_text = gesamter_doc_text + seite.extract_text()
        tutor.dokumente_speichern(anzeigename,gesamter_doc_text, art)

    
    fachwechsel(aktuellesfach)

    


def zeigepdfvorschau():
    global aktuelles_pdf_dokument, aktuelle_pdf_seite, aktueller_zoom
    if aktuelles_pdf_dokument is None: return
    seite = aktuelles_pdf_dokument.load_page(aktuelle_pdf_seite)

    zoom_matrix = pymupdf.Matrix(aktueller_zoom, aktueller_zoom)
    pix = seite.get_pixmap(matrix=zoom_matrix)

    bild = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    tk_bild = ImageTk.PhotoImage(bild)
    pdf_canvas.delete("all")
    pdf_canvas.create_image(0, 0, anchor="nw", image=tk_bild)
    pdf_canvas.image = tk_bild
    pdf_canvas.configure(scrollregion=pdf_canvas.bbox("all"))

    
def zoom_in():
    global aktueller_zoom
    global aktuelles_pdf_dokument
    aktueller_zoom += 0.1
    zeigepdfvorschau()

def zoom_out(): 
    global aktueller_zoom
    global aktuelles_pdf_dokument
    aktueller_zoom -= 0.1
    zeigepdfvorschau()

def naechste_seite():
    global aktuelle_pdf_seite
    global aktuelles_pdf_dokument
    if aktuelle_pdf_seite != aktuelles_pdf_dokument.page_count -1:
        aktuelle_pdf_seite += 1
    zeigepdfvorschau()

def vorherige_seite():
    global aktuelle_pdf_seite
    global aktuelles_pdf_dokument
    if aktuelle_pdf_seite != 0:
        aktuelle_pdf_seite -= 1
    zeigepdfvorschau()

def aufgabeladen(automatischer_pfad=None):
    global aktueller_zoom
    global gespeicherte_pdfs
    global aktuellesfach
    
    global aktuelles_pdf_dokument
    if automatischer_pfad:
        pdf = automatischer_pfad
    else: 
        pdf = filedialog.askopenfilename()
    gespeicherte_pdfs[aktuellesfach] = pdf
    aktuelles_pdf_dokument = pymupdf.open(pdf)

    aufgaben_text = ""
    for seite in aktuelles_pdf_dokument:
        aufgaben_text += seite.get_text()   
    tutor.setze_aufgabe(aufgaben_text)
    global aktuelle_pdf_seite 
    aktuelle_pdf_seite = 0
    aktueller_zoom = 0.5
    zeigepdfvorschau()


def aufgabe_schliessen():
    global aktuelles_pdf_dokument
    global gespeicherte_pdfs
    global aktuellesfach

    if aktuellesfach in gespeicherte_pdfs:
        del gespeicherte_pdfs[aktuellesfach]
    aktuelles_pdf_dokument = None
    pdf_canvas.delete("all")
    tutor.setze_aufgabe("")


def bild_einfuegen(event):
    global aktuelle_bilder
    try:
        bild = ImageGrab.grabclipboard()

        if bild is not None:
            aktuelle_bilder.append(bild)
        update_bild_vorschau()
    except Exception:
        pass

def bild_loeschen(index):
    global aktuelle_bilder
    aktuelle_bilder.pop(index)
    update_bild_vorschau()

def update_bild_vorschau():
    for widget in bild_vorschau_frame.winfo_children():
        widget.destroy()
    for index, bild in enumerate(aktuelle_bilder):
        kachel = c.CTkFrame(bild_vorschau_frame, fg_color="transparent")
        kachel.pack(side="left")
        bild_kopie = bild.copy()
        bild_kopie.thumbnail((100,100))
        ctk_thumbnail = c.CTkImage(light_image=bild_kopie, dark_image=bild_kopie, size=(bild_kopie.width, bild_kopie.height))
        thumbnail = c.CTkLabel(kachel, image=ctk_thumbnail, text="")
        thumbnail.image = ctk_thumbnail
        thumbnail.pack(side="top", pady=2)

        loeschen = c.CTkButton(kachel, text="X", width=20,fg_color="red", command=lambda i=index: bild_loeschen(i))
        loeschen.pack(side="top", pady=2)




def gui_fach_loeschen(fach_name, reihe):
    loeschen = messagebox.askyesno("Fach löschen", "Willst du das Fach und alle Datein wirklich löschen?")
    if loeschen == True:
        reihe.destroy()
        with open("faecher.json", "r") as f:
            faecher_liste = json.load(f)
        faecher_liste.remove(fach_name)
        with open("faecher.json", "w") as w:
            json.dump(faecher_liste, w)



        chat_datei = fach_name + "_chat.json"
        stoff_datei = fach_name + "_stoff.json"
        aufgaben_datei = fach_name + "_aufgaben.json"

        if os.path.exists(chat_datei):
            os.remove(chat_datei)
        if os.path.exists(stoff_datei):
            os.remove(stoff_datei)
        if os.path.exists(aufgaben_datei):
            os.remove(aufgaben_datei)

        global aktuellesfach
        if fach_name == aktuellesfach:
            if len(faecher_liste) > 0:
                fachwechsel(faecher_liste[0])
            else:
                zeige_welcome_screen()
                
def zeige_welcome_screen():
    global aktuellesfach
    aktuellesfach= ""
    leftframe.pack_forget()
    centerframe.pack_forget()
    rightframe.pack_forget()

    welcome_frame.pack(fill="both", expand=True, padx=10, pady=10)
    einstellungen = {}
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            einstellungen = json.load(f)
            
    einstellungen["letztes_fach"] = ""
    with open("config.json", "w") as w:
        json.dump(einstellungen, w, indent=4)

def bild_laden_dialog():
    dateipfaede = filedialog.askopenfilenames(filetypes= [("Bilder", "*.png *.jpg *.jpeg")])
    if dateipfaede:

        for pfad in dateipfaede:
            bild = Image.open(pfad)
            aktuelle_bilder.append(bild)
        update_bild_vorschau()

def show_settings():
    setting_fenster = c.CTkToplevel(app)
    setting_fenster.title("Settings")
    setting_fenster.geometry("700x850")
    setting_fenster.attributes("-topmost", True)

    config = {}
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)

    apikeylabel = c.CTkLabel(setting_fenster, text="API-Key")
    modelllabel = c.CTkLabel(setting_fenster, text="Modell")
    apikey = c.CTkEntry(setting_fenster, width=400)
    modell = c.CTkEntry(setting_fenster, width=400)
    
    apikey.insert(0, config.get("api_key", ""))
    modell.insert(0, config.get("modell", "qwen/qwen3.6-27b"))

    apikeylabel.pack(pady=(10, 0))
    apikey.pack(pady=5)
    modelllabel.pack(pady=(10, 0))
    modell.pack(pady=5)

    c.CTkLabel(setting_fenster, text="Custom System Prompt").pack(pady=(10, 0))
    customprompt = c.CTkTextbox(setting_fenster, width=500, height=150)
    customprompt.insert("1.0", config.get("custom_prompt", "Du bist ein hilfreicher Tutor."))
    customprompt.pack(pady=5)

    def setze_preset(text):
        customprompt.delete("1.0", "end")
        customprompt.insert("1.0", text)

    button_frame = c.CTkFrame(setting_fenster, fg_color="transparent")
    button_frame.pack(pady=5)
    
    c.CTkButton(button_frame, text="Standart", command=lambda: setze_preset("Du bist ein geduldiger akademischer Tutor. Liefere keine fertigen Lösungen, sondern führe den Studenten mit gezielten Leitfragen selbst auf den richtigen Weg. Dein Ziel ist der Aha-Effekt")).pack(side="left", padx=5)
    c.CTkButton(button_frame, text="Klausur-Drill", command=lambda: setze_preset("Du bist ein strenger Prüfer. Keine langen Erklärungen, kein Drumherumreden. Antworte extrem kurz, präzise und knallhart. Fokus liegt zu 100prozent auf Klausurrelevanz und dem Erkennen von typischen Fehlern.")).pack(side="left", padx=5)
    c.CTkButton(button_frame, text="Simpler Erklär-stil", command=lambda: setze_preset("Du bist ein lockerer Kommilitone. Erkläre extrem komplexe Konzepte so einfach wie möglich. Nutze viele Metaphern und Vergleiche aus dem echten Leben (z.B. Videospiele, Alltag). Vermeide Fachsprache, wo es nur geht.")).pack(side="left", padx=5)

    c.CTkLabel(setting_fenster, text="Stoff Prompt").pack(pady=(10, 0))
    stoff_prompt_box = c.CTkTextbox(setting_fenster, width=500, height=60)
    stoff_prompt_box.insert("1.0", config.get("stoff_prompt", "--- VORLESUNGSSTOFF (Theorie & Grundlagen) ---"))
    stoff_prompt_box.pack(pady=5)

    c.CTkLabel(setting_fenster, text="Aufgaben Prompt").pack(pady=(10, 0))
    aufgaben_prompt_box = c.CTkTextbox(setting_fenster, width=500, height=60)
    aufgaben_prompt_box.insert("1.0", config.get("aufgaben_prompt", "--- ALTKLAUSUREN & ÜBUNGEN (Extrem prüfungsrelevant) ---"))
    aufgaben_prompt_box.pack(pady=5)

    def speichern():
        config["api_key"] = apikey.get()
        config["modell"] = modell.get()
        config["custom_prompt"] = customprompt.get("1.0", "end-1c")
        config["stoff_prompt"] = stoff_prompt_box.get("1.0", "end-1c")
        config["aufgaben_prompt"] = aufgaben_prompt_box.get("1.0", "end-1c")
        
        with open("config.json", "w") as w:
            json.dump(config, w, indent=4)
            
        tutor.setze_api_key(config["api_key"])
        setting_fenster.destroy()

    speicher_button = c.CTkButton(setting_fenster, text="Speichern", command=speichern)
    speicher_button.pack(pady=20)



def check_api_key():
    config = {}

    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)

    if "api_key" not in config or config["api_key"] == "":
        dialog = c.CTkInputDialog(text="Bitte API-Key eingeben:", title="Erster Start")
        echter_key = dialog.get_input()


        if echter_key:
            config["api_key"] = echter_key
            with open("config.json", "w") as w:
                json.dump(config, w, indent=4)


        else:
            app.destroy()
            sys.exit()
            return
    tutor.setze_api_key(config["api_key"])

def render_markdown(textbox, text):
    zeilen = text.split('\n')
    for zeile in zeilen:
        aktueller_tag = None
        if zeile.startswith("### "):
            zeile = zeile[4:]
            aktueller_tag = "heading"
        elif zeile.startswith("## "):
            zeile = zeile[3:]
            aktueller_tag = "heading"
        
        if aktueller_tag:
            zeile = zeile.replace("**", "") 
            textbox.insert("end", zeile + "\n", aktueller_tag)
        else:
            teile = zeile.split("**")
            for i, teil in enumerate(teile):
                if i % 2 == 1:
                    textbox.insert("end", teil, "bold")
                else:
                    textbox.insert("end", teil)
            textbox.insert("end", "\n")



welcome_frame = c.CTkFrame(app)
welcome_label = c.CTkLabel(welcome_frame, text="Du hast noch keine Fächer... Erstelle hier ein neues!", font=("Segoe UI", 24, "bold"))
welcome_button = c.CTkButton(welcome_frame, text="Neues Fach erstellen", width=250, height=50, font=("Segoe UI", 16, "bold"), fg_color="#5865F2", hover_color="#4752C4", command=fachadd)

welcome_label.place(relx=0.5, rely=0.45, anchor="center")
welcome_button.place(relx=0.5, rely=0.55, anchor="center")

leftframe = c.CTkFrame(app, fg_color="#2b2d31")
box_stoff = c.CTkScrollableFrame(leftframe, label_text="Relevante Quellen", scrollbar_button_color="#1e1f22", scrollbar_button_hover_color="#4e5058")
upload_stoff = c.CTkButton(box_stoff, text="Upload", command=lambda: dokumente_laden("stoff"), fg_color="#4e5058", hover_color="#6d6f78", corner_radius=4)
box_Aufgaben = c.CTkScrollableFrame(leftframe, label_text="Relevante Aufgaben", scrollbar_button_color="#1e1f22", scrollbar_button_hover_color="#4e5058")
upload_Aufgaben= c.CTkButton(box_Aufgaben, text="Upload", command=lambda: dokumente_laden("aufgaben"), fg_color="#4e5058", hover_color="#6d6f78", corner_radius=4)
centerframe = c.CTkFrame(app, fg_color="transparent")
rightframe = c.CTkFrame(app, fg_color="#2b2d31")

bold_font = c.CTkFont(family="Segoe UI", size=14, weight="bold")
heading_font = c.CTkFont(family="Segoe UI", size=16, weight="bold")
chatfenster = c.CTkTextbox(centerframe, width=700, height=400, fg_color="#1e1f22", corner_radius=8, font=("Segoe UI", 14), wrap="word")
chatfenster.configure(state="disabled")
chatfenster._textbox.tag_config("bold", font=bold_font)
chatfenster._textbox.tag_config("heading", font=heading_font, foreground="#5865F2")

toolbar = c.CTkFrame(centerframe)
eingabe_frame = c.CTkFrame(centerframe, fg_color="transparent")
eingabefeld = c.CTkTextbox(eingabe_frame, width=700, height=70, fg_color="#1e1f22", border_width=0, corner_radius=8, font=("Segoe UI", 14), wrap="word")
eingabefeld.bind("<Control-v>", bild_einfuegen)
eingabefeld.bind("<Return>", enter_senden)
bild_vorschau_frame = c.CTkFrame(centerframe, fg_color="transparent")
button = c.CTkButton(eingabe_frame, text= "Senden", height=70, command=nachricht_senden, fg_color="#5865F2", hover_color="#4752C4",  corner_radius=6)
delbutton = c.CTkButton(toolbar, text="Empty chat", command=chat_leeren, corner_radius=6, fg_color="#4e5058", hover_color="#ed4245")
bilduploadbutton = c.CTkButton(toolbar, text="Upload Screenshots", command=bild_laden_dialog, fg_color="#4e5058", hover_color="#6d6f78",  corner_radius=6)
settingsbutton = c.CTkButton(toolbar, text="Settings", command=show_settings, fg_color="#4e5058", hover_color="#6d6f78", corner_radius=6)
pdf_canvas = tk.Canvas(rightframe, bg="#2b2b2b", highlightthickness=0)
scroll_y = c.CTkScrollbar(rightframe, orientation="vertical", command=pdf_canvas.yview)
scroll_x = c.CTkScrollbar(rightframe, orientation="horizontal", command=pdf_canvas.xview)
pdf_canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
pdf_toolbar = c.CTkFrame(rightframe)

pdf_toolbar.pack(fill="x", pady =5, padx=5)
scroll_x.pack(side="bottom", fill="x")
scroll_y.pack(side="right", fill="y")
pdf_canvas.pack(side="left", fill="both", expand=True)

pdf_aufgabeladen = c.CTkButton(pdf_toolbar, text="Upload", command=aufgabeladen, fg_color="#4e5058", hover_color="#6d6f78", corner_radius=4)
pdf_vor = c.CTkButton(pdf_toolbar, width=40, text=">", command=naechste_seite,  fg_color="#4e5058", hover_color="#6d6f78", corner_radius=4)
pdf_zurueck = c.CTkButton(pdf_toolbar, width=40, text="<", command=vorherige_seite,  fg_color="#4e5058", hover_color="#6d6f78", corner_radius=4)
pdf_zoomin = c.CTkButton(pdf_toolbar, width=40, text="+", command=zoom_in,  fg_color="#4e5058", hover_color="#6d6f78", corner_radius=4)
pdf_zoomout = c.CTkButton(pdf_toolbar, width=40, text="-",command=zoom_out,  fg_color="#4e5058", hover_color="#6d6f78", corner_radius=4)
pdf_schliessen = c.CTkButton(pdf_toolbar, width=40, text="X", command=aufgabe_schliessen, fg_color="#ed4245", hover_color="#c83436", corner_radius=4)

pdf_aufgabeladen.pack(side="left", pady=5, padx=5)

pdf_zurueck.pack(side="left", pady=5, padx=5)
pdf_vor.pack(side="left", pady=5, padx=5)
pdf_zoomin.pack(side="left", pady=5, padx=5)
pdf_zoomout.pack(side="left", pady=5, padx=5)
pdf_schliessen.pack(side="right", padx=5, pady=5)



leftframe.pack(side="left", fill="both", expand=True, padx=10, pady=10)
centerframe.pack(side="left", fill="both", expand=True, padx=10, pady=10)
rightframe.pack(side="left", fill="both", expand=True, padx=10, pady=10)
box_stoff.pack(fill="both", expand=True, padx=5, pady=5)
box_Aufgaben.pack(fill="both", expand=True, padx=5, pady=5)
upload_stoff.pack(pady=10)
upload_Aufgaben.pack(pady=10)


toolbar.pack(side="top", fill="x", pady=5)

eingabe_frame.pack(side="bottom", fill="x", pady=(0,10))

bild_vorschau_frame.pack(side="bottom", fill="x", pady=2)
chatfenster.pack(side="top", fill="both", expand=True, pady=(0, 10))






eingabefeld.pack(side="left", fill="both", expand=True, padx=(0,10))
button.pack(side="right")
delbutton.pack(side="right", padx=5, pady=3)
settingsbutton.pack(side="left", padx=5, pady=3)
bilduploadbutton.pack(side="right", padx=5, pady=3)



check_api_key()
if os.path.exists("config.json"):
    with open("config.json", "r") as f:
        einstellungen = json.load(f)
        if "letztes_fach" in einstellungen:
            letztes_fach = einstellungen["letztes_fach"]
            fachwechsel(letztes_fach)

fachladen()
if aktuellesfach == "":
    zeige_welcome_screen()
app.mainloop()
