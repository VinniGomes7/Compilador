# semantic.py

class TabelaSimbolos:
    def __init__(self):
        # Uma lista de dicionários. Cada dicionário é um nível de escopo (Global, Local...)
        self.escopos = [{}]

    def entrar_escopo(self):
        # Cria uma nova camada de variáveis (ex: ao entrar num { ... })
        self.escopos.append({})

    def sair_escopo(self):
        # Joga fora a camada mais interna ao sair do }
        if len(self.escopos) > 1:
            self.escopos.pop()

    def definir(self, nome, tipo):
        # Tenta guardar a variável. Se já existir no mesmo nível, dá erro.
        if nome in self.escopos[-1]:
            return False
        self.escopos[-1][nome] = tipo
        return True

    def buscar(self, nome):
        # Procura a variável do bolso (local) até a casa toda (global)
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None

class AnalisadorSemantico:
    def __init__(self):
        self.tabela = TabelaSimbolos()
        self.funcoes = {}

    def verificar(self, node):
        if isinstance(node, list):
            for item in node:
                self.verificar(item)
            return None

        kind = node.get("kind")

        # --- LÓGICA DE LITERAIS (Básico) ---
        if kind == "lit":
            return node["tipo"] # Retorna 'int', 'boolean', etc.

        # --- LÓGICA DE VARIÁVEIS ---
        elif kind == "var":
            tipo = self.tabela.buscar(node["nome"])
            if not tipo:
                raise Exception(f"Erro Semântico: Variável '{node['nome']}' não declarada (linha {node.get('linha')})")
            return tipo

        # --- DECLARAÇÃO ---
        elif kind == "vardecl":
            # 1. Tenta definir na tabela
            if not self.tabela.definir(node["nome"], node["tipo"]):
                raise Exception(f"Erro Semântico: Variável '{node['nome']}' já declarada (linha {node['linha']})")
            
            # 2. Se tiver valor inicial (int x = 10), checa se o tipo bate
            if node.get("expr"):
                tipo_expr = self.verificar(node["expr"])
                if tipo_expr != node["tipo"]:
                    raise Exception(f"Erro de Tipo: Tentando atribuir {tipo_expr} para {node['tipo']} (linha {node['linha']})")
            return node["tipo"]

        # --- ATRIBUIÇÃO (x = ...) ---
        elif kind == "assign":
            tipo_var = self.tabela.buscar(node["nome"])
            if not tipo_var:
                raise Exception(f"Erro Semântico: Variável '{node['nome']}' não declarada (linha {node['linha']})")
            
            tipo_expr = self.verificar(node["expr"])
            if tipo_var != tipo_expr:
                raise Exception(f"Erro de Tipo: Variável '{node['nome']}' é {tipo_var}, mas recebeu {tipo_expr} (linha {node['linha']})")
            return tipo_var

        # --- OPERAÇÕES MATEMÁTICAS/LÓGICAS ---
        elif kind == "binop":
            tipo_esq = self.verificar(node["left"])
            tipo_dir = self.verificar(node["right"])
            op = node["op"]

            # Operadores matemáticos (+, -, *, /) só aceitam números
            if op in ("+", "-", "*", "/"):
                if tipo_esq in ("int", "float") and tipo_dir in ("int", "float"):
                    # Se um for float, o resultado é float (promoção de tipo)
                    return "float" if (tipo_esq == "float" or tipo_dir == "float") else "int"
                raise Exception(f"Erro de Tipo: Operador '{op}' não suporta {tipo_esq} e {tipo_dir}")

            # Operadores relacionais (==, !=, <, >) resultam em boolean
            if op in ("==", "!=", "<", ">", "<=", ">="):
                return "boolean"

        # --- BLOCOS E ESCOPO ---
        elif kind in ("funcbody", "procbody", "if", "while"):
            self.tabela.entrar_escopo()
            
            # Se for função/proc, registra os parâmetros no novo escopo
            for p_tipo, p_nome in node.get("params", []):
                self.tabela.definir(p_nome, p_tipo)
            
            # Verifica todos os comandos interrnos
            for cmd in node.get("body", []):
                self.verificar(cmd)

            self.tabela.sair_escopo()
            return None
        
        # --- REGISTRAR FUNÇÕES/PROCS ---
        elif kind in ("funcdecl", "procdecl"):
            nome = node["nome"]
            # Extraímos apenas os tipos da lista de tuplas (tipo, nome)
            tipos_params = [p[0] for p in node.get("params", [])]
            
            if nome in self.funcoes:
                raise Exception(f"Erro Semântico: Função/Procedimento '{nome}' já declarado (linha {node['linha']})")
            
            self.funcoes[nome] = tipos_params
            return None

        # --- VERIFICAR CHAMADAS (CALL) ---
        elif kind == "call":
            nome = node["nome"]
            if nome not in self.funcoes:
                raise Exception(f"Erro Semântico: Função/Procedimento '{nome}' não declarado (linha {node['linha']})")
            
            params_esperados = self.funcoes[nome]
            # Verificamos os tipos dos argumentos passados na chamada
            args_passados = [self.verificar(arg) for arg in node.get("args", [])]

            # 1. Verifica quantidade
            if len(args_passados) != len(params_esperados):
                raise Exception(f"Erro de Argumento: '{nome}' espera {len(params_esperados)} argumentos, mas recebeu {len(args_passados)} (linha {node['linha']})")
            
            # 2. Verifica tipos (Tipagem Forte)
            for i, (tipo_exp, tipo_arq) in enumerate(zip(params_esperados, args_passados)):
                if tipo_exp != tipo_arq:
                    # Permitir promoção de int para float se você quiser ser amigável, 
                    # mas para "Tipagem Forte" pura, devem ser iguais.
                    raise Exception(f"Erro de Tipo: Argumento {i+1} de '{nome}' deve ser {tipo_exp}, mas recebeu {tipo_arq} (linha {node['linha']})")
            
            return "void" # Ou o tipo de retorno da função se você implementar funcdecl com tipo
        
        return None