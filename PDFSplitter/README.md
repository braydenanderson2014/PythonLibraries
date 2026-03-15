# PDF Utility – User Guide

*Last updated: 2025-06-08*

---

## ✨ Overview

Everything you need in one desktop window — with live progress bars and an ever-present **Cancel** button.

| Main Capabilities                                                                                                          | At a Glance |
| -------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **Split** PDFs page-by-page, every *N* pages, or custom ranges                                                             | ✅           |
| **Merge** many PDFs quickly & safely                                                                                       | ✅           |
| **Render / Mark-Up** in tabs (pen, line, rectangle, highlight, editable text boxes, eraser, colour & font controls, print) | ✅           |
| **Search** by file-name *or* page text (loaded list / any folder)                                                          | ✅           |
| Image → PDF conversion                                                                                                     | ✅           |
| Folder scan, rename, duplicate, delete                                                                                     | ✅           |
| Repair damaged PDFs                                                                                                        | ✅           |
| Remove blank pages                                                                                                         | ✅           |
| **Text-to-Speech playback** with full transport controls                                                                   | ✅           |

---

## 🚀 Feature Walk-Through

### 1. Adding Files

`➕ Add Files` → pick PDFs → done.

### 2. Removing from the List

Select rows → `🗑 Remove Selected` (files stay on disk).

### 3. Scanning a Folder

`📂 Scan Folder` → choose a folder → every PDF inside (recursively) is listed.

### 4. Searching PDFs

`🔍 Search` → enter term → pick **Loaded files** or **Directory** → optionally tick **Content** and **Only selected** → **Search**.
Double-click a result to open the PDF (jumps to first hit on a content search).

### 5. Splitting PDFs

1. Select one + PDF(s).
2. `✂️ Split PDF` → choose **Page-by-page / Every *N* pages / Ranges**.
3. Dual progress dialog appears — cancel any time.

### 6. Merging PDFs

Select **≥ 2** PDFs → `🡒 Merge PDFs` → name the file → watch the workers fly.

### 7. Repairing PDFs

Select a damaged PDF → `🛠 Repair` → fixed copy appears next to the original.

### 8. Removing Blank Pages

Select a PDF → `🧹 Remove White Pages`.

### 9. Rendering & Editing PDFs

| Action               | Notes                                                                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Open**             | `👁 View` (read-only) or `✏️ Edit` (editing unlocked). Renderer’s **File** menu also offers **Open PDF…** and **Open from Program…**. |
| **Tabs**             | Up to 4 visible; **◀ ▶** cycle; extra tabs drop into a combobox. Tab shows **×** to close + “\*” if unsaved.                          |
| **Scroll**           | All pages stack vertically; wheel or drag. Status bar reads “Page *n* / *total*”.                                                     |
| **Tools**            | Pen, Line, Rectangle, Highlight, Text Box, **E-Seg** (segment eraser). Choose **Color** + font size before drawing/typing.            |
| **Read-Only ⇄ Edit** | Toggle **Enable Edit / Lock** per tab.                                                                                                |
| **Save**             | **Save** (incremental when allowed) or **Save As** (always succeeds).                                                                 |
| **Print**            | Uses OS print dialog on Windows, `lpr` on Unix-likes.                                                                                 |
| **Close**            | Click **×** → prompts to **Save / Don’t Save / Cancel** if dirty.                                                                     |

> **Tip:** Text boxes stay editable until you save; other marks bake in immediately.

### 10. Playback Control (Text-to-Speech)

Select a PDF → `🔈 Read` opens the **Playback Control** dialog:

| Control    | Shortcut | Description                       |
| ---------- | -------- | --------------------------------- |
| `▶ Play`   | —        | Start reading from the first page |
| `⏸ Pause`  | —        | Pause instantly                   |
| `⏵ Resume` | —        | Continue from pause               |
| `⏹ Stop`   | —        | Stop & reset progress             |
| `⏭ Skip`   | —        | Next page                         |
| `⏮ Rewind` | —        | Previous page                     |

A progress bar shows real-time reading progress; the dialog closes playback automatically when you exit.

### 11. Viewing • Renaming • Duplicating • Deleting

| Button               | Does                         |
| -------------------- | ---------------------------- |
| **👁 View PDF**      | Opens renderer (read-only)   |
| **✏️ Rename PDF**    | Prompts for new file name    |
| **📄 Duplicate PDF** | Makes a copy                 |
| **🗑 Delete PDF**    | Permanently removes the file |

### 12. Converting Images

`🖼 Convert Images` → pick PNG/JPG/BMP → each saves as a PDF to the *Converted* directory.

### 13. Selecting Files & Shortcuts

| Action            | Effect                   |
| ----------------- | ------------------------ |
| Click             | select that row          |
| **Ctrl + Click**  | toggle that row          |
| **Shift + Click** | select range             |
| **Ctrl + A**      | (after 1 row) select all |

Status bar shows **N file(s) selected**.

### 14. Toolbar Button States

| Button group                                                | Enabled when…  |
| ----------------------------------------------------------- | -------------- |
| **Split**                                                   | ≥ 1 selected   |
| **Merge**                                                   | ≥ 2 selected   |
| **View / Edit**                                             | ≥ 1            |
| **Rename**                                                  | exactly 1      |
| **Delete / Duplicate / Repair / Remove white / Read aloud** | ≥ 1            |
| **Remove Selected / Clear / Convert PDF→Image**             | ≥ 1            |
| **Sort**                                                    | list has > 1   |
| **Select All**                                              | list not empty |

---

## ⚙ Settings Controller

All preferences live in a single `settings.ini` file:

| Setting                                          | What it does                             | Default                      |
| ------------------------------------------------ | ---------------------------------------- | ---------------------------- |
| **Theme**                                        | `Light` or `Dark` (applied instantly)    | Light                        |
| **output / split / merge / convert directories** | Default save locations                   | user Documents \PDFUtility\… |
| **temporary\_file\_location**                    | Where large merges/splits create chunks  | OS temp dir                  |
| **log\_dir**                                     | Folder for per-run log files             | `…\PDFUtility\Logs`          |
| **auto\_convert\_dir**                           | Watched folder for auto-conversions      | `…\PDFUtility\AutoConvert`   |
| **text\_to\_speech\_rate**                       | Words-per-minute for playback            | 150                          |
| **text\_to\_speech\_volume**                     | 0 – 1 volume scalar                      | 1                            |
| **cleanup\_run\_count**                          | Auto-purge logs after this many launches | 3                            |

### Where the file lives

* **Bundled EXE** (PyInstaller) →
  `%USERPROFILE%\Documents\PDFUtility\settings.ini`
* **Source run** → sits next to the script.

`Settings ▸ Restore Defaults` rewrites the file with factory values, and every change is persisted the moment you click **Save**.

---

## 🛠 Under the Hood

* Chunked, parallel merge/split (≤ 4 workers) with disk & RAM guards
* Dual progress dialog (overall + current worker)
* Immediate list refresh on any new PDF (split/merged/edited/converted)
* Background-thread search & TTS so the UI never blocks
* Smart toolbar refreshes after every click/shortcut

---

## ✅ Capabilities & ❌ Limits

| ✅ Can do                                                                                                                                               | ❌ Cannot do                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| Split, merge, annotate (pen/line/rect/highlight/text), repair, convert images, search names & content, folder scan, blank-page removal, text-to-speech | Edit embedded PDF text/images, password-protect, OCR |

---

## 🩺 Troubleshooting

| Issue                     | Remedy                                                 |
| ------------------------- | ------------------------------------------------------ |
| “No results found”        | Check spelling or enable **Content** search.           |
| Slow operation            | Large PDFs need time; watch the live progress bars.    |
| Unsaved edits lost        | Tabs always prompt; you likely clicked **Don’t Save**. |
| Deleted file accidentally | Deletion is permanent — restore from backup.           |

Logs are written to the *Log folder* (see Settings). Support may ask for them.

---

## 🆘 Support & Updates

**Author:** Brayden Anderson
GitHub: [https://github.com/braydenanderson2014](https://github.com/braydenanderson2014)

Grab the latest build for new features & fixes — happy PDF-wrangling! 🚀

---

## 🧪 Experimental PDF Editor (Inline Editing)

Leverage our new in-editor PDF editing features directly within PDF Utility:

* **Multi-Page Stacked View**: Renders every page in a single scrollable canvas, stacked vertically with adjustable zoom and centering.
* **Inline Text Editing**: Toggle Read-Only ⇄ Edit mode to overlay editable text widgets matching original fonts, sizes & colors.
* **Annotation Tools**: Pen, Line, Rectangle, Highlight, Text Box, and E-Seg (segment eraser), plus a plugin API under `editor/tools/`.
* **Tab System**: Up to 4 tabs visible (overflow via dropdown), “×” to close with Save prompt, and unsaved “∗” indicator.
* **Directory Scanner & Batch Import**: `Scan Directory…` finds PDFs recursively and pops up a multi-select list; `Add PDFs from Main` uses host-fed lists.
* **Copy & Open Paths**: File menu offers **Copy File Path** (to clipboard) and **Open Containing Folder** for the active tab’s PDF.
* **Public API**: `FileAPI.open_document()`, `FileAPI.save_document()`, `FileAPI.get_document_bytes()` let external code drive the editor.
* **Modular Architecture**: Built on Tkinter + PyMuPDF + PIL with clean separation: `DocumentModel`, `PDFRenderer`, `TextOverlay`, `TabManager`, `EditorWindow`, and `FileAPI`.

Enjoy experimenting with live PDF editing right in PDF Utility! 🚀
