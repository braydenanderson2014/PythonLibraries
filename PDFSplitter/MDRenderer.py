# md_viewer.py  – colour-aware & bullet-proof table support
from __future__ import annotations
import re, importlib, tkinter as tk
from html.parser import HTMLParser
from textwrap import shorten
from typing import List


# ───────────────────── ensure python-markdown exists ──────────────────────
def _require_markdown():
    try:
        return importlib.import_module("markdown")
    except ModuleNotFoundError:
        import tkinter.messagebox as mb
        mb.showerror(
            "Missing dependency",
            "python-markdown is not installed.\n\n"
            "Run:\n    pip install markdown"
        )
        raise

md = _require_markdown()


# ───────────────────────── HTML→Tk parser class ───────────────────────────
class _HTML2Tk(HTMLParser):
    """Turn a subset of HTML into tagged ranges inside a Tk.Text."""

    def __init__(self, text: tk.Text, max_cell: int = 60):
        super().__init__()
        self.t = text
        self.max_cell = max_cell

        # inline flags
        self.bold = self.italic = self.code = False
        self.link: str | None = None
        self.color: str | None = None

        # table state
        self.table: List[List[str]] = []
        self.row:   List[str] | None = None
        self.cell:  List[str] | None = None

    # ── helpers ───────────────────────────────────────────────────────────
    def _apply_style(self, start: str, end: str):
        if self.bold:   self.t.tag_add("bold",   start, end)
        if self.italic: self.t.tag_add("italic", start, end)
        if self.code:   self.t.tag_add("code",   start, end)
        if self.color:
            tag = f"clr_{self.color.lstrip('#')}"
            if not self.t.tag_names().__contains__(tag):
                self.t.tag_config(tag, foreground=self.color)
            self.t.tag_add(tag, start, end)
        if self.link:
            self.t.tag_add("link", start, end)
            self.t.tag_bind("link", "<Button-1>",
                            lambda e, url=self.link: __import__("webbrowser").open(url))

    def _text(self, data: str):
        if self.cell is not None:          # inside a <td>/<th>
            self.cell.append(data)
            return
        if not data:
            return
        start = self.t.index("end")
        self.t.insert("end", data)
        self._apply_style(start, "end")

    # table → monospace grid
    def _render_table(self):
        if not self.table:
            return
        cols = max(len(r) for r in self.table)
        widths = [0] * cols
        for r in self.table:
            for c, cell in enumerate(r):
                widths[c] = max(widths[c], len(cell))

        mono_start = self.t.index("end")
        for ridx, row in enumerate(self.table):
            line = "| " + " | ".join(
                f"{row[c]:<{widths[c]}}" for c in range(cols)
            ) + " |\n"
            self.t.insert("end", line)
            if ridx == 0:
                self.t.insert(
                    "end",
                    "|" + "|".join("-" * (w + 2) for w in widths) + "|\n"
                )
        mono_end = self.t.index("end")
        self.t.tag_add("mono", mono_start, mono_end)
        self.table.clear()

    # ── HTMLParser overrides ──────────────────────────────────────────────
    def handle_starttag(self, tag, attrs):
        if tag in ("strong", "b"): self.bold = True
        elif tag in ("em", "i"):   self.italic = True
        elif tag == "code":        self.code = True
        elif tag == "a":           self.link = dict(attrs).get("href")
        elif tag == "span":
            style = dict(attrs).get("style", "")
            m = re.search(r"color\s*:\s*([^;]+)", style)
            if m: self.color = m.group(1).strip()
        elif tag == "table":       self.table = []
        elif tag == "tr":          self.row   = []
        elif tag in ("td", "th"):  self.cell  = []

    def handle_endtag(self, tag):
        if tag in ("strong", "b"): self.bold = False
        elif tag in ("em", "i"):   self.italic = False
        elif tag == "code":        self.code = False
        elif tag == "a":           self.link = None
        elif tag == "span":        self.color = None
        elif tag in ("td", "th"):
            txt = shorten("".join(self.cell).strip(),
                          self.max_cell,
                          placeholder="…")
            self.row.append(txt)
            self.cell = None
        elif tag == "tr":
            self.table.append(self.row)
            self.row = None
        elif tag == "table":
            self._render_table()
            self._text("\n")

    def handle_data(self, data):          self._text(data)
    def handle_startendtag(self, tag, attrs):
        if tag == "br": self._text("\n")

    def close(self):
        super().close()
        self._render_table()   # safety flush


# ─────────────────────── markdown → widget entry point ────────────────────
_TABLE_LINE_RE = re.compile(r"\s*\|.*\|\s*$")

def _inject_ascii_tables(md_src: str) -> str:
    """Detect pipe tables that might confuse python-markdown and
       wrap them in raw `<table>` markup so we always get a table."""
    out, buf = [], []
    def flush():
        if not buf:
            return
        out.append("<table>")
        for row in buf:
            cells = [c.strip() or " " for c in row.strip("|").split("|")]
            out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        out.append("</table>")
        buf.clear()

    for line in md_src.splitlines():
        if _TABLE_LINE_RE.match(line):
            buf.append(line)
        else:
            flush()
            out.append(line)
    flush()
    return "\n".join(out)


def render_markdown_to_text(md_text: str, widget: tk.Text):
    """
    Render *md_text* inside *widget* with support for:
      • headings, bold/italic, code, lists  
      • links (clickable)  
      • colour spans (`<span style="color:#ff0">`)  
      • tables (genuine or pipe-style)  
    """
    # first, pre-wrap ASCII pipe tables (if any)
    md_text = _inject_ascii_tables(md_text)

    # markdown → HTML
    html = md.markdown(md_text,
                       extensions=["tables", "fenced_code",
                                   "sane_lists", "nl2br"])

    # feed into HTML→Tk parser
    p = _HTML2Tk(widget)
    p.feed(html)
    p.close()


"""
rich_help.py – embed a real HTML renderer into a Tk window.

If `tkinterweb` is available you get:
  • colour emoji   • CSS colour spans   • full tables   • link clicks
Else we fall back to the Text-based parser (needs md_viewer.py).
"""
import os, tempfile, pathlib, tkinter as tk
from tkinter import ttk, messagebox
import importlib, markdown, webbrowser, inspect, sys

import markdown        # you already depend on this
def _engine(frame):
    return getattr(frame, "browser",
           getattr(frame, "html_engine", "tkhtml"))


def _get_htmlframe():
    try:
        module = importlib.import_module("tkinterweb")
        return module.HtmlFrame
    except ModuleNotFoundError:
        return None


def _supported_kwargs(cls, **candidate):
    """Return only those kwargs that *cls*.__init__ really accepts."""
    sig = inspect.signature(cls.__init__)
    return {k: v for k, v in candidate.items() if k in sig.parameters}


def _install_link_hook(frame):
    """
    Make link clicks open in the system browser for every TkinterWeb variant.
    Newer versions offer .on_link_click; older have .web.bind("<<HTMLLink>>",…)
    """
    if hasattr(frame, "on_link_click"):
        frame.on_link_click(lambda url: webbrowser.open(url))
    else:
        # Tkhtml3 path
        def _cb(event):
            href = event.widget.href if hasattr(event.widget, "href") else None
            if href:
                webbrowser.open(href)
        try:
            frame.web.bind("<<HTMLLink>>", _cb, add="+")
        except Exception:
            pass


# ────────────────────────────────────────────────────────────────────────────
def show_readme(parent: tk.Misc, readme_path: str):
    with open(readme_path, encoding="utf-8") as fh:
        md_src = fh.read()

    win = tk.Toplevel(parent)
    win.title("Help Guide")
    win.geometry("900x650")

    HtmlFrame = _get_htmlframe()
    if HtmlFrame:
        # markdown → html
        html = markdown.markdown(
            md_src,
            extensions=["tables", "fenced_code", "sane_lists", "codehilite"],
        )

        # choose kwargs this HtmlFrame supports
        kw = _supported_kwargs(
            HtmlFrame,
            browser="edgechromium",          # fails silently if unsupported
            messages_enabled=False,
            horizontal_scrollbar=True,
        )
        try:
            frame = HtmlFrame(win, **kw)
        except tk.TclError as e:
            # e.g. unsupported browser= parameter
            messagebox.showwarning("HTML engine fallback", str(e))
            HtmlFrame = None   # trigger plain-text path
        else:
            frame.pack(fill=tk.BOTH, expand=True)
            # load html – different names in different releases
            for meth in ("load_html", "set_html", "add_html"):
                if hasattr(frame, meth):
                    getattr(frame, meth)(html)
                    break
            _install_link_hook(frame)
    # -----------------------------------------------------------------------
    if HtmlFrame is None:
        # Plain-text fallback using md_viewer
        outer = ttk.Frame(win, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        y = ttk.Scrollbar(outer, orient=tk.VERTICAL)
        x = ttk.Scrollbar(outer, orient=tk.HORIZONTAL)
        txt = tk.Text(
            outer,
            wrap=tk.NONE,
            yscrollcommand=y.set,
            xscrollcommand=x.set,
        )
        y.config(command=txt.yview); y.pack(side=tk.RIGHT, fill=tk.Y)
        x.config(command=txt.xview); x.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        txt.tag_config("bold",   font=("TkDefaultFont", 11, "bold"))
        txt.tag_config("italic", font=("TkDefaultFont", 11, "italic"))
        txt.tag_config("mono",   font=("Courier New",   10))
        txt.tag_config("code",   font=("Courier New",   10), background="#f6f8fa")
        txt.tag_config("link",   foreground="blue", underline=True)

        render_markdown_to_text(md_src, txt)
        txt.config(state=tk.DISABLED)

    ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)