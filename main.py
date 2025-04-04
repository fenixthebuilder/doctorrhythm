import pygame
import time
import numpy as np
import csv
import tempfile
import wave
import os
import threading
from music21 import stream, note, duration, metadata, tempo

# --- CONFIG ---
LARGHEZZA, ALTEZZA = 1000, 700
BATTITI_PER_BATTUTA = 4
BATTUTE = 8
TEMPO_MAX_ATTESA = 3.0
METRONOMO_ATTIVO = True
LINGUA = "IT"

pygame.init()
pygame.mixer.init()
finestra = pygame.display.set_mode((LARGHEZZA, ALTEZZA))
pygame.display.set_caption("Doctor Rhythm")
font = pygame.font.SysFont(None, 28)
clock = pygame.time.Clock()

def genera_click(freq=1000, durata=0.03):
    sr = 44100
    t = np.linspace(0, durata, int(sr * durata), False)
    onda = 0.5 * np.sign(np.sin(2 * np.pi * freq * t))
    data = (onda * 32767).astype(np.int16)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    path = temp.name
    temp.close()
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data.tobytes())
    return path

click_normale = pygame.mixer.Sound(genera_click(800))
click_accentato = pygame.mixer.Sound(genera_click(1200))
click_normale.set_volume(0.3)     # Valore da 0.0 a 1.0
click_accentato.set_volume(0.4)   # Accentato leggermente più forte, ma meno trapanante


tap_times, delta_taps = [], []
bpm = 0
fase = "menu"
eventi_nota = []
visual_timeline = []
ultimo_tap, start_record = 0, 0
beat_index_visivo = 0

# --- FUNZIONI ---

def calcola_bpm():
    if len(tap_times) < 2: return None
    diff = [b - a for a, b in zip(tap_times[:-1], tap_times[1:])]
    return round(60 / (sum(diff) / len(diff)))

def calcola_nota(durata_in_beats):
    if durata_in_beats <= 0:
        return ("Pausa" if LINGUA == "IT" else "Rest"), 0

    dizionario = {
        4.0: ("Semibreve", "Whole Note"),
        2.0: ("Minima", "Half Note"),
        1.5: ("Semiminima puntata", "Dotted Quarter"),
        1.0: ("Semiminima", "Quarter Note"),
        0.75: ("Ottavo puntato", "Dotted Eighth"),
        0.6667: ("Terzina di semiminima", "Quarter Triplet"),
        0.5: ("Ottavo", "Eighth Note"),
        0.3333: ("Terzina di ottavo", "Eighth Triplet"),
        0.25: ("Sedicesimo", "Sixteenth Note"),
        0.1667: ("Terzina di sedicesimi", "Sixteenth Triplet"),
        0.125: ("Trentaduesimo", "Thirty-second Note")
    }

    vicino = min(dizionario.keys(), key=lambda x: abs(x - durata_in_beats))
    nome_it, nome_en = dizionario[vicino]
    nome_finale = nome_it if LINGUA == "IT" else nome_en
    return nome_finale, round(vicino, 4)

def aggiungi_evento_visuale(nome, durata):
    misura, beat = 1, 1
    for ev in visual_timeline:
        if ev["misura"] == misura and ev["beat"] == beat:
            beat += 1
            if beat > BATTITI_PER_BATTUTA:
                misura += 1
                beat = 1
    visual_timeline.append({"misura": misura, "beat": beat, "durata": durata})

def disegna_testo(txt, x, y, colore=(255, 255, 255)):
    surf = font.render(txt, True, colore)
    finestra.blit(surf, (x, y))

def avvia_metronomo_thread():
    def suona():
        global beat_index_visivo
        intervallo = 60 / bpm if bpm > 0 else 0.5
        beat_index_visivo = 0
        for i in range(BATTUTE * BATTITI_PER_BATTUTA):
            if fase != "registra": break
            (click_accentato if i % BATTITI_PER_BATTUTA == 0 else click_normale).play()
            beat_index_visivo = i % BATTITI_PER_BATTUTA
            time.sleep(intervallo)
    threading.Thread(target=suona, daemon=True).start()

def disegna_visualizzazione():
    finestra.fill((20, 20, 20))
    
    # Mostra BPM
    disegna_testo(f"BPM: {bpm}", 20, 20)

    # Messaggio per la fase di registrazione
    if fase == "registra":
        msg = "Premi ENTER per terminare" if LINGUA == "IT" else "Press ENTER to finish"
        disegna_testo(msg, 20, 50, (255, 255, 0))

    # Visualizzazione della timeline delle note
    y = 100
    misura_corrente = 0
    for ev in visual_timeline:
        if ev["misura"] != misura_corrente:
            misura_corrente = ev["misura"]
            y += 30
        nome_nota, _ = calcola_nota(ev["durata"])
        disegna_testo(f"{ev['misura']} / {ev['beat']} - {nome_nota} ({ev['durata']})", 40, y)
        y += 20

    # Comandi disponibili nella fase di analisi
    if fase == "analisi":
        hint_it = "S=CSV  X=MIDI  P=Play  C=Nuova Reg.  L=Lingua  V=Piano Roll  ESC=Esci"
        hint_en = "S=CSV  X=MIDI  P=Play  C=New Reg.  L=Language  V=Piano Roll  ESC=Exit"
        disegna_testo(hint_it if LINGUA == "IT" else hint_en, 40, ALTEZZA - 40)

def esporta_csv():
    with open("ritmo.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Misura", "Beat", "Nota", "Durata"])
        for ev in visual_timeline:
            writer.writerow([ev["misura"], ev["beat"], ev["nota"], ev["durata"]])

def esporta_midi_dal_piano_roll(piano_roll_data):
    s = stream.Stream()
    s.append(metadata.Metadata(title="Piano Roll Export"))
    s.append(tempo.MetronomeMark(number=bpm))
    for ev in piano_roll_data:
        dur = ev["durata"]
        n = note.Rest() if ev["nota"].lower() == "pausa" else note.Note("C4")
        n.duration = duration.Duration(dur)
        s.append(n)
    s.write("midi", fp="pianoroll.mid")


def esporta_midi():
    s = stream.Stream()
    s.append(metadata.Metadata(title="Rhythm Export"))
    s.append(tempo.MetronomeMark(number=bpm))
    for ev in visual_timeline:
        n = note.Rest() if ev["nota"].lower() == "pausa" else note.Note("C4")
        n.duration = duration.Duration(ev["durata"])
        s.append(n)
    s.write("midi", fp="ritmo.mid")


def play_midi():
    if os.path.exists("ritmo.mid"):
        os.startfile("ritmo.mid")

# === PIANO ROLL ===
def apri_piano_roll():
    screen = pygame.display.set_mode((1000, 400))
    pygame.display.set_caption("Piano Roll")
    clock = pygame.time.Clock()
    grid_size = 40
    height = 30
    piano_roll_data = [{"x": ev["beat"] * grid_size + (ev["misura"]-1)*BATTITI_PER_BATTUTA*grid_size,
                    "y": 100,
                    "w": max(int(ev["durata"]*grid_size), 10),
                    "h": height,
                    "durata": ev["durata"],
                    "nota": calcola_nota(ev["durata"])[0]} for ev in visual_timeline]

    dragging = None
    resizing = None
    run_roll = True
    while run_roll:
        screen.fill((30, 30, 30))
        for x in range(0, 1000, grid_size):
            pygame.draw.line(screen, (60, 60, 60), (x, 0), (x, 400))
        for note in piano_roll_data:
            rect = pygame.Rect(note["x"], note["y"], note["w"], note["h"])
            pygame.draw.rect(screen, (100, 200, 100), rect)
        legenda = {
    "IT": "Click: aggiungi | Trascina: sposta | Resize | BACKSPACE: elimina | S: esporta MIDI",
    "EN": "Click: add | Drag: move | Resize | BACKSPACE: delete | S: export MIDI"
}
        disegna_testo(legenda[LINGUA], 20, 360, (200, 200, 200))


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_roll = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run_roll = False
                elif event.key == pygame.K_s:
                    esporta_midi_dal_piano_roll(piano_roll_data)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                for note in reversed(piano_roll_data):
                    rect = pygame.Rect(note["x"], note["y"], note["w"], note["h"])
                    if rect.collidepoint(x, y):
                        if x > note["x"] + note["w"] - 10:
                            resizing = note
                        else:
                            dragging = note
                        offset_x = x - note["x"]
                        break
                else:
                    if event.button == 1:
                        grid_x = (x // grid_size) * grid_size
                        piano_roll_data.append({
                            "x": grid_x, "y": 100, "w": grid_size, "h": height,
                            "durata": 1.0, "nota": "Semiminima"
                        })
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = None
                resizing = None
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                x, y = pygame.mouse.get_pos()
                for note in piano_roll_data:
                    rect = pygame.Rect(note["x"], note["y"], note["w"], note["h"])
                    if rect.collidepoint(x, y):
                        piano_roll_data.remove(note)
                        break

        if dragging:
            x, y = pygame.mouse.get_pos()
            dragging["x"] = x - offset_x
        if resizing:
            x, y = pygame.mouse.get_pos()
            resizing["w"] = max(10, x - resizing["x"])
            resizing["durata"] = round(resizing["w"] / grid_size, 2)

        pygame.display.flip()
        clock.tick(60)
    pygame.display.set_mode((LARGHEZZA, ALTEZZA))

# === MAIN LOOP ===
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            elif event.key == pygame.K_l and fase in ["menu", "analisi"]:
                LINGUA = "EN" if LINGUA == "IT" else "IT"
    
                # Se siamo nella home, ridisegniamo subito la schermata
                if fase == "menu":
                    finestra.fill((30, 30, 30))
                    disegna_testo("T - Tap Tempo (4 Tap)" if LINGUA == "IT" else "T - Tap Tempo (4 Taps)", 40, 100)
                    disegna_testo("R - Registra ritmo" if LINGUA == "IT" else "R - Record rhythm", 40, 140)
                    disegna_testo("L - Cambia lingua" if LINGUA == "IT" else "L - Change language", 40, 180)
                    disegna_testo("ESC - Esci" if LINGUA == "IT" else "ESC - Exit", 40, 220)
                    pygame.display.flip()
            elif event.key == pygame.K_t:
                tap_times.append(time.time())
                if len(tap_times) > 4: tap_times.pop(0)
                if len(tap_times) == 4:
                    bpm = calcola_bpm()
                    tap_times.clear()
                    fase = "menu"
            elif event.key == pygame.K_r and bpm > 0:
                eventi_nota.clear()
                visual_timeline.clear()
                fase = "registra"
                delta_taps.clear()
                start_record = ultimo_tap = time.time()
                if METRONOMO_ATTIVO: avvia_metronomo_thread()
            elif event.key == pygame.K_RETURN and fase == "registra":
                if visual_timeline: fase = "analisi"
            elif event.key == pygame.K_c and fase == "analisi":
                eventi_nota.clear()
                visual_timeline.clear()
                fase = "registra"
                delta_taps.clear()
                start_record = ultimo_tap = time.time()
                if METRONOMO_ATTIVO: avvia_metronomo_thread()
            elif event.key == pygame.K_s and fase == "analisi":
                esporta_csv()
            elif event.key == pygame.K_x and fase == "analisi":
                esporta_midi()
            elif event.key == pygame.K_p and fase == "analisi":
                play_midi()
            elif event.key == pygame.K_v and fase == "analisi":
                apri_piano_roll()
            elif fase == "registra":
                now = time.time()
                delta = now - (delta_taps[-1] if delta_taps else start_record)
                durata = delta * bpm / 60
                nome, valore = calcola_nota(durata)
                eventi_nota.append((nome, valore))
                aggiungi_evento_visuale(nome, valore)
                delta_taps.append(now)
                ultimo_tap = now

    if fase == "registra" and time.time() - ultimo_tap > TEMPO_MAX_ATTESA and visual_timeline:
        fase = "analisi"

    if fase == "menu":
        finestra.fill((30, 30, 30))
        disegna_testo("T - Tap Tempo (4 Tap)", 40, 100)
        disegna_testo("R - Registra ritmo", 40, 140)
        disegna_testo("L - Cambia lingua", 40, 180)
        disegna_testo("ESC - Esci", 40, 220)
    elif fase in ["registra", "analisi"]:
        disegna_visualizzazione()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
