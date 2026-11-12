# PoopDeck — a DIY macro pad (Arduino + Python)

<img width="200" height="200" alt="Какашка с клавиатурой PoopDeck" src="https://github.com/user-attachments/assets/d98b0c41-20b5-439f-83db-f3b429b93adf" />

Press a key on a 4×4 keypad and your computer does something: type text, open a link, press a hotkey,
launch a program, run a Python expression — or all of that in a chain.

> The project name is taken from the sketch file name (`poopdeckskecth.ino`). Rename it however you like.

```
┌──────────┐  key char   ┌───────────┐  USB serial   ┌───────────────┐  KEYS[...]  ┌───────────┐
│ 4×4 pad  │ ──────────▶ │  Arduino  │ ────────────▶ │ main.py (PC)  │ ──────────▶ │  action   │
└──────────┘             └───────────┘  9600 baud    └───────────────┘             └───────────┘
```

1. The Arduino scans the keypad and prints the pressed key (`1`–`9`, `0`, `*`, `#`, `A`–`D`) plus a newline to the serial port.
2. `main.py` reads one line at a time from that port.
3. If the line is a key in the `KEYS` dictionary (`config.py`), the matching action runs.

---

## Contents

- [What you need](#what-you-need)
- [Wiring and key layout](#wiring-and-key-layout)
- [Flash the Arduino](#flash-the-arduino)
- [Install and run the PC script](#install-and-run-the-pc-script)
- [Configuration (`config.py`)](#configuration-configpy)
- [Command types reference](#command-types-reference)
- [Add a new key binding](#add-a-new-key-binding)
- [Add a new command type (template)](#add-a-new-command-type-template)
- [Config helpers: reusable templates in `config.py`](#config-helpers-reusable-templates-in-configpy)
- [Combo commands](#combo-commands)
- [Platform notes](#platform-notes)
- [Choosing the serial port](#choosing-the-serial-port)
- [Troubleshooting](#troubleshooting)
- [Project layout](#project-layout)

---

## What you need

**Hardware**

- An Arduino-compatible board with USB serial. The sketch uses digital pins 4–11, which exist on Uno/Nano-style boards.
- A 4×4 matrix keypad (16 keys, 8 wires).
- Jumper wires and a USB cable.

**Software**

- Arduino IDE (or any tool that can flash a `.ino`) with the **Keypad** library by Mark Stanley and Alexander Brevig
  (Arduino IDE → *Tools → Manage Libraries… → search "Keypad"*).
- **Python 3.10 or newer** (`main.py` uses `match`/`case`).
- Python packages: `pyserial`, `keyboard`, `pyperclip`.

---

## Wiring and key layout

The sketch scans the matrix with these pins:

| Keypad side | Arduino pins (in this order)       | In the sketch                 |
|-------------|------------------------------------|-------------------------------|
| Rows 1–4    | `7`, `6`, `5`, `4`                 | `byte rowPins[ROWS] = {7, 6, 5, 4};`  |
| Columns 1–4 | `11`, `10`, `9`, `8`               | `byte colPins[COLS] = {11, 10, 9, 8};` |

Connect the four row wires to pins 7, 6, 5, 4 and the four column wires to pins 11, 10, 9, 8.
If the wrong keys show up when you press a button, check the wire order (or swap the arrays in the sketch).

The key matrix defined in the sketch:

```
        col1 col2 col3 col4
row1      1    2    3    A
row2      4    5    6    B
row3      7    8    9    C
row4      *    0    #    D
```

The comment at the top of `config.py` shows how the keys are **physically arranged on the author's pad**
(the keypad is mounted rotated relative to the matrix above):

```
# D C B A
# # 9 6 3
# 0 8 5 2
# * 7 4 1
```

The software only cares about the **character** that is sent, not the position. If you mount your pad differently,
just edit that comment so it matches what you see.

---

## Flash the Arduino

1. Put `poopdeckskecth.ino` in a folder with the same name (the Arduino IDE requires `poopdeckskecth/poopdeckskecth.ino`).
   If you fix the spelling ("sketch"), rename **both** the folder and the file.
2. Install the **Keypad** library (see above).
3. Select your board and port, then upload.
4. Test it without the PC script: open *Tools → Serial Monitor*, set **9600 baud**, press keys.
   You should see one character per press (`A`, `5`, `#`, …).

What the sketch does:

```cpp
#include <Keypad.h>
// ... matrix + pins ...
void setup() { Serial.begin(9600); }
void loop() {
  char customKey = customKeypad.getKey();
  if (customKey) {
    Serial.println(customKey);   // e.g. "A\r\n"
  }
}
```

---

## Install and run the PC script

```bash
pip install pyserial keyboard pyperclip
python main.py
```

(Optional `requirements.txt`: `pyserial`, `keyboard`, `pyperclip`.)

What `main.py` does on start:

1. Lists serial ports and uses the **last** one found (see [Choosing the serial port](#choosing-the-serial-port)).
2. Opens it with `BAUD_RATE` from `config.py` (default `9600`).
3. Waits 2 seconds (an Arduino usually resets when the port is opened).
4. Loops forever: read a line → strip whitespace → if it is a key in `KEYS`, run its command.

Close the Arduino IDE's Serial Monitor before running `main.py` — only one program can own the port.

---

## Configuration (`config.py`)

`config.py` is plain Python. It has two parts: the `KEYS` dictionary and a few settings.

### `KEYS`

```python
KEYS = {
    'KEY': ["command_type", argument],
}
```

- **KEY** — the character sent by the Arduino: `1`–`9`, `0`, `*`, `#`, `A`, `B`, `C`, `D`.
  (`,` in the example config is not a physical key; it is a spare entry that other bindings can call through `commands`.)
- **command_type** — one of the [types below](#command-types-reference). An empty string `""` means "do nothing".
- **argument** — depends on the type: a string, or a list of strings.

Unused keys are listed as `'9': ["", ""],` so they are easy to find later.

### Settings

| Name           | Default | Meaning |
|----------------|---------|---------|
| `BAUD_RATE`    | `9600`  | Must match `Serial.begin(...)` in the sketch. |
| `IS_MAC`       | `True`  | Chooses the paste shortcut for `keyboard_paste` (`command+v` on macOS, `ctrl+v` otherwise). Set to `False` on Windows/Linux. |
| `CURRENT_PORT` | `None`  | Placeholder that `main.py` overwrites when it finds a port (see [below](#choosing-the-serial-port)). |

---

## Command types reference

All types are handled in `run_command()` in `main.py`.

| Type | Argument | What it does | Example |
|------|----------|--------------|---------|
| `commands` | list of **key names** from `KEYS` | Runs the bindings of those keys, in order. | `'D': ["commands", ['#', ',']]` |
| `open_link` | URL string | Opens the URL in the default browser (`webbrowser.open`). | `'1': ["open_link", "https://example.com"]` |
| `keyboard_paste` | text | Copies the text to the clipboard and presses paste (Cmd+V / Ctrl+V). Good for long or non-Latin text. **Overwrites your clipboard.** | `'2': ["keyboard_paste", "Hello, world"]` |
| `keyboard_write` | text | Types the text character by character (`keyboard.write`). Depends on the keyboard layout. | `'#': ["keyboard_write", "hello"]` |
| `keyboard_hotkey` | list of key names | Presses all keys together, then releases them. | `'C': ["keyboard_hotkey", ['command', 'tab']]` |
| `keyboard_line` | list of keys | Sends the keys **one after another** (`keyboard.send`). Items can be characters or key names like `'enter'`; a hotkey string such as `'ctrl+c'` also works. | `'A': ["keyboard_line", ['h', 'i', 'enter']]` |
| `python` | Python **expression** string | Runs `eval()` in `main.py`'s namespace (so `os`, `time`, `subprocess`, `webbrowser`, `keyboard`, `pyperclip` are available). Expressions only — no `import`, no statements. | `'B': ["python", "print('1')"]` |
| `system` | command (list is safest) | `subprocess.Popen(...)`. Pass a **list** such as `["open", "-a", "Safari"]`; on POSIX a single string is treated as one program name, not a shell command line. | `'4': ["system", ["open", "-a", "Safari"]]` |
| `program` | path of an executable | Starts the program detached from the script (new process group on Windows, new session on macOS/Linux, output discarded). | `'5': ["program", "/path/to/app"]` |
| `""` | anything | Does nothing. | `'9': ["", ""]` |

Notes:

- `keyboard_hotkey` takes key **names** understood by the `keyboard` library (`'ctrl'`, `'shift'`, `'alt'`, `'command'`, `'tab'`, `'t'`, …).
  The shortcut for "switch window" is `['command', 'tab']` on macOS and `['alt', 'tab']` on Windows/Linux.
- `keyboard_line` is the right tool for a **sequence** (for example: open a chat, type a command, press Enter).
  `keyboard_write` is the right tool for plain text.
- `commands` can call any other binding, including other `commands`. Do not make loops (`A → B → A`).

---

## Add a new key binding

1. Pick the key (the character the Arduino sends), for example `9`.
2. Open `config.py` and replace the empty entry:

   ```python
   '9': ["", ""],
   ```

   with a real one:

   ```python
   '9': ["open_link", "https://example.com"],
   ```

3. Save and restart `python main.py` (the config is read once at startup).
4. Press the key.

More examples:

```python
'1': ["keyboard_hotkey", ['ctrl', 'shift', 't']],          # reopen closed tab (Windows/Linux)
'2': ["keyboard_paste",  "my.email@example.com"],          # paste a long string
'3': ["keyboard_line",   ['t', '/', 'h', 'e', 'l', 'p', 'enter']],  # sequence of keys
'4': ["system",          ["open", "-a", "Calculator"]],    # macOS: open an app
'5': ["python",          "webbrowser.open('https://example.com')"],
```

---

## Add a new command type (template)

A *command type* is one `case` in `run_command()` (`main.py`). Adding one takes three steps.

### Step 1 — add a `case`

```python
# main.py  (add any imports at the top of the file)
import urllib.request

def run_command(line: str) -> None:
    match KEYS[line][0]:
        # ... existing cases ...

        case "http_get":                      # <- your new type
            urllib.request.urlopen(KEYS[line][1], timeout=5)
```

Inside a `case`, `KEYS[line][1]` is the argument from `config.py`. It can be any Python value: a string, a list, a number, a dict.

### Step 2 — use it in `config.py`

```python
'5': ["http_get", "http://192.168.1.50/toggle"],    # e.g. toggle a smart light with a local URL
```

### Step 3 — restart and test

Restart `main.py` and press the key.

### Example with several arguments

Use a list (or a dict) when the type needs more than one value:

```python
# main.py
case "write_slow":
    text, delay = KEYS[line][1]
    keyboard.write(text, delay=delay)      # delay in seconds between characters

# config.py
'6': ["write_slow", ["typing demo", 0.05]],
```

### Good habits for new types

- **Keep it short.** If a case grows, move the logic into a function above `run_command()` and call it from the case.
- **Catch errors.** `main.py` has no `try/except` around `run_command()`: an unhandled exception ends the script.
  Either guard your own code or wrap the call in the main loop (see [ideas](#known-limitations-and-ideas)).
- **Don't block for long.** The main loop is single-threaded; while a command runs, later key presses wait in the serial buffer.
  For long jobs start a subprocess (`subprocess.Popen`) or a thread.
- **Document it.** Add a row to the [command types table](#command-types-reference).

---

## Config helpers: reusable templates in `config.py`

Because `config.py` is Python, you can write small functions to avoid repeating yourself:

```python
def link(url):          return ["open_link", url]
def hotkey(*keys):      return ["keyboard_hotkey", list(keys)]
def typed(text):        return ["keyboard_write", text]
def keys(*seq):         return ["keyboard_line", list(seq)]
def combo(*names):      return ["commands", list(names)]

KEYS = {
    '1': link("https://example.com"),
    '2': hotkey('ctrl', 'shift', 't'),
    '3': typed("hello"),
    '4': keys('h', 'i', 'enter'),
    ',': typed("hiiiii"),
    '#': typed("hello"),
    'D': combo('#', ','),
}
```

Define the helpers **above** `KEYS`. The result is exactly the same dictionary format that `main.py` expects.

---

## Combo commands

`commands` runs several existing bindings from a single key:

```python
KEYS = {
    '#': ["keyboard_write", "hello"],
    ',': ["keyboard_write", "hiiiii"],
    'D': ["commands", ['#', ',']],      # D -> runs '#' then ','  => types "hellohiiiii"
}
```

The argument is a list of **key names** (the dictionary keys), not of command types.
That is also why `,` exists in the example config: it is a spare slot that combos can use even though the pad has no `,` key.

---

## Platform notes

- **macOS** (`IS_MAC = True` in the default config): the `keyboard` library typically needs to run as root
  (`sudo python main.py`) and the terminal app may need *Accessibility / Input Monitoring* permission
  (*System Settings → Privacy & Security*). Use `command` instead of `ctrl` in hotkeys.
- **Windows**: set `IS_MAC = False`. Works without admin rights in most cases. Use `alt+tab`, `ctrl+...`.
  Serial ports look like `COM3`.
- **Linux**: set `IS_MAC = False`. The `keyboard` library needs root. Serial ports look like `/dev/ttyUSB0` or `/dev/ttyACM0`;
  you may need to add your user to the `dialout` group.

---

## Choosing the serial port

By default `main.py` does this:

```python
ports = serial.tools.list_ports.comports()
for _ in ports: CURRENT_PORT = _.device      # the LAST port in the list wins
ser = serial.Serial(CURRENT_PORT, BAUD_RATE, timeout=1)
```

So with several serial devices connected, you may get the wrong one, and if none are found `CURRENT_PORT` stays `None`
(the script then fails with a "port is not open" error).

To list the ports:

```bash
python -m serial.tools.list_ports
```

To pin a specific port, replace the two lines above with:

```python
CURRENT_PORT = "/dev/cu.usbmodem1101"   # or "COM3" on Windows
ser = serial.Serial(CURRENT_PORT, BAUD_RATE, timeout=1)
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Script crashes at start, "port is not open" / `None` port | No serial device found | Plug in the Arduino, check the cable (data cable, not charge-only), run `python -m serial.tools.list_ports`. |
| `could not open port` / `Resource busy` | Another program (Arduino Serial Monitor) holds the port | Close it. |
| Wrong device opened | Several ports, last one is used | [Pin the port](#choosing-the-serial-port). |
| Nothing happens on key press | Key has an empty binding or no entry in `KEYS` | Check `config.py` (`["", ""]` does nothing). Test the pad in the Arduino Serial Monitor first. |
| Wrong keys appear | Row/column wires swapped | Compare with the pin table and the matrix in the sketch. |
| Garbage characters | Baud rate mismatch | `Serial.begin(9600)` and `BAUD_RATE = 9600` must match. |
| Hotkeys / typing do nothing (macOS/Linux) | `keyboard` lacks permissions | Run with `sudo`; on macOS grant Accessibility / Input Monitoring. |
| Paste shortcut is wrong | `IS_MAC` mismatch | Set `IS_MAC` correctly for your OS. |
| `SyntaxError` near `match` | Python older than 3.10 | Upgrade Python. |
| Text typed in the wrong layout / missing characters | `keyboard.write` depends on the active layout | Use `keyboard_paste` instead. |
| Script stops after a key press, traceback in the terminal | Exception inside a command (bad argument, missing import) | Fix the config entry or the `case`; consider wrapping calls in `try/except`. |
| After editing `config.py` nothing changed | Config is read at startup | Restart `main.py`. |


---

## Project layout

```
poopdeck/
├── poopdeckskecth/
│   └── poopdeckskecth.ino    # Arduino sketch: scans the keypad, prints the key
├── main.py                   # PC script: reads serial, runs commands
├── config.py                 # KEYS bindings + settings
└── README.md                 # this file
```
