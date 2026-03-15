pyinstaller --onefile --name PDFUtility_ALPHA_Build-1-0-0_7042025 
  --add-data "readme.md;." 
  --add-data ".env;." 
  --add-data "editor/renderers/html_renderer/settings.json;editor/renderers/html_renderer" 
  --add-data "editor/renderers/markdown_renderer/settings.json;editor/renderers/markdown_renderer" 
  --add-data "editor/renderers/pdf_renderer/settings.json;editor/renderers/pdf_renderer" 
  pdfSplitter.py