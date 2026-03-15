# editor/renderers/html_renderer/css_interceptor.py

import os
from bs4 import BeautifulSoup

class CSSInterceptor:
    """
    Extracts <style> and <link rel="stylesheet"> tags,
    inlines any local .css files, then reinserts a single <style> block.
    """

    def __init__(self, html: str, base_path: str = None):
        self.base_path = base_path
        self.soup = BeautifulSoup(html, "html.parser")

    def inline_css(self) -> str:
        # 1) Gather all embedded <style> content
        css_text = ""
        for style_tag in self.soup.find_all("style"):
            if style_tag.string:
                css_text += style_tag.string + "\n"
            elif style_tag.get_text():
                css_text += style_tag.get_text() + "\n"
            style_tag.decompose()

        # 2) Gather <link rel="stylesheet" href="...">
        for link in self.soup.find_all("link"):
            rel = link.get("rel", [])
            if isinstance(rel, str):
                rel = [rel]
            if "stylesheet" in rel:
                href = link.get("href", "")
                if self.base_path and href and not href.startswith(('http://', 'https://', '//')):
                    # Handle relative paths
                    if href.startswith('/'):
                        css_file = os.path.join(self.base_path, href.lstrip('/'))
                    else:
                        css_file = os.path.join(self.base_path, href)
                    try:
                        with open(css_file, "r", encoding="utf-8", errors="replace") as f:
                            css_content = f.read()
                            css_text += f"/* {href} */\n{css_content}\n"
                    except IOError:
                        # Keep external links as is
                        continue
                elif href.startswith(('http://', 'https://', '//')):
                    # Keep external stylesheets as links
                    continue
                link.decompose()

        # 3) Reinsert combined <style> into <head>
        if css_text.strip():
            head = self.soup.head
            if not head:
                head = self.soup.new_tag("head")
                if self.soup.html:
                    self.soup.html.insert(0, head)
                else:
                    self.soup.insert(0, head)
                    
            style = self.soup.new_tag("style", type="text/css")
            style.string = css_text.strip()
            head.append(style)

        return str(self.soup)
