# Tutorial System - JSON Format Documentation

This directory contains JSON files that define interactive tutorials for the PDF Utility application.

## File Structure

Each tutorial should be a separate JSON file with the following structure:

```json
{
    "name": "tutorial_identifier",
    "title": "Human Readable Title",
    "description": "Brief description of what this tutorial covers",
    "steps": [
        {
            "target": "widget_name_or_id",
            "text": "<b>Step Title</b><br><br>Step description with HTML formatting",
            "button_text": "Next",
            "highlight_style": "pulse",
            "arrow_direction": "auto"
        }
    ]
}
```

## Field Descriptions

### Root Level Fields
- **name** (required): Unique identifier for the tutorial, used internally
- **title** (optional): Human-readable title for the tutorial
- **description** (optional): Brief description of the tutorial purpose
- **steps** (required): Array of tutorial steps

### Step Fields
- **target** (required): Name or ID of the UI widget to highlight
- **text** (required): HTML-formatted text to display in the tutorial box
- **button_text** (optional): Text for the "Next" button (default: "Next")
- **highlight_style** (optional): Visual style for highlighting the target widget
- **arrow_direction** (optional): Direction for the pointing arrow

## Highlight Styles

Available highlight styles:
- `dashed_border`: Dashed border around the target (default)
- `solid_border`: Solid border with semi-transparent fill
- `glow`: Glowing effect with multiple rings
- `pulse`: Pulsing border that changes intensity

## Arrow Directions

Available arrow directions:
- `auto`: Automatically determine best direction (default)
- `left`: Point to the left
- `right`: Point to the right
- `top`: Point upward
- `bottom`: Point downward
- `none`: No arrow

## HTML Formatting

The `text` field supports HTML formatting:
- `<b>Bold text</b>`
- `<em>Italic text</em>`
- `<br>` for line breaks
- `<br><br>` for paragraph spacing
- Basic color and styling tags

## Example Tutorial

See any of the existing `.json` files in this directory for complete examples.

## Adding New Tutorials

1. Create a new `.json` file in this directory
2. Follow the structure above
3. The tutorial will be automatically loaded when the application starts
4. Use `reload_tutorials()` method for development/testing

## Widget Target Names

Common widget targets include:
- Main application: `menuBar`, `statusBar`, `tabs`
- PDF operations: `add_pdf_btn`, `pdf_list`, `split_btn`, `merge_btn`
- File operations: `add_files_btn`, `scan_dir_btn`, `browse_button`
- Settings: `general_tab`, `performance_tab`, `apply_button`

Check the source code of each widget to find the exact object names.
