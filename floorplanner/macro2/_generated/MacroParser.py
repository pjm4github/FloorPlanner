# Generated from MacroParser.g4 by ANTLR 4.11.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,27,139,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,1,0,3,0,38,8,0,1,0,5,0,41,
        8,0,10,0,12,0,44,9,0,1,0,3,0,47,8,0,1,0,1,0,1,1,1,1,3,1,53,8,1,1,
        1,3,1,56,8,1,1,2,1,2,1,3,1,3,1,3,1,3,1,3,1,3,1,3,1,3,3,3,68,8,3,
        1,4,3,4,71,8,4,1,4,1,4,1,4,5,4,76,8,4,10,4,12,4,79,9,4,1,5,1,5,1,
        6,3,6,84,8,6,1,6,1,6,1,6,1,7,3,7,90,8,7,1,7,1,7,1,7,1,8,3,8,96,8,
        8,1,8,1,8,1,8,1,8,1,9,4,9,103,8,9,11,9,12,9,104,1,10,1,10,1,10,1,
        11,1,11,3,11,112,8,11,1,12,1,12,4,12,116,8,12,11,12,12,12,117,1,
        13,5,13,121,8,13,10,13,12,13,124,9,13,1,13,1,13,1,14,1,14,1,15,1,
        15,1,15,1,16,1,16,1,16,1,17,1,17,1,17,1,17,0,0,18,0,2,4,6,8,10,12,
        14,16,18,20,22,24,26,28,30,32,34,0,2,1,0,5,10,1,0,24,25,141,0,42,
        1,0,0,0,2,55,1,0,0,0,4,57,1,0,0,0,6,67,1,0,0,0,8,70,1,0,0,0,10,80,
        1,0,0,0,12,83,1,0,0,0,14,89,1,0,0,0,16,95,1,0,0,0,18,102,1,0,0,0,
        20,106,1,0,0,0,22,109,1,0,0,0,24,113,1,0,0,0,26,122,1,0,0,0,28,127,
        1,0,0,0,30,129,1,0,0,0,32,132,1,0,0,0,34,135,1,0,0,0,36,38,3,2,1,
        0,37,36,1,0,0,0,37,38,1,0,0,0,38,39,1,0,0,0,39,41,5,18,0,0,40,37,
        1,0,0,0,41,44,1,0,0,0,42,40,1,0,0,0,42,43,1,0,0,0,43,46,1,0,0,0,
        44,42,1,0,0,0,45,47,3,2,1,0,46,45,1,0,0,0,46,47,1,0,0,0,47,48,1,
        0,0,0,48,49,5,0,0,1,49,1,1,0,0,0,50,52,3,4,2,0,51,53,3,6,3,0,52,
        51,1,0,0,0,52,53,1,0,0,0,53,56,1,0,0,0,54,56,3,6,3,0,55,50,1,0,0,
        0,55,54,1,0,0,0,56,3,1,0,0,0,57,58,5,15,0,0,58,5,1,0,0,0,59,68,3,
        8,4,0,60,68,3,14,7,0,61,68,3,16,8,0,62,68,3,22,11,0,63,68,3,24,12,
        0,64,68,3,30,15,0,65,68,3,32,16,0,66,68,3,34,17,0,67,59,1,0,0,0,
        67,60,1,0,0,0,67,61,1,0,0,0,67,62,1,0,0,0,67,63,1,0,0,0,67,64,1,
        0,0,0,67,65,1,0,0,0,67,66,1,0,0,0,68,7,1,0,0,0,69,71,3,18,9,0,70,
        69,1,0,0,0,70,71,1,0,0,0,71,72,1,0,0,0,72,73,3,10,5,0,73,77,3,20,
        10,0,74,76,3,12,6,0,75,74,1,0,0,0,76,79,1,0,0,0,77,75,1,0,0,0,77,
        78,1,0,0,0,78,9,1,0,0,0,79,77,1,0,0,0,80,81,7,0,0,0,81,11,1,0,0,
        0,82,84,3,18,9,0,83,82,1,0,0,0,83,84,1,0,0,0,84,85,1,0,0,0,85,86,
        5,11,0,0,86,87,3,20,10,0,87,13,1,0,0,0,88,90,3,18,9,0,89,88,1,0,
        0,0,89,90,1,0,0,0,90,91,1,0,0,0,91,92,5,12,0,0,92,93,3,20,10,0,93,
        15,1,0,0,0,94,96,3,18,9,0,95,94,1,0,0,0,95,96,1,0,0,0,96,97,1,0,
        0,0,97,98,5,13,0,0,98,99,5,17,0,0,99,100,5,17,0,0,100,17,1,0,0,0,
        101,103,5,16,0,0,102,101,1,0,0,0,103,104,1,0,0,0,104,102,1,0,0,0,
        104,105,1,0,0,0,105,19,1,0,0,0,106,107,5,17,0,0,107,108,5,17,0,0,
        108,21,1,0,0,0,109,111,5,1,0,0,110,112,5,27,0,0,111,110,1,0,0,0,
        111,112,1,0,0,0,112,23,1,0,0,0,113,115,5,4,0,0,114,116,3,26,13,0,
        115,114,1,0,0,0,116,117,1,0,0,0,117,115,1,0,0,0,117,118,1,0,0,0,
        118,25,1,0,0,0,119,121,5,23,0,0,120,119,1,0,0,0,121,124,1,0,0,0,
        122,120,1,0,0,0,122,123,1,0,0,0,123,125,1,0,0,0,124,122,1,0,0,0,
        125,126,3,28,14,0,126,27,1,0,0,0,127,128,7,1,0,0,128,29,1,0,0,0,
        129,130,5,2,0,0,130,131,3,28,14,0,131,31,1,0,0,0,132,133,5,3,0,0,
        133,134,3,28,14,0,134,33,1,0,0,0,135,136,5,14,0,0,136,137,5,17,0,
        0,137,35,1,0,0,0,15,37,42,46,52,55,67,70,77,83,89,95,104,111,117,
        122
    ]

class MacroParser ( Parser ):

    grammarFileName = "MacroParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'TYPE'", "'KEYDOWN'", "'KEYUP'", "'KEY'", 
                     "'CLICK'", "'RCLICK'", "'MCLICK'", "'DCLICK'", "'XCLICK1'", 
                     "'XCLICK2'", "'DRAG'", "'MOVE'", "'WHEEL'", "'WAIT'", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "' '" ]

    symbolicNames = [ "<INVALID>", "TYPE", "KEYDOWN", "KEYUP", "KEY", "CLICK", 
                      "RCLICK", "MCLICK", "DCLICK", "XCLICK1", "XCLICK2", 
                      "DRAG", "MOVE", "WHEEL", "WAIT", "TOOL", "MOD", "NUMBER", 
                      "NL", "WS", "COMMENT", "KEY_WS", "KEY_COMMENT", "KMOD", 
                      "KNAMED", "KCHAR", "TEXT_SEP", "TEXT" ]

    RULE_macro = 0
    RULE_line = 1
    RULE_toolSelect = 2
    RULE_command = 3
    RULE_mouseChain = 4
    RULE_clickVerb = 5
    RULE_dragSegment = 6
    RULE_move = 7
    RULE_wheel = 8
    RULE_modifiers = 9
    RULE_point = 10
    RULE_typeText = 11
    RULE_keyPress = 12
    RULE_keyStroke = 13
    RULE_keyName = 14
    RULE_keyDown = 15
    RULE_keyUp = 16
    RULE_wait = 17

    ruleNames =  [ "macro", "line", "toolSelect", "command", "mouseChain", 
                   "clickVerb", "dragSegment", "move", "wheel", "modifiers", 
                   "point", "typeText", "keyPress", "keyStroke", "keyName", 
                   "keyDown", "keyUp", "wait" ]

    EOF = Token.EOF
    TYPE=1
    KEYDOWN=2
    KEYUP=3
    KEY=4
    CLICK=5
    RCLICK=6
    MCLICK=7
    DCLICK=8
    XCLICK1=9
    XCLICK2=10
    DRAG=11
    MOVE=12
    WHEEL=13
    WAIT=14
    TOOL=15
    MOD=16
    NUMBER=17
    NL=18
    WS=19
    COMMENT=20
    KEY_WS=21
    KEY_COMMENT=22
    KMOD=23
    KNAMED=24
    KCHAR=25
    TEXT_SEP=26
    TEXT=27

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.11.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class MacroContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(MacroParser.EOF, 0)

        def NL(self, i:int=None):
            if i is None:
                return self.getTokens(MacroParser.NL)
            else:
                return self.getToken(MacroParser.NL, i)

        def line(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MacroParser.LineContext)
            else:
                return self.getTypedRuleContext(MacroParser.LineContext,i)


        def getRuleIndex(self):
            return MacroParser.RULE_macro

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMacro" ):
                return visitor.visitMacro(self)
            else:
                return visitor.visitChildren(self)




    def macro(self):

        localctx = MacroParser.MacroContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_macro)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 42
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,1,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 37
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if ((_la) & ~0x3f) == 0 and ((1 << _la) & 129022) != 0:
                        self.state = 36
                        self.line()


                    self.state = 39
                    self.match(MacroParser.NL) 
                self.state = 44
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,1,self._ctx)

            self.state = 46
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if ((_la) & ~0x3f) == 0 and ((1 << _la) & 129022) != 0:
                self.state = 45
                self.line()


            self.state = 48
            self.match(MacroParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class LineContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def toolSelect(self):
            return self.getTypedRuleContext(MacroParser.ToolSelectContext,0)


        def command(self):
            return self.getTypedRuleContext(MacroParser.CommandContext,0)


        def getRuleIndex(self):
            return MacroParser.RULE_line

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLine" ):
                return visitor.visitLine(self)
            else:
                return visitor.visitChildren(self)




    def line(self):

        localctx = MacroParser.LineContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_line)
        self._la = 0 # Token type
        try:
            self.state = 55
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [15]:
                self.enterOuterAlt(localctx, 1)
                self.state = 50
                self.toolSelect()
                self.state = 52
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if ((_la) & ~0x3f) == 0 and ((1 << _la) & 96254) != 0:
                    self.state = 51
                    self.command()


                pass
            elif token in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 16]:
                self.enterOuterAlt(localctx, 2)
                self.state = 54
                self.command()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ToolSelectContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TOOL(self):
            return self.getToken(MacroParser.TOOL, 0)

        def getRuleIndex(self):
            return MacroParser.RULE_toolSelect

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitToolSelect" ):
                return visitor.visitToolSelect(self)
            else:
                return visitor.visitChildren(self)




    def toolSelect(self):

        localctx = MacroParser.ToolSelectContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_toolSelect)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 57
            self.match(MacroParser.TOOL)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CommandContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def mouseChain(self):
            return self.getTypedRuleContext(MacroParser.MouseChainContext,0)


        def move(self):
            return self.getTypedRuleContext(MacroParser.MoveContext,0)


        def wheel(self):
            return self.getTypedRuleContext(MacroParser.WheelContext,0)


        def typeText(self):
            return self.getTypedRuleContext(MacroParser.TypeTextContext,0)


        def keyPress(self):
            return self.getTypedRuleContext(MacroParser.KeyPressContext,0)


        def keyDown(self):
            return self.getTypedRuleContext(MacroParser.KeyDownContext,0)


        def keyUp(self):
            return self.getTypedRuleContext(MacroParser.KeyUpContext,0)


        def wait(self):
            return self.getTypedRuleContext(MacroParser.WaitContext,0)


        def getRuleIndex(self):
            return MacroParser.RULE_command

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCommand" ):
                return visitor.visitCommand(self)
            else:
                return visitor.visitChildren(self)




    def command(self):

        localctx = MacroParser.CommandContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_command)
        try:
            self.state = 67
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,5,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 59
                self.mouseChain()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 60
                self.move()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 61
                self.wheel()
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 62
                self.typeText()
                pass

            elif la_ == 5:
                self.enterOuterAlt(localctx, 5)
                self.state = 63
                self.keyPress()
                pass

            elif la_ == 6:
                self.enterOuterAlt(localctx, 6)
                self.state = 64
                self.keyDown()
                pass

            elif la_ == 7:
                self.enterOuterAlt(localctx, 7)
                self.state = 65
                self.keyUp()
                pass

            elif la_ == 8:
                self.enterOuterAlt(localctx, 8)
                self.state = 66
                self.wait()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MouseChainContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def clickVerb(self):
            return self.getTypedRuleContext(MacroParser.ClickVerbContext,0)


        def point(self):
            return self.getTypedRuleContext(MacroParser.PointContext,0)


        def modifiers(self):
            return self.getTypedRuleContext(MacroParser.ModifiersContext,0)


        def dragSegment(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MacroParser.DragSegmentContext)
            else:
                return self.getTypedRuleContext(MacroParser.DragSegmentContext,i)


        def getRuleIndex(self):
            return MacroParser.RULE_mouseChain

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMouseChain" ):
                return visitor.visitMouseChain(self)
            else:
                return visitor.visitChildren(self)




    def mouseChain(self):

        localctx = MacroParser.MouseChainContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_mouseChain)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 70
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==16:
                self.state = 69
                self.modifiers()


            self.state = 72
            self.clickVerb()
            self.state = 73
            self.point()
            self.state = 77
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==11 or _la==16:
                self.state = 74
                self.dragSegment()
                self.state = 79
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ClickVerbContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CLICK(self):
            return self.getToken(MacroParser.CLICK, 0)

        def RCLICK(self):
            return self.getToken(MacroParser.RCLICK, 0)

        def MCLICK(self):
            return self.getToken(MacroParser.MCLICK, 0)

        def DCLICK(self):
            return self.getToken(MacroParser.DCLICK, 0)

        def XCLICK1(self):
            return self.getToken(MacroParser.XCLICK1, 0)

        def XCLICK2(self):
            return self.getToken(MacroParser.XCLICK2, 0)

        def getRuleIndex(self):
            return MacroParser.RULE_clickVerb

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitClickVerb" ):
                return visitor.visitClickVerb(self)
            else:
                return visitor.visitChildren(self)




    def clickVerb(self):

        localctx = MacroParser.ClickVerbContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_clickVerb)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 80
            _la = self._input.LA(1)
            if not(((_la) & ~0x3f) == 0 and ((1 << _la) & 2016) != 0):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DragSegmentContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DRAG(self):
            return self.getToken(MacroParser.DRAG, 0)

        def point(self):
            return self.getTypedRuleContext(MacroParser.PointContext,0)


        def modifiers(self):
            return self.getTypedRuleContext(MacroParser.ModifiersContext,0)


        def getRuleIndex(self):
            return MacroParser.RULE_dragSegment

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDragSegment" ):
                return visitor.visitDragSegment(self)
            else:
                return visitor.visitChildren(self)




    def dragSegment(self):

        localctx = MacroParser.DragSegmentContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_dragSegment)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 83
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==16:
                self.state = 82
                self.modifiers()


            self.state = 85
            self.match(MacroParser.DRAG)
            self.state = 86
            self.point()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MoveContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def MOVE(self):
            return self.getToken(MacroParser.MOVE, 0)

        def point(self):
            return self.getTypedRuleContext(MacroParser.PointContext,0)


        def modifiers(self):
            return self.getTypedRuleContext(MacroParser.ModifiersContext,0)


        def getRuleIndex(self):
            return MacroParser.RULE_move

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMove" ):
                return visitor.visitMove(self)
            else:
                return visitor.visitChildren(self)




    def move(self):

        localctx = MacroParser.MoveContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_move)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 89
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==16:
                self.state = 88
                self.modifiers()


            self.state = 91
            self.match(MacroParser.MOVE)
            self.state = 92
            self.point()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WheelContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.dx = None # Token
            self.dy = None # Token

        def WHEEL(self):
            return self.getToken(MacroParser.WHEEL, 0)

        def NUMBER(self, i:int=None):
            if i is None:
                return self.getTokens(MacroParser.NUMBER)
            else:
                return self.getToken(MacroParser.NUMBER, i)

        def modifiers(self):
            return self.getTypedRuleContext(MacroParser.ModifiersContext,0)


        def getRuleIndex(self):
            return MacroParser.RULE_wheel

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWheel" ):
                return visitor.visitWheel(self)
            else:
                return visitor.visitChildren(self)




    def wheel(self):

        localctx = MacroParser.WheelContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_wheel)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 95
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==16:
                self.state = 94
                self.modifiers()


            self.state = 97
            self.match(MacroParser.WHEEL)
            self.state = 98
            localctx.dx = self.match(MacroParser.NUMBER)
            self.state = 99
            localctx.dy = self.match(MacroParser.NUMBER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ModifiersContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def MOD(self, i:int=None):
            if i is None:
                return self.getTokens(MacroParser.MOD)
            else:
                return self.getToken(MacroParser.MOD, i)

        def getRuleIndex(self):
            return MacroParser.RULE_modifiers

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitModifiers" ):
                return visitor.visitModifiers(self)
            else:
                return visitor.visitChildren(self)




    def modifiers(self):

        localctx = MacroParser.ModifiersContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_modifiers)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 102 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 101
                self.match(MacroParser.MOD)
                self.state = 104 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==16):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PointContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.x = None # Token
            self.y = None # Token

        def NUMBER(self, i:int=None):
            if i is None:
                return self.getTokens(MacroParser.NUMBER)
            else:
                return self.getToken(MacroParser.NUMBER, i)

        def getRuleIndex(self):
            return MacroParser.RULE_point

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPoint" ):
                return visitor.visitPoint(self)
            else:
                return visitor.visitChildren(self)




    def point(self):

        localctx = MacroParser.PointContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_point)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 106
            localctx.x = self.match(MacroParser.NUMBER)
            self.state = 107
            localctx.y = self.match(MacroParser.NUMBER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeTextContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TYPE(self):
            return self.getToken(MacroParser.TYPE, 0)

        def TEXT(self):
            return self.getToken(MacroParser.TEXT, 0)

        def getRuleIndex(self):
            return MacroParser.RULE_typeText

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeText" ):
                return visitor.visitTypeText(self)
            else:
                return visitor.visitChildren(self)




    def typeText(self):

        localctx = MacroParser.TypeTextContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_typeText)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 109
            self.match(MacroParser.TYPE)
            self.state = 111
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==27:
                self.state = 110
                self.match(MacroParser.TEXT)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class KeyPressContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def KEY(self):
            return self.getToken(MacroParser.KEY, 0)

        def keyStroke(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MacroParser.KeyStrokeContext)
            else:
                return self.getTypedRuleContext(MacroParser.KeyStrokeContext,i)


        def getRuleIndex(self):
            return MacroParser.RULE_keyPress

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitKeyPress" ):
                return visitor.visitKeyPress(self)
            else:
                return visitor.visitChildren(self)




    def keyPress(self):

        localctx = MacroParser.KeyPressContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_keyPress)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 113
            self.match(MacroParser.KEY)
            self.state = 115 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 114
                self.keyStroke()
                self.state = 117 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (((_la) & ~0x3f) == 0 and ((1 << _la) & 58720256) != 0):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class KeyStrokeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def keyName(self):
            return self.getTypedRuleContext(MacroParser.KeyNameContext,0)


        def KMOD(self, i:int=None):
            if i is None:
                return self.getTokens(MacroParser.KMOD)
            else:
                return self.getToken(MacroParser.KMOD, i)

        def getRuleIndex(self):
            return MacroParser.RULE_keyStroke

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitKeyStroke" ):
                return visitor.visitKeyStroke(self)
            else:
                return visitor.visitChildren(self)




    def keyStroke(self):

        localctx = MacroParser.KeyStrokeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_keyStroke)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 122
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==23:
                self.state = 119
                self.match(MacroParser.KMOD)
                self.state = 124
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 125
            self.keyName()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class KeyNameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def KCHAR(self):
            return self.getToken(MacroParser.KCHAR, 0)

        def KNAMED(self):
            return self.getToken(MacroParser.KNAMED, 0)

        def getRuleIndex(self):
            return MacroParser.RULE_keyName

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitKeyName" ):
                return visitor.visitKeyName(self)
            else:
                return visitor.visitChildren(self)




    def keyName(self):

        localctx = MacroParser.KeyNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_keyName)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 127
            _la = self._input.LA(1)
            if not(_la==24 or _la==25):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class KeyDownContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def KEYDOWN(self):
            return self.getToken(MacroParser.KEYDOWN, 0)

        def keyName(self):
            return self.getTypedRuleContext(MacroParser.KeyNameContext,0)


        def getRuleIndex(self):
            return MacroParser.RULE_keyDown

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitKeyDown" ):
                return visitor.visitKeyDown(self)
            else:
                return visitor.visitChildren(self)




    def keyDown(self):

        localctx = MacroParser.KeyDownContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_keyDown)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 129
            self.match(MacroParser.KEYDOWN)
            self.state = 130
            self.keyName()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class KeyUpContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def KEYUP(self):
            return self.getToken(MacroParser.KEYUP, 0)

        def keyName(self):
            return self.getTypedRuleContext(MacroParser.KeyNameContext,0)


        def getRuleIndex(self):
            return MacroParser.RULE_keyUp

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitKeyUp" ):
                return visitor.visitKeyUp(self)
            else:
                return visitor.visitChildren(self)




    def keyUp(self):

        localctx = MacroParser.KeyUpContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_keyUp)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 132
            self.match(MacroParser.KEYUP)
            self.state = 133
            self.keyName()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WaitContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.ms = None # Token

        def WAIT(self):
            return self.getToken(MacroParser.WAIT, 0)

        def NUMBER(self):
            return self.getToken(MacroParser.NUMBER, 0)

        def getRuleIndex(self):
            return MacroParser.RULE_wait

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWait" ):
                return visitor.visitWait(self)
            else:
                return visitor.visitChildren(self)




    def wait(self):

        localctx = MacroParser.WaitContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_wait)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 135
            self.match(MacroParser.WAIT)
            self.state = 136
            localctx.ms = self.match(MacroParser.NUMBER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





