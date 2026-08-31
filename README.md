LearnTut
Ein KI-Tutor, den ich in Python geschrieben habe. Läuft mit der Groq API.
Man kann seine Skripte als PDF reinladen, eigene Fächer anlegen und sich gezielt mit der KI Aufgaben bearbeiten.

Features
Eigene Fächer & Themen strukturieren

Skripte und Dokumente einlesen (PyPDF2 / PyMuPDF)

Interaktive KI-Nachhilfe 

Lokales Setup
git clone https://github.com/yannickthar/LearnTut.git

Module installieren:
pip install customtkinter PyPDF2 PyMuPDF pillow groq

App starten:
python app.py

Den Groq API-Key müsst ihr in keinen Dateien eintragen. Startet einfach die App – sie fragt euch beim ersten Mal direkt nach dem Key und speichert ihn lokal ab.
