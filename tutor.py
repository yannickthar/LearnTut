import os
import json
from dotenv import load_dotenv
from groq import Groq
import base64
import io
import re
import rag_engine

temporaere_aufgabe = ""
aktuelledatei = ""
client = None
myapi_key = os.getenv("GROQ_API_KEY")




tutor_prompt = r"""
    WICHTIGE SYSTEM-REGELN FÜR DAS UI:
    Deine Antworten werden in einem speziellen Text-Terminal ausgegeben. Du MUSST folgende Formatierungs-Regeln strikt einhalten:

    1. HERVORHEBUNGEN & ÜBERSCHRIFTEN (SEHR WICHTIG): 
        - Nutze für Überschriften oder neue Abschnitte IMMER drei Rauten (z. B. `### Wichtige Konzepte`).
        - Nutze für Kernbegriffe, Definitionen oder wichtige Wörter IMMER Sternchen für Fettgedrucktes (z. B. `**Zusammenfassung:**`).
        - Verwende KEINE anderen Markdown-Elemente wie Kursivdruck oder Unterstriche.
    2. ABSOLUTES LATEX-VERBOT: Verwende NIEMALS Backslashes (\), Dollarzeichen ($) oder TeX-Befehle (wie \cup, \mathcal{P}, \subseteq).
    3. MATHEMATIK ALS TEXT: Schreibe Formeln als normalen, gesprochenen Fließtext (z. B. "vereint mit" statt "\cup", "Teilmenge von" statt "\subseteq").
    4. PERFEKTE LESBARKEIT & STRUKTUR:
        - KEINE TEXTWÄNDE! Mache nach jedem Gedanken, vor jeder Liste und nach jeder Liste zwingend eine LEERE ZEILE (doppelter Zeilenumbruch).
        - Nutze für Listen einfache Bindestriche (-).
        - Für Erklärungen zu Unterpunkten rücke mit 3 Leerzeichen und einem Pfeil ein (z. B. "   -> Das bedeutet...").
        - Fasse dich kurz und prägnant. Antworte auf den Punkt.
    5. Antworte immer auf Deutsch, außer der User verlangt explizit eine andere Sprache.
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


    zerschnitten_text = rag_engine.erstelle_chunks(text)
    vektor = rag_engine.vektoren_erstellen(zerschnitten_text)
    vektor_liste = vektor.tolist()


    if os.path.exists(speicherpfad):
        with open(speicherpfad, "r") as f:
            sammlung = json.load(f)
    sammlung[dateiname] = {"chunks": zerschnitten_text, "vektoren": vektor_liste}    
    with open(speicherpfad, "w") as w:
         json.dump(sammlung, w, indent=4)








def wissen_abrufen(art, frage):
    global aktuelledatei
    speicherpfad = aktuelledatei.replace("chat.json", art + ".json")
    alle_chunks = []
    alle_vektoren = []


    if os.path.exists(speicherpfad):
        with open(speicherpfad, "r") as f:
            sammlung = json.load(f)
        for dateiname in sammlung:
            alle_chunks.extend(sammlung[dateiname]["chunks"])
            alle_vektoren.extend(sammlung[dateiname]["vektoren"])

    if len(alle_chunks) == 0 :
        return ""
    beste_treffer = rag_engine.suche(frage, alle_chunks,alle_vektoren, anzahl=3)
    return "\n\n".join(beste_treffer)




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
     global preanswer

     preanswer = [{"role": "system", "content": lade_system_prompt()}]
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
    
    erweiterte_suche = eingabe
    
    trigger_woerter = [
        "klausur", "relevant", "vergleich", "ähnlich", "vorlesung", "abgleich", 
        "wichtig", "prüfungsrelevant", "vergleiche", "zusammenhang", 
        "klausuraufgabe", "stoff", "folien", "skript", "altklausur", 
        "altklausuren", "fokus", "schwerpunkt", "übereinstimmung", "zusammenfassen"
    ]
    
    sucht_nach_relevanz = any(wort in eingabe.lower() for wort in trigger_woerter)

    if sucht_nach_relevanz and temporaere_aufgabe != "":
        alle_woerter = temporaere_aufgabe.replace("\n", " ").split()
        fachbegriffe = list(set([wort for wort in alle_woerter if len(wort) >= 5]))
        such_keywords = " ".join(fachbegriffe[:15])
        
        erweiterte_suche = eingabe + " Relevante Themen: " + such_keywords

    wissen_stoff = wissen_abrufen("stoff", erweiterte_suche)
    wissen_aufgaben = wissen_abrufen("aufgaben", erweiterte_suche)
    
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
    if len(apinachrichten) > 7:
        apinachrichten = [apinachrichten[0]] + apinachrichten[-6:]

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
        kombi_wissen = (
            "SYSTEM-WARNUNG: Du HAST Zugriff auf die Altklausuren und Vorlesungsskripte des Users! "
            "Sie werden dir direkt hier im Text unter den entsprechenden Überschriften bereitgestellt. "
            "Behaupte NIEMALS, es seien keine Altklausuren hochgeladen worden, sondern nutze zwingend den Text unten.\n\n"
        )
        
        if wissen_stoff:
            stoff_prefix = config.get("stoff_prompt", "--- VORLESUNGSSTOFF ---")
            kombi_wissen += stoff_prefix + "\n" + wissen_stoff + "\n\n"
            
        if wissen_aufgaben:
            aufgaben_prefix = config.get("aufgaben_prompt", "--- ALTKLAUSUREN & ÜBUNGEN ---")
            kombi_wissen += aufgaben_prefix + "\n" + wissen_aufgaben + "\n"

        apinachrichten.insert(0, {"role": "system", "content": kombi_wissen})

    
             



    if temporaere_aufgabe != "":
         klartext_anweisung = (
            "WICHTIGE INFO: Der User hat gerade ein Übungsblatt in der App geöffnet. "
            "Wenn der User sagt 'mach Aufgabe X' oder sich auf 'das Blatt' bezieht, "
            "musst du zwingend diesen Text hier nutzen:\n\n"
            "--- START ÜBUNGSBLATT ---\n"
            f"{temporaere_aufgabe}\n"
            "--- ENDE ÜBUNGSBLATT ---"
        )
         apinachrichten.insert(0, {"role": "system", "content": klartext_anweisung})
    try:
        antwort = client.chat.completions.create(
            model = config.get("modell", "qwen/qwen3.6-27b"),
            messages= apinachrichten,
            max_tokens=950
            )
        ki_text= antwort.choices[0].message.content
    except Exception as e:
         return f"System-Fehler: {str(e)}"
    ki_text = re.sub(r"<think>.*?(?:</think>|$)", "", ki_text, flags=re.DOTALL).strip()
    
    if not ki_text:
        return "Fehler: Die KI hat nur nachgedacht, aber keine fertige Antwort geliefert."
    preanswer.append({"role": "assistant", "content": ki_text})
    with open(aktuelledatei, "w") as f:
        json.dump(preanswer, f, indent=4)
    return(ki_text)











