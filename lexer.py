import re
from tokens import Token

class AnalisadorLexico:
    PALAVRAS_RESERVADAS = {
        "int", "boolean", "procedure",
        "char", "float", "void",
        "if", "else", "while",
        "return", "break", "continue",
        "print", "true", "false"
    }

    PADROES = [
        ("NUM_FLOAT", r"\d+\.\d+"),   
        ("NUM",    r"\d+"), 
        ("CHAR_LIT", r"'.*?'"),
        ("ID",     r"[A-Za-z_][A-Za-z0-9_]*"),
        ("OP",     r"==|!=|>=|<=|[+\-*/<>]"),
        ("ATRIB",  r"="),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("LBRACE", r"\{"),
        ("RBRACE", r"\}"),
        ("VIRG",   r","),
        ("PTO_V",  r";"),
        ("WS",     r"[ \t\r]+"),
        ("NL",     r"\n"),
        ("OUTRO",  r"."),
    ]

    REGEX = re.compile("|".join(f"(?P<{n}>{p})" for n, p in PADROES))

    def __init__(self, codigo):
        self.codigo = codigo
        self.tokens = []
        self.linha = 1
        self.coluna = 1

    def analisar(self):
        for m in self.REGEX.finditer(self.codigo):
            tipo = m.lastgroup
            txt = m.group()

            if tipo == "NUM":
                self.tokens.append(Token("NUM", int(txt), self.linha, self.coluna))

            elif tipo == "NUM_FLOAT":
                self.tokens.append(Token("NUM", float(txt), self.linha, self.coluna))

            elif tipo == "ID":
                if txt in self.PALAVRAS_RESERVADAS:
                    self.tokens.append(Token(txt.upper(), txt, self.linha, self.coluna))
                else:
                    self.tokens.append(Token("ID", txt, self.linha, self.coluna))

            elif tipo in ("OP", "ATRIB", "LPAREN", "RPAREN", "LBRACE", "RBRACE", "VIRG", "PTO_V"):
                self.tokens.append(Token(tipo, txt, self.linha, self.coluna))

            elif tipo == "WS":
                pass

            elif tipo == "NL":
                self.linha += 1
                self.coluna = 0

            elif tipo == "OUTRO":
                raise Exception(f"Erro léxico: símbolo inválido '{txt}' na linha {self.linha}")

            elif tipo == "CHAR_LIT":
                # Remove as aspas para guardar apenas o caractere
                valor_char = txt[1:-1]
                self.tokens.append(Token("CHAR", valor_char, self.linha, self.coluna))

            self.coluna += len(txt)

        self.tokens.append(Token("EOF", None, self.linha, self.coluna))
        return self.tokens