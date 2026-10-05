/*
 * MacroLexer.g4 — lexer for the FloorPlanner input-macro language.
 *
 * Target-independent: no embedded actions or predicates, so the same
 * grammar generates Python3, Java, C#, JavaScript, C++, Go, etc.
 *
 * Generate (Python):
 *   antlr4 -Dlanguage=Python3 -visitor MacroLexer.g4 MacroParser.g4
 */
lexer grammar MacroLexer;

// ---------------------------------------------------------------------
// DEFAULT mode: tool letters, mouse commands, numbers, modifiers
// ---------------------------------------------------------------------

// Keyboard commands switch modes so that their arguments are not
// tokenized as tool letters, modifiers or numbers.
TYPE    : 'TYPE'    -> pushMode(TEXT_MODE) ;
KEYDOWN : 'KEYDOWN' -> pushMode(KEY_MODE) ;
KEYUP   : 'KEYUP'   -> pushMode(KEY_MODE) ;
KEY     : 'KEY'     -> pushMode(KEY_MODE) ;

// Mouse commands
CLICK   : 'CLICK' ;
RCLICK  : 'RCLICK' ;
MCLICK  : 'MCLICK' ;
DCLICK  : 'DCLICK' ;
XCLICK1 : 'XCLICK1' ;
XCLICK2 : 'XCLICK2' ;
DRAG    : 'DRAG' ;
MOVE    : 'MOVE' ;
WHEEL   : 'WHEEL' ;

// Timing
WAIT    : 'WAIT' ;

// Application command (spec sec 14): '@' and an uppercase name, then its
// arguments to the end of the line. The '@' is what keeps a name such as
// DOOR from being read as the tool letters D O O R. Switches mode so the
// arguments are not tokenized as tool letters, modifiers or numbers.
APPCMD  : '@' [A-Z] [A-Z0-9_]* -> pushMode(ARG_MODE) ;

// Single-letter tool selection (e.g. I = wall, S = select). Keywords
// above win by longest match, so "CLICK" is never read as tool "C".
TOOL    : [A-Z] ;

// Modifier prefixes (AutoHotkey convention): + Shift, ^ Ctrl, ! Alt, # Meta
MOD     : [+^!#] ;

NUMBER  : '-'? DIGIT+ ( '.' DIGIT+ )? ;

NL      : '\r'? '\n' ;
WS      : [ \t]+ -> skip ;
COMMENT : ';' ~[\r\n]* -> skip ;

fragment DIGIT : [0-9] ;

// ---------------------------------------------------------------------
// KEY_MODE: arguments of KEY / KEYDOWN / KEYUP, up to end of line
// ---------------------------------------------------------------------
mode KEY_MODE;

KEY_NL      : '\r'? '\n' -> popMode, type(NL) ;
KEY_WS      : [ \t]+ -> skip ;
KEY_COMMENT : ';' ~[\r\n]* -> skip ;

KMOD        : [+^!#] ;

// {Enter}, {F5}, {Space}, and escaped literals {+} {^} {!} {#} {;} {{} {}}
KNAMED      : '{' ( '}' | ~[}\r\n]+ ) '}' ;

// Any other single character is a key (letters are case-insensitive)
KCHAR       : ~[ \t\r\n{}+^!#;] ;

// ---------------------------------------------------------------------
// TEXT_MODE / TEXT_BODY_MODE: argument of TYPE, taken verbatim
// ---------------------------------------------------------------------
mode TEXT_MODE;

// Exactly one separator space is consumed; any further leading spaces
// belong to the text.
TEXT_SEP    : ' ' -> skip, mode(TEXT_BODY_MODE) ;
TEXT_NL     : '\r'? '\n' -> popMode, type(NL) ;

mode TEXT_BODY_MODE;

TEXT        : ~[\r\n]+ ;
BODY_NL     : '\r'? '\n' -> popMode, type(NL) ;

// ---------------------------------------------------------------------
// ARG_MODE: arguments of an application command, up to end of line
// ---------------------------------------------------------------------
mode ARG_MODE;

ARG_NL      : '\r'? '\n' -> popMode, type(NL) ;
ARG_WS      : [ \t]+ -> skip ;
ARG_COMMENT : ';' ~[\r\n]* -> skip ;

// "Living Room", "plans/my den.json" -- no escapes; cannot contain a quote
ASTRING     : '"' ~["\r\n]* '"' ;

// A bare argument: a name, a number, a path, a feet-inches length (12'6").
// It may CONTAIN a quote but not start with one, and cannot contain ';'.
AWORD       : ~[ \t\r\n";] ~[ \t\r\n;]* ;
