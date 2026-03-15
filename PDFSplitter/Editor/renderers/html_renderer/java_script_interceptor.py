# editor/renderers/html_renderer/java_script_interceptor.py

from bs4 import BeautifulSoup, Comment

class JavaScriptInterceptor:
    """
    Strips out <script> tags to avoid raw JS showing up
    and to prevent execution in a static preview.
    """

    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "html.parser")

    def strip_scripts(self) -> str:
        """Strip all script tags and their content."""
        for script in self.soup.find_all("script"):
            script.decompose()
        
        # Also remove inline event handlers
        for tag in self.soup.find_all():
            # Remove common event attributes
            event_attrs = [attr for attr in tag.attrs.keys() 
                          if attr.lower().startswith('on')]
            for attr in event_attrs:
                del tag[attr]
                
        return str(self.soup)

    def safe_scripts(self) -> str:
        """
        Replace potentially harmful scripts with safe alternatives
        or comments for preview purposes.
        """
        for script in self.soup.find_all("script"):
            src = script.get("src", "")
            if src:
                # Replace external scripts with comments
                comment = self.soup.new_string(f"<!-- External script: {src} -->", 
                                              Comment)
                script.replace_with(comment)
            else:
                # Replace inline scripts with comments showing their content
                script_content = script.get_text()
                if script_content.strip():
                    comment = self.soup.new_string(
                        f"<!-- Inline script (disabled for preview):\n{script_content[:200]}{'...' if len(script_content) > 200 else ''}\n-->", 
                        Comment)
                    script.replace_with(comment)
                else:
                    script.decompose()
        
        # Remove inline event handlers but preserve them as data attributes
        for tag in self.soup.find_all():
            event_attrs = [(attr, tag[attr]) for attr in tag.attrs.keys() 
                          if attr.lower().startswith('on')]
            for attr, value in event_attrs:
                tag[f'data-original-{attr}'] = value
                del tag[attr]
                
        return str(self.soup)

    def inline_scripts(self) -> str:
        """
        Inlines any <script> tags by moving their content into a single
        <script> tag at the end of the document.
        """
        script_content = ""
        for script in self.soup.find_all("script"):
            if script.string:
                script_content += script.string
            script.decompose()

        if script_content:
            new_script = self.soup.new_tag("script")
            new_script.string = script_content
            self.soup.body.append(new_script)

        return str(self.soup)