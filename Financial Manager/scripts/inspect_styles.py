from PyQt6.QtWidgets import QApplication, QWidget
import sys, os

# Ensure project root is on sys.path so imports like 'ui.login' work when running from scripts/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.login import LoginDialog

app = QApplication.instance() or QApplication([])
print('APP stylesheet length:', len(app.styleSheet()))

dlg = LoginDialog()
print('Dialog stylesheet length:', len(dlg.styleSheet()))

children = dlg.findChildren(QWidget)
print('Child widgets:', len(children))
count = 0
for w in children:
    name = w.objectName() or '<no-name>'
    cls = type(w).__name__
    ss = w.styleSheet() or ''
    txt = ''
    try:
        if hasattr(w, 'text'):
            txt = w.text()
        elif hasattr(w, 'placeholderText'):
            txt = w.placeholderText()
        elif hasattr(w, 'title'):
            txt = w.title()
    except Exception:
        txt = ''
    print(f'{count:03d}: {cls:20s} name={name:20s} text={txt[:30]:30s} ss_len={len(ss):4d} ss_snip={ss[:80]!r}')
    count += 1

# Print a few specific widget styles if available
try:
    print('\nUSERNAME_EDIT stylesheet:\n', dlg.username_edit.styleSheet())
    print('\nPASSWORD_EDIT stylesheet:\n', dlg.password_edit.styleSheet())
    print('\nPW_CONTAINER stylesheet:\n', dlg.findChild(QWidget, '') and dlg.findChild(QWidget, '').styleSheet())
except Exception as e:
    print('Error printing specific widgets:', e)

# Quit the app
app.quit()
