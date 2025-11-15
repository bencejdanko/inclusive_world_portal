"""
Views for rendering youth-friendly "How to" documentation from markdown files.
"""
import os
from pathlib import Path

import markdown
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.utils.safestring import mark_safe


# Directory where markdown documentation files are stored
HOWTO_DOCS_DIR = Path(__file__).parent / 'howto_docs'


def get_doc_list():
    """
    Get a list of available documentation files.
    Returns a list of dicts with 'slug', 'title', and 'order' keys.
    """
    if not HOWTO_DOCS_DIR.exists():
        return []
    
    docs = []
    for md_file in sorted(HOWTO_DOCS_DIR.glob('*.md')):
        # Extract metadata from filename (e.g., "01-getting-started.md")
        filename = md_file.stem
        parts = filename.split('-', 1)
        
        if len(parts) == 2 and parts[0].isdigit():
            order = int(parts[0])
            slug = parts[1]
        else:
            order = 999
            slug = filename
        
        # Read first line as title (if it's a heading)
        title = slug.replace('-', ' ').title()
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('# '):
                    title = first_line[2:].strip()
        except Exception:
            pass
        
        docs.append({
            'slug': slug,
            'title': title,
            'order': order,
            'filename': md_file.name,
        })
    
    # Sort by order
    docs.sort(key=lambda x: x['order'])
    return docs


def get_doc_content(slug):
    """
    Get the content of a documentation file by slug.
    Returns a dict with 'title', 'content_html', and 'raw_content'.
    """
    # Find the file that matches the slug
    for md_file in HOWTO_DOCS_DIR.glob('*.md'):
        filename = md_file.stem
        # Check if slug matches (with or without order prefix)
        if filename == slug or (filename.split('-', 1)[1] if '-' in filename else filename) == slug:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                
                # Convert markdown to HTML with extensions
                md = markdown.Markdown(extensions=[
                    'extra',  # Tables, fenced code blocks, etc.
                    'codehilite',  # Syntax highlighting
                    'toc',  # Table of contents
                    'nl2br',  # Newline to <br>
                ])
                content_html = md.convert(raw_content)
                
                # Extract title from first heading or use filename
                title = slug.replace('-', ' ').title()
                if raw_content.strip().startswith('# '):
                    title = raw_content.split('\n')[0][2:].strip()
                
                return {
                    'title': title,
                    'content_html': mark_safe(content_html),
                    'raw_content': raw_content,
                    'toc': md.toc if hasattr(md, 'toc') else '',
                }
            except Exception as e:
                raise Http404(f"Error reading documentation: {e}")
    
    raise Http404("Documentation not found")


@login_required
def howto_index(request):
    """
    Display the index page with a list of all available documentation.
    """
    docs = get_doc_list()
    
    context = {
        'docs': docs,
        'page_title': 'How To Guides',
    }
    return render(request, 'portal/howto_index.html', context)


@login_required
def howto_detail(request, slug):
    """
    Display a specific documentation page.
    """
    doc_content = get_doc_content(slug)
    docs = get_doc_list()
    
    # Find current doc index for prev/next navigation
    current_index = None
    for i, doc in enumerate(docs):
        if doc['slug'] == slug:
            current_index = i
            break
    
    prev_doc = docs[current_index - 1] if current_index and current_index > 0 else None
    next_doc = docs[current_index + 1] if current_index is not None and current_index < len(docs) - 1 else None
    
    context = {
        'doc': doc_content,
        'docs': docs,
        'current_slug': slug,
        'prev_doc': prev_doc,
        'next_doc': next_doc,
        'page_title': doc_content['title'],
    }
    return render(request, 'portal/howto_detail.html', context)
