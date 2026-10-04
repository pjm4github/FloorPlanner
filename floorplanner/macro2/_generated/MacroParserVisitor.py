# Generated from MacroParser.g4 by ANTLR 4.11.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .MacroParser import MacroParser
else:
    from MacroParser import MacroParser

# This class defines a complete generic visitor for a parse tree produced by MacroParser.

class MacroParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by MacroParser#macro.
    def visitMacro(self, ctx:MacroParser.MacroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#line.
    def visitLine(self, ctx:MacroParser.LineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#toolSelect.
    def visitToolSelect(self, ctx:MacroParser.ToolSelectContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#command.
    def visitCommand(self, ctx:MacroParser.CommandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#mouseChain.
    def visitMouseChain(self, ctx:MacroParser.MouseChainContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#clickVerb.
    def visitClickVerb(self, ctx:MacroParser.ClickVerbContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#dragSegment.
    def visitDragSegment(self, ctx:MacroParser.DragSegmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#move.
    def visitMove(self, ctx:MacroParser.MoveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#wheel.
    def visitWheel(self, ctx:MacroParser.WheelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#modifiers.
    def visitModifiers(self, ctx:MacroParser.ModifiersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#point.
    def visitPoint(self, ctx:MacroParser.PointContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#typeText.
    def visitTypeText(self, ctx:MacroParser.TypeTextContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#keyPress.
    def visitKeyPress(self, ctx:MacroParser.KeyPressContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#keyStroke.
    def visitKeyStroke(self, ctx:MacroParser.KeyStrokeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#keyName.
    def visitKeyName(self, ctx:MacroParser.KeyNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#keyDown.
    def visitKeyDown(self, ctx:MacroParser.KeyDownContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#keyUp.
    def visitKeyUp(self, ctx:MacroParser.KeyUpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MacroParser#wait.
    def visitWait(self, ctx:MacroParser.WaitContext):
        return self.visitChildren(ctx)



del MacroParser