# How To Documentation

This directory contains markdown files that are automatically rendered as youth-friendly "How To" guides in the portal.

## Adding New Documentation

### File Naming Convention

Name your markdown files using this format:
```
[order]-[slug].md
```

Examples:
- `01-getting-started.md`
- `02-registering-for-programs.md`
- `15-advanced-features.md`

- **Order**: A number (01-99) that determines the display order
- **Slug**: A URL-friendly name (lowercase, hyphens instead of spaces)

### File Structure

Each markdown file should start with a level 1 heading (`#`) as the title:

```markdown
# Your Guide Title

Introduction paragraph...

## Section 1

Content here...

## Section 2

More content...
```

### Markdown Features Supported

The portal supports these markdown features:

- **Headings**: `#`, `##`, `###`, etc.
- **Bold**: `**bold text**`
- **Italic**: `*italic text*`
- **Lists**: Unordered (`-`) and ordered (`1.`)
- **Links**: `[text](url)`
- **Images**: `![alt text](image-url)`
- **Code**: Inline \`code\` and code blocks with \`\`\`
- **Blockquotes**: `> quote text`
- **Tables**: Markdown table syntax
- **Emojis**: 🎉 ✅ 📚 (paste directly)

### Writing Youth-Friendly Content

**Tips for creating accessible documentation:**

1. **Use simple language** - Avoid jargon and complex terms
2. **Break into steps** - Use numbered lists for processes
3. **Add visuals** - Use emojis and icons to make it engaging
4. **Use examples** - Show real scenarios
5. **Include tips** - Use blockquotes for helpful hints
6. **Keep it short** - Break long guides into multiple files

### Example Template

```markdown
# How to [Do Something]

Brief introduction explaining what this guide covers. 🎯

## Before You Start

List any prerequisites:
- ✅ Thing you need to have done
- ✅ Another requirement

## Step-by-Step Instructions

### Step 1: First Action

1. Click on **Something**
2. Do this thing
3. Then do that

> **Tip:** Helpful hint here!

### Step 2: Next Action

Continue with clear instructions...

## Troubleshooting

**Problem:** Common issue
**Solution:** How to fix it

---

**Previous Guide:** [Previous](previous-slug) | **Next Guide:** [Next](next-slug)
```

## Viewing Your Documentation

After adding or editing markdown files:

1. The changes are immediately available (no restart needed in development)
2. Navigate to `/portal/howto/` to see the index
3. Click on your guide to view it
4. The navigation sidebar automatically updates

## Best Practices

- **Test your markdown** - Preview it before committing
- **Check links** - Make sure internal links work
- **Use consistent formatting** - Follow the existing style
- **Keep it updated** - Review guides when features change
- **Get feedback** - Ask users if the guides are helpful

## Technical Details

- Files are read from: `inclusive_world_portal/portal/howto_docs/`
- Views are in: `inclusive_world_portal/portal/howto_views.py`
- Templates are in: `inclusive_world_portal/templates/portal/howto_*.html`
- URL pattern: `/portal/howto/` and `/portal/howto/<slug>/`
