# BST_visualizer_PyQt
binary search tree visualizer written in Python + PyQt5

![UI](bst_ui.png)

## Compilation

Use **Python 3.9+** to compile `bst_visualizer.py`, **PyQt5** required.

```bash
brew install python3.10
pip install pyqt5
```

```bash
python bst_visualizer.py
```

EXE files are made with `PyInstaller`:
```bash
pip install pyinstaller
pyinstaller -F bst_visualizer.py
```
