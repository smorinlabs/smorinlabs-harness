---
description: Render a side-by-side preview of all themes in the catalog as an HTML page.
---

Render the preview template, write it to a temp HTML file, and print the path
so the user can open it in their browser.

## Behavior

1. Read `assets/preview-template.html` from this plugin's directory using
   `${CLAUDE_PLUGIN_ROOT}/assets/preview-template.html`.

2. Write a copy to a stable path. Use
   `/tmp/use-html-theme-preview.html` (overwriting any existing file).
   Confirm by writing through the Write tool.

3. Print the path to the user with a one-line `open <path>` suggestion:

   ```
   Preview written to /tmp/use-html-theme-preview.html
   Open with: open /tmp/use-html-theme-preview.html
   ```

4. Do NOT pick a theme automatically. The preview is informational; the user
   chooses via `/theme <name>` or the next HTML-request picker.

## Implementation

Read the template, then write it verbatim to the destination. No
substitutions, no parameter injection — the preview is a static asset.

```
Read ${CLAUDE_PLUGIN_ROOT}/assets/preview-template.html
Write /tmp/use-html-theme-preview.html <same contents>
```

Print the open suggestion.
