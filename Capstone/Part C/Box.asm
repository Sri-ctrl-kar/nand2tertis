
// NAND2TETRIS CAPSTONE - PART C
// K = 47
// Box: 64 pixels wide, 20 rows tall
// Starting screen address = 17888

(START)
    // Check keyboard
    @KBD
    D=M
    @BLACK
    D;JGT

    // No key pressed: draw white
    @VALUE
    M=0
    @DRAW
    0;JMP

(BLACK)
    // Key pressed: draw black
    @VALUE
    M=-1

(DRAW)
    // Starting address: SCREEN + 32*47 = 17888
    @17888
    D=A
    @ADDR
    M=D

    // 20 rows
    @20
    D=A
    @ROWS
    M=D

(ROW_LOOP)
    // Four words = 64 pixels
    @4
    D=A
    @COLS
    M=D

(COL_LOOP)
    // Write black or white
    @VALUE
    D=M
    @ADDR
    A=M
    M=D

    // Move to next screen word
    @ADDR
    M=M+1

    // Decrease column counter
    @COLS
    M=M-1
    D=M
    @COL_LOOP
    D;JGT

    // Skip remaining 28 words to next screen row
    @28
    D=A
    @ADDR
    M=D+M

    // Decrease row counter
    @ROWS
    M=M-1
    D=M
    @ROW_LOOP
    D;JGT

    // Check keyboard again
    @START
    0;JMP
