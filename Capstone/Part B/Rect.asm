
// Draws a rectangle at the top-left corner of the screen.
// The height is stored in RAM[0].

@R0
D=M
@INFINITE_LOOP
D;JLE

@SCREEN
D=A
@addr
M=D

@R0
D=M
@n
M=D

(LOOP)
@n
D=M
@END
D;JEQ

@addr
A=M
M=-1

@addr
D=M
@32
D=D+A
@addr
M=D

@n
M=M-1
@LOOP
0;JMP

(END)
@END
0;JMP

(INFINITE_LOOP)
@INFINITE_LOOP
0;JMP
