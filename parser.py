from tokens import Token

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        return self.tokens[self.i]

    def consume(self, tipo=None):
        tok = self.peek()
        if tipo and tok.tipo != tipo:
            raise ParseError(f"Esperado {tipo}, encontrado {tok.tipo} (linha {tok.linha})")
        self.i += 1
        return tok

    def accept(self, tipo):
        if self.peek().tipo == tipo:
            return self.consume()
        return None

    # ---------- PROGRAMA ----------
    def parse_program(self):
        elems = []
        while self.peek().tipo != "EOF":
            item = self.parse_declaration_or_command()
            if isinstance(item, list):
                elems.extend(item)
            else:
                elems.append(item)
        return elems

    def parse_declaration_or_command(self):
        t = self.peek().tipo
        if t in ("INT", "BOOLEAN"):
            return self.parse_type_decl()
        if t == "PROCEDURE":
            return self.parse_procedure()
        return self.parse_command()

    # ---------- DECLARAÇÕES ----------
    def parse_type_decl(self):
        tipo_tok = self.consume()
        tipo = tipo_tok.valor

        id_tok = self.consume("ID")
        nome = id_tok.valor

        if self.accept("LPAREN"):  # função
            params = self.parse_param_list_opt()
            self.consume("RPAREN")
            self.consume("LBRACE")

            body = self.parse_command_list()

            # return opcional
            return_expr = None
            if self.accept("RETURN"):
                return_expr = self.parse_expression()
                self.consume("PTO_V")

            self.consume("RBRACE")

            return [
                {"kind": "funcdecl", "nome": nome, "tipo": tipo, "params": params, "linha": tipo_tok.linha},
                {"kind": "funcbody", "nome": nome, "params": params, "body": body, "return": return_expr, "linha": tipo_tok.linha}
            ]

        # var declaration
        expr = None
        if self.accept("ATRIB"):
            expr = self.parse_expression()
        self.consume("PTO_V")

        return {"kind": "vardecl", "tipo": tipo, "nome": nome, "expr": expr, "linha": tipo_tok.linha}

    def parse_procedure(self):
        proc_tok = self.consume("PROCEDURE")
        id_tok = self.consume("ID")
        nome = id_tok.valor

        self.consume("LPAREN")
        params = self.parse_param_list_opt()
        self.consume("RPAREN")

        self.consume("LBRACE")
        body = self.parse_command_list()
        self.consume("RBRACE")

        return [
            {"kind": "procdecl", "nome": nome, "params": params, "linha": proc_tok.linha},
            {"kind": "procbody", "nome": nome, "params": params, "body": body, "linha": proc_tok.linha}
        ]

    def parse_param_list_opt(self):
        params = []
        if self.peek().tipo in ("INT", "BOOLEAN"):
            while True:
                tipo = self.consume().valor
                nome = self.consume("ID").valor
                params.append((tipo, nome))
                if not self.accept("VIRG"):
                    break
        return params

    # ---------- COMANDOS ----------
    def parse_command_list(self):
        cmds = []
        while self.peek().tipo not in ("RBRACE", "EOF"):
            cmds.append(self.parse_command())
        return cmds

    def parse_command(self):
        t = self.peek().tipo

        if t == "ID":
            id_tok = self.consume("ID")
            nome = id_tok.valor

            if self.accept("ATRIB"):
                expr = self.parse_expression()
                self.consume("PTO_V")
                return {"kind": "assign", "nome": nome, "expr": expr, "linha": id_tok.linha}

            if self.accept("LPAREN"):
                args = self.parse_arg_list_opt()
                self.consume("RPAREN")
                self.consume("PTO_V")
                return {"kind": "call", "nome": nome, "args": args, "linha": id_tok.linha}

            raise ParseError(f"Erro: esperado '=' ou '(' após {nome}")

        if t == "IF":
            if_tok = self.consume("IF")
            self.consume("LPAREN")
            cond = self.parse_expression()
            self.consume("RPAREN")

            self.consume("LBRACE")
            body = self.parse_command_list()
            self.consume("RBRACE")

            else_body = None
            if self.accept("ELSE"):
                self.consume("LBRACE")
                else_body = self.parse_command_list()
                self.consume("RBRACE")

            return {"kind": "if", "cond": cond, "body": body, "else": else_body, "linha": if_tok.linha}

        if t == "WHILE":
            while_tok = self.consume("WHILE")
            self.consume("LPAREN")
            cond = self.parse_expression()
            self.consume("RPAREN")

            self.consume("LBRACE")
            body = self.parse_command_list()
            self.consume("RBRACE")

            return {"kind": "while", "cond": cond, "body": body, "linha": while_tok.linha}

        if t == "RETURN":
            ret_tok = self.consume("RETURN")
            expr = self.parse_expression()
            self.consume("PTO_V")
            return {"kind": "return", "expr": expr, "linha": ret_tok.linha}

        if t == "PRINT":
            p = self.consume("PRINT")
            self.consume("LPAREN")
            expr = self.parse_expression()
            self.consume("RPAREN")
            self.consume("PTO_V")
            return {"kind": "print", "expr": expr, "linha": p.linha}

        if t == "BREAK":
            tok = self.consume("BREAK")
            self.consume("PTO_V")
            return {"kind": "jump", "op": "break", "linha": tok.linha}

        if t == "CONTINUE":
            tok = self.consume("CONTINUE")
            self.consume("PTO_V")
            return {"kind": "jump", "op": "continue", "linha": tok.linha}

        raise ParseError(f"Comando inválido na linha {self.peek().linha}")

    # ---------- EXPRESSÕES ----------
    def parse_arg_list_opt(self):
        args = []
        if self.peek().tipo != "RPAREN":
            args.append(self.parse_expression())
            while self.accept("VIRG"):
                args.append(self.parse_expression())
        return args

    def parse_expression(self):
        left = self.parse_arith_expr()

        if self.peek().tipo == "OP" and self.peek().valor in ("==", "!=", ">", "<", ">=", "<="):
            op = self.consume("OP").valor
            right = self.parse_arith_expr()
            return {"kind": "binop", "op": op, "left": left, "right": right}

        return left

    def parse_arith_expr(self):
        node = self.parse_term()
        while self.peek().tipo == "OP" and self.peek().valor in ("+", "-"):
            op = self.consume("OP").valor
            right = self.parse_term()
            node = {"kind": "binop", "op": op, "left": node, "right": right}
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek().tipo == "OP" and self.peek().valor in ("*", "/"):
            op = self.consume("OP").valor
            right = self.parse_factor()
            node = {"kind": "binop", "op": op, "left": node, "right": right}
        return node

    def parse_factor(self):
        t = self.peek().tipo

        if t == "NUM":
            tok = self.consume("NUM")
            return {"kind": "lit", "tipo": "int", "valor": tok.valor}

        if t == "TRUE":
            self.consume("TRUE")
            return {"kind": "lit", "tipo": "boolean", "valor": True}

        if t == "FALSE":
            self.consume("FALSE")
            return {"kind": "lit", "tipo": "boolean", "valor": False}

        if t == "ID":
            tok = self.consume("ID")
            nome = tok.valor

            if self.accept("LPAREN"):
                args = self.parse_arg_list_opt()
                self.consume("RPAREN")
                return {"kind": "call", "nome": nome, "args": args, "linha": tok.linha}

            return {"kind": "var", "nome": nome, "linha": tok.linha}

        if t == "LPAREN":
            self.consume("LPAREN")
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr

        raise ParseError(f"Fator inválido na linha {self.peek().linha}")