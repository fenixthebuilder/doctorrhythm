import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["pygame", "numpy", "time", "csv", "tempfile", "os", "wave", "os", "threading", "music21"]
}
    
setup(name="Doctor Rhythm", version="1.0", description="Music Transcription Tool", executables=[Executable("main.py", target_name= "Doctor_Rhythm", base = "Win32GUI")])