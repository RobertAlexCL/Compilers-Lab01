import sys
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from YAPLLexer import YAPLLexer
from YAPLParser import YAPLParser
from YAPLListener import YAPLListener
from graphviz import Digraph
from antlr4.tree.Trees import Trees

class TypeCheckingListener(YAPLListener):
    def __init__(self):
        self.symbol_table = {} 
        self.current_class = None
        self.classes = {}

    def enterClass_prod(self, ctx):
        self.current_class = ctx.TYPE_ID(0).getText()
        self.classes[self.current_class] = {}

    def exitClass_prod(self, ctx):
        self.current_class = None

    def enterFeature(self, ctx):
        if ctx.id_() and ctx.TYPE_ID():
            id_name = ctx.id_().getText()
            id_type = ctx.TYPE_ID().getText()
            if self.current_class:
                self.classes[self.current_class][id_name] = id_type
            else:
                self.symbol_table[id_name] = id_type

    def exitExpr(self, ctx):
        if ctx.id_() and ctx.expr():
            for id_node in ctx.id_():  
                id_name = id_node.getText()  
                id_type = self.symbol_table.get(id_name)
                exprs = ctx.expr()
                if isinstance(exprs, list):
                    for expr in exprs:
                        expr_type = self.get_expr_type(expr)
                        if id_type != expr_type:
                            print(f"Error de tipo: se esperaba '{id_type}' pero se obtuvo '{expr_type}'")
                else:
                    expr_type = self.get_expr_type(exprs)
                    if id_type != expr_type:
                        print(f"Error de tipo: se esperaba '{id_type}' pero se obtuvo '{expr_type}'")
        elif ctx.expr() and len(ctx.expr()) == 2:
            left_type = self.get_expr_type(ctx.expr(0))
            right_type = self.get_expr_type(ctx.expr(1))
            if ctx.getChild(1).getText() in ['+', '-', '*', '/']:
                if left_type != right_type or left_type != 'Int':
                    print(f"Error de tipo: se esperaba 'Int' pero se obtuvo '{left_type}' y '{right_type}'")
            elif ctx.getChild(1).getText() in ['<', '<=', '=']:
                if left_type != right_type:
                    print(f"Error de tipo: se esperaba '{left_type}' pero se obtuvo '{right_type}'")
        elif ctx.NOT():
            expr_type = self.get_expr_type(ctx.expr(0))
            if expr_type != 'Boolean':
                print(f"Error de tipo: se esperaba 'Boolean' pero se obtuvo '{expr_type}'")

    def get_expr_type(self, expr):
        for child in expr.getChildren():
            if isinstance(child, TerminalNode):
                if child.getSymbol().type == YAPLParser.INTEGER:
                    return 'Int'
                elif child.getSymbol().type == YAPLParser.STRING:
                    return 'String'
                elif child.getSymbol().type in [YAPLParser.TRUE, YAPLParser.FALSE]:
                    return 'Boolean'
                elif child.getSymbol().type == YAPLParser.ID:
                    return self.symbol_table.get(child.getText())
            elif isinstance(child, YAPLParser.IdContext):
                return self.symbol_table.get(child.getText())
        return None




class MyListener(YAPLListener, ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print(f"Error de sintaxis en la línea {line}, columna {column}: {msg}")

    def visitErrorNode(self, node):
        print(f"Error: nodo no reconocido '{node.getText()}'")

def visualize_tree(node, dot):
    if isinstance(node, TerminalNode):
        dot.node(str(id(node)), str(node.getSymbol().text))
    else:
        rule_name = YAPLParser.ruleNames[node.getRuleContext().getRuleIndex()]
        dot.node(str(id(node)), rule_name)
        for i in range(node.getChildCount()):
            child = node.getChild(i)
            visualize_tree(child, dot)
            dot.edge(str(id(node)), str(id(child)))

def main(argv):
    input_stream = FileStream(argv[1], encoding='utf-8')
    lexer = YAPLLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = YAPLParser(stream)
    parser.removeErrorListeners()  
    parser.addErrorListener(MyListener())  

    tree = parser.source()

    listener = TypeCheckingListener()
    walker = ParseTreeWalker()
    walker.walk(listener, tree)

    if parser.getNumberOfSyntaxErrors() == 0: 
        # Generar representación gráfica
        dot = Digraph(comment='Abstract Syntax Tree')
        visualize_tree(tree, dot)
        dot.render('tree', format='png', view=True)

        # Generar representación textual
        textual_representation = Trees.toStringTree(tree, None, parser)
        print(textual_representation)
    else:
        print("Se encontraron errores durante el análisis. No se generará ningún árbol.")

if __name__ == '__main__':
    main(sys.argv)
