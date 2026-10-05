/*
 * MacroParser.g4 — parser for the FloorPlanner input-macro language.
 * Requires MacroLexer.g4.
 */
parser grammar MacroParser;

options { tokenVocab = MacroLexer; }

// A macro is a sequence of lines. Blank and comment-only lines are
// permitted anywhere (comments are skipped by the lexer).
macro
    : ( line? NL )* line? EOF
    ;

// [tool letter] [command]
line
    : toolSelect command?
    | command
    ;

toolSelect
    : TOOL
    ;

command
    : mouseChain
    | move
    | wheel
    | typeText
    | keyPress
    | keyDown
    | keyUp
    | wait
    | appCommand
    ;

// ---- Mouse ----------------------------------------------------------

// Press at the head point, optional drag segments, release at the end.
mouseChain
    : modifiers? clickVerb point dragSegment*
    ;

clickVerb
    : CLICK | RCLICK | MCLICK | DCLICK | XCLICK1 | XCLICK2
    ;

dragSegment
    : modifiers? DRAG point
    ;

move
    : modifiers? MOVE point
    ;

wheel
    : modifiers? WHEEL dx=NUMBER dy=NUMBER
    ;

modifiers
    : MOD+
    ;

point
    : x=NUMBER y=NUMBER
    ;

// ---- Keyboard -------------------------------------------------------

typeText
    : TYPE TEXT?
    ;

keyPress
    : KEY keyStroke+
    ;

keyStroke
    : KMOD* keyName
    ;

keyName
    : KCHAR
    | KNAMED
    ;

keyDown
    : KEYDOWN keyName
    ;

keyUp
    : KEYUP keyName
    ;

// ---- Timing ---------------------------------------------------------

wait
    : WAIT ms=NUMBER
    ;

// ---- Application commands (spec sec 14) -----------------------------

// @NAME arg arg ...  -- the application acts directly; no input is simulated.
appCommand
    : APPCMD appArg*
    ;

appArg
    : ASTRING
    | AWORD
    ;
