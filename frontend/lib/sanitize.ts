/**
 * Minimal client-side HTML sanitizer.
 *
 * Strips dangerous elements (script, iframe, object, embed, form),
 * event-handler attributes (on*), style attributes, and javascript: hrefs.
 * Runs in both SSR and client contexts without external dependencies.
 */

const DANGEROUS_TAGS = /<(script|style|iframe|object|embed|form|input|button|textarea|select|noscript|svg)\b[\s\S]*?>[\s\S]*?<\/\1>|<(script|style|iframe|object|embed|form|input|button|textarea|select|noscript|svg)\b[\s\S]*?\/?>/gi;
const EVENT_HANDLER_ATTRS = /\s+on[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi;
const STYLE_ATTR = /\s+style\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi;
const JAVASCRIPT_HREF = /\shref\s*=\s*(?:"javascript:[^"]*"|'javascript:[^']*')/gi;
const JAVASCRIPT_SRC = /\ssrc\s*=\s*(?:"javascript:[^"]*"|'javascript:[^']*')/gi;
const DATA_IMG_SRC = /\ssrc\s*=\s*(?:"data:[^"]*"|'data:[^']*')/gi;

export function sanitizeHtml(html: string): string {
  if (!html) return "";
  return html
    .replace(DANGEROUS_TAGS, "")
    .replace(EVENT_HANDLER_ATTRS, "")
    .replace(STYLE_ATTR, "")
    .replace(JAVASCRIPT_HREF, "")
    .replace(JAVASCRIPT_SRC, "")
    .replace(DATA_IMG_SRC, "");
}
