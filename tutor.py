import os
import json
from dotenv import load_dotenv
from groq import Groq
import base64
import io



temporaere_aufgabe = ""
aktuelledatei = ""
client = None
myapi_key = os.getenv("GROQ_API_KEY")




tutor_prompt = """
    WICHTIGE SYSTEM-REGELN FÜR DAS UI:
    Deine Antworten werden in einem simplen Text-Terminal ohne Formatierungs-Engine ausgegeben. Du MUSST folgende Regeln absolut strikt einhalten:

    1. ABSOLUTES MARKDOWN-VERBOT: Verwende NIEMALS Sternchen (*), Unterstriche (_) oder Rauten (#). 
    2. HERVORHEBUNGEN: Schreibe Überschriften oder Kernbegriffe komplett in GROSSBUCHSTABEN (z.B. WICHTIG:, ZUSAMMENFASSUNG:).
    3. ABSOLUTES LATEX-VERBOT: Verwende NIEMALS Backslashes (\), Dollarzeichen ($) oder TeX-Befehle (wie \cup, \mathcal{P}, \subseteq).
    4. MATHEMATIK ALS TEXT: Schreibe Formeln als normalen, gesprochenen Fließtext (z. B. "vereint mit" statt "\cup").
    5. PERFEKTE LESBARKEIT & STRUKTUR (EXTREM WICHTIG):
        - KEINE TEXTWÄNDE! Mache nach jedem Gedanken, vor jeder Liste und nach jeder Liste zwingend eine LEERE ZEILE (doppelter Zeilenumbruch).
        - Nutze für Hauptpunkte einfache Bindestriche (-).
        - Für Unterpunkte oder Erklärungen MUSST du einrücken! Nutze dafür 3 Leerzeichen und einen Pfeil (z. B. "   -> Das bedeutet...").
        - Halte deine Sätze kurz, prägnant und extrem übersichtlich.
    """


def lade_system_prompt():
    global tutor_prompt
    if os.path.exists("config.json"):
        with open("config.json", "r") as f: 
            config = json.load(f)
        persoenlichkeit = config.get("custom_prompt", "Du bist ein hilfreicher Tutor")
        return persoenlichkeit + "\n\n" + tutor_prompt
    return "Du bist ein hilfreicher Tutor\n\n" + tutor_prompt
    
preanswer = [{"role": "system", "content": lade_system_prompt()}]


def setze_aufgabe(text):
     global temporaere_aufgabe
     temporaere_aufgabe = text



def ladefach(fach):
    global preanswer
    global aktuelledatei

    aktuelledatei = fach + "_chat.json"

    preanswer = [{"role": "system", "content": lade_system_prompt()}]

    if os.path.exists(aktuelledatei):
        with open(aktuelledatei, "r") as f:
            preanswer = json.load(f)

    return preanswer
            


def kontext_laden(text):
    global preanswer
    global aktuelledatei

    preanswer.append({"role": "user", "content": text})
    with open(aktuelledatei, "w") as f:
                json.dump(preanswer, f, indent=4)
    return preanswer



def dokumente_speichern(dateiname, text, art):
    global aktuelledatei
    speicherpfad = aktuelledatei.replace("chat.json", art + ".json")
    sammlung = {}

    if os.path.exists(speicherpfad):
        with open(speicherpfad, "r") as f:
             sammlung = json.load(f)
    sammlung[dateiname] = text 
    with open(speicherpfad, "w") as w:
         json.dump(sammlung, w, indent=4)

def wissen_abrufen(art):
    global aktuelledatei
    speicherpfad = aktuelledatei.replace("chat.json", art + ".json")
    geballtes_wissen= ""

    if os.path.exists(speicherpfad):
        with open(speicherpfad, "r") as f:
               sammlung = json.load(f)
        for dateiname in sammlung:
               geballtes_wissen = geballtes_wissen + sammlung[dateiname] + "\n"

    return geballtes_wissen



def dokument_loeschen(dateiname, art):
     global aktuelledatei
     speicherpfad = aktuelledatei.replace("chat.json", art + ".json")

     if os.path.exists(speicherpfad):
        with open(speicherpfad, "r") as f:
               sammlung = json.load(f)
        if dateiname in sammlung:
                   del sammlung[dateiname]
        with open(speicherpfad, "w") as w:
             json.dump(sammlung, w)


def chat_leeren():
     global aktuelledatei
     if os.path.exists(aktuelledatei):
          with open(aktuelledatei, "w") as w:
            json.dump([], w)

def setze_api_key(key):
     global client
     client = Groq(api_key=key)
        

def generiere_antwort(eingabe, bilder=None):
    global preanswer
    global aktuelledatei
    global temporaere_aufgabe
    config = {}
    

    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
             config = json.load(f)


    
    if not eingabe:
        return("")
    
    wissen_stoff = wissen_abrufen("stoff")
    wissen_aufgaben = wissen_abrufen("aufgaben")

    
    if eingabe.startswith("/"):
        if eingabe.startswith("/load"):
            try:
                befehllist= eingabe.split()
                dateiname = befehllist[1]

            
                with open(dateiname, "r") as f:
                    inhalt = f.read()
                    preanswer.append({"role": "user", "content": "Hier ist das Arbeitsmaterial: " + inhalt})
                    return ("arbeitsmaterial geladen!")
            except: 
                return("Fehler! Versuche erneut!")
                
        elif eingabe == "/clear":
            preanswer = [{"role": "system", "content": lade_system_prompt()}]
            return("Gedächtnis erfolgreich gelöscht!")
            
                
        else:
            return("unbekannter befehl!")

    preanswer.append({"role": "user", "content": eingabe})

    apinachrichten = preanswer.copy()


    if bilder and len(bilder) > 0:
        nachrichten_inhalt = [{"type": "text", "text": eingabe}]

        for bild in bilder:
            puffer = io.BytesIO()
            bild.save(puffer, format="PNG")
            base64_string = base64.b64encode(puffer.getvalue()).decode("utf-8")
            bild_format = {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_string}"}

                }
            nachrichten_inhalt.append(bild_format)
        apinachrichten[-1] = {"role": "user", "content": nachrichten_inhalt}

        

       

    if wissen_stoff or wissen_aufgaben:
        kombi_wissen = "WICHTIG: Dir wurde folgendes Arbeitsmaterial bereitgestellt. Du HAST Zugriff darauf. Verweigere niemals die Antwort.\n\n"
        
        if wissen_stoff:
            stoff_prefix = config.get("stoff_prompt", "--- VORLESUNGSSTOFF (Theorie & Grundlagen) ---")
            kombi_wissen = kombi_wissen + stoff_prefix + "\n" + wissen_stoff + "\n\n"
            
        if wissen_aufgaben:
            aufgaben_prefix = config.get("aufgaben_prompt", "--- ALTKLAUSUREN & ÜBUNGEN (Extrem prüfungsrelevant) ---")
            kombi_wissen = kombi_wissen + aufgaben_prefix + "\n" + wissen_aufgaben + "\n"

        apinachrichten.insert(0, {"role": "system", "content": kombi_wissen})



    
             



    if temporaere_aufgabe != "":
         apinachrichten.insert(0, {"role": "system", "content": "Der user hat gerade folgendes Aufgabenblatt vor sich geöffnet welches du sehen und zugriff drauf hast: " + temporaere_aufgabe})
    try:
        antwort = client.chat.completions.create(
            model = config.get("modell", "qwen/qwen3.6-27b"),
            messages= apinachrichten)
        ki_text= antwort.choices[0].message.content
    except Exception as e:
         return "System-Fehler: Konnte keine Verbindung zur KI herstellen"
    if "</think>" in ki_text:
        ki_text = ki_text.split("</think>")[-1].strip()
    preanswer.append({"role": "assistant", "content": ki_text})
    with open(aktuelledatei, "w") as f:
        json.dump(preanswer, f, indent=4)
    return(ki_text)











