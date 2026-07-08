; =============================================================================
;  raycaster.asm  -  A textured-look raycaster maze for 64-bit Windows.
;
;  Hand-written x86-64 assembly, NASM/Intel syntax, NO C runtime.
;  Renders a Wolfenstein-style pseudo-3D maze into a software framebuffer
;  using the DDA grid-marching algorithm, then blits it with StretchDIBits.
;  The whole "engine" is the per-column inner loop below - which is exactly
;  why tight code shows up directly as a huge FPS number.
;
;  Controls:  W / Up      forward
;             S / Down     backward
;             A / Left     turn left
;             D / Right    turn right
;             Q            strafe left
;             E            strafe right
;             ESC          quit
;
;  Build (Windows, GoLink):   see build.bat
;  Build (Linux cross):       see build.sh
; =============================================================================

bits 64
default rel

; ----- tunables --------------------------------------------------------------
%define RENDER_W 320            ; internal render width  (fewer pixels = faster)
%define RENDER_H 200            ; internal render height
%define WIN_W    960            ; window client width  (framebuffer is stretched)
%define WIN_H    600            ; window client height
%define CENTER_Y (RENDER_H/2)

; ----- Win32 imports ---------------------------------------------------------
extern GetModuleHandleA
extern QueryPerformanceCounter
extern QueryPerformanceFrequency
extern ExitProcess
extern LoadCursorA
extern RegisterClassExA
extern CreateWindowExA
extern DefWindowProcA
extern DestroyWindow
extern PostQuitMessage
extern PeekMessageA
extern TranslateMessage
extern DispatchMessageA
extern GetAsyncKeyState
extern GetDC
extern GetClientRect
extern SetWindowTextA
extern ShowWindow
extern StretchDIBits
extern SetStretchBltMode

global start

; =============================================================================
section .text
; =============================================================================

; ------------------------------------------------------------------ WndProc --
; LRESULT WndProc(HWND rcx, UINT edx=msg, WPARAM r8, LPARAM r9)
WndProc:
    sub     rsp, 0x28                   ; shadow space + 16-align
    cmp     edx, 0x0002                 ; WM_DESTROY
    je      .destroy
    cmp     edx, 0x0010                 ; WM_CLOSE
    je      .close
    call    DefWindowProcA              ; args already in rcx/rdx/r8/r9
    add     rsp, 0x28
    ret
.destroy:
    xor     ecx, ecx
    call    PostQuitMessage
    xor     eax, eax
    add     rsp, 0x28
    ret
.close:
    call    DestroyWindow               ; hwnd already in rcx
    xor     eax, eax
    add     rsp, 0x28
    ret

; -------------------------------------------------------------------- start --
start:
    push    rbp
    mov     rbp, rsp
    sub     rsp, 0x100                  ; frame: shadow + stack args (16-aligned)

    ; --- hInstance ---
    xor     ecx, ecx
    call    GetModuleHandleA
    mov     [hInst], rax

    ; --- fill WNDCLASSEXA ---
    mov     dword [wc+0],  80           ; cbSize
    mov     dword [wc+4],  0x0023       ; CS_HREDRAW|CS_VREDRAW|CS_OWNDC
    lea     rax, [WndProc]
    mov     [wc+8],  rax                ; lpfnWndProc
    mov     dword [wc+16], 0            ; cbClsExtra
    mov     dword [wc+20], 0            ; cbWndExtra
    mov     rax, [hInst]
    mov     [wc+24], rax                ; hInstance
    mov     qword [wc+32], 0            ; hIcon
    xor     ecx, ecx
    mov     edx, 32512                  ; IDC_ARROW
    call    LoadCursorA
    mov     [wc+40], rax                ; hCursor
    mov     qword [wc+48], 0            ; hbrBackground (we paint every pixel)
    mov     qword [wc+56], 0            ; lpszMenuName
    lea     rax, [className]
    mov     [wc+64], rax                ; lpszClassName
    mov     qword [wc+72], 0            ; hIconSm

    lea     rcx, [wc]
    call    RegisterClassExA

    ; --- CreateWindowExA ---
    xor     ecx, ecx                    ; dwExStyle
    lea     rdx, [className]
    lea     r8,  [title]
    mov     r9d, 0x10CF0000             ; WS_OVERLAPPEDWINDOW | WS_VISIBLE
    mov     r10d, 0x80000000            ; CW_USEDEFAULT (zero-extended)
    mov     [rsp+0x20], r10             ; X
    mov     [rsp+0x28], r10             ; Y
    mov     qword [rsp+0x30], WIN_W
    mov     qword [rsp+0x38], WIN_H
    mov     qword [rsp+0x40], 0         ; parent
    mov     qword [rsp+0x48], 0         ; menu
    mov     rax, [hInst]
    mov     [rsp+0x50], rax             ; hInstance
    mov     qword [rsp+0x58], 0         ; lpParam
    call    CreateWindowExA
    mov     [hwnd], rax

    ; --- device context (CS_OWNDC => persistent, fetch once) ---
    mov     rcx, [hwnd]
    call    GetDC
    mov     [hdc], rax

    mov     rcx, [hdc]
    mov     edx, 3                      ; COLORONCOLOR (clean nearest-neighbour scale)
    call    SetStretchBltMode

    mov     rcx, [hwnd]
    mov     edx, 5                      ; SW_SHOW
    call    ShowWindow

    ; --- timing init ---
    lea     rcx, [freq]
    call    QueryPerformanceFrequency
    lea     rcx, [qpc_last]
    call    QueryPerformanceCounter
    mov     rax, [qpc_last]
    mov     [fps_last], rax
    mov     dword [frames], 0

; ------------------------------------------------------------- main loop -----
.frame:
    ; ----- drain the message queue -----
.pump:
    lea     rcx, [msg]
    xor     edx, edx
    xor     r8d, r8d
    xor     r9d, r9d
    mov     qword [rsp+0x20], 1         ; PM_REMOVE
    call    PeekMessageA
    test    eax, eax
    jz      .no_msg
    cmp     dword [msg+8], 0x0012       ; WM_QUIT
    je      .exit
    lea     rcx, [msg]
    call    TranslateMessage
    lea     rcx, [msg]
    call    DispatchMessageA
    jmp     .pump
.no_msg:

    ; ----- delta time -----
    lea     rcx, [qpc_now]
    call    QueryPerformanceCounter
    mov     rax, [qpc_now]
    sub     rax, [qpc_last]
    mov     rcx, [qpc_now]
    mov     [qpc_last], rcx
    cvtsi2sd xmm0, rax
    mov     rax, [freq]
    cvtsi2sd xmm1, rax
    divsd   xmm0, xmm1                  ; dt = counts/freq  (seconds)
    comisd  xmm0, [d_dtmax]
    jbe     .dtok
    movsd   xmm0, [d_dtmax]            ; clamp huge first-frame dt
.dtok:
    movsd   [frameDt], xmm0
    movsd   xmm1, [moveSpeedC]
    mulsd   xmm1, xmm0
    movsd   [moveStep], xmm1           ; moveStep = speed*dt
    movsd   xmm1, [rotSpeedC]
    mulsd   xmm1, xmm0
    movsd   [rotStep], xmm1            ; rotStep  = rot*dt

    ; ----- input -----
    mov     ecx, 0x1B                   ; ESC
    call    GetAsyncKeyState
    test    ax, 0x8000
    jnz     .exit

    mov     ecx, 0x57                   ; 'W'
    call    GetAsyncKeyState
    test    ax, 0x8000
    jnz     .go_fwd
    mov     ecx, 0x26                   ; VK_UP
    call    GetAsyncKeyState
    test    ax, 0x8000
    jz      .no_fwd
.go_fwd:
    ; posX += dirX*moveStep ; posY += dirY*moveStep  (per-axis => wall slide)
    movsd   xmm0, [dirX]
    mulsd   xmm0, [moveStep]
    addsd   xmm0, [posX]
    call    move_x
    movsd   xmm0, [dirY]
    mulsd   xmm0, [moveStep]
    addsd   xmm0, [posY]
    call    move_y
.no_fwd:

    mov     ecx, 0x53                   ; 'S'
    call    GetAsyncKeyState
    test    ax, 0x8000
    jnz     .go_back
    mov     ecx, 0x28                   ; VK_DOWN
    call    GetAsyncKeyState
    test    ax, 0x8000
    jz      .no_back
.go_back:
    movsd   xmm0, [dirX]
    mulsd   xmm0, [moveStep]
    movsd   xmm1, [neg_mask]
    xorpd   xmm0, xmm1                  ; -dirX*step
    addsd   xmm0, [posX]
    call    move_x
    movsd   xmm0, [dirY]
    mulsd   xmm0, [moveStep]
    movsd   xmm1, [neg_mask]
    xorpd   xmm0, xmm1
    addsd   xmm0, [posY]
    call    move_y
.no_back:

    mov     ecx, 0x41                   ; 'A'
    call    GetAsyncKeyState
    test    ax, 0x8000
    jnz     .go_left
    mov     ecx, 0x25                   ; VK_LEFT
    call    GetAsyncKeyState
    test    ax, 0x8000
    jz      .no_left
.go_left:
    movsd   xmm0, [rotStep]             ; +angle
    call    rotate
.no_left:

    mov     ecx, 0x44                   ; 'D'
    call    GetAsyncKeyState
    test    ax, 0x8000
    jnz     .go_right
    mov     ecx, 0x27                   ; VK_RIGHT
    call    GetAsyncKeyState
    test    ax, 0x8000
    jz      .no_right
.go_right:
    movsd   xmm0, [rotStep]
    movsd   xmm1, [neg_mask]
    xorpd   xmm0, xmm1                  ; -angle
    call    rotate
.no_right:

    mov     ecx, 0x51                   ; 'Q' strafe left  => pos += (-dirY,+dirX)*step
    call    GetAsyncKeyState
    test    ax, 0x8000
    jz      .no_sl
    movsd   xmm0, [dirY]
    mulsd   xmm0, [moveStep]
    movsd   xmm1, [neg_mask]
    xorpd   xmm0, xmm1
    addsd   xmm0, [posX]
    call    move_x
    movsd   xmm0, [dirX]
    mulsd   xmm0, [moveStep]
    addsd   xmm0, [posY]
    call    move_y
.no_sl:

    mov     ecx, 0x45                   ; 'E' strafe right => pos += (+dirY,-dirX)*step
    call    GetAsyncKeyState
    test    ax, 0x8000
    jz      .no_sr
    movsd   xmm0, [dirY]
    mulsd   xmm0, [moveStep]
    addsd   xmm0, [posX]
    call    move_x
    movsd   xmm0, [dirX]
    mulsd   xmm0, [moveStep]
    movsd   xmm1, [neg_mask]
    xorpd   xmm0, xmm1
    addsd   xmm0, [posY]
    call    move_y
.no_sr:

    ; ----- render one frame into the framebuffer -----
    call    render

    ; ----- blit framebuffer -> window, scaled to the client rect -----
    mov     rcx, [hwnd]
    lea     rdx, [crect]
    call    GetClientRect
    mov     eax, [crect+8]
    sub     eax, [crect+0]              ; client width
    mov     r10d, eax
    mov     ecx, [crect+12]
    sub     ecx, [crect+4]             ; client height
    mov     r11d, ecx
    test    r10d, r10d
    jle     .skipblit
    test    r11d, r11d
    jle     .skipblit
    mov     rcx, [hdc]
    xor     edx, edx                    ; xDest
    xor     r8d, r8d                    ; yDest
    mov     r9d, r10d                   ; DestWidth
    mov     [rsp+0x20], r11            ; DestHeight
    mov     qword [rsp+0x28], 0         ; xSrc
    mov     qword [rsp+0x30], 0         ; ySrc
    mov     qword [rsp+0x38], RENDER_W  ; SrcWidth
    mov     qword [rsp+0x40], RENDER_H  ; SrcHeight
    lea     rax, [framebuffer]
    mov     [rsp+0x48], rax             ; lpBits
    lea     rax, [bmi]
    mov     [rsp+0x50], rax             ; BITMAPINFO
    mov     qword [rsp+0x58], 0         ; DIB_RGB_COLORS
    mov     qword [rsp+0x60], 0x00CC0020 ; SRCCOPY
    call    StretchDIBits
.skipblit:

    ; ----- FPS counter in the title bar (once/second) -----
    inc     dword [frames]
    mov     rax, [qpc_now]
    sub     rax, [fps_last]
    cmp     rax, [freq]
    jl      .no_fps
    mov     eax, [frames]
    call    build_title
    mov     rcx, [hwnd]
    lea     rdx, [titlebuf]
    call    SetWindowTextA
    mov     dword [frames], 0
    mov     rax, [qpc_now]
    mov     [fps_last], rax
.no_fps:

    jmp     .frame

.exit:
    xor     ecx, ecx
    call    ExitProcess

; ------------------------------------------------------------------- render --
; Draw the whole scene into `framebuffer`.  Reads player state from memory.
; Owns every register (caller reloads state from memory afterwards).
render:
    movsd   xmm9,  [abs_mask]           ; xmm9 = |x| bitmask (low 64)
    movsd   xmm10, [posX]
    movsd   xmm11, [posY]
    movsd   xmm12, [dirX]
    movsd   xmm13, [dirY]
    movsd   xmm14, [planeX]
    movsd   xmm15, [planeY]
    xor     ebx, ebx                    ; ebx = screen column x

.col_loop:
    ; cameraX = 2*x/W - 1
    cvtsi2sd xmm0, ebx
    mulsd   xmm0, [d_2]
    divsd   xmm0, [d_W]
    subsd   xmm0, [d_1]                 ; xmm0 = cameraX

    ; rayDir = dir + plane*cameraX
    movsd   xmm1, xmm14
    mulsd   xmm1, xmm0
    addsd   xmm1, xmm12                 ; xmm1 = rayDirX
    movsd   xmm2, xmm15
    mulsd   xmm2, xmm0
    addsd   xmm2, xmm13                 ; xmm2 = rayDirY

    ; deltaDist = |1/rayDir|   (rayDir==0 -> +inf, harmless)
    movsd   xmm3, [d_1]
    divsd   xmm3, xmm1
    andpd   xmm3, xmm9                  ; xmm3 = deltaDistX
    movsd   xmm4, [d_1]
    divsd   xmm4, xmm2
    andpd   xmm4, xmm9                  ; xmm4 = deltaDistY

    ; mapX/mapY = int(pos)
    cvttsd2si r8d, xmm10                ; r8d = mapX
    cvttsd2si r9d, xmm11                ; r9d = mapY

    ; --- step + initial sideDist, X axis ---
    xorpd   xmm5, xmm5
    comisd  xmm1, xmm5
    jb      .rx_neg
    mov     r10d, 1                     ; stepX = +1
    cvtsi2sd xmm6, r8d
    addsd   xmm6, [d_1]
    subsd   xmm6, xmm10                 ; (mapX+1 - posX)
    mulsd   xmm6, xmm3                  ; * deltaDistX = sideDistX
    jmp     .rx_done
.rx_neg:
    mov     r10d, -1                    ; stepX = -1
    cvtsi2sd xmm6, r8d
    movsd   xmm7, xmm10
    subsd   xmm7, xmm6                  ; (posX - mapX)
    mulsd   xmm7, xmm3
    movsd   xmm6, xmm7                  ; sideDistX
.rx_done:

    ; --- step + initial sideDist, Y axis ---
    comisd  xmm2, xmm5
    jb      .ry_neg
    mov     r11d, 1                     ; stepY = +1
    cvtsi2sd xmm7, r9d
    addsd   xmm7, [d_1]
    subsd   xmm7, xmm11
    mulsd   xmm7, xmm4                  ; sideDistY
    jmp     .ry_done
.ry_neg:
    mov     r11d, -1                    ; stepY = -1
    cvtsi2sd xmm8, r9d
    movsd   xmm7, xmm11
    subsd   xmm7, xmm8
    mulsd   xmm7, xmm4
.ry_done:
    ; xmm6=sideDistX  xmm7=sideDistY  xmm3=deltaDistX  xmm4=deltaDistY

    ; --- DDA march ---
    lea     rsi, [map]
.dda:
    comisd  xmm6, xmm7
    jb      .stepx
    addsd   xmm7, xmm4                  ; sideDistY += deltaDistY
    add     r9d, r11d                   ; mapY += stepY
    mov     r13d, 1                     ; side = 1 (y side)
    jmp     .checkhit
.stepx:
    addsd   xmm6, xmm3                  ; sideDistX += deltaDistX
    add     r8d, r10d                   ; mapX += stepX
    xor     r13d, r13d                  ; side = 0 (x side)
.checkhit:
    mov     eax, r9d
    shl     eax, 4                      ; mapY*16
    add     eax, r8d
    movzx   r15d, byte [rsi+rax]        ; cell value
    test    r15d, r15d
    jz      .dda                        ; empty => keep marching

    ; --- perpendicular wall distance ---
    test    r13d, r13d
    jnz     .perp_y
    movsd   xmm0, xmm6
    subsd   xmm0, xmm3                  ; sideDistX - deltaDistX
    jmp     .perp_ok
.perp_y:
    movsd   xmm0, xmm7
    subsd   xmm0, xmm4
.perp_ok:
    comisd  xmm0, [d_min]
    jae     .perp_have
    movsd   xmm0, [d_min]               ; guard against divide-by-~0
.perp_have:
    ; xmm0 = perpWallDist

    ; --- wall strip extents ---
    movsd   xmm1, [d_H]
    divsd   xmm1, xmm0
    cvttsd2si eax, xmm1                 ; lineHeight
    mov     ecx, eax
    sar     ecx, 1                      ; half = lineHeight/2
    mov     esi, CENTER_Y
    sub     esi, ecx                    ; drawStart
    test    esi, esi
    jns     .s_ok
    xor     esi, esi
.s_ok:
    mov     edx, CENTER_Y
    add     edx, ecx                    ; drawEnd
    cmp     edx, RENDER_H
    jle     .e_ok
    mov     edx, RENDER_H
.e_ok:
    mov     [d_start], esi
    mov     [d_end],   edx

    ; --- distance shading:  shade256 = clamp(1 - dist/D, minShade, 1) * 256 ---
    movsd   xmm1, xmm0
    divsd   xmm1, [d_shadeDist]
    movsd   xmm2, [d_1]
    subsd   xmm2, xmm1
    comisd  xmm2, [d_shadeMin]
    jae     .sh1
    movsd   xmm2, [d_shadeMin]
.sh1:
    comisd  xmm2, [d_1]
    jbe     .sh2
    movsd   xmm2, [d_1]
.sh2:
    mulsd   xmm2, [d_256]
    cvttsd2si r14d, xmm2                ; r14d = shade (0..256)
    test    r13d, r13d
    jz      .noside
    sar     r14d, 1                     ; y-facing walls are darker
.noside:

    ; --- wall colour = palette[cell] * shade ---
    lea     rsi, [palette]
    mov     eax, [rsi+r15*4]            ; 0x00RRGGBB
    mov     ecx, eax
    shr     ecx, 16
    and     ecx, 0xFF                   ; R
    imul    ecx, r14d
    shr     ecx, 8
    mov     edx, eax
    shr     edx, 8
    and     edx, 0xFF                   ; G
    imul    edx, r14d
    shr     edx, 8
    mov     r8d, eax
    and     r8d, 0xFF                   ; B
    imul    r8d, r14d
    shr     r8d, 8
    shl     ecx, 16
    shl     edx, 8
    or      ecx, edx
    or      ecx, r8d
    mov     [wallColor], ecx

    ; --- paint the column: ceiling | wall | floor ---
    lea     rdi, [framebuffer]
    mov     eax, ebx
    lea     rdi, [rdi+rax*4]            ; &framebuffer[0][x]
    xor     ecx, ecx                    ; y = 0
    mov     edx, [d_start]
    mov     eax, [ceilColor]
.ceil:
    cmp     ecx, edx
    jge     .ceildone
    mov     [rdi], eax
    add     rdi, RENDER_W*4
    inc     ecx
    jmp     .ceil
.ceildone:
    mov     edx, [d_end]
    mov     eax, [wallColor]
.wall:
    cmp     ecx, edx
    jge     .walldone
    mov     [rdi], eax
    add     rdi, RENDER_W*4
    inc     ecx
    jmp     .wall
.walldone:
    mov     edx, RENDER_H
    mov     eax, [floorColor]
.floor:
    cmp     ecx, edx
    jge     .coldone
    mov     [rdi], eax
    add     rdi, RENDER_W*4
    inc     ecx
    jmp     .floor
.coldone:
    inc     ebx
    cmp     ebx, RENDER_W
    jl      .col_loop
    ret

; ------------------------------------------------------------------ move_x ---
; xmm0 = candidate posX ; commit if the target cell is empty.
move_x:
    cvttsd2si eax, xmm0
    movsd   xmm1, [posY]
    cvttsd2si ecx, xmm1
    shl     ecx, 4
    add     eax, ecx
    lea     rsi, [map]
    movzx   edx, byte [rsi+rax]
    test    edx, edx
    jnz     .blocked
    movsd   [posX], xmm0
.blocked:
    ret

; ------------------------------------------------------------------ move_y ---
move_y:
    cvttsd2si ecx, xmm0                 ; int(candidate Y)
    movsd   xmm1, [posX]
    cvttsd2si eax, xmm1                 ; int(posX)
    shl     ecx, 4
    add     eax, ecx
    lea     rsi, [map]
    movzx   edx, byte [rsi+rax]
    test    edx, edx
    jnz     .blocked
    movsd   [posY], xmm0
.blocked:
    ret

; ------------------------------------------------------------------ rotate ---
; xmm0 = angle (radians).  Rotate (dir) and (plane) by it.
rotate:
    movsd   [tmp_angle], xmm0
    fld     qword [tmp_angle]
    fsincos                             ; ST0=cos, ST1=sin
    fstp    qword [c_cos]
    fstp    qword [c_sin]
    movsd   xmm1, [c_cos]
    movsd   xmm2, [c_sin]
    ; dir
    movsd   xmm3, [dirX]
    movsd   xmm4, [dirY]
    movsd   xmm5, xmm3
    mulsd   xmm5, xmm1
    movsd   xmm6, xmm4
    mulsd   xmm6, xmm2
    subsd   xmm5, xmm6                  ; dirX*cos - dirY*sin
    movsd   xmm6, xmm3
    mulsd   xmm6, xmm2
    movsd   xmm7, xmm4
    mulsd   xmm7, xmm1
    addsd   xmm6, xmm7                  ; dirX*sin + dirY*cos
    movsd   [dirX], xmm5
    movsd   [dirY], xmm6
    ; plane
    movsd   xmm3, [planeX]
    movsd   xmm4, [planeY]
    movsd   xmm5, xmm3
    mulsd   xmm5, xmm1
    movsd   xmm6, xmm4
    mulsd   xmm6, xmm2
    subsd   xmm5, xmm6
    movsd   xmm6, xmm3
    mulsd   xmm6, xmm2
    movsd   xmm7, xmm4
    mulsd   xmm7, xmm1
    addsd   xmm6, xmm7
    movsd   [planeX], xmm5
    movsd   [planeY], xmm6
    ret

; -------------------------------------------------------------- build_title --
; eax = fps.  Builds  titlebuf = title_pre + itoa(fps) + title_suf
build_title:
    push    rbx
    mov     ebx, eax                    ; save fps
    lea     rdi, [titlebuf]
    lea     rsi, [title_pre]
.cp1:
    mov     cl, [rsi]
    test    cl, cl
    jz      .cp1done
    mov     [rdi], cl
    inc     rsi
    inc     rdi
    jmp     .cp1
.cp1done:
    ; itoa(ebx) -> rdi
    mov     eax, ebx
    test    eax, eax
    jnz     .nz
    mov     byte [rdi], '0'
    inc     rdi
    jmp     .num_done
.nz:
    lea     r8, [numbuf+16]             ; fill backwards
    mov     r9d, 10
.divloop:
    xor     edx, edx
    div     r9d                         ; edx:eax / 10
    add     dl, '0'
    dec     r8
    mov     [r8], dl
    test    eax, eax
    jnz     .divloop
    lea     r10, [numbuf+16]
.cpnum:
    cmp     r8, r10
    jae     .num_done
    mov     al, [r8]
    mov     [rdi], al
    inc     rdi
    inc     r8
    jmp     .cpnum
.num_done:
    lea     rsi, [title_suf]
.cp2:
    mov     cl, [rsi]
    mov     [rdi], cl
    test    cl, cl
    jz      .cp2done
    inc     rsi
    inc     rdi
    jmp     .cp2
.cp2done:
    pop     rbx
    ret

; =============================================================================
section .data
; =============================================================================
align 8
; --- player state (writable) ---
posX      dq 11.5
posY      dq 11.5
dirX      dq -0.7071
dirY      dq -0.7071
planeX    dq -0.4667
planeY    dq 0.4667

; --- math constants ---
d_2         dq 2.0
d_1         dq 1.0
d_W         dq 320.0                    ; == RENDER_W
d_H         dq 200.0                    ; == RENDER_H
d_min       dq 0.0001
d_shadeDist dq 11.0
d_shadeMin  dq 0.25
d_256       dq 256.0
d_dtmax     dq 0.1
moveSpeedC  dq 3.4                      ; world units / second
rotSpeedC   dq 2.4                      ; radians / second
abs_mask    dq 0x7FFFFFFFFFFFFFFF
neg_mask    dq 0x8000000000000000

; --- colours ---
ceilColor   dd 0x00303048
floorColor  dd 0x00232320
palette      dd 0x00000000, 0x00C83C3C, 0x0038C850, 0x00466EDC, 0x00C8C8C8, 0x00DCBE3C

; --- strings ---
className   db "RaycastWnd", 0
title       db "Raycaster (x86-64 asm) - initializing...", 0
title_pre   db "Raycaster (x86-64 asm)   |   FPS: ", 0
title_suf   db "   |   WASD/QE move, A/D or arrows turn, ESC quit", 0

; --- BITMAPINFO (top-down 32bpp) ---
align 4
bmi:
    dd 40                               ; biSize
    dd RENDER_W                         ; biWidth
    dd -RENDER_H                        ; biHeight (negative => top-down)
    dw 1                                ; biPlanes
    dw 32                               ; biBitCount
    dd 0                                ; biCompression = BI_RGB
    dd 0                                ; biSizeImage
    dd 0                                ; biXPelsPerMeter
    dd 0                                ; biYPelsPerMeter
    dd 0                                ; biClrUsed
    dd 0                                ; biClrImportant

; --- the maze: 16x16, row-major [y*16 + x]; 0=empty, 1..5=wall colours ---
align 4
map:
    db 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
    db 1,0,0,0,0,0,2,0,0,0,0,3,0,0,0,1
    db 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1
    db 1,0,0,4,0,0,0,0,0,0,4,0,0,0,0,1
    db 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1
    db 1,0,0,0,0,5,5,5,0,0,0,0,0,0,0,1
    db 1,0,2,0,0,5,0,5,0,0,0,0,3,0,0,1
    db 1,0,0,0,0,5,0,0,0,0,0,0,0,0,0,1
    db 1,0,0,0,0,5,5,5,0,0,0,0,0,0,0,1
    db 1,0,0,0,0,0,0,0,0,0,0,0,4,0,0,1
    db 1,0,0,4,0,0,0,0,0,0,0,0,0,0,0,1
    db 1,0,0,0,0,0,0,0,2,0,0,0,0,0,0,1
    db 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1
    db 1,0,3,0,0,0,0,0,0,0,0,4,0,0,0,1
    db 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1
    db 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1

; =============================================================================
section .bss
; =============================================================================
align 16
framebuffer resb RENDER_W*RENDER_H*4

align 8
hInst       resq 1
hwnd        resq 1
hdc         resq 1
freq        resq 1
qpc_last    resq 1
qpc_now     resq 1
fps_last    resq 1
frameDt     resq 1
moveStep    resq 1
rotStep     resq 1
tmp_angle   resq 1
c_cos       resq 1
c_sin       resq 1
frames      resd 1
wallColor   resd 1
d_start     resd 1
d_end       resd 1

align 8
wc          resb 80                     ; WNDCLASSEXA
msg         resb 48                     ; MSG
crect       resb 16                     ; RECT
titlebuf    resb 128
numbuf      resb 16
