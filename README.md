# Doctor Rhythm 🎵

**Doctor Rhythm** is a Python script designed to help musicians, teachers and student to transcribe musical rhythms in a interactive way. You can:

- Tap the rhythm (tap tempo)
- Automatically calculates the BPM
- View and save the rhythm in a CSV or/and MIDI file format
- Use a graphic piano roll to edit the notes
- Export the piano roll changes as MIDI

## Main Functions

- ⏱️ BPM calculation from taps
- 🎧 Metronome
- 📝 Rhythm recording
- 📄 CSV Export
- 🎼 MIDI Export
- 🎹 Piano Roll to visually edit the rhythm

## How To Use

1. **T - Tap Tempo**: tap 4 times to set a BPM
2. **R - Registra**: start tapping the rhythm
3. **ENTER**: stops the recording
4. **S**: export in CSV
5. **X**: export in MIDI
6. **P**: plays the exported MIDI file
7. **C**: record new rhythm at the previous BPM
8. **L**: sets the language from Italian to English and viceversa
5. **V**: open the Piano Roll
6. **ESC**: exit

## Piano Roll

In the Piano Roll window:
- **Left Click**: to add a note
- **Drag**: to move a note in the grid
- **Drag right border**: to modify the length
- **BACKSPACE**: to delete a note
- **S**: to export the modified MIDI

## IF YOU ALREADY GENERATED THE MIDI FILE BEFORE THE PIANO ROLL, **DELETE THAT** AND GENERATE THE NEW ONE FROM THE PIANO ROLL!

## Requirements

- Python 3.7+
- Libraries:
  - `pygame`
  - `music21`
  - `numpy`

Install the required packages with:

```bash
pip install pygame music21 numpy
```

## Contribute
Feel free to contribute to this project how you want. 
