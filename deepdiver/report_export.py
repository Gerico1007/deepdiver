"""
Report export
Part of DeepDiver - NotebookLM Podcast Automation System

Reports (Interactive and Document) have no file download in Gemini Notebook;
Document reports only export to Google Docs/Sheets. Both kinds render their
text in a <labs-tailwind-doc-viewer> made of structured blocks (observed
2026-10-06): div.paragraph.heading1-3, div.paragraph.normal, ul/ol > li,
table, pre, hr, and, in Interactive reports, <inline-artifact-renderer> for
an embedded studio item. Chat answers use the same blocks, with sources as
button.citation-marker. This module turns that DOM into Markdown.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

# Scoped to the Studio's artifact viewer: every chat answer is also a
# <labs-tailwind-doc-viewer>, and the chat panel comes first in the DOM, so an
# unscoped selector saved the notebook's first chat answer as the report
# (Episode 550, notebook 0ae51b4c, found by the T6 lead on 2026-10-07).
REPORT_VIEWER_SELECTOR = 'artifact-viewer labs-tailwind-doc-viewer'

# Evaluated in the page with the doc viewer element as its argument.
REPORT_TO_MARKDOWN_JS = r"""
(root) => {
  const out = [];
  const inline = (el, skipLists) => {
    let s = '';
    el.childNodes.forEach(n => {
      if (n.nodeType === 3) { s += n.textContent; return; }
      if (n.nodeType !== 1) return;
      const t = n.tagName.toLowerCase();
      if (skipLists && (t === 'ul' || t === 'ol')) return;
      const inner = inline(n, skipLists);
      const m = inner.match(/^(\s*)([\s\S]*?)(\s*)$/);
      if ((t === 'b' || t === 'strong') && m[2]) s += `${m[1]}**${m[2]}**${m[3]}`;
      else if ((t === 'i' || t === 'em') && m[2]) s += `${m[1]}*${m[2]}*${m[3]}`;
      else if (t === 'button' && String(n.className).includes('citation-marker') && /^\d+$/.test(n.innerText.trim())) s += ` [${n.innerText.trim()}]`;
      else if (t === 'button') return;
      else if (t === 'code') s += '`' + n.textContent + '`';
      else if (t === 'a') s += `[${inner}](${n.getAttribute('href') || ''})`;
      else s += inner;
    });
    return s.replace(/[ \t]+/g, ' ');
  };
  // Items sit inside wrapper elements under their list, so an item belongs
  // to the list that is its nearest ul/ol ancestor.
  const list = (el, depth) => {
    const ordered = el.tagName.toLowerCase() === 'ol';
    let i = 1;
    for (const li of el.querySelectorAll('li')) {
      if (li.parentElement.closest('ul,ol') !== el) continue;
      out.push('  '.repeat(depth) + (ordered ? `${i++}.` : '-') + ' ' + inline(li, true).trim());
      for (const sub of li.querySelectorAll('ul,ol')) {
        if (sub.parentElement.closest('li') === li) list(sub, depth + 1);
      }
    }
  };
  const table = (el) => {
    const rows = Array.from(el.querySelectorAll('tr')).map(tr =>
      Array.from(tr.querySelectorAll('th,td')).map(c => (c.innerText || '').replace(/\s+/g, ' ').replace(/\|/g, '\\|').trim()));
    if (!rows.length) return;
    out.push('| ' + rows[0].join(' | ') + ' |');
    out.push('|' + rows[0].map(() => ' --- ').join('|') + '|');
    rows.slice(1).forEach(r => out.push('| ' + r.join(' | ') + ' |'));
    out.push('');
  };
  const walk = (el) => {
    for (const c of el.children) {
      const t = c.tagName.toLowerCase();
      const cls = String(c.className || '');
      const heading = cls.match(/\bheading(\d)\b/);
      if (t === 'div' && cls.includes('paragraph') && heading) {
        out.push('#'.repeat(+heading[1]) + ' ' + inline(c).trim(), '');
      } else if (t === 'div' && cls.includes('paragraph') && !cls.includes('table-paragraph')) {
        const text = inline(c).trim();
        if (text) out.push(text, '');
      } else if (t === 'ul' || t === 'ol') {
        list(c, 0); out.push('');
      } else if (t === 'table') {
        table(c);
      } else if (t === 'pre') {
        out.push('```', c.textContent.replace(/\n$/, ''), '```', '');
      } else if (t === 'hr') {
        out.push('---', '');
      } else if (t === 'inline-artifact-renderer') {
        // An embedded studio item, or a tile recommending one to generate
        // ("Recommended · Infographic").
        const lines = (c.innerText || '').split('\n').map(x => x.trim()).filter(x => x && !/^[a-z_]+$/.test(x));
        const titleEl = c.querySelector('.artifact-title, [class*=title]');
        const name = (titleEl && titleEl.innerText.trim()) || lines[lines.length - 1] || 'studio item';
        const kind = lines.find(x => x.includes('·')) || 'Studio item';
        out.push(`> ${kind}: ${name}`, '');
      } else {
        walk(c);
      }
    }
  };
  walk(root);
  return out.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
}
"""


def report_html_document(title: str, inner_html: str) -> str:
    """Wrap a report's rendered HTML in a minimal standalone page."""
    from html import escape
    return (
        '<!doctype html>\n<html><head><meta charset="utf-8">'
        f'<title>{escape(title)}</title></head>\n<body>\n'
        f'<h1>{escape(title)}</h1>\n{inner_html}\n</body></html>\n'
    )
