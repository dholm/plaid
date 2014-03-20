from app import app
from jinja2 import Markup, escape
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
import pygments.lexers as lexers
from pygments.lexer import RegexLexer, bygroups
from pygments.token import *


class CodeHtmlFormatter(HtmlFormatter):

    def wrap(self, source, outfile):
        return self._wrap_code(source)

    def _wrap_code(self, source):
        lines = list(source)
        mw = len(str(len(lines) -1))
        num = 0
        yield 0, '<pre class="highlight">'
        for i, t in lines:
            if i == 1:
                line = '<span><a name="l-%d" href="#l-%d">%*d</a></span> ' % (num, num, mw, num)
                num += 1
                line += t
            yield i, line
        yield 0, '</pre>'


def render_patch(data):
    lexer = lexers.get_lexer_by_name('diff')
    formatter = CodeHtmlFormatter(encoding='utf-8')
    return Markup(highlight(data, lexer, formatter).decode('utf-8'))

class EmailLexer(RegexLexer):
    tokens = {
        'root': [
            (r'\s*<[^>]*>', Keyword),
            (r'^([^:]*)(: )', bygroups(Name.Attribute, Operator)),
            (r'.*\n', Text)
        ]
    }

def render_headers(data):
    lexer = EmailLexer()
    formatter = HtmlFormatter(encoding='utf-8')
    return Markup(highlight(data, lexer, formatter).decode('utf-8'))

app.jinja_env.globals.update(render_headers=render_headers)
app.jinja_env.globals.update(render_patch=render_patch)
