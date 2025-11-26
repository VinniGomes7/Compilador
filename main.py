import sys
from lexer import AnalisadorLexico
from parser import Parser, ParseError

def executar_arquivo(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            codigo = f.read()

        print("=== LEXER ===")
        lexer = AnalisadorLexico(codigo)
        tokens = lexer.analisar()
        for t in tokens:
            print(t)

        print("\n=== PARSER ===")
        parser = Parser(tokens)

        elementos = []
        while parser.peek().tipo != "EOF":
            item = parser.parse_declaration_or_command()
            if isinstance(item, list):
                elementos.extend(item)
            else:
                elementos.append(item)

        import pprint
        pprint.pprint(elementos)

    except ParseError as e:
        print("\nERRO DE SINTAXE:")
        print(e)

    except FileNotFoundError:
        print("Arquivo não encontrado:", caminho)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python main.py <arquivo.txt>")
        sys.exit(1)

    executar_arquivo(sys.argv[1])