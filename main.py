import time
import keyboard
import serial
import serial.tools.list_ports
import pyperclip
import os
import subprocess
import webbrowser

from config import *


ports = serial.tools.list_ports.comports()
for _ in ports: CURRENT_PORT=_.device

ser = serial.Serial(CURRENT_PORT, BAUD_RATE, timeout=1)


def run_command(line: str) -> None:
	match KEYS[line][0]:
		case "commands":
			for l in KEYS[line][1]:
				run_command(l)
		case "open_link":
			webbrowser.open(KEYS[line][1])
		case "keyboard_paste":
			pyperclip.copy(KEYS[line][1])
			if IS_MAC:
				keyboard.press('command+v')
				keyboard.release('command+v')
			else:
				keyboard.press('ctrl+v')
				keyboard.release('ctrl+v')
		case "keyboard_write":
			keyboard.write(KEYS[line][1])
		case "keyboard_hotkey":
			for key in KEYS[line][1]:
				keyboard.press(key)
			for key in KEYS[line][1]:
				keyboard.release(key)
		case "keyboard_line":
			for key in KEYS[line][1]:
				keyboard.send(key)
		case "python":
			eval(KEYS[line][1])
		case "system":
			subprocess.Popen(KEYS[line][1])
		case "program":
			if(os.name) == "nt":
				subprocess.Popen(
					[fr"{KEYS[line][1]}"],
					creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
					close_fds=True
				)
			elif os.name == "posix":
				subprocess.Popen(
					[KEYS[line][1]], 
					start_new_session=True,
					stdout=subprocess.DEVNULL,
					stderr=subprocess.DEVNULL,
					stdin=subprocess.DEVNULL
				)
					

time.sleep(2)
while True:
	line = ser.readline().decode("utf-8", errors="ignore").strip()
	if line in KEYS.keys():
		run_command(line)