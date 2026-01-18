# ☠️ INST-DEATH ☠️

```
    ___  _   _  _____ _____       ____  _____    _  _____ _   _
   |_ _|| \ | |/ ____|_   _|     |  _ \| ____|  / \|_   _| | | |
    | | |  \| | (___   | |  _____| | | |  _|   / _ \ | | | |_| |
    | | | |\  |\___ \  | | |_____| |_| | |___ / ___ \| | |  _  |
   |___||_| \_||____/  |_|       |____/|_____/_/   \_\_| |_| |_|

```

> *Rip the guts out of your Ableton Live projects and forge them into Hapax instrument definitions.*

---

## WHAT IS THIS

INST-DEATH parses your `.als` files and extracts:
- **Instrument Racks** → Macro names become CC assignments
- **Drum Racks** → Pads become drum lane definitions

---

## REQUIREMENTS

- Python 3.10+
- Flask

```bash
pip install flask
```

---

## USAGE

**1. Start the server:**
```bash
python app.py
```

**2. Open the server:** http://localhost:5001

**3. Feed it your .als file** (drag & drop or click)

**4. Configure your instrument definition files:**
- Select which racks to extract
- Assign MIDI channels (1-16)
- Drum racks auto-split into groups of 8

**5. Execute.** Download your `.zip`.

---

## OUTPUT FORMAT

### Instrument Rack → POLY Definition
```
VERSION 1
TRACKNAME 1-Instrument Rack
TYPE POLY
OUTPORT USBD
OUTCHAN 1

[CC]
1 FREQ
2 RES
3 RELEASE
4 SHAPE
5 OCTAVE
6 DTUNE
7 NOIZ
8 GLIZZ
[/CC]

[ASSIGN]
1 CC:1
2 CC:2
3 CC:3
4 CC:4
5 CC:5
6 CC:6
7 CC:7
8 CC:8
[/ASSIGN]
```

### Drum Rack → DRUM Definition
```
VERSION 1
TRACKNAME 2-Kit_p1
TYPE DRUM
OUTPORT USBD
OUTCHAN 2

[DRUMLANES]
1:NULL:NULL:36 Kick
2:NULL:NULL:37 Snare
3:NULL:NULL:38 HiHat
4:NULL:NULL:39 Clap
[/DRUMLANES]
```

---

## TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Macros showing "Macro 1, 2, 3..." | Rename them in Ableton and **SAVE** before upload |
| Too many drum pads | They auto-split into groups of 8. Each group = separate file |
| Need different channels | Set per-track or per-drum-group in the UI |

---

## 📁 FILE NAMING

```
Instrument Rack  →  {track_name}.txt
Drum Rack        →  {track_name}_part1.txt, _part2.txt, ...
Download         →  {project}_hapax.zip
```
