# -*- coding: utf-8 -*-
"""
Gerenciador de Capas e Metadados para MP3
Ferramenta genérica com perfis configuráveis.
Licença: MIT
"""

import os, io, re, json, sys, time, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from difflib import SequenceMatcher
from PIL import Image, ImageGrab, ImageTk
from mutagen.id3 import (ID3, APIC, TIT2, TPE1, TALB, TRCK, TYER, TDRC,
                         TCON, TPOS, ID3NoHeaderError)

try:
    from mutagen.mp3 import MP3
except ImportError:
    MP3 = None

try:
    import musicbrainzngs
    import requests
    ONLINE_OK = True
    musicbrainzngs.set_useragent(
        "GerenciadorCapasMP3", "1.0",
        "https://github.com/Kdu5411/gerenciador-capas-mp3")
except ImportError:
    ONLINE_OK = False

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND = True
except ImportError:
    DND = False

try:
    import pygame
    PLAYER_DISPONIVEL = True
except ImportError:
    PLAYER_DISPONIVEL = False

try:
    from i18n import (T, definir_idioma, idioma_atual,
                      IDIOMAS_DISPONIVEIS, IDIOMA_PADRAO,
                      nome_do_idioma, codigo_do_nome)
    I18N_OK = True
except ImportError:
    I18N_OK = False
    IDIOMAS_DISPONIVEIS = [("pt_BR", "Português (Brasil)")]
    IDIOMA_PADRAO = "pt_BR"

    def T(chave, **kwargs):
        return chave

    def definir_idioma(x):
        pass

    def idioma_atual():
        return "pt_BR"

    def nome_do_idioma(x):
        return x

    def codigo_do_nome(x):
        return "pt_BR"

LADO_PREVIEW = 180
LADO_THUMB = 40
LADO_MINI = 80
ALTURA_LINHA = 44
SEEK_ALTURA = 20

COR_IDLE    = "#666666"
COR_WORKING = "#0066cc"
COR_OK      = "#008800"
COR_ERRO    = "#b00000"
COR_AVISO   = "#cc7000"

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

FONTES_DISPONIVEIS = ["MusicBrainz", "iTunes", "Deezer"]
NOMES_SUSPEITOS = {"", "mp3", "audio", "track", "music", "unknown"}

TAMANHOS_CAPA_UI = [
    "Padrão do perfil",
    "100 x 100", "150 x 150", "200 x 200", "250 x 250",
    "300 x 300", "400 x 400", "500 x 500", "600 x 600",
    "800 x 800", "1000 x 1000",
]

FILTROS_UI = [
    "Mostrar todas",
    "Só sem capa",
    "Só sem artista/título",
    "Só sem álbum",
    "Só sem ano",
    "Só incompletas (qualquer)",
]

# Mapeamento: valor interno PT -> chave i18n
_FILTROS_MAP_I18N = {
    "Mostrar todas": "filtro_mostrar_todas",
    "Só sem capa": "filtro_sem_capa2",
    "Só sem artista/título": "filtro_sem_artista2",
    "Só sem álbum": "filtro_sem_album2",
    "Só sem ano": "filtro_sem_ano2",
    "Só incompletas (qualquer)": "filtro_incompletas2",
}
_TAMANHOS_MAP_I18N = {
    "Padrão do perfil": "tam_padrao",
}


def _filtro_para_display(pt):
    return T(_FILTROS_MAP_I18N.get(pt, pt))


def _display_para_filtro(display):
    for pt, chave in _FILTROS_MAP_I18N.items():
        if T(chave) == display:
            return pt
    return "Mostrar todas"


def _tam_para_display(pt):
    return T(_TAMANHOS_MAP_I18N.get(pt, pt))


def _display_para_tam(display):
    for pt, chave in _TAMANHOS_MAP_I18N.items():
        if T(chave) == display:
            return pt
    return display


_PLAYER_REF = {"player": None}




# # =====================================================================
# BOTOES CANVAS COM ICONES DESENHADOS (zero emoji)
# =====================================================================

_BOTOES_CANVAS = []


def _cores_botao():
    c = C()
    if TEMA["escuro"]:
        return (c["bg"], "#2a2a2a", "#4a4a4a", "#e8e8e8", "#3a3a3a")
    return (c["bg"], "#ffffff", "#c0c0c0", "#1a1a1a", "#e8e8e8")


def _d_player(cv, tipo, cx, cy, cor, r):
    if tipo == "play":
        cv.create_polygon(cx - 5*r, cy - 8*r, cx - 5*r, cy + 8*r,
                          cx + 8*r, cy, fill=cor, outline=cor,
                          tags="icone")
    elif tipo == "pause":
        cv.create_rectangle(cx - 7*r, cy - 8*r, cx - 3*r, cy + 8*r,
                            fill=cor, outline="", tags="icone")
        cv.create_rectangle(cx + 3*r, cy - 8*r, cx + 7*r, cy + 8*r,
                            fill=cor, outline="", tags="icone")
    elif tipo == "stop":
        cv.create_rectangle(cx - 7*r, cy - 7*r, cx + 7*r, cy + 7*r,
                            fill=cor, outline="", tags="icone")
    elif tipo == "anterior":
        cv.create_rectangle(cx - 9*r, cy - 7*r, cx - 6*r, cy + 7*r,
                            fill=cor, outline="", tags="icone")
        cv.create_polygon(cx + 8*r, cy - 7*r, cx + 8*r, cy + 7*r,
                          cx - 4*r, cy, fill=cor, outline=cor,
                          tags="icone")
    elif tipo == "proxima":
        cv.create_polygon(cx - 8*r, cy - 7*r, cx - 8*r, cy + 7*r,
                          cx + 4*r, cy, fill=cor, outline=cor,
                          tags="icone")
        cv.create_rectangle(cx + 6*r, cy - 7*r, cx + 9*r, cy + 7*r,
                            fill=cor, outline="", tags="icone")
    elif tipo == "rewind":
        cv.create_polygon(cx, cy - 7*r, cx, cy + 7*r,
                          cx + 8*r, cy, fill=cor, outline=cor,
                          tags="icone")
        cv.create_polygon(cx - 8*r, cy - 7*r, cx - 8*r, cy + 7*r,
                          cx, cy, fill=cor, outline=cor, tags="icone")
    elif tipo == "forward":
        cv.create_polygon(cx, cy - 7*r, cx, cy + 7*r,
                          cx - 8*r, cy, fill=cor, outline=cor,
                          tags="icone")
        cv.create_polygon(cx + 8*r, cy - 7*r, cx + 8*r, cy + 7*r,
                          cx, cy, fill=cor, outline=cor, tags="icone")


def _d_seta(cv, tipo, cx, cy, cor, r):
    def cima(x, yt, yb):
        cv.create_line(x, yb, x, yt + 3*r, fill=cor,
                       width=max(2, int(2*r)), capstyle="round",
                       tags="icone")
        cv.create_polygon(x - 4*r, yt + 4*r, x + 4*r, yt + 4*r,
                          x, yt - 2*r, fill=cor, outline=cor,
                          tags="icone")

    def baixo(x, yt, yb):
        cv.create_line(x, yt, x, yb - 3*r, fill=cor,
                       width=max(2, int(2*r)), capstyle="round",
                       tags="icone")
        cv.create_polygon(x - 4*r, yb - 4*r, x + 4*r, yb - 4*r,
                          x, yb + 2*r, fill=cor, outline=cor,
                          tags="icone")

    if tipo == "subir":
        cima(cx, cy - 8*r, cy + 8*r)
    elif tipo == "descer":
        baixo(cx, cy - 8*r, cy + 8*r)
    elif tipo == "topo":
        cima(cx, cy - 12*r, cy - r)
        cima(cx, cy - r, cy + 10*r)
    elif tipo == "fim":
        baixo(cx, cy - 10*r, cy + r)
        baixo(cx, cy + r, cy + 12*r)


def _d_trash(cv, cx, cy, cor, r):
    w = max(1, int(2*r))
    cv.create_line(cx - 8*r, cy - 6*r, cx + 8*r, cy - 6*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx - 3*r, cy - 6*r, cx - 3*r, cy - 9*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx - 3*r, cy - 9*r, cx + 3*r, cy - 9*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx + 3*r, cy - 9*r, cx + 3*r, cy - 6*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx - 6*r, cy - 6*r, cx - 5*r, cy + 8*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx + 6*r, cy - 6*r, cx + 5*r, cy + 8*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx - 5*r, cy + 8*r, cx + 5*r, cy + 8*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx - 2*r, cy - 2*r, cx - 2*r, cy + 5*r,
                   fill=cor, width=max(1, int(r)), tags="icone")
    cv.create_line(cx + 2*r, cy - 2*r, cx + 2*r, cy + 5*r,
                   fill=cor, width=max(1, int(r)), tags="icone")


def _d_folder(cv, cx, cy, cor, r):
    w = max(1, int(2*r))
    cv.create_line(cx - 9*r, cy - 6*r, cx - 3*r, cy - 6*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx - 3*r, cy - 6*r, cx - r, cy - 3*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx - 9*r, cy - 6*r, cx - 9*r, cy + 8*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx - 9*r, cy + 8*r, cx + 9*r, cy + 8*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx + 9*r, cy + 8*r, cx + 9*r, cy - 3*r,
                   fill=cor, width=w, tags="icone")
    cv.create_line(cx + 9*r, cy - 3*r, cx - r, cy - 3*r,
                   fill=cor, width=w, tags="icone")


def _d_save(cv, cx, cy, cor, r):
    w = max(1, int(2*r))
    cv.create_rectangle(cx - 8*r, cy - 8*r, cx + 8*r, cy + 8*r,
                        outline=cor, width=w, tags="icone")
    cv.create_rectangle(cx - 5*r, cy - 8*r, cx + 3*r, cy - 2*r,
                        fill=cor, outline=cor, tags="icone")
    cv.create_rectangle(cx - 5*r, cy + r, cx + 5*r, cy + 8*r,
                        outline=cor, width=w, tags="icone")


def _d_gear(cv, cx, cy, cor, r):
    import math
    raio = 8 * r
    raio_buraco = 3 * r
    cv.create_oval(cx - raio, cy - raio, cx + raio, cy + raio,
                   outline=cor, width=max(2, int(2*r)),
                   tags="icone")
    for i in range(8):
        ang = i * (math.pi / 4)
        x1 = cx + math.cos(ang) * raio
        y1 = cy + math.sin(ang) * raio
        x2 = cx + math.cos(ang) * (raio + 3*r)
        y2 = cy + math.sin(ang) * (raio + 3*r)
        cv.create_line(x1, y1, x2, y2, fill=cor,
                       width=max(2, int(2.5*r)), capstyle="round",
                       tags="icone")
    cv.create_oval(cx - raio_buraco, cy - raio_buraco,
                   cx + raio_buraco, cy + raio_buraco,
                   outline=cor, width=max(1, int(1.5*r)),
                   tags="icone")


def _d_dispatch(cv, tipo, cx, cy, cor, r):
    if tipo in ("play", "pause", "stop", "anterior", "proxima",
                "rewind", "forward"):
        _d_player(cv, tipo, cx, cy, cor, r)
    elif tipo in ("topo", "subir", "descer", "fim"):
        _d_seta(cv, tipo, cx, cy, cor, r)
    elif tipo == "trash":
        _d_trash(cv, cx, cy, cor, r)
    elif tipo == "folder":
        _d_folder(cv, cx, cy, cor, r)
    elif tipo == "save":
        _d_save(cv, cx, cy, cor, r)
    elif tipo == "gear":
        _d_gear(cv, cx, cy, cor, r)


def criar_botao_canvas(parent, tipo, comando, tooltip_texto="",
                        size=46, lado="left", padx=3):
    bg, circ_bg, circ_border, icon_fg, hover_bg = _cores_botao()
    r = size / 46.0
    centro = size // 2

    frame = tk.Frame(parent, bg=bg)
    if lado == "left":
        frame.pack(side="left", padx=padx)
    elif lado == "right":
        frame.pack(side="right", padx=padx)
    else:
        frame.pack(padx=padx)

    cv = tk.Canvas(frame, width=size, height=size, bg=bg,
                   highlightthickness=0, bd=0, cursor="hand2")
    cv.pack()
    circle_id = cv.create_oval(2, 2, size - 2, size - 2,
                                fill=circ_bg, outline=circ_border, width=1)
    _d_dispatch(cv, tipo, centro, centro, icon_fg, r)

    info = {
        "canvas": cv, "frame": frame, "circle_id": circle_id,
        "tipo": tipo, "size": size, "centro": centro, "r": r,
        "circ_bg": circ_bg, "hover_bg": hover_bg,
    }

    def on_enter(e, _i=info):
        try:
            _i["canvas"].itemconfig(_i["circle_id"],
                                     fill=_i["hover_bg"])
        except Exception:
            pass

    def on_leave(e, _i=info):
        try:
            _i["canvas"].itemconfig(_i["circle_id"],
                                     fill=_i["circ_bg"])
        except Exception:
            pass

    cv.bind("<Button-1>", lambda e: comando())
    cv.bind("<Enter>", on_enter)
    cv.bind("<Leave>", on_leave)

    if tooltip_texto:
        ToolTip(cv, tooltip_texto, atraso=500)

    _BOTOES_CANVAS.append(info)
    return info


def atualizar_botoes_canvas():
    bg, circ_bg, circ_border, icon_fg, hover_bg = _cores_botao()
    for info in list(_BOTOES_CANVAS):
        try:
            cv = info["canvas"]
            cv.config(bg=bg)
            cv.itemconfig(info["circle_id"], fill=circ_bg,
                          outline=circ_border)
            info["circ_bg"] = circ_bg
            info["hover_bg"] = hover_bg
            for item in cv.find_all():
                if item != info["circle_id"]:
                    cv.delete(item)
            _d_dispatch(cv, info["tipo"], info["centro"],
                         info["centro"], icon_fg, info["r"])
        except Exception:
            pass


def criar_botao_seta(parent, direcao, comando, tooltip_texto):
    return criar_botao_canvas(parent, direcao, comando,
                                tooltip_texto, size=46, lado="left",
                                padx=3)


# =====================================================================
# TEMA
# =====================================================================

# TEMA
# =====================================================================
TEMA = {"escuro": False, "auto": False}

PALETA = {
    "claro": {
        "bg": "#f5f5f5", "fg": "#1a1a1a",
        "entry_bg": "#ffffff", "entry_fg": "#1a1a1a",
        "select_bg": "#1a4a7a", "select_fg": "#ffffff",
        "border": "#c0c0c0",
        "button_bg": "#e6e6e6", "button_active": "#d0d0d0",
        "btn_primary": "#1a4a7a", "btn_primary_fg": "#ffffff",
        "btn_primary_hover": "#14406a",
        "btn_danger": "#a02020", "btn_danger_fg": "#ffffff",
        "btn_danger_hover": "#801818",
        "btn_success": "#1a6a2a", "btn_success_fg": "#ffffff",
        "btn_success_hover": "#155020",
        "btn_warning": "#a05818", "btn_warning_fg": "#ffffff",
        "btn_warning_hover": "#804010",
        "trough": "#e0e0e0", "tab_bg": "#e8e8e8", "tab_selected": "#ffffff",
        "heading_bg": "#e1e1e1", "heading_fg": "#1a1a1a",
        "preview_bg": "#dddddd", "preview_fg": "#888888",
        "row_frozen_bg": "#ffe5e5", "row_frozen_fg": "#802020",
        "entry_disabled_bg": "#ececec", "entry_disabled_fg": "#888888",
        "row_match_bg": "#e5f0e5", "row_orphan_bg": "#ffe5e5",
        "seek_bg": "#dcdcdc", "seek_fill": "#1a4a7a",
        "seek_handle": "#1a4a7a", "seek_hover": "#14406a",
    },
    "escuro": {
        "bg": "#1a1a1a", "fg": "#e8e8e8",
        "entry_bg": "#252525", "entry_fg": "#e8e8e8",
        "select_bg": "#7a1a1a", "select_fg": "#ffffff",
        "border": "#404040",
        "button_bg": "#2a2a2a", "button_active": "#3a3a3a",
        "btn_primary": "#8a1a1a", "btn_primary_fg": "#ffffff",
        "btn_primary_hover": "#a02020",
        "btn_danger": "#c02020", "btn_danger_fg": "#ffffff",
        "btn_danger_hover": "#e02828",
        "btn_success": "#1a6a3a", "btn_success_fg": "#ffffff",
        "btn_success_hover": "#20804a",
        "btn_warning": "#a05818", "btn_warning_fg": "#ffffff",
        "btn_warning_hover": "#c06818",
        "trough": "#222222", "tab_bg": "#242424", "tab_selected": "#3a3a3a",
        "heading_bg": "#2a2a2a", "heading_fg": "#e8e8e8",
        "preview_bg": "#2a2a2a", "preview_fg": "#999999",
        "row_frozen_bg": "#3a1a1a", "row_frozen_fg": "#e08080",
        "entry_disabled_bg": "#1e1e1e", "entry_disabled_fg": "#666666",
        "row_match_bg": "#1a2a1a", "row_orphan_bg": "#2a1a1a",
        "seek_bg": "#2a2a2a", "seek_fill": "#c02020",
        "seek_handle": "#e02828", "seek_hover": "#a02020",
    },
}


def C():
    return PALETA["escuro"] if TEMA["escuro"] else PALETA["claro"]


def detectar_tema_sistema():
    try:
        if sys.platform == "win32":
            import winreg
            k = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion"
                r"\Themes\Personalize")
            v, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
            winreg.CloseKey(k)
            return v == 0
    except Exception:
        pass
    return None


def aplicar_tema_global(escuro):
    TEMA["escuro"] = escuro
    c = PALETA["escuro"] if escuro else PALETA["claro"]
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    opts = {
        "TFrame": {"configure": {"background": c["bg"]}},
        "TLabel": {"configure": {"background": c["bg"],
                                  "foreground": c["fg"]}},
        "TLabelframe": {"configure": {
            "background": c["bg"], "foreground": c["fg"],
            "bordercolor": c["border"], "lightcolor": c["bg"],
            "darkcolor": c["bg"], "relief": "solid", "borderwidth": 1}},
        "TLabelframe.Label": {"configure": {
            "background": c["bg"], "foreground": c["fg"]}},
        "TButton": {
            "configure": {"background": c["button_bg"],
                          "foreground": c["fg"],
                          "bordercolor": c["border"],
                          "lightcolor": c["button_bg"],
                          "darkcolor": c["button_bg"],
                          "focuscolor": c["button_bg"]},
            "map": {"background": [("active", c["button_active"]),
                                    ("pressed", c["button_active"]),
                                    ("disabled", c["button_bg"])],
                    "foreground": [("disabled", c["border"])]}},
        "TCheckbutton": {
            "configure": {"background": c["bg"], "foreground": c["fg"],
                          "focuscolor": c["bg"]},
            "map": {"background": [("active", c["bg"])],
                    "foreground": [("disabled", c["border"])]}},
        "TRadiobutton": {
            "configure": {"background": c["bg"], "foreground": c["fg"],
                          "focuscolor": c["bg"]}},
        "TEntry": {"configure": {"fieldbackground": c["entry_bg"],
                                  "foreground": c["entry_fg"],
                                  "insertcolor": c["entry_fg"],
                                  "bordercolor": c["border"],
                                  "lightcolor": c["border"],
                                  "darkcolor": c["border"]}},
        "TCombobox": {
            "configure": {"fieldbackground": c["entry_bg"],
                          "foreground": c["entry_fg"],
                          "background": c["button_bg"],
                          "arrowcolor": c["fg"],
                          "bordercolor": c["border"],
                          "lightcolor": c["border"],
                          "darkcolor": c["border"]},
            "map": {"fieldbackground": [("readonly", c["entry_bg"])],
                    "foreground": [("readonly", c["entry_fg"])],
                    "background": [("readonly", c["button_bg"])]}},
        "TNotebook": {"configure": {"background": c["bg"], "borderwidth": 0}},
        "TNotebook.Tab": {
            "configure": {"background": c["tab_bg"],
                          "foreground": c["fg"],
                          "bordercolor": c["border"],
                          "lightcolor": c["bg"], "darkcolor": c["bg"]},
            "map": {"background": [("selected", c["tab_selected"])]}},
        "Treeview": {
            "configure": {"background": c["entry_bg"],
                          "fieldbackground": c["entry_bg"],
                          "foreground": c["fg"],
                          "bordercolor": c["border"],
                          "lightcolor": c["border"],
                          "darkcolor": c["border"],
                          "rowheight": 26},
            "map": {"background": [("selected", c["select_bg"])],
                    "foreground": [("selected", c["select_fg"])]}},
        "Treeview.Heading": {
            "configure": {"background": c["heading_bg"],
                          "foreground": c["heading_fg"],
                          "bordercolor": c["border"],
                          "lightcolor": c["heading_bg"],
                          "darkcolor": c["heading_bg"]},
            "map": {"background": [("active", c["button_active"])]}},
        "TScrollbar": {
            "configure": {"background": c["button_bg"],
                          "troughcolor": c["trough"],
                          "bordercolor": c["border"],
                          "arrowcolor": c["fg"]},
            "map": {"background": [("active", c["button_active"])]}},
        "TSeparator": {"configure": {"background": c["border"]}},
        "TPanedwindow": {"configure": {"background": c["bg"]}},
        "Primary.TButton": {
            "configure": {"background": c["btn_primary"],
                          "foreground": c["btn_primary_fg"],
                          "lightcolor": c["btn_primary"],
                          "darkcolor": c["btn_primary"],
                          "focuscolor": c["btn_primary"]},
            "map": {"background": [("active", c["btn_primary_hover"]),
                                    ("pressed", c["btn_primary_hover"])]}},
        "Danger.TButton": {
            "configure": {"background": c["btn_danger"],
                          "foreground": c["btn_danger_fg"],
                          "lightcolor": c["btn_danger"],
                          "darkcolor": c["btn_danger"],
                          "focuscolor": c["btn_danger"]},
            "map": {"background": [("active", c["btn_danger_hover"]),
                                    ("pressed", c["btn_danger_hover"])]}},
        "Success.TButton": {
            "configure": {"background": c["btn_success"],
                          "foreground": c["btn_success_fg"],
                          "lightcolor": c["btn_success"],
                          "darkcolor": c["btn_success"],
                          "focuscolor": c["btn_success"]},
            "map": {"background": [("active", c["btn_success_hover"]),
                                    ("pressed", c["btn_success_hover"])]}},
        "Warning.TButton": {
            "configure": {"background": c["btn_warning"],
                          "foreground": c["btn_warning_fg"],
                          "lightcolor": c["btn_warning"],
                          "darkcolor": c["btn_warning"],
                          "focuscolor": c["btn_warning"]},
            "map": {"background": [("active", c["btn_warning_hover"]),
                                    ("pressed", c["btn_warning_hover"])]}},
        "Player.TButton": {
            "configure": {"background": c["button_bg"],
                          "foreground": c["fg"],
                          "lightcolor": c["button_bg"],
                          "darkcolor": c["button_bg"],
                          "focuscolor": c["button_bg"],
                          "padding": 6},
            "map": {"background": [("active", c["button_active"]),
                                    ("pressed", c["button_active"])]}},
    }
    style.theme_settings("clam", opts)


def _aplicar_em_tk(widget, escuro):
    c = PALETA["escuro"] if escuro else PALETA["claro"]
    cls = widget.winfo_class()
    try:
        if cls in ("Frame", "Toplevel", "Tk"):
            widget.configure(bg=c["bg"],
                             highlightbackground=c["border"],
                             highlightcolor=c["border"])
        elif cls == "Label":
            widget.configure(bg=c["bg"], fg=c["fg"])
        elif cls == "Listbox":
            widget.configure(bg=c["entry_bg"], fg=c["entry_fg"],
                             selectbackground=c["select_bg"],
                             selectforeground=c["select_fg"],
                             highlightbackground=c["border"])
        elif cls == "Text":
            widget.configure(bg=c["entry_bg"], fg=c["entry_fg"],
                             insertbackground=c["entry_fg"],
                             selectbackground=c["select_bg"],
                             selectforeground=c["select_fg"],
                             highlightbackground=c["border"])
        elif cls == "Menu":
            widget.configure(bg=c["entry_bg"], fg=c["entry_fg"],
                             activebackground=c["select_bg"],
                             activeforeground=c["select_fg"], bd=0)
        elif cls == "Scrollbar":
            widget.configure(bg=c["button_bg"], troughcolor=c["trough"],
                             activebackground=c["button_active"], bd=0)
        elif cls == "Canvas":
            widget.configure(bg=c["bg"], highlightthickness=0)
    except tk.TclError:
        pass
    for filho in widget.winfo_children():
        _aplicar_em_tk(filho, escuro)


def aplicar_tema_widget(widget):
    escuro = TEMA["escuro"]
    aplicar_tema_global(escuro)
    _aplicar_em_tk(widget, escuro)


# =====================================================================
# ÍCONE
# =====================================================================

def aplicar_tema_janela(jan):
    """Aplica o tema escuro/claro numa janela Toplevel."""
    try:
        c = C()
        jan.configure(bg=c["bg"])
        aplicar_tema_global(TEMA["escuro"])
        _aplicar_em_tk(jan, TEMA["escuro"])
        aplicar_barra_escura_windows(jan, TEMA["escuro"])
    except Exception:
        pass

def aplicar_barra_escura_windows(root, escuro):
    """Aplica o dark mode na barra de titulo do Windows 10+."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        if hwnd == 0:
            hwnd = root.winfo_id()
        value = ctypes.c_int(1 if escuro else 0)
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Win 10 2004+)
        # Fallback pra atributo 19 em versoes antigas
        for attr in (20, 19):
            try:
                res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr,
                    ctypes.byref(value), ctypes.sizeof(value))
                if res == 0:
                    break
            except Exception:
                continue
    except Exception:
        pass

def _caminho_icone_base():
    # 1) Se estiver rodando como .exe (PyInstaller)
    if getattr(sys, "frozen", False):
        # Tenta primeiro ao lado do .exe
        base = os.path.dirname(sys.executable)
        p = os.path.join(base, "icon.png")
        if os.path.exists(p):
            return p
        # PyInstaller 6.x guarda recursos em _MEIPASS/_internal
        if hasattr(sys, "_MEIPASS"):
            p = os.path.join(sys._MEIPASS, "icon.png")
            if os.path.exists(p):
                return p
            # Alguns layouts colocam em _internal subpasta
            p = os.path.join(sys._MEIPASS, "_internal", "icon.png")
            if os.path.exists(p):
                return p
    # 2) Rodando como .py normal
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "icon.png")

def aplicar_icone_janela(root):
    try:
        # 1) Tenta usar o .ico diretamente (melhor qualidade no Windows)
        ico = os.path.splitext(_caminho_icone_base())[0] + ".ico"
        if sys.platform == "win32" and os.path.exists(ico):
            try:
                root.iconbitmap(default=ico)
                return
            except Exception:
                pass
        # 2) Fallback: PhotoImage com PNG redimensionado
        png = _caminho_icone_base()
        if not os.path.exists(png):
            return
        img = Image.open(png)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        # Redimensiona pra tamanho padrão de ícone de janela
        img = img.resize((64, 64), Image.LANCZOS)
        import base64
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = base64.b64encode(buf.getvalue()).decode()
        photo = tk.PhotoImage(data=data)
        root.iconphoto(True, photo)
        root._icon_ref = photo
    except Exception as e:
        print(f"Erro ao aplicar ícone: {e}")


# =====================================================================
# CONFIG
# =====================================================================
def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(_base_dir(), "config.json")
PERFIS_PATH = os.path.join(_base_dir(), "perfis.json")
COVER_SKIP_PATH = os.path.join(_base_dir(), "covers_ignore.json")

CONFIG_DEFAULT = {
    "modo_escuro": False,
    "tema_automatico": True,
    "tamanho_capa_override": "Padrão do perfil",
    "ordem_playlists": [],
    "filtro_atual": "Mostrar todas",
    "pastas_salvas": [],
    "idioma": "pt_BR",
    "janela_geometry": "",
    "janela_zoom": True,
    "primeira_execucao": True,
}


def carregar_config():
    if not os.path.exists(CONFIG_PATH):
        return dict(CONFIG_DEFAULT)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in CONFIG_DEFAULT.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return dict(CONFIG_DEFAULT)


def salvar_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar config: {e}")


def carregar_skip_covers():
    if not os.path.exists(COVER_SKIP_PATH):
        return set()
    try:
        with open(COVER_SKIP_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return set(os.path.normcase(os.path.abspath(p)) for p in dados)
    except Exception:
        return set()


def salvar_skip_covers(conjunto):
    try:
        with open(COVER_SKIP_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted(conjunto), f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar skip covers: {e}")


PERFIS_DEFAULT = {
    "Flip Vita 4G": {
        "descricao": "Feature phone Unisoc (UMS9117). ID3v2.3 UTF-16, "
                     "sem TDRC, capa 250x250, grava ID3v1 tambem.",
        "tag_version": 3, "encoding": 1,
        "keep_frames": ["TIT2", "TPE1", "TALB", "TRCK", "TYER"],
        "cover_size": 250, "cover_quality": 90, "cover_subsampling": 0,
        "cover_progressive": False, "cover_mime": "image/jpeg",
        "cover_type": 3, "write_id3v1": True,
    },
    "Universal (maxima compatibilidade)": {
        "descricao": "Funciona em Android, Windows, TV, caixa de som, "
                     "som automotivo e iPods antigos.",
        "tag_version": 3, "encoding": 1,
        "keep_frames": ["TIT2", "TPE1", "TALB", "TRCK", "TYER", "TCON"],
        "cover_size": 500, "cover_quality": 90, "cover_subsampling": 0,
        "cover_progressive": False, "cover_mime": "image/jpeg",
        "cover_type": 3, "write_id3v1": True,
    },
}


def carregar_perfis():
    if not os.path.exists(PERFIS_PATH):
        salvar_perfis(PERFIS_DEFAULT)
        return {k: dict(v) for k, v in PERFIS_DEFAULT.items()}
    try:
        with open(PERFIS_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for nome, conf in PERFIS_DEFAULT.items():
            if nome not in dados:
                dados[nome] = dict(conf)
        return dados
    except Exception:
        return {k: dict(v) for k, v in PERFIS_DEFAULT.items()}


def salvar_perfis(perfis):
    try:
        with open(PERFIS_PATH, "w", encoding="utf-8") as f:
            json.dump(perfis, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar perfis: {e}")


# =====================================================================
# UTIL
# =====================================================================
def nome_arquivo_suspeito(caminho):
    base = os.path.splitext(os.path.basename(caminho))[0].strip()
    if base.lower() in NOMES_SUSPEITOS:
        return True
    if not re.search(r'\w', base):
        return True
    return False


def sanitizar_nome(txt, fallback="sem-nome"):
    txt = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', txt).strip()
    txt = txt.rstrip(". ")
    return txt or fallback


def pasta_tem_mp3(caminho):
    try:
        for raiz, _dirs, files in os.walk(caminho):
            if any(f.lower().endswith(".mp3") for f in files):
                return True
    except Exception:
        pass
    return False


def similaridade(a, b):
    if not a or not b:
        return 0
    return int(SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100)


def titulo_do_nome(caminho):
    base = os.path.splitext(os.path.basename(caminho))[0]
    base = re.sub(r'^\d+[-_.\s]+', '', base).strip()
    return base or "sem-nome"


def fmt_tempo(seg):
    try:
        seg = int(seg)
    except (TypeError, ValueError):
        return "0:00"
    if seg < 0:
        seg = 0
    m = seg // 60
    s = seg % 60
    return f"{m}:{s:02d}"


def nome_curto_pasta(caminho):
    try:
        base = os.path.basename(os.path.normpath(caminho))
        return base or caminho
    except Exception:
        return caminho


# =====================================================================
# IMAGEM
# =====================================================================
def redimensionar(img, lado):
    w, h = img.size
    m = min(w, h)
    img = img.crop(((w - m) // 2, (h - m) // 2,
                    (w - m) // 2 + m, (h - m) // 2 + m))
    return img.resize((lado, lado), Image.LANCZOS)


def preparar_capa(bytes_img, profile):
    lado = int(profile.get("cover_size", 250))
    qualidade = int(profile.get("cover_quality", 90))
    subsampling = int(profile.get("cover_subsampling", 0))
    progressivo = bool(profile.get("cover_progressive", False))
    img = Image.open(io.BytesIO(bytes_img))
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = redimensionar(img, lado)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=qualidade, progressive=progressivo,
             optimize=False, subsampling=subsampling)
    return buf.getvalue()


def preview_quadrado(bytes_img, lado, cor_fundo=(221, 221, 221)):
    canvas = Image.new("RGB", (lado, lado), cor_fundo)
    if bytes_img:
        try:
            img = Image.open(io.BytesIO(bytes_img))
            img.thumbnail((lado, lado), Image.LANCZOS)
            if img.mode != "RGB":
                img = img.convert("RGB")
            canvas.paste(img, ((lado - img.width) // 2,
                               (lado - img.height) // 2))
        except Exception:
            pass
    return ImageTk.PhotoImage(canvas)


def thumb_pequena(bytes_img):
    canvas = Image.new("RGB", (LADO_THUMB, LADO_THUMB), (200, 200, 200))
    if bytes_img:
        try:
            img = Image.open(io.BytesIO(bytes_img))
            img.thumbnail((LADO_THUMB, LADO_THUMB), Image.LANCZOS)
            if img.mode != "RGB":
                img = img.convert("RGB")
            canvas.paste(img, ((LADO_THUMB - img.width) // 2,
                               (LADO_THUMB - img.height) // 2))
        except Exception:
            pass
    return ImageTk.PhotoImage(canvas)


def thumb_mini(bytes_img, lado=LADO_MINI):
    canvas = Image.new("RGB", (lado, lado), (200, 200, 200))
    if bytes_img:
        try:
            img = Image.open(io.BytesIO(bytes_img))
            img.thumbnail((lado, lado), Image.LANCZOS)
            if img.mode != "RGB":
                img = img.convert("RGB")
            canvas.paste(img, ((lado - img.width) // 2,
                               (lado - img.height) // 2))
        except Exception:
            pass
    return ImageTk.PhotoImage(canvas)


# =====================================================================
# TAGS
# =====================================================================
FRAME_CLASSES = {"TIT2": TIT2, "TPE1": TPE1, "TALB": TALB,
                 "TRCK": TRCK, "TCON": TCON, "TPOS": TPOS}


def ler_info(caminho):
    try:
        tags = ID3(caminho)
    except ID3NoHeaderError:
        return {"rotulo": os.path.basename(caminho), "capa": None,
                "artista": "", "titulo": "", "album": "", "faixa": "",
                "ano": "", "genero": ""}
    artista = str(tags.get("TPE1", "")).strip() if "TPE1" in tags else ""
    titulo = str(tags.get("TIT2", "")).strip() if "TIT2" in tags else ""
    album = str(tags.get("TALB", "")).strip() if "TALB" in tags else ""
    faixa = str(tags.get("TRCK", "")).strip() if "TRCK" in tags else ""
    genero = str(tags.get("TCON", "")).strip() if "TCON" in tags else ""
    ano = ""
    if "TYER" in tags:
        ano = str(tags["TYER"]).strip()
    elif "TDRC" in tags:
        ano = str(tags["TDRC"]).strip()[:4]
    suspeito = nome_arquivo_suspeito(caminho)
    if not artista and not titulo:
        if suspeito:
            rotulo = f"⚠️ (arquivo: {os.path.basename(caminho)})"
        else:
            rotulo = os.path.basename(caminho)
    else:
        a = artista or "(sem artista)"
        t = titulo or "(sem título)"
        rotulo = f"{a} — {t}"
        if suspeito:
            rotulo = "⚠️ " + rotulo
    capa = None
    for a in tags.getall("APIC"):
        if a.type == 3:
            capa = a.data
            break
    if capa is None:
        for a in tags.getall("APIC"):
            capa = a.data
            break
    return {"rotulo": rotulo, "capa": capa, "artista": artista,
            "titulo": titulo, "album": album, "faixa": faixa, "ano": ano,
            "genero": genero}


def _liberar_player_seguro():
    p = _PLAYER_REF.get("player")
    if p is None:
        return
    try:
        p.liberar_total()
    except Exception as e:
        print(f"Erro em liberar_total: {e}")


def _salvar_com_retry(tags, caminho, save_kwargs,
                       tentativas=15, delay=0.3):
    ultimo_erro = None
    for i in range(tentativas):
        try:
            tags.save(caminho, **save_kwargs)
            return True
        except PermissionError as e:
            ultimo_erro = e
            if i == 0:
                _liberar_player_seguro()
            time.sleep(delay)
        except Exception:
            raise
    if ultimo_erro:
        raise ultimo_erro
    return False


def aplicar_completo(caminho, dados, imagem_bytes, profile,
                     ignorar_capa=False):
    try:
        tags = ID3(caminho)
    except ID3NoHeaderError:
        tags = ID3()

    capa_antiga = None
    if ignorar_capa:
        for a in tags.getall("APIC"):
            if a.type == 3:
                capa_antiga = a
                break
        if capa_antiga is None:
            for a in tags.getall("APIC"):
                capa_antiga = a
                break

    tags.delete()

    v2 = int(profile.get("tag_version", 3))
    enc = int(profile.get("encoding", 1))
    keep = set(profile.get("keep_frames", []))
    v1 = 2 if profile.get("write_id3v1", True) else 0

    for frame in ("TIT2", "TPE1", "TALB", "TRCK", "TCON"):
        if frame not in keep:
            continue
        campo = {"TIT2": "titulo", "TPE1": "artista", "TALB": "album",
                 "TRCK": "faixa", "TCON": "genero"}[frame]
        valor = str(dados.get(campo, "")).strip()
        if valor:
            tags.add(FRAME_CLASSES[frame](encoding=enc, text=valor))

    ano = str(dados.get("ano", "")).strip()
    if ano and ano[:4].isdigit():
        if v2 == 3 and "TYER" in keep:
            tags.add(TYER(encoding=0, text=ano[:4]))
        elif v2 >= 4 and "TDRC" in keep:
            tags.add(TDRC(encoding=enc, text=ano[:4]))

    if ignorar_capa and capa_antiga is not None:
        tags.add(capa_antiga)
    elif imagem_bytes:
        nova = preparar_capa(imagem_bytes, profile)
        mime = profile.get("cover_mime", "image/jpeg")
        tipo = int(profile.get("cover_type", 3))
        tags.add(APIC(encoding=0, mime=mime, type=tipo, desc="",
                      data=nova))

    save_kwargs = {"v1": v1, "v2_version": v2}
    pad = profile.get("padding")
    if pad is not None and str(pad) != "":
        try:
            save_kwargs["padding"] = int(pad)
        except Exception:
            pass

    _salvar_com_retry(tags, caminho, save_kwargs)


def normalizar(caminho, profile):
    info = ler_info(caminho)
    aplicar_completo(caminho, info, info["capa"], profile,
                     ignorar_capa=False)
    return True


# =====================================================================
# BUSCA ONLINE
# =====================================================================
def extrair_artistas_mb(artist_credit):
    nomes = []
    for item in artist_credit:
        if isinstance(item, dict):
            art = item.get("artist")
            if isinstance(art, dict):
                nome = art.get("name")
                if nome:
                    nomes.append(nome)
    return nomes


def buscar_release_groups(artista, titulo):
    res = musicbrainzngs.search_release_groups(
        artist=artista, releasegroup=titulo, limit=15)
    return res.get("release-group-list", [])


def buscar_recordings(artista, titulo):
    res = musicbrainzngs.search_recordings(
        artist=artista or "", recording=titulo, limit=15)
    return res.get("recording-list", [])


def url_capa_rg(rg_id, tamanho=500):
    for sufixo in (f"front-{tamanho}", "front"):
        url = f"https://coverartarchive.org/release-group/{rg_id}/{sufixo}"
        try:
            r = requests.get(url, allow_redirects=True, timeout=10)
            if r.status_code == 200 and r.content:
                return r.content
        except Exception:
            pass
    return None


def url_capa_release(release_id, tamanho=500):
    for sufixo in (f"front-{tamanho}", "front"):
        url = f"https://coverartarchive.org/release/{release_id}/{sufixo}"
        try:
            r = requests.get(url, allow_redirects=True, timeout=10)
            if r.status_code == 200 and r.content:
                return r.content
        except Exception:
            pass
    return None


def obter_faixas_rg(rg_id):
    try:
        res = musicbrainzngs.browse_releases(release_group=rg_id, limit=1)
        releases = res.get("release-list", [])
        if not releases:
            return None, []
        release = releases[0]
        release_id = release["id"]
        res2 = musicbrainzngs.get_release_by_id(
            release_id, includes=["recordings"])
        faixas = []
        for medium in res2["release"].get("medium-list", []):
            for track in medium.get("track-list", []):
                pos = track.get("number",
                                 str(track.get("position", "")))
                titulo = track.get("recording", {}).get("title", "")
                faixas.append({"pos": str(pos), "titulo": titulo})
        return release_id, faixas
    except Exception as e:
        print(f"Erro ao obter faixas: {e}")
        return None, []


def obter_faixas_release(release_id):
    try:
        res2 = musicbrainzngs.get_release_by_id(
            release_id, includes=["recordings"])
        faixas = []
        for medium in res2["release"].get("medium-list", []):
            for track in medium.get("track-list", []):
                pos = track.get("number",
                                 str(track.get("position", "")))
                titulo = track.get("recording", {}).get("title", "")
                faixas.append({"pos": str(pos), "titulo": titulo})
        return faixas
    except Exception as e:
        print(f"Erro ao obter faixas: {e}")
        return []


def contar_faixas_rg(rg_id):
    _, faixas = obter_faixas_rg(rg_id)
    return len(faixas) if faixas else None


def buscar_itunes(artista, titulo, limite=10):
    try:
        termo = f"{artista} {titulo}".strip()
        r = requests.get("https://itunes.apple.com/search",
                         params={"term": termo,
                                 "media": "music", "limit": limite},
                         timeout=10)
        if r.status_code == 200:
            return r.json().get("results", [])
    except Exception:
        pass
    return []


def buscar_deezer(artista, titulo):
    try:
        r = requests.get("https://api.deezer.com/search",
                         params={"q": f'artist:"{artista}" track:"{titulo}"'},
                         timeout=10)
        if r.status_code == 200:
            return r.json().get("data", [])
    except Exception:
        pass
    return []


def baixar_bytes(url, timeout=15):
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and r.content:
            return r.content
    except Exception:
        pass
    return None


def buscar_musicbrainz_album(a, t):
    lista = []
    query = f"{a} {t}".strip()
    try:
        for rg in buscar_release_groups(a, t):
            nomes = extrair_artistas_mb(rg.get("artist-credit", []))
            artista_mb = ", ".join(nomes) or a
            album_mb = rg.get("title", "")
            tipo = rg.get("primary-type", "") or "Álbum"
            try:
                score = int(rg.get("ext:score", 0))
            except (ValueError, TypeError):
                score = 0
            if score == 0:
                score = similaridade(query, f"{artista_mb} {album_mb}")
            lista.append({
                "fonte": "MusicBrainz", "score": score, "tipo": tipo,
                "artista": artista_mb, "album": album_mb, "titulo": "",
                "faixas": "", "ano": rg.get("first-release-date", "")[:4],
                "id": rg["id"], "id_tipo": "release-group",
                "artwork": None,
            })
    except Exception as e:
        print(f"Erro MB: {e}")
    return lista


def buscar_itunes_album(a, t):
    lista = []
    query = f"{a} {t}".strip()
    try:
        for r in buscar_itunes(a, t):
            art = r.get("artistName", "")
            alb = r.get("collectionName", "")
            tipo = r.get("collectionType", "") or "Álbum"
            lista.append({
                "fonte": "iTunes",
                "score": similaridade(query, f"{art} {alb}"),
                "tipo": tipo, "artista": art, "album": alb,
                "titulo": "", "faixas": r.get("trackCount", ""),
                "ano": r.get("releaseDate", "")[:4], "id": None,
                "id_tipo": None,
                "artwork": (r.get("artworkUrl100", "") or "")
                            .replace("100x100", "600x600"),
            })
    except Exception as e:
        print(f"Erro iTunes: {e}")
    return lista


def buscar_deezer_album(a, t):
    lista = []
    query = f"{a} {t}".strip()
    try:
        for r in buscar_deezer(a, t):
            art = r.get("artist", {}).get("name", "")
            alb = r.get("album", {}).get("title", "")
            lista.append({
                "fonte": "Deezer",
                "score": similaridade(query, f"{art} {alb}"),
                "tipo": "Álbum", "artista": art, "album": alb,
                "titulo": "", "faixas": "", "ano": "", "id": None,
                "id_tipo": None,
                "artwork": r.get("album", {}).get("cover_xl", ""),
            })
    except Exception as e:
        print(f"Erro Deezer: {e}")
    return lista


def buscar_musicbrainz_titulo(a, t):
    lista = []
    query = f"{a} {t}".strip()
    try:
        for rec in buscar_recordings(a, t):
            nomes = extrair_artistas_mb(rec.get("artist-credit", []))
            artista_mb = ", ".join(nomes) or a
            titulo_mb = rec.get("title", "")
            releases = rec.get("release-list", [])
            album_mb = ""
            ano_mb = ""
            release_id = None
            if releases:
                releases_ord = sorted(
                    releases, key=lambda x: x.get("date", "9999"))
                r0 = releases_ord[0]
                album_mb = r0.get("title", "")
                ano_mb = r0.get("date", "")[:4]
                release_id = r0.get("id")
            try:
                score = int(rec.get("ext:score", 0))
            except (ValueError, TypeError):
                score = 0
            if score == 0:
                score = similaridade(query, f"{artista_mb} {titulo_mb}")
            lista.append({
                "fonte": "MusicBrainz", "score": score, "tipo": "Single",
                "artista": artista_mb, "album": album_mb,
                "titulo": titulo_mb, "faixas": "", "ano": ano_mb,
                "id": release_id,
                "id_tipo": "release" if release_id else None,
                "artwork": None,
            })
    except Exception as e:
        print(f"Erro MB (titulo): {e}")
    return lista


def buscar_itunes_titulo(a, t):
    lista = []
    query = f"{a} {t}".strip()
    try:
        for r in buscar_itunes(a, t):
            art = r.get("artistName", "")
            alb = r.get("collectionName", "")
            tit = r.get("trackName", "")
            lista.append({
                "fonte": "iTunes",
                "score": similaridade(query, f"{art} {tit}"),
                "tipo": "Single", "artista": art, "album": alb,
                "titulo": tit, "faixas": "",
                "ano": r.get("releaseDate", "")[:4], "id": None,
                "id_tipo": None,
                "artwork": (r.get("artworkUrl100", "") or "")
                            .replace("100x100", "600x600"),
            })
    except Exception as e:
        print(f"Erro iTunes (titulo): {e}")
    return lista


def buscar_deezer_titulo(a, t):
    lista = []
    query = f"{a} {t}".strip()
    try:
        for r in buscar_deezer(a, t):
            art = r.get("artist", {}).get("name", "")
            alb = r.get("album", {}).get("title", "")
            tit = r.get("title", "")
            lista.append({
                "fonte": "Deezer",
                "score": similaridade(query, f"{art} {tit}"),
                "tipo": "Single", "artista": art, "album": alb,
                "titulo": tit, "faixas": "", "ano": "", "id": None,
                "id_tipo": None,
                "artwork": r.get("album", {}).get("cover_xl", ""),
            })
    except Exception as e:
        print(f"Erro Deezer (titulo): {e}")
    return lista


# =====================================================================
# STATUS
# =====================================================================
class StatusLabel(ttk.Label):
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._animando = False
        self._base = ""
        self._frame = 0
        self._job = None

    def set_idle(self, texto=""):
        self._parar()
        self.config(text=texto, foreground=COR_IDLE)

    def set_ok(self, texto):
        self._parar()
        self.config(text="✓ " + texto, foreground=COR_OK)

    def set_erro(self, texto):
        self._parar()
        self.config(text="✗ " + texto, foreground=COR_ERRO)

    def set_aviso(self, texto):
        self._parar()
        self.config(text="⚠ " + texto, foreground=COR_AVISO)

    def set_working(self, texto):
        self._base = texto
        self._frame = 0
        self._animando = True
        self.config(foreground=COR_WORKING)
        self._tick()

    def _tick(self):
        if not self._animando:
            return
        ch = SPINNER_FRAMES[self._frame % len(SPINNER_FRAMES)]
        self.config(text=f"{ch}  {self._base}")
        self._frame += 1
        self._job = self.after(80, self._tick)

    def _parar(self):
        self._animando = False
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

# =====================================================================
# TOOLTIP
# =====================================================================
class ToolTip:
    """Mostra uma dica flutuante quando o mouse fica parado em cima
    de um widget por um tempo (estilo OBS / VSCode)."""

    def __init__(self, widget, texto, atraso=600):
        self.widget = widget
        self.texto = texto
        self.atraso = atraso
        self._job = None
        self._tip = None
        widget.bind("<Enter>", self._agendar, add="+")
        widget.bind("<Leave>", self._cancelar, add="+")
        widget.bind("<ButtonPress>", self._cancelar, add="+")

    def _agendar(self, event=None):
        self._cancelar()
        try:
            self._job = self.widget.after(self.atraso, self._mostrar)
        except Exception:
            pass

    def _cancelar(self, event=None):
        if self._job:
            try:
                self.widget.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None

    def _mostrar(self):
        if self._tip:
            return
        try:
            x = self.widget.winfo_rootx() + 10
            y = (self.widget.winfo_rooty()
                 + self.widget.winfo_height() + 4)
            self._tip = tk.Toplevel(self.widget)
            self._tip.wm_overrideredirect(True)
            self._tip.wm_geometry(f"+{x}+{y}")
            c = C()
            tk.Label(self._tip, text=self.texto,
                     bg=c["entry_bg"], fg=c["entry_fg"],
                     padx=8, pady=4, font=("Segoe UI", 9),
                     relief="solid", borderwidth=1,
                     highlightbackground=c["border"]).pack()
        except Exception:
            pass


# =====================================================================
# SEEK BAR
# =====================================================================
class SeekBar(tk.Canvas):
    def __init__(self, parent, on_seek=None, **kw):
        altura = kw.pop("height", SEEK_ALTURA)
        super().__init__(parent, height=altura, highlightthickness=0,
                         bd=0, **kw)
        self.on_seek = on_seek
        self._valor = 0.0
        self._total = 100.0
        self._arrastando = False
        self._hover = False

        self.bind("<Configure>", lambda e: self._redesenhar())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self._hover = True
        self._redesenhar()

    def _on_leave(self, e):
        self._hover = False
        self._redesenhar()

    def configurar_total(self, total):
        try:
            self._total = float(total) if total > 0 else 100.0
        except Exception:
            self._total = 100.0
        self._redesenhar()

    def definir_valor(self, valor, forcar=False):
        if self._arrastando and not forcar:
            return
        try:
            self._valor = max(0.0, min(float(valor), self._total))
        except Exception:
            self._valor = 0.0
        self._redesenhar()

    def obter_valor(self):
        return self._valor

    def _pos_para_valor(self, x):
        try:
            w = max(1, self.winfo_width())
        except Exception:
            w = 1
        margem = 8
        util = max(1, w - 2 * margem)
        frac = (x - margem) / util
        frac = max(0.0, min(1.0, frac))
        return frac * self._total

    def _press(self, event):
        self._arrastando = True
        self._valor = self._pos_para_valor(event.x)
        self._redesenhar()

    def _drag(self, event):
        self._valor = self._pos_para_valor(event.x)
        self._redesenhar()

    def _release(self, event):
        self._valor = self._pos_para_valor(event.x)
        self._arrastando = False
        self._redesenhar()
        if self.on_seek:
            try:
                self.on_seek(self._valor)
            except Exception:
                pass

    def _redesenhar(self):
        c = C()
        try:
            self.delete("all")
            w = max(1, self.winfo_width())
            h = max(1, self.winfo_height())
            margem = 8
            meio = h // 2
            self.create_line(margem, meio, w - margem, meio,
                             fill=c["seek_bg"], width=4,
                             capstyle="round")
            if self._total > 0:
                frac = self._valor / self._total
            else:
                frac = 0.0
            frac = max(0.0, min(1.0, frac))
            x_prog = margem + frac * (w - 2 * margem)
            if x_prog > margem:
                self.create_line(margem, meio, x_prog, meio,
                                 fill=c["seek_fill"], width=4,
                                 capstyle="round")
            raio = 7 if self._hover or self._arrastando else 5
            self.create_oval(x_prog - raio, meio - raio,
                             x_prog + raio, meio + raio,
                             fill=c["seek_handle"], outline="")
        except Exception:
            pass


# =====================================================================
# PLAYER
# =====================================================================
class Player:
    def __init__(self):
        self.iniciado = False
        self.tocando = False
        self.musica_atual = None
        self.duracao = 0.0
        self.posicao_base = 0.0
        self.tempo_inicio = 0.0
        self._fila = []
        self._idx_fila = -1
        self.on_fim = None

    def _garantir_init(self):
        if not PLAYER_DISPONIVEL:
            return False
        if not self.iniciado:
            try:
                pygame.mixer.init()
                self.iniciado = True
            except Exception as e:
                print(f"Erro pygame.mixer: {e}")
                return False
        return True

    def definir_fila(self, caminhos, idx_atual=None):
        self._fila = list(caminhos)
        if idx_atual is not None:
            self._idx_fila = idx_atual
        else:
            self._idx_fila = -1

    def tocar(self, caminho, inicio=0.0):
        if not self._garantir_init():
            return False
        if self.musica_atual:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass
            self.musica_atual = None
        try:
            try:
                self.duracao = (MP3(caminho).info.length
                                if MP3 is not None else 0.0)
            except Exception:
                self.duracao = 0.0
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.play(start=float(inicio))
            self.tocando = True
            self.musica_atual = caminho
            self.posicao_base = float(inicio)
            self.tempo_inicio = time.time()
            if caminho in self._fila:
                self._idx_fila = self._fila.index(caminho)
            return True
        except Exception as e:
            print(f"Erro ao tocar: {e}")
            return False

    def posicao_atual(self):
        if not self.tocando:
            return self.posicao_base
        return self.posicao_base + (time.time() - self.tempo_inicio)

    def seek(self, segundos):
        if not self.musica_atual or not self.iniciado:
            return
        try:
            seg = max(0.0, float(segundos))
            if self.duracao > 0:
                seg = min(seg, self.duracao)
            pygame.mixer.music.play(start=seg)
            self.posicao_base = seg
            self.tempo_inicio = time.time()
            self.tocando = True
        except Exception as e:
            print(f"Erro seek: {e}")

    def pular(self, delta_segundos):
        self.seek(self.posicao_atual() + delta_segundos)

    def proxima(self):
        if not self._fila:
            return False
        if self._idx_fila < 0:
            return False
        prox = self._idx_fila + 1
        if prox >= len(self._fila):
            return False
        self._idx_fila = prox
        return self.tocar(self._fila[prox], inicio=0.0)

    def anterior(self):
        if not self._fila:
            return False
        if self._idx_fila < 0:
            return False
        ant = self._idx_fila - 1
        if ant < 0:
            return False
        self._idx_fila = ant
        return self.tocar(self._fila[ant], inicio=0.0)

    def parar(self):
        if not self.iniciado:
            self.musica_atual = None
            self.tocando = False
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        try:
            pygame.mixer.music.unload()
        except Exception:
            pass
        self.tocando = False
        self.posicao_base = 0.0
        self.musica_atual = None
        self.duracao = 0.0

    def liberar_total(self):
        if not PLAYER_DISPONIVEL:
            return
        try:
            if self.iniciado:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass
                try:
                    pygame.mixer.quit()
                except Exception:
                    pass
        except Exception:
            pass
        self.iniciado = False
        self.tocando = False
        self.musica_atual = None
        self.duracao = 0.0
        self.posicao_base = 0.0

    def pausar(self):
        if not self.iniciado or not self.tocando:
            return
        try:
            self.posicao_base = self.posicao_atual()
            pygame.mixer.music.pause()
            self.tocando = False
        except Exception:
            pass

    def retomar(self):
        if not self.iniciado or not self.musica_atual:
            return
        try:
            pygame.mixer.music.unpause()
            self.tocando = True
            self.tempo_inicio = time.time()
        except Exception:
            pass

    def liberar(self, caminho=None):
        if caminho is None or self.musica_atual == caminho:
            self.parar()


# =====================================================================
# PLAYER CONTROL
# =====================================================================
class PlayerControl(ttk.Frame):
    def __init__(self, parent, app, mostrar_capa=True):
        super().__init__(parent, padding=4)
        self.app = app
        self.mostrar_capa = mostrar_capa
        self._botoes_widgets = []
        self.btn_play_canvas = None
        self.btn_play_item = None
        self.icone_play_atual = "▶"

        if mostrar_capa:
            topo = ttk.Frame(self)
            topo.pack(fill="x", pady=(0, 4))

            self.frame_capa = tk.Frame(topo, bg=C()["preview_bg"],
                                        width=LADO_MINI, height=LADO_MINI,
                                        highlightthickness=0, bd=0)
            self.frame_capa.pack(side="left", padx=(0, 8))
            self.frame_capa.pack_propagate(False)
            self.lbl_capa_mini = tk.Label(self.frame_capa,
                                           bg=C()["preview_bg"],
                                           text="♪",
                                           fg=C()["preview_fg"],
                                           font=("Segoe UI", 20))
            self.lbl_capa_mini.pack(fill="both", expand=True)
            self._capa_tk = None

            info = ttk.Frame(topo)
            info.pack(side="left", fill="both", expand=True)

            self.lbl_titulo = ttk.Label(info, text=T("player_nada_tocando"),
                                         font=("Segoe UI", 10, "bold"),
                                         wraplength=220,
                                         justify="left")
            self.lbl_titulo.pack(anchor="w")
            self.lbl_artista_album = ttk.Label(
                info, text="", foreground="#888",
                wraplength=220, justify="left")
            self.lbl_artista_album.pack(anchor="w", pady=(2, 0))
        else:
            self.lbl_titulo = ttk.Label(self, text=T("player_nada_tocando"),
                                         font=("Segoe UI", 9, "bold"))
            self.lbl_titulo.pack(anchor="w")
            self.lbl_artista_album = ttk.Label(self, text="",
                                                foreground="#888")
            self.lbl_artista_album.pack(anchor="w")

        linha_seek = ttk.Frame(self)
        linha_seek.pack(fill="x", pady=(4, 4))

        self.lbl_pos = ttk.Label(linha_seek, text="0:00", width=5,
                                  anchor="e")
        self.lbl_pos.pack(side="left")
        self.seek_bar = SeekBar(linha_seek, on_seek=self._seek_solicitado)
        self.seek_bar.pack(side="left", fill="x", expand=True, padx=4)
        self.lbl_dur = ttk.Label(linha_seek, text="0:00", width=5,
                                  anchor="w")
        self.lbl_dur.pack(side="left")

        self.frame_botoes = ttk.Frame(self)
        self.frame_botoes.pack(fill="x", pady=(4, 0))
        self._construir_botoes()

    def _construir_botoes(self):
        for w in self.frame_botoes.winfo_children():
            w.destroy()
        self._botoes_widgets = []
        self.btn_play_canvas = None
        self.btn_play_item = None

        if not PLAYER_DISPONIVEL:
            ttk.Label(self.frame_botoes, text="(pip install pygame-ce)",
                      foreground="#cc7000").pack()
            return

        linha = ttk.Frame(self.frame_botoes)
        linha.pack(anchor="center")

        self._add_botao(linha, "anterior", T("player_anterior"),
                        self._anterior)
        self._add_botao(linha, "rewind", T("player_voltar_10"),
                        lambda: self._pular(-10))
        self._add_botao(linha, "play", T("player_play_pause"),
                        self._toggle_play, is_play=True)
        self._add_botao(linha, "forward", T("player_avancar_10"),
                        lambda: self._pular(10))
        self._add_botao(linha, "proxima", T("player_proxima"),
                        self._proxima)
        self._add_botao(linha, "stop", T("player_parar"), self._parar)

    def _add_botao(self, parent, tipo, nome, comando, is_play=False):
        info = criar_botao_canvas(parent, tipo, comando, nome,
                                    size=46, lado="left", padx=3)
        if is_play:
            self.btn_play_info = info

    def atualizar_cores(self):
        try:
            atualizar_botoes_canvas()
        except Exception:
            pass

    def _seek_solicitado(self, valor):
        if self.app.player.musica_atual:
            self.app.player.seek(valor)

    def _toggle_play(self):
        p = self.app.player
        if not p.musica_atual:
            self.app._tocar_selecionada_para(self)
            return
        if p.tocando:
            p.pausar()
        else:
            p.retomar()
        self.atualizar()

    def _pular(self, delta):
        p = self.app.player
        if p.musica_atual:
            p.pular(delta)

    def _anterior(self):
        p = self.app.player
        if p.anterior():
            self.app._on_trocar_musica()
        else:
            p.seek(0)

    def _proxima(self):
        p = self.app.player
        if p.proxima():
            self.app._on_trocar_musica()
        else:
            p.seek(0)

    def _parar(self):
        self.app.player.parar()
        self.app._on_trocar_musica()

    def atualizar(self):
        p = self.app.player

        try:
            info = getattr(self, "btn_play_info", None)
            if info:
                novo = "pause" if (p.musica_atual and p.tocando) else "play"
                if info.get("tipo") != novo:
                    info["tipo"] = novo
                    bg, cb, cbo, ifg, hb = _cores_botao()
                    cv = info["canvas"]
                    for it in cv.find_all():
                        if it != info["circle_id"]:
                            cv.delete(it)
                    _d_dispatch(cv, novo, info["centro"], info["centro"],
                                 ifg, info["r"])
        except Exception:
            pass

        if not p.musica_atual:
            try:
                self.lbl_titulo.config(text=T("player_nada_tocando"))
                self.lbl_artista_album.config(text="")
                self.lbl_pos.config(text="0:00")
                self.lbl_dur.config(text="0:00")
                self.seek_bar.configurar_total(100)
                self.seek_bar.definir_valor(0, forcar=True)
                if self.mostrar_capa:
                    self._set_capa(None)
            except Exception:
                pass
            return

        info = self.app._info_de(p.musica_atual)
        titulo = info.get("titulo") or os.path.basename(p.musica_atual)
        artista = info.get("artista") or ""
        album = info.get("album") or ""
        try:
            self.lbl_titulo.config(text=titulo)
            partes = []
            if artista:
                partes.append(artista)
            if album:
                partes.append(album)
            self.lbl_artista_album.config(text=" · ".join(partes)
                                           if partes else "")
        except Exception:
            pass

        if self.mostrar_capa:
            self._set_capa(info.get("capa"))

        try:
            dur = p.duracao
            self.seek_bar.configurar_total(dur if dur > 0 else 100)
            self.lbl_dur.config(text=fmt_tempo(dur))
        except Exception:
            pass

    def _set_capa(self, capa_bytes):
        try:
            if capa_bytes:
                photo = thumb_mini(capa_bytes, LADO_MINI)
                self._capa_tk = photo
                self.lbl_capa_mini.config(image=photo, text="")
            else:
                self._capa_tk = None
                self.lbl_capa_mini.config(image="", text="♪",
                                           fg=C()["preview_fg"])
        except Exception:
            pass

    def tick_seek(self):
        p = self.app.player
        if not p.musica_atual:
            return
        try:
            pos = p.posicao_atual()
            if p.duracao > 0 and pos > p.duracao:
                pos = p.duracao
            if not self.seek_bar._arrastando:
                self.seek_bar.definir_valor(pos)
                self.lbl_pos.config(text=fmt_tempo(pos))
        except Exception:
            pass


# =====================================================================
# EDITOR DE METADADOS
# =====================================================================
class EditorMetadadosWindow:
    def __init__(self, parent, arquivos, profile, on_done=None,
                 ignorar_capa=False):
        self.parent = parent
        self.arquivos = sorted(arquivos,
                               key=lambda p: os.path.basename(p).lower())
        self.profile = profile
        self.on_done = on_done
        self.resultados = []
        self.faixas_mb = []
        self.mapeamento = []
        self.capa_bytes_atual = None
        self.capa_tk = None
        self.arquivo_ref = self.arquivos[0] if self.arquivos else None
        self.contagem_pendente = {}
        self.escuro = TEMA["escuro"]
        self._entry_inline = None
        self._var_inline = None
        self._undo_stack = []
        self._redo_stack = []
        self._max_undo = 30
        self._undo_stack = []
        self._redo_stack = []
        self._max_undo = 30

        self.dados_por_musica = {}
        for caminho in self.arquivos:
            info = ler_info(caminho)
            titulo = info["titulo"] or titulo_do_nome(caminho)
            self.dados_por_musica[caminho] = {
                "titulo": titulo,
                "faixa": info["faixa"] or "",
                "artista_orig": info["artista"],
                "album_orig": info["album"],
                "ano_orig": info["ano"],
                "genero_orig": info["genero"],
            }

        self.janela = tk.Toplevel(parent)
        n = len(self.arquivos)
        titulo = (T("editor_titulo_1") if n == 1
                  else T("editor_titulo_n", n=n))
        self.janela.title(titulo)
        self.janela.geometry("1100x820")
        self.janela.minsize(960, 700)
        self.janela.transient(parent)
        self.janela.configure(bg=C()["bg"])
        self.janela.grab_set()

        self.var_ignorar_capa = tk.BooleanVar(value=ignorar_capa)
        self.var_aplicar_artista = tk.BooleanVar(value=True)
        self.var_aplicar_album = tk.BooleanVar(value=True)
        self.var_aplicar_ano = tk.BooleanVar(value=True)
        self.var_aplicar_genero = tk.BooleanVar(value=True)

        modo_padrao = "titulo" if n == 1 else "album"
        self.var_modo_busca = tk.StringVar(value=modo_padrao)

        self._ui()
        self._carregar_inicial()
        aplicar_tema_janela(self.janela)
        self._aplicar_cores_tags()

    def _aplicar_cores_tags(self):
        c = C()
        try:
            self.tree_map.tag_configure("matched",
                background=c["row_match_bg"])
            self.tree_map.tag_configure("orphan",
                background=c["row_orphan_bg"])
            self.tree_map.tag_configure("placeholder",
                foreground="#888888")
        except Exception:
            pass

    def _ui(self):
        c = C()

        topo = ttk.Frame(self.janela, padding=6)
        topo.pack(side="top", fill="x")
        ttk.Label(topo, text=T("lbl_perfil")).pack(side="left")
        ttk.Label(topo, text=self.profile.get("descricao", "")[:55],
                  foreground="gray").pack(side="left", padx=8)
        ttk.Button(topo, text=T("editor_trocar_perfil"),
                   command=self._trocar_perfil).pack(side="right")

        aviso = ttk.Frame(self.janela, padding=(10, 2))
        aviso.pack(side="top", fill="x")
        ttk.Checkbutton(
            aviso,
            text=T("editor_nao_alterar_capa"),
            variable=self.var_ignorar_capa,
        ).pack(side="left")

        busca = ttk.LabelFrame(self.janela, text=T("editor_buscar_online"))
        busca.pack(side="top", fill="x", padx=8, pady=4)

        rad_frame = ttk.Frame(busca)
        rad_frame.grid(row=0, column=0, columnspan=4, sticky="w",
                       padx=4, pady=(4, 2))
        ttk.Label(rad_frame, text=T("editor_buscar_por")).pack(side="left")
        ttk.Radiobutton(rad_frame, text=T("editor_modo_titulo"),
                        variable=self.var_modo_busca, value="titulo",
                        command=self._trocar_modo_busca).pack(side="left",
                                                              padx=6)
        ttk.Radiobutton(rad_frame, text=T("editor_modo_album"),
                        variable=self.var_modo_busca, value="album",
                        command=self._trocar_modo_busca).pack(side="left",
                                                              padx=6)

        ttk.Label(busca, text=T("editor_artista")).grid(row=1, column=0,
                                                padx=4, pady=3, sticky="e")
        self.entry_busca_artista = ttk.Entry(busca, width=28)
        self.entry_busca_artista.grid(row=1, column=1, padx=4, pady=3,
                                       sticky="we")

        ttk.Label(busca, text=T("editor_termo")).grid(row=1, column=2,
                                              padx=4, pady=3, sticky="e")
        self.entry_busca_termo = ttk.Entry(busca, width=40)
        self.entry_busca_termo.grid(row=1, column=3, padx=4, pady=3,
                                     sticky="we")

        fontes_frame = ttk.Frame(busca)
        fontes_frame.grid(row=2, column=0, columnspan=3, sticky="w",
                          padx=4, pady=(4, 6))
        ttk.Label(fontes_frame, text=T("editor_fontes")).pack(side="left")
        self.var_fontes = {}
        for f in FONTES_DISPONIVEIS:
            var = tk.BooleanVar(value=True)
            self.var_fontes[f] = var
            ttk.Checkbutton(fontes_frame, text=f,
                            variable=var).pack(side="left", padx=4)

        self.btn_buscar = ttk.Button(busca, text=T("editor_btn_buscar"),
                                     command=self._buscar,
                                     style="Primary.TButton")
        self.btn_buscar.grid(row=2, column=3, padx=4, pady=(4, 6),
                             sticky="e")

        busca.columnconfigure(1, weight=1)
        busca.columnconfigure(3, weight=2)

        comuns = ttk.LabelFrame(
            self.janela,
            text=T("editor_campos_comuns"))
        comuns.pack(side="top", fill="x", padx=8, pady=4)

        self.chk_artista = ttk.Checkbutton(
            comuns, text="✓", variable=self.var_aplicar_artista,
            command=self._atualizar_estado_entries)
        self.chk_artista.grid(row=0, column=0, padx=(4, 0), pady=3)
        ttk.Label(comuns, text=T("editor_artista")).grid(row=0, column=1,
                                                 padx=4, pady=3, sticky="e")
        self.entry_artista = ttk.Entry(comuns, width=30)
        self.entry_artista.grid(row=0, column=2, padx=4, pady=3, sticky="we")

        self.chk_album = ttk.Checkbutton(
            comuns, text="✓", variable=self.var_aplicar_album,
            command=self._atualizar_estado_entries)
        self.chk_album.grid(row=0, column=3, padx=(12, 0), pady=3)
        ttk.Label(comuns, text=T("editor_album")).grid(row=0, column=4,
                                               padx=4, pady=3, sticky="e")
        self.entry_album = ttk.Entry(comuns, width=30)
        self.entry_album.grid(row=0, column=5, padx=4, pady=3, sticky="we")

        self.chk_ano = ttk.Checkbutton(
            comuns, text="✓", variable=self.var_aplicar_ano,
            command=self._atualizar_estado_entries)
        self.chk_ano.grid(row=1, column=0, padx=(4, 0), pady=3)
        ttk.Label(comuns, text=T("editor_ano")).grid(row=1, column=1,
                                             padx=4, pady=3, sticky="e")
        self.entry_ano = ttk.Entry(comuns, width=30)
        self.entry_ano.grid(row=1, column=2, padx=4, pady=3, sticky="we")

        self.chk_genero = ttk.Checkbutton(
            comuns, text="✓", variable=self.var_aplicar_genero,
            command=self._atualizar_estado_entries)
        self.chk_genero.grid(row=1, column=3, padx=(12, 0), pady=3)
        ttk.Label(comuns, text=T("editor_genero")).grid(row=1, column=4,
                                                padx=4, pady=3, sticky="e")
        self.entry_genero = ttk.Entry(comuns, width=30)
        self.entry_genero.grid(row=1, column=5, padx=4, pady=3, sticky="we")

        comuns.columnconfigure(2, weight=1)
        comuns.columnconfigure(5, weight=1)

        log_frame = ttk.Frame(self.janela, padding=(8, 0, 8, 6))
        log_frame.pack(side="bottom", fill="x")
        self.log = scrolledtext.ScrolledText(log_frame, height=3,
                                              wrap="word")
        self.log.pack(fill="x")

        barra = ttk.Frame(self.janela, padding=(8, 4, 8, 2))
        barra.pack(side="bottom", fill="x")
        self.status = StatusLabel(barra, text="", anchor="w")
        self.status.pack(side="left", fill="x", expand=True)

        inf = ttk.Frame(self.janela, padding=(8, 6, 8, 6))
        inf.pack(side="bottom", fill="x")
        n = len(self.arquivos)
        txt = T("editor_aplicar_todas") if n > 1 else T("editor_aplicar")
        self.btn_aplicar = ttk.Button(inf, text=txt, command=self._aplicar,
                                      style="Success.TButton", width=20)
        self.btn_aplicar.pack(side="right", padx=4, ipady=6)
        ttk.Button(inf, text=T("editor_cancelar"),
                   command=self.janela.destroy,
                   style="Danger.TButton", width=12).pack(side="right",
                                                          ipady=6)
        btn_redo = ttk.Button(inf, text="\u21b7", width=3,
                              command=self._redo)
        btn_redo.pack(side="left", padx=2, ipady=6)
        ToolTip(btn_redo, "Ctrl+Y", atraso=400)
        btn_undo = ttk.Button(inf, text="\u21b6", width=3,
                              command=self._undo)
        btn_undo.pack(side="left", padx=2, ipady=6)
        ToolTip(btn_undo, "Ctrl+Z", atraso=400)

        corpo = ttk.Frame(self.janela)
        corpo.pack(side="top", fill="both", expand=True, padx=8, pady=4)

        esq = ttk.Frame(corpo)
        esq.pack(side="left", fill="both", expand=True)

        paned = ttk.PanedWindow(esq, orient="vertical")
        paned.pack(fill="both", expand=True)

        f_res = ttk.Frame(paned)
        paned.add(f_res, weight=1)
        ttk.Label(f_res,
                  text=T("editor_resultados_online"),
                  foreground="gray").pack(anchor="w", padx=4, pady=(0, 2))
        res_frame = ttk.Frame(f_res)
        res_frame.pack(fill="both", expand=True)
        cols = ("score", "tipo", "fonte", "artista", "album", "faixas",
                "ano")
        self.tree = ttk.Treeview(res_frame, columns=cols, show="headings",
                                 selectmode="browse", height=5)
        cab = {"score": T("editor_col_score"),
               "tipo": T("editor_col_tipo"),
               "fonte": T("editor_col_fonte"),
               "artista": T("editor_col_artista"),
               "album": T("editor_col_album"),
               "faixas": T("editor_col_faixas"),
               "ano": T("editor_col_ano")}
        widths = {"score": 50, "tipo": 70, "fonte": 85, "artista": 130,
                  "album": 200, "faixas": 50, "ano": 45}
        for col in cols:
            self.tree.heading(col, text=cab[col])
            anchor = "center" if col in ("score", "faixas", "ano",
                                          "tipo") else "w"
            self.tree.column(col, width=widths[col], anchor=anchor)
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(res_frame, orient="vertical",
                           command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_resultado)

        f_map = ttk.Frame(paned)
        paned.add(f_map, weight=3)

        topo_map = ttk.Frame(f_map)
        topo_map.pack(fill="x", padx=4, pady=(4, 2))
        ttk.Label(
            topo_map,
            text=T("editor_mapeamento_hint"),
            foreground="gray").pack(side="left")
        ttk.Button(topo_map, text=T("editor_limpar_assoc"),
                   command=self._limpar_mapeamento).pack(side="right",
                                                         padx=2)
        ttk.Button(topo_map, text=T("editor_auto_associar"),
                   command=self._auto_associar,
                   style="Primary.TButton").pack(side="right", padx=2)

        map_frame = ttk.Frame(f_map)
        map_frame.pack(fill="both", expand=True)
        cols_m = ("num", "titulo_album", "titulo_final", "arquivo",
                  "status")
        self.tree_map = ttk.Treeview(map_frame, columns=cols_m,
                                     show="headings",
                                     selectmode="extended", height=10)
        self.tree_map.heading("num", text=T("editor_col_num"))
        self.tree_map.heading("titulo_album", text=T("editor_col_titulo_album"))
        self.tree_map.heading("titulo_final", text=T("editor_col_titulo_final"))
        self.tree_map.heading("arquivo", text=T("editor_col_arquivo"))
        self.tree_map.heading("status", text=T("editor_col_status"))
        self.tree_map.column("num", width=45, anchor="center",
                             stretch=False)
        self.tree_map.column("titulo_album", width=240)
        self.tree_map.column("titulo_final", width=240)
        self.tree_map.column("arquivo", width=260)
        self.tree_map.column("status", width=90, anchor="center")
        self.tree_map.pack(side="left", fill="both", expand=True)
        sb2 = ttk.Scrollbar(map_frame, orient="vertical",
                            command=self.tree_map.yview)
        sb2.pack(side="right", fill="y")
        self.tree_map.config(yscrollcommand=sb2.set)
        self.tree_map.bind("<Double-1>", self._iniciar_edicao_inline)

        self.menu_map = tk.Menu(self.janela, tearoff=0)
        self.menu_map.add_command(label=T("editor_ctx_associar"),
                                  command=self._associar_dialog)
        self.menu_map.add_command(label=T("editor_ctx_remover"),
                                  command=self._remover_associacao)
        self.menu_map.add_separator()
        self.menu_map.add_command(label=T("editor_ctx_auto_numerar"),
                                  command=self._auto_numerar)
        self.menu_map.add_command(label=T("editor_ctx_tirar_nomes"),
                                  command=self._titulos_dos_nomes)
        self.menu_map.add_command(label=T("editor_ctx_usar_titulo"),
                                  command=self._usar_titulo_album)
        self.tree_map.bind("<Button-3>", self._menu_map_popup)

        dir_ = ttk.LabelFrame(corpo, text=T("editor_capa"))
        dir_.pack(side="left", fill="y", padx=(8, 0), ipadx=6, ipady=6)
        self.frame_capa = tk.Frame(dir_, bg=c["preview_bg"],
                                   width=LADO_PREVIEW,
                                   height=LADO_PREVIEW,
                                   highlightthickness=0, bd=0)
        self.frame_capa.pack(padx=6, pady=6)
        self.frame_capa.pack_propagate(False)
        self.lbl_capa = tk.Label(self.frame_capa, bg=c["preview_bg"],
                                 text=T("editor_sem_capa"), fg=c["preview_fg"])
        self.lbl_capa.pack(fill="both", expand=True)
        bt = ttk.Frame(dir_)
        bt.pack(pady=4)
        ttk.Button(bt, text=T("editor_do_pc"),
                   command=self._capa_do_pc).pack(side="left", padx=2)
        ttk.Button(bt, text=T("btn_colar"),
                   command=self._capa_colar).pack(side="left", padx=2)

        self.janela.bind("<Control-v>", lambda e: self._capa_colar())
        self.janela.bind("<Control-z>", self._undo)
        self.janela.bind("<Control-y>", self._redo)
        self.janela.bind("<Control-z>", self._undo)
        self.janela.bind("<Control-Z>", self._undo)
        self.janela.bind("<Control-y>", self._redo)
        self.janela.bind("<Control-Y>", self._redo)

    def _snapshot_estado(self):
        import copy
        return {
            "mapeamento": copy.deepcopy(self.mapeamento),
            "capa_bytes_atual": self.capa_bytes_atual,
        }

    def _push_undo(self):
        self._undo_stack.append(self._snapshot_estado())
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _restaurar_estado(self, estado):
        self.mapeamento = estado["mapeamento"]
        self.capa_bytes_atual = estado["capa_bytes_atual"]
        if self.capa_bytes_atual:
            self.capa_tk = preview_quadrado(self.capa_bytes_atual,
                                            LADO_PREVIEW)
            self.lbl_capa.config(image=self.capa_tk, text="")
        else:
            self.capa_tk = preview_quadrado(None, LADO_PREVIEW)
            self.lbl_capa.config(image=self.capa_tk,
                                  text=T("editor_sem_capa"))
        self._reconstruir_mapeamento()

    def _undo(self, event=None):
        if not self._undo_stack:
            return
        self._redo_stack.append(self._snapshot_estado())
        estado = self._undo_stack.pop()
        self._restaurar_estado(estado)

    def _redo(self, event=None):
        if not self._redo_stack:
            return
        self._undo_stack.append(self._snapshot_estado())
        estado = self._redo_stack.pop()
        self._restaurar_estado(estado)

    def _snapshot_estado(self):
        import copy
        return {
            "mapeamento": copy.deepcopy(self.mapeamento),
            "capa_bytes_atual": self.capa_bytes_atual,
        }

    def _push_undo(self):
        self._undo_stack.append(self._snapshot_estado())
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _restaurar_estado(self, estado):
        self.mapeamento = estado["mapeamento"]
        self.capa_bytes_atual = estado["capa_bytes_atual"]
        if self.capa_bytes_atual:
            self.capa_tk = preview_quadrado(self.capa_bytes_atual,
                                            LADO_PREVIEW)
            self.lbl_capa.config(image=self.capa_tk, text="")
        else:
            self.capa_tk = preview_quadrado(None, LADO_PREVIEW)
            self.lbl_capa.config(image=self.capa_tk,
                                  text=T("editor_sem_capa"))
        self._reconstruir_mapeamento()

    def _undo(self, event=None):
        if not self._undo_stack:
            return
        self._redo_stack.append(self._snapshot_estado())
        self._restaurar_estado(self._undo_stack.pop())

    def _redo(self, event=None):
        if not self._redo_stack:
            return
        self._undo_stack.append(self._snapshot_estado())
        self._restaurar_estado(self._redo_stack.pop())

    def _menu_map_popup(self, event):
        row = self.tree_map.identify_row(event.y)
        if row and row not in self.tree_map.selection():
            self.tree_map.selection_set(row)
        try:
            self.menu_map.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_map.grab_release()

    def _trocar_modo_busca(self):
        pass

    def _atualizar_estado_entries(self):
        c = C()
        pares = [
            (self.var_aplicar_artista, self.entry_artista),
            (self.var_aplicar_album, self.entry_album),
            (self.var_aplicar_ano, self.entry_ano),
            (self.var_aplicar_genero, self.entry_genero),
        ]
        for var, entry in pares:
            try:
                if var.get():
                    entry.configure(state="normal")
                else:
                    entry.configure(
                        state="readonly",
                        readonlybackground=c["entry_disabled_bg"])
            except tk.TclError:
                pass

    def _iniciar_edicao_inline(self, event):
        if self._entry_inline is not None:
            try:
                self._entry_inline.destroy()
            except Exception:
                pass
            self._entry_inline = None

        row_id = self.tree_map.identify_row(event.y)
        col_id = self.tree_map.identify_column(event.x)
        if not row_id:
            return

        bbox = self.tree_map.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, w, h = bbox
        idx = int(row_id)
        if idx < 0 or idx >= len(self.mapeamento):
            return
        row = self.mapeamento[idx]

        if col_id == "#1":
            col_key = "num"
            widget_cls = "entry"
        elif col_id == "#3":
            col_key = "titulo_final"
            widget_cls = "entry"
        elif col_id == "#4":
            col_key = None
            widget_cls = "combo"
        else:
            return

        if widget_cls == "entry":
            valor = str(row.get(col_key, ""))
            var = tk.StringVar(value=valor)
            entry = tk.Entry(self.tree_map, textvariable=var,
                             font=("Segoe UI", 9))
            try:
                entry.configure(bg=C()["entry_bg"], fg=C()["entry_fg"],
                                insertbackground=C()["entry_fg"],
                                relief="solid", borderwidth=1)
            except Exception:
                pass
            entry.place(x=x, y=y, width=w, height=h)
            entry.focus_set()
            entry.select_range(0, "end")
            self._entry_inline = entry
            self._var_inline = var

            def confirmar(e=None, _idx=idx, _key=col_key, _var=var,
                          _w=entry):
                try:
                    novo = _var.get().strip()
                    self.mapeamento[_idx][_key] = novo
                    _w.destroy()
                    self._entry_inline = None
                    self._reconstruir_mapeamento()
                except Exception:
                    pass

            def cancelar(e=None, _w=entry):
                try:
                    _w.destroy()
                except Exception:
                    pass
                self._entry_inline = None

            entry.bind("<Return>", confirmar)
            entry.bind("<Escape>", cancelar)
            entry.bind("<FocusOut>", confirmar)
        else:
            usados = set()
            for i, r in enumerate(self.mapeamento):
                if i == idx:
                    continue
                if r.get("caminho"):
                    usados.add(r["caminho"])
            opcoes = [T("editor_sem_assoc")]
            for caminho in self.arquivos:
                if caminho in usados:
                    continue
                opcoes.append(os.path.basename(caminho))
            if row.get("caminho"):
                nome_atual = os.path.basename(row["caminho"])
                if nome_atual not in opcoes:
                    opcoes.insert(1, nome_atual)

            var = tk.StringVar(
                value=os.path.basename(row["caminho"])
                      if row.get("caminho") else T("editor_sem_assoc"))
            combo = ttk.Combobox(self.tree_map, textvariable=var,
                                 values=opcoes, state="readonly")
            combo.place(x=x, y=y, width=w, height=h)
            combo.focus_set()

            def confirmar_combo(e=None, _idx=idx, _var=var, _w=combo):
                try:
                    escolha = _var.get()
                    if escolha == T("editor_sem_assoc"):
                        self.mapeamento[_idx]["caminho"] = None
                    else:
                        for caminho in self.arquivos:
                            if os.path.basename(caminho) == escolha:
                                self.mapeamento[_idx]["caminho"] = caminho
                                break
                    _w.destroy()
                    self._entry_inline = None
                    self._reconstruir_mapeamento()
                except Exception:
                    pass

            combo.bind("<<ComboboxSelected>>", confirmar_combo)
            combo.bind("<Escape>",
                        lambda e, _w=combo: (_w.destroy(),))
            self._entry_inline = combo

    def _reconstruir_mapeamento(self):
        self.tree_map.delete(*self.tree_map.get_children())
        for i, row in enumerate(self.mapeamento):
            titulo_album = ""
            if (row.get("idx_mb") is not None
                    and 0 <= row["idx_mb"] < len(self.faixas_mb)):
                titulo_album = self.faixas_mb[row["idx_mb"]]["titulo"]
            arquivo = os.path.basename(row["caminho"]) \
                if row.get("caminho") else T("editor_sem_assoc")
            status = "OK" if row.get("caminho") else "⚠ s/ arq."
            tag = "matched" if row.get("caminho") else "orphan"
            self.tree_map.insert("", "end", iid=str(i),
                                 values=(row.get("num", ""),
                                         titulo_album,
                                         row.get("titulo_final", ""),
                                         arquivo,
                                         status),
                                 tags=(tag,))
        total = len(self.mapeamento)
        ok = sum(1 for r in self.mapeamento if r.get("caminho"))
        if total:
            self.status.set_ok(T("editor_map_ok", ok=ok, total=total))
        else:
            self.status.set_idle(T("editor_sem_mapeamento"))

    def _auto_associar(self):
        if not self.faixas_mb:
            self.status.set_aviso(
                T("editor_aviso_selecione_album"))
            return

        self._push_undo()
        usados = set()
        novo = []
        for i, f in enumerate(self.faixas_mb):
            titulo_mb = f["titulo"].lower()
            melhor_score = 0
            melhor_caminho = None
            for caminho in self.arquivos:
                if caminho in usados:
                    continue
                d = self.dados_por_musica.get(caminho, {})
                titulo_local = d.get("titulo", "").lower()
                score = similaridade(titulo_mb, titulo_local)
                if score > melhor_score:
                    melhor_score = score
                    melhor_caminho = caminho
            if melhor_score >= 60:
                caminho_final = melhor_caminho
                usados.add(caminho_final)
            else:
                caminho_final = None
            novo.append({
                "idx_mb": i,
                "caminho": caminho_final,
                "num": f["pos"],
                "titulo_final": f["titulo"],
            })
        for caminho in self.arquivos:
            if caminho in usados:
                continue
            d = self.dados_por_musica.get(caminho, {})
            novo.append({
                "idx_mb": None,
                "caminho": caminho,
                "num": d.get("faixa", ""),
                "titulo_final": d.get("titulo", ""),
            })
        self.mapeamento = novo
        self._reconstruir_mapeamento()

    def _limpar_mapeamento(self):
        self._push_undo()
        novo = []
        for caminho in self.arquivos:
            d = self.dados_por_musica.get(caminho, {})
            novo.append({
                "idx_mb": None,
                "caminho": caminho,
                "num": d.get("faixa", ""),
                "titulo_final": d.get("titulo", ""),
            })
        self.mapeamento = novo
        self._reconstruir_mapeamento()

    def _remover_associacao(self):
        sel = self.tree_map.selection()
        if not sel:
            return
        self._push_undo()
        for iid in sel:
            idx = int(iid)
            if 0 <= idx < len(self.mapeamento):
                self.mapeamento[idx]["caminho"] = None
        self._reconstruir_mapeamento()

    def _associar_dialog(self):
        sel = self.tree_map.selection()
        if not sel:
            messagebox.showinfo(T("dialogo_aviso"), T("editor_msg_selecione_linha"))
            return
        idx = int(sel[0])
        if 0 > idx or idx >= len(self.mapeamento):
            return
        usados = set()
        for i, r in enumerate(self.mapeamento):
            if i == idx:
                continue
            if r.get("caminho"):
                usados.add(r["caminho"])
        disponiveis = [c for c in self.arquivos if c not in usados]

        dlg = tk.Toplevel(self.janela)
        dlg.title(T("editor_associar_titulo"))
        dlg.geometry("460x500")
        dlg.transient(self.janela)
        dlg.grab_set()
        dlg.configure(bg=C()["bg"])
        ttk.Label(dlg, text=T("editor_associar_hint"),
                  padding=8).pack(anchor="w")
        lb = tk.Listbox(dlg, height=18)
        lb.insert("end", T("editor_sem_assoc"))
        for c in disponiveis:
            lb.insert("end", os.path.basename(c))
        lb.pack(fill="both", expand=True, padx=8)
        bt = ttk.Frame(dlg, padding=8)
        bt.pack(side="bottom", fill="x")

        def ok():
            s = lb.curselection()
            if not s:
                dlg.destroy()
                return
            escolha = lb.get(s[0])
            if escolha == T("editor_sem_assoc"):
                self.mapeamento[idx]["caminho"] = None
            else:
                for c in self.arquivos:
                    if os.path.basename(c) == escolha:
                        self.mapeamento[idx]["caminho"] = c
                        break
            dlg.destroy()
            self._reconstruir_mapeamento()

        ttk.Button(bt, text="OK", command=ok,
                   style="Primary.TButton", width=10).pack(side="right",
                                                           padx=4, ipady=3)
        ttk.Button(bt, text=T("cancelar"), command=dlg.destroy,
                   style="Danger.TButton", width=10).pack(side="right",
                                                          ipady=3)
        aplicar_tema_janela(dlg)

    def _auto_numerar(self):
        self._push_undo()
        for i, row in enumerate(self.mapeamento, 1):
            row["num"] = str(i)
        self._reconstruir_mapeamento()
        self.status.set_ok(T("editor_numeradas", n=len(self.mapeamento)))

    def _titulos_dos_nomes(self):
        self._push_undo()
        for row in self.mapeamento:
            if row.get("caminho"):
                row["titulo_final"] = titulo_do_nome(row["caminho"])
        self._reconstruir_mapeamento()
        self.status.set_ok(T("editor_titulos_nomes"))

    def _usar_titulo_album(self):
        self._push_undo()
        for row in self.mapeamento:
            if (row.get("idx_mb") is not None
                    and 0 <= row["idx_mb"] < len(self.faixas_mb)):
                row["titulo_final"] = self.faixas_mb[
                    row["idx_mb"]]["titulo"]
        self._reconstruir_mapeamento()
        self.status.set_ok(T("editor_titulos_album"))

    def _trocar_perfil(self):
        dlg = PerfilPicker(self.janela, self.profile)
        self.janela.wait_window(dlg.janela)
        if dlg.escolhido:
            self.profile = dlg.escolhido
            self.log.insert("end", "Perfil alterado.\n")
            self.log.see("end")

    def _carregar_inicial(self):
        if not self.arquivo_ref:
            return
        info = ler_info(self.arquivo_ref)
        for entry, v in [(self.entry_artista, info["artista"]),
                         (self.entry_album, info["album"]),
                         (self.entry_ano, info["ano"]),
                         (self.entry_genero, info["genero"])]:
            entry.delete(0, tk.END)
            entry.insert(0, v)

        modo = self.var_modo_busca.get()
        self.entry_busca_artista.delete(0, tk.END)
        self.entry_busca_artista.insert(0, info["artista"])
        self.entry_busca_termo.delete(0, tk.END)
        if modo == "titulo":
            self.entry_busca_termo.insert(
                0, self.dados_por_musica[self.arquivo_ref]["titulo"])
        else:
            self.entry_busca_termo.insert(0, info["album"])

        self.capa_bytes_atual = info["capa"]
        self.capa_tk = preview_quadrado(info["capa"], LADO_PREVIEW)
        self.lbl_capa.config(image=self.capa_tk, text="")

        self._limpar_mapeamento()
        self._mostrar_placeholder_lista(T("editor_placeholder_buscar"))
        self._atualizar_estado_entries()

    def _mostrar_placeholder_lista(self, texto):
        self.tree.delete(*self.tree.get_children())
        self.tree.insert("", "end", iid="__placeholder__",
                         values=("", "", texto, "", "", "", ""),
                         tags=("placeholder",))
        try:
            self.tree.tag_configure("placeholder", foreground="#888")
        except Exception:
            pass

    def _set_ocupado(self, ocupado):
        estado = "disabled" if ocupado else "normal"
        try:
            self.btn_buscar.config(state=estado)
            self.btn_aplicar.config(state=estado)
        except Exception:
            pass

    def _buscar(self):
        if not ONLINE_OK:
            messagebox.showerror(T("dlg_faltam_bibs"),
                                 T("dlg_pip_install"))
            return
        a = self.entry_busca_artista.get().strip()
        t = self.entry_busca_termo.get().strip()
        if not (a or t):
            messagebox.showwarning(T("dialogo_aviso"), T("editor_msg_preencha"))
            return
        fontes = [f for f, var in self.var_fontes.items() if var.get()]
        if not fontes:
            messagebox.showwarning(T("dialogo_aviso"), T("editor_msg_marque_fonte"))
            return

        modo = self.var_modo_busca.get()
        self.resultados = []
        self._set_ocupado(True)
        self._mostrar_placeholder_lista(T("editor_placeholder_buscando"))
        modo_txt = T("editor_alvo_titulo") if modo == "titulo" else T("editor_alvo_album")
        self.status.set_working(
            T("editor_buscando_em", modo=modo_txt, fontes=", ".join(fontes)))

        lock = threading.Lock()
        pendentes = [len(fontes)]

        def adicionar(itens):
            with lock:
                self.resultados.extend(itens)

        def terminar(nome):
            with lock:
                pendentes[0] -= 1
                if pendentes[0] > 0:
                    self.janela.after(0, lambda:
                        self.status.set_working(T("editor_aguardando")))
                    return
            self.janela.after(0, self._popular)

        if modo == "titulo":
            fn_mb, fn_it, fn_dz = (buscar_musicbrainz_titulo,
                                    buscar_itunes_titulo,
                                    buscar_deezer_titulo)
        else:
            fn_mb, fn_it, fn_dz = (buscar_musicbrainz_album,
                                    buscar_itunes_album,
                                    buscar_deezer_album)

        def r_mb():
            try:
                adicionar(fn_mb(a, t))
            finally:
                terminar("MusicBrainz")

        def r_it():
            try:
                adicionar(fn_it(a, t))
            finally:
                terminar("iTunes")

        def r_dz():
            try:
                adicionar(fn_dz(a, t))
            finally:
                terminar("Deezer")

        fns = {"MusicBrainz": r_mb, "iTunes": r_it, "Deezer": r_dz}
        for nome in fontes:
            threading.Thread(target=fns[nome], daemon=True).start()

    def _popular(self):
        self._set_ocupado(False)
        self.tree.delete(*self.tree.get_children())
        if not self.resultados:
            self._mostrar_placeholder_lista(T("editor_placeholder_nenhum"))
            self.status.set_erro(T("editor_placeholder_nenhum"))
            return
        self.resultados.sort(key=lambda r: r.get("score", 0), reverse=True)
        for i, r in enumerate(self.resultados):
            self.tree.insert("", "end", iid=str(i),
                             values=(r.get("score", ""),
                                     r.get("tipo", ""),
                                     r["fonte"],
                                     r["artista"], r["album"],
                                     r["faixas"], r["ano"]))
        n = len(self.resultados)
        self.status.set_ok(T("editor_resultados_n", n=n))

    def _on_select_resultado(self, event=None):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            return
        idx = int(sel[0])
        r = self.resultados[idx]
        modo = self.var_modo_busca.get()

        if r["artista"]:
            self.var_aplicar_artista.set(True)
            self.entry_artista.delete(0, tk.END)
            self.entry_artista.insert(0, r["artista"])
        if r["album"]:
            self.var_aplicar_album.set(True)
            self.entry_album.delete(0, tk.END)
            self.entry_album.insert(0, r["album"])
        if r["ano"]:
            self.var_aplicar_ano.set(True)
            self.entry_ano.delete(0, tk.END)
            self.entry_ano.insert(0, r["ano"])
        self._atualizar_estado_entries()

        if modo == "titulo" and r.get("titulo") and len(self.arquivos) == 1:
            caminho = self.arquivos[0]
            self.dados_por_musica[caminho]["titulo"] = r["titulo"]

        self.lbl_capa.config(image="", text=T("editor_baixando_capa"),
                             fg=C()["preview_fg"])
        self.status.set_working(T("editor_baixando_capa_fonte", fonte=r["fonte"]))

        def baixar_capa():
            b = None
            if r.get("artwork"):
                b = baixar_bytes(r["artwork"])
            elif r["fonte"] == "MusicBrainz" and r.get("id"):
                if r.get("id_tipo") == "release-group":
                    b = url_capa_rg(r["id"], 500)
                elif r.get("id_tipo") == "release":
                    b = url_capa_release(r["id"], 500)

            def fim():
                if b:
                    self.capa_bytes_atual = b
                    self.capa_tk = preview_quadrado(b, LADO_PREVIEW)
                    self.lbl_capa.config(image=self.capa_tk, text="")
                else:
                    self.capa_bytes_atual = None
                    self.capa_tk = preview_quadrado(None, LADO_PREVIEW)
                    self.lbl_capa.config(image=self.capa_tk,
                                         text="(sem capa)",
                                         fg=C()["preview_fg"])

            self.janela.after(0, fim)

        threading.Thread(target=baixar_capa, daemon=True).start()

        if (r["fonte"] == "MusicBrainz"
                and r.get("id")
                and r.get("id_tipo") == "release-group"):
            self.status.set_working(T("editor_baixando_faixas"))

            def obter():
                _, faixas = obter_faixas_rg(r["id"])

                def fim():
                    if faixas:
                        self.faixas_mb = faixas
                        self.status.set_ok(
                            T("editor_album_n_faixas", n=len(faixas)))
                        self._auto_associar()
                    else:
                        self.status.set_aviso(
                            T("editor_erro_obter_faixas"))

                self.janela.after(0, fim)

            threading.Thread(target=obter, daemon=True).start()
        elif (r["fonte"] == "MusicBrainz"
                and r.get("id")
                and r.get("id_tipo") == "release"):
            self.status.set_working(T("editor_baixando_faixas"))

            def obter2():
                faixas = obter_faixas_release(r["id"])

                def fim2():
                    if faixas:
                        self.faixas_mb = faixas
                        self.status.set_ok(
                            T("editor_release_n_faixas", n=len(faixas)))
                        self._auto_associar()
                    else:
                        self.status.set_aviso(
                            T("editor_erro_obter_faixas"))

                self.janela.after(0, fim2)

            threading.Thread(target=obter2, daemon=True).start()
        else:
            self.faixas_mb = []
            self._limpar_mapeamento()
            self.status.set_ok(T("editor_capa_campos_ok"))

    def _capa_do_pc(self):
        c = filedialog.askopenfilename(
            title=T("dlg_escolher_capa"),
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp"),
                       ("Todos", "*.*")])
        if not c:
            return
        self._push_undo()
        with open(c, "rb") as f:
            self.capa_bytes_atual = f.read()
        self.capa_tk = preview_quadrado(self.capa_bytes_atual, LADO_PREVIEW)
        self.lbl_capa.config(image=self.capa_tk, text="")
        self.status.set_ok(T("editor_capa_do_pc_ok"))

    def _capa_colar(self):
        try:
            img = ImageGrab.grabclipboard()
            if img is None:
                return
            self._push_undo()
            if isinstance(img, Image.Image):
                buf = io.BytesIO()
                img.convert("RGB").save(buf, "PNG")
                self.capa_bytes_atual = buf.getvalue()
                self.capa_tk = preview_quadrado(self.capa_bytes_atual,
                                                LADO_PREVIEW)
                self.lbl_capa.config(image=self.capa_tk, text="")
                self.status.set_ok(T("editor_capa_colada"))
            elif isinstance(img, list) and img:
                with open(img[0], "rb") as f:
                    self.capa_bytes_atual = f.read()
                self.capa_tk = preview_quadrado(self.capa_bytes_atual,
                                                LADO_PREVIEW)
                self.lbl_capa.config(image=self.capa_tk, text="")
                self.status.set_ok(T("editor_capa_colada"))
        except Exception as e:
            self.status.set_erro(T("erro_generico", e=e))

    def _aplicar(self):
        valores_comuns = {
            "artista": self.entry_artista.get().strip(),
            "album": self.entry_album.get().strip(),
            "ano": self.entry_ano.get().strip(),
            "genero": self.entry_genero.get().strip(),
        }
        aplicar_comuns = {
            "artista": self.var_aplicar_artista.get(),
            "album": self.var_aplicar_album.get(),
            "ano": self.var_aplicar_ano.get(),
            "genero": self.var_aplicar_genero.get(),
        }
        if not any(aplicar_comuns.values()):
            if not messagebox.askyesno(
                    T("dialogo_confirmar"),
                    T("editor_msg_confirmar_campos")):
                return

        ignorar_capa = self.var_ignorar_capa.get()

        tarefas = []
        for row in self.mapeamento:
            caminho = row.get("caminho")
            if not caminho:
                continue
            dados = {}
            d_orig = self.dados_por_musica.get(caminho, {})
            for campo, aplicar in aplicar_comuns.items():
                if aplicar:
                    dados[campo] = valores_comuns[campo]
                else:
                    dados[campo] = d_orig.get(f"{campo}_orig", "")
            dados["titulo"] = row.get("titulo_final", "")
            dados["faixa"] = row.get("num", "")
            tarefas.append((caminho, dados))

        if not tarefas:
            messagebox.showinfo(T("dialogo_aviso"),
                T("editor_msg_nada_aplicar"))
            return

        try:
            pai = self.parent
            caminhos_alvo = [c for c, _ in tarefas]
            if (hasattr(pai, "player") and pai.player.musica_atual
                    and pai.player.musica_atual in caminhos_alvo):
                pai.player.parar()
            elif hasattr(pai, "player"):
                pai.player.liberar_total()
        except Exception:
            pass

        self._set_ocupado(True)
        self.status.set_working(T("editor_aplicando", n=len(tarefas)))

        def rodar():
            ok = 0
            erros = []
            for caminho, dados in tarefas:
                try:
                    aplicar_completo(caminho, dados, self.capa_bytes_atual,
                                     self.profile,
                                     ignorar_capa=ignorar_capa)
                    ok += 1
                    try:
                        pai = self.parent
                        if hasattr(pai, "_invalidar_thumb"):
                            pai._invalidar_thumb(caminho)
                        if hasattr(pai, "_invalidar_info"):
                            pai._invalidar_info(caminho)
                    except Exception:
                        pass
                except Exception as e:
                    erros.append((os.path.basename(caminho), str(e)))

            def finalizar():
                self._set_ocupado(False)
                for nome, err in erros:
                    self.log.insert("end", f"ERRO {nome}: {err}\n")
                self.log.see("end")
                if ok == len(tarefas):
                    self.status.set_ok(T("editor_aplicado", n=ok))
                else:
                    self.status.set_erro(f"{ok}/{len(tarefas)}")
                if self.on_done:
                    try:
                        self.on_done()
                    except Exception:
                        pass
                if ok == len(tarefas):
                    messagebox.showinfo(T("dialogo_pronto"),
                        T("editor_msg_pronto", n=ok))
                    self.janela.destroy()

            self.janela.after(0, finalizar)

        threading.Thread(target=rodar, daemon=True).start()


# =====================================================================
# SELETOR DE PERFIL
# =====================================================================
class PerfilPicker:
    def __init__(self, parent, perfil_atual_nome_or_dict):
        self.escolhido = None
        self.perfis = carregar_perfis()
        self.janela = tk.Toplevel(parent)
        self.janela.title(T("perfil_escolher_titulo"))
        self.janela.geometry("460x420")
        self.janela.transient(parent)
        self.janela.grab_set()
        self.janela.configure(bg=C()["bg"])

        ttk.Label(self.janela, text=T("perfil_selecione"),
                  padding=8).pack(anchor="w")
        self.lista = tk.Listbox(self.janela, height=12)
        for nome in self.perfis:
            self.lista.insert("end", nome)
        self.lista.pack(fill="both", expand=True, padx=8)
        self.desc = ttk.Label(self.janela, text="", wraplength=420,
                              foreground="gray", padding=8)
        self.desc.pack(fill="x")
        self.lista.bind("<<ListboxSelect>>", self._on_sel)

        bt = ttk.Frame(self.janela, padding=8)
        bt.pack(side="bottom", fill="x")
        ttk.Button(bt, text=T("perfil_btn_escolher"), command=self._ok,
                   style="Primary.TButton", width=12).pack(side="right",
                                                          ipady=4)
        ttk.Button(bt, text=T("cancelar"), command=self.janela.destroy,
                   style="Danger.TButton", width=12).pack(side="right",
                                                          padx=4, ipady=4)

        aplicar_tema_janela(self.janela)

    def _on_sel(self, e=None):
        sel = self.lista.curselection()
        if not sel:
            return
        self.desc.config(text=self.perfis[self.lista.get(sel[0])].get(
            "descricao", ""))

    def _ok(self):
        sel = self.lista.curselection()
        if not sel:
            return
        nome = self.lista.get(sel[0])
        self.escolhido = dict(self.perfis[nome])
        self.janela.destroy()


# =====================================================================
# GERENCIADOR DE PERFIS
# =====================================================================
class PerfisWindow:
    def __init__(self, parent, on_change=None):
        self.on_change = on_change
        self.perfis = carregar_perfis()
        self.nome_atual = None

        self.janela = tk.Toplevel(parent)
        self.janela.title(T("perfil_gerenciar_titulo"))
        self.janela.geometry("860x680")
        self.janela.transient(parent)
        self.janela.configure(bg=C()["bg"])
        self.janela.grab_set()

        esq = ttk.Frame(self.janela, padding=6)
        esq.pack(side="left", fill="y")
        ttk.Label(esq, text=T("perfis_titulo_label")).pack(anchor="w")
        self.lista = tk.Listbox(esq, width=28, height=20)
        self.lista.pack(fill="y", expand=True, pady=4)
        self.lista.bind("<<ListboxSelect>>", self._on_sel)
        ttk.Button(esq, text=T("perfis_btn_novo"),
                   command=self._novo).pack(fill="x", pady=2)
        ttk.Button(esq, text=T("perfis_btn_remover"),
                   command=self._remover,
                   style="Danger.TButton").pack(fill="x")

        dir_ = ttk.Frame(self.janela, padding=6)
        dir_.pack(side="left", fill="both", expand=True)

        normal = ttk.LabelFrame(dir_, text=T("perfis_basicas"))
        normal.pack(fill="x", pady=4)
        self.entries = {}

        def add(label, key, row):
            ttk.Label(normal, text=label).grid(row=row, column=0,
                                               sticky="e", padx=4, pady=3)
            e = ttk.Entry(normal, width=42)
            e.grid(row=row, column=1, sticky="we", padx=4, pady=3)
            self.entries[key] = e

        add(T("perfis_nome"), "_nome", 0)
        add(T("perfis_descricao"), "descricao", 1)
        add(T("perfis_tag_version"), "tag_version", 2)
        add(T("perfis_encoding"), "encoding", 3)
        add(T("perfis_keep_frames"), "keep_frames", 4)
        add(T("perfis_cover_size"), "cover_size", 5)
        add(T("perfis_cover_quality"), "cover_quality", 6)
        add(T("perfis_write_id3v1"), "write_id3v1", 7)
        normal.columnconfigure(1, weight=1)

        self.var_avancado = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            dir_,
            text=T("perfis_modo_avancado"),
            variable=self.var_avancado,
            command=self._toggle_avancado
        ).pack(anchor="w", padx=4, pady=(10, 2))

        self.frame_avancado = ttk.LabelFrame(dir_, text=T("perfis_avancadas"))
        av = self.frame_avancado
        self.entries_av = {}

        def add_av(label, key, row):
            ttk.Label(av, text=label).grid(row=row, column=0, sticky="e",
                                           padx=4, pady=3)
            e = ttk.Entry(av, width=42)
            e.grid(row=row, column=1, sticky="we", padx=4, pady=3)
            self.entries_av[key] = e

        add_av(T("perfis_subsampling"), "cover_subsampling", 0)
        add_av(T("perfis_progressive"), "cover_progressive", 1)
        add_av(T("perfis_mime"), "cover_mime", 2)
        add_av(T("perfis_apic_tipo"), "cover_type", 3)
        add_av(T("perfis_padding"), "padding", 4)
        add_av(T("perfis_unsync"), "unsync", 5)
        add_av(T("perfis_remove_padding"), "remove_padding", 6)
        av.columnconfigure(1, weight=1)

        bt = ttk.Frame(dir_)
        bt.pack(side="bottom", fill="x", pady=8)
        ttk.Button(bt, text=T("perfis_salvar"), command=self._salvar,
                   style="Success.TButton", width=12).pack(side="right",
                                                           ipady=4)
        ttk.Button(bt, text=T("perfis_cancelar"), command=self.janela.destroy,
                   style="Danger.TButton", width=12).pack(side="right",
                                                          padx=4, ipady=4)

        ttk.Label(dir_, text=T("perfis_arquivo_label") + " " + PERFIS_PATH,
                  foreground="gray").pack(side="bottom", anchor="w",
                                          pady=(6, 0))

        self._recarregar_lista()
        if self.perfis:
            self.lista.selection_set(0)
            self._on_sel()

        aplicar_tema_janela(self.janela)

    def _toggle_avancado(self):
        if self.var_avancado.get():
            self.frame_avancado.pack(fill="x", pady=6)
        else:
            self.frame_avancado.pack_forget()

    def _recarregar_lista(self):
        self.lista.delete(0, "end")
        for nome in self.perfis:
            self.lista.insert("end", nome)

    def _on_sel(self, e=None):
        sel = self.lista.curselection()
        if not sel:
            return
        nome = self.lista.get(sel[0])
        self.nome_atual = nome
        p = self.perfis[nome]
        valores = {
            "_nome": nome, "descricao": p.get("descricao", ""),
            "tag_version": str(p.get("tag_version", 3)),
            "encoding": str(p.get("encoding", 1)),
            "keep_frames": ", ".join(p.get("keep_frames", [])),
            "cover_size": str(p.get("cover_size", 250)),
            "cover_quality": str(p.get("cover_quality", 90)),
            "write_id3v1": "sim" if p.get("write_id3v1", True) else "nao",
        }
        for k, e in self.entries.items():
            e.delete(0, tk.END)
            e.insert(0, valores.get(k, ""))
        valores_av = {
            "cover_subsampling": str(p.get("cover_subsampling", 0)),
            "cover_progressive": "sim" if p.get("cover_progressive",
                                                 False) else "nao",
            "cover_mime": p.get("cover_mime", "image/jpeg"),
            "cover_type": str(p.get("cover_type", 3)),
            "padding": str(p.get("padding", "")),
            "unsync": "sim" if p.get("unsync", False) else "nao",
            "remove_padding": "sim" if p.get("remove_padding",
                                              False) else "nao",
        }
        for k, e in self.entries_av.items():
            e.delete(0, tk.END)
            e.insert(0, valores_av.get(k, ""))

    def _novo(self):
        nome = T("perfil_novo_perfil", n=len(self.perfis)+1)
        self.perfis[nome] = dict(
            PERFIS_DEFAULT["Universal (maxima compatibilidade)"])
        self._recarregar_lista()
        self.lista.selection_clear(0, "end")
        self.lista.selection_set("end")
        self._on_sel()

    def _remover(self):
        if not self.nome_atual:
            return
        if not messagebox.askyesno(T("dialogo_confirmar"),
                                   T("perfis_msg_remover", nome=self.nome_atual)):
            return
        self.perfis.pop(self.nome_atual, None)
        self.nome_atual = None
        self._recarregar_lista()

    def _bool(self, s):
        return s.strip().lower() in ("sim", "s", "yes", "y", "1", "true")

    def _salvar(self):
        nome = self.entries["_nome"].get().strip()
        if not nome:
            messagebox.showwarning(T("dialogo_aviso"), T("perfis_msg_nome_vazio"))
            return
        try:
            keep = [x.strip().upper() for x in
                    self.entries["keep_frames"].get().split(",")
                    if x.strip()]
            p = {
                "descricao": self.entries["descricao"].get().strip(),
                "tag_version": int(self.entries["tag_version"].get() or "3"),
                "encoding": int(self.entries["encoding"].get() or "1"),
                "keep_frames": keep,
                "cover_size": int(self.entries["cover_size"].get() or "250"),
                "cover_quality": int(self.entries["cover_quality"].get()
                                     or "90"),
                "write_id3v1": self._bool(
                    self.entries["write_id3v1"].get()),
                "cover_subsampling": int(
                    self.entries_av["cover_subsampling"].get() or "0"),
                "cover_progressive": self._bool(
                    self.entries_av["cover_progressive"].get()),
                "cover_mime": self.entries_av["cover_mime"].get().strip()
                              or "image/jpeg",
                "cover_type": int(
                    self.entries_av["cover_type"].get() or "3"),
                "unsync": self._bool(self.entries_av["unsync"].get()),
                "remove_padding": self._bool(
                    self.entries_av["remove_padding"].get()),
            }
            pad = self.entries_av["padding"].get().strip()
            if pad:
                p["padding"] = int(pad)
        except Exception as e:
            messagebox.showerror(T("dialogo_erro"), T("perfis_msg_valor_invalido", err=e))
            return
        if self.nome_atual and self.nome_atual != nome:
            self.perfis.pop(self.nome_atual, None)
        self.perfis[nome] = p
        salvar_perfis(self.perfis)
        self.nome_atual = nome
        self._recarregar_lista()
        if self.on_change:
            try:
                self.on_change()
            except Exception:
                pass
        messagebox.showinfo("OK", T("perfil_salvo"))




# =====================================================================
# ONBOARDING - Boas-vindas + Escolher idioma + Tutorial
# =====================================================================
class OnboardingWindow:
    """Janela de primeira execucao: escolher idioma + tutorial."""

    def __init__(self, parent):
        self.parent = parent
        self.idioma_escolhido = None
        self.tema_escolhido = None
        self.slide_atual = 0
        self.total_slides = 5
        self._idioma_temp = IDIOMA_PADRAO

        self.janela = tk.Toplevel(parent)
        self.janela.title("Bem-vindo / Welcome")
        self.janela.geometry("720x520")
        self.janela.resizable(False, False)
        self.janela.configure(bg=C()["bg"])
        try:
            aplicar_barra_escura_windows(self.janela, TEMA["escuro"])
        except Exception:
            pass
        try:
            self.janela.lift()
            self.janela.attributes("-topmost", True)
            self.janela.attributes("-topmost", False)
        except Exception:
            pass

        # Centraliza
        self.janela.update_idletasks()
        w = self.janela.winfo_width()
        h = self.janela.winfo_height()
        sw = self.janela.winfo_screenwidth()
        sh = self.janela.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.janela.geometry(f"+{x}+{y}")

        # Container principal
        self.container = ttk.Frame(self.janela)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Comeca pela tela de escolher idioma
        self._mostrar_escolher_idioma()

    # -----------------------------------------------------------------
    # TELA 1 - Escolher idioma
    # -----------------------------------------------------------------
    def _mostrar_escolher_idioma(self):
        self._limpar_container()

        ttk.Label(self.container, text="Bem-vindo / Welcome / Bienvenido",
                  font=("Segoe UI", 16, "bold")).pack(pady=(20, 6))
        ttk.Label(self.container,
                  text="Escolha seu idioma / Choose your language / "
                       "Elige tu idioma:",
                  font=("Segoe UI", 11)).pack(pady=(0, 30))

        # Nomes dos idiomas
        nomes = [nome for _, nome in IDIOMAS_DISPONIVEIS]
        self.combo_idioma_onb = ttk.Combobox(
            self.container, values=nomes, state="readonly", width=28,
            font=("Segoe UI", 11))
        self.combo_idioma_onb.set(nomes[0] if nomes else "")
        self.combo_idioma_onb.pack(pady=10)

        ttk.Label(self.container,
                  text="(Você poderá mudar depois em Configurações)",
                  foreground="gray", font=("Segoe UI", 9)).pack(pady=(4, 30))

        ttk.Button(self.container, text=T("onb_continuar"),
                   command=self._confirmar_idioma,
                   style="Primary.TButton",
                   width=28).pack(ipady=8)

    def _confirmar_idioma(self):
        nome = self.combo_idioma_onb.get()
        codigo = codigo_do_nome(nome)
        self.idioma_escolhido = codigo
        self._idioma_temp = codigo
        try:
            definir_idioma(codigo)
        except Exception:
            pass
        self._mostrar_escolher_tema()

    def _mostrar_escolher_tema(self):
        self._limpar_container()

        ttk.Label(self.container,
                  text=T("onb_escolha_tema"),
                  font=("Segoe UI", 14, "bold")).pack(pady=(20, 30))

        self.var_tema_onb = tk.StringVar(value="auto")

        def _mk(label, valor):
            ttk.Radiobutton(self.container, text=label,
                            variable=self.var_tema_onb,
                            value=valor).pack(pady=6,
                                              anchor="center")

        _mk(T("onb_tema_auto"), "auto")
        _mk(T("onb_tema_claro"), "claro")
        _mk(T("onb_tema_escuro"), "escuro")

        ttk.Button(self.container, text=T("onb_continuar"),
                   command=self._confirmar_tema,
                   style="Primary.TButton",
                   width=28).pack(pady=(30, 0), ipady=8)

    def _confirmar_tema(self):
        self.tema_escolhido = self.var_tema_onb.get()
        # Aplica preview imediato
        if self.tema_escolhido == "escuro":
            TEMA["escuro"] = True
            TEMA["auto"] = False
        elif self.tema_escolhido == "claro":
            TEMA["escuro"] = False
            TEMA["auto"] = False
        else:  # auto
            TEMA["auto"] = True
            d = detectar_tema_sistema()
            if d is not None:
                TEMA["escuro"] = d
        try:
            aplicar_tema_global(TEMA["escuro"])
            _aplicar_em_tk(self.janela, TEMA["escuro"])
            aplicar_barra_escura_windows(self.janela, TEMA["escuro"])
        except Exception:
            pass
        # Fecha — o tour interativo roda depois que o app abrir
        self._fechar()

    # -----------------------------------------------------------------
    # TELA 2 - Tutorial
    # -----------------------------------------------------------------
    def _mostrar_tutorial(self):
        self._limpar_container()

        # Header
        header = ttk.Frame(self.container)
        header.pack(fill="x")
        ttk.Label(header, text=T("onb_bemvindo"),
                  font=("Segoe UI", 14, "bold")).pack(side="left")

        # Area do slide
        self.frame_slide = ttk.Frame(self.container)
        self.frame_slide.pack(fill="both", expand=True, pady=(20, 10))

        # Navegacao
        nav = ttk.Frame(self.container)
        nav.pack(fill="x", side="bottom")

        self.btn_anterior = ttk.Button(nav, text=T("onb_anterior"),
                                       command=self._slide_anterior)
        self.btn_anterior.pack(side="left", padx=4, ipady=6)

        self.btn_pular = ttk.Button(nav, text=T("onb_pular"),
                                     command=self._pular,
                                     style="Danger.TButton")
        self.btn_pular.pack(side="right", padx=4, ipady=6)

        self.btn_prox = ttk.Button(nav, text=T("onb_proximo"),
                                    command=self._slide_proximo,
                                    style="Success.TButton")
        self.btn_prox.pack(side="right", padx=4, ipady=6)

        # Indicador de progresso
        self.lbl_prog = ttk.Label(nav, text="", foreground="gray")
        self.lbl_prog.pack(side="left", padx=20)

        self.slide_atual = 0
        self._render_slide()

    def _render_slide(self):
        for w in self.frame_slide.winfo_children():
            w.destroy()

        num = self.slide_atual + 1
        titulo = T(f"onb_slide{num}_titulo")
        texto = T(f"onb_slide{num}_texto")

        ttk.Label(self.frame_slide, text=titulo,
                  font=("Segoe UI", 22, "bold")).pack(pady=(40, 20))
        ttk.Label(self.frame_slide, text=texto,
                  font=("Segoe UI", 11), wraplength=600,
                  justify="center").pack(padx=20)

        # Atualiza botoes
        self.btn_anterior.config(
            state=("normal" if self.slide_atual > 0 else "disabled"))

        if self.slide_atual == self.total_slides - 1:
            self.btn_prox.config(text=T("onb_comecar"),
                                  style="Success.TButton")
            self.btn_pular.config(state="disabled")
        else:
            self.btn_prox.config(text=T("onb_proximo"))
            self.btn_pular.config(state="normal")

        # Progresso
        self.lbl_prog.config(
            text=f"{num}/{self.total_slides}")

    def _slide_anterior(self):
        if self.slide_atual > 0:
            self.slide_atual -= 1
            self._render_slide()

    def _slide_proximo(self):
        if self.slide_atual < self.total_slides - 1:
            self.slide_atual += 1
            self._render_slide()
        else:
            self._fechar()

    def _pular(self):
        self._fechar()

    def _fechar(self):
        try:
            self.janela.destroy()
        except Exception:
            pass

    def _limpar_container(self):
        for w in self.container.winfo_children():
            w.destroy()



# =====================================================================
# TUTORIAL INTERATIVO (estilo CapCut)
# =====================================================================


# =====================================================================
# TUTORIAL INTERATIVO - versao leve (so bolha + borda)
# =====================================================================
class TutorialOverlay:
    """Tour interativo: destaca widget com borda e mostra bolha."""

    def __init__(self, root, app, passos):
        self.root = root
        self.app = app
        self.passos = passos
        self.idx = 0
        self.anel = None
        self.bubble = None
        self._ativo = False
        self._transp = "#ff00ff"  # cor magica de transparencia

    def iniciar(self):
        self._ativo = True
        self.root.bind("<Escape>", lambda e: self._fechar())
        self.root.after(150, self._mostrar_passo)

    def _get_alvo(self, widget_callable):
        if widget_callable is None:
            return None
        try:
            w = widget_callable()
            if w is None:
                return None
            self.root.update_idletasks()
            x = w.winfo_rootx()
            y = w.winfo_rooty()
            ww = w.winfo_width()
            hh = w.winfo_height()
            if ww <= 1 or hh <= 1:
                return None
            return (x, y, ww, hh)
        except Exception:
            return None

    def _mostrar_passo(self):
        if not self._ativo:
            return
        if self.idx >= len(self.passos):
            self._fechar()
            return

        passo = self.passos[self.idx]

        hook = passo.get("pre_hook")
        if hook:
            try:
                hook()
                self.root.update_idletasks()
                self.root.update()
            except Exception:
                pass

        self.root.after(150, self._desenhar)

    def _desenhar(self):
        if not self._ativo:
            return
        passo = self.passos[self.idx]
        alvo = self._get_alvo(passo.get("widget"))

        self._destruir_anel()
        if alvo:
            self._criar_anel(alvo)
        self._criar_bubble(passo, alvo)

    def _destruir_anel(self):
        if self.anel is not None:
            try:
                self.anel.destroy()
            except Exception:
                pass
            self.anel = None

    def _criar_anel(self, alvo):
        x, y, w, h = alvo
        margem = 6
        ax = x - margem
        ay = y - margem
        aw = w + 2 * margem
        ah = h + 2 * margem

        try:
            self.anel = tk.Toplevel(self.root)
            self.anel.overrideredirect(True)
            try:
                self.anel.attributes("-topmost", True)
            except Exception:
                pass
            try:
                self.anel.attributes("-transparentcolor", self._transp)
            except Exception:
                pass
            self.anel.configure(bg=self._transp)
            self.anel.geometry(f"{aw}x{ah}+{ax}+{ay}")

            cv = tk.Canvas(self.anel, bg=self._transp,
                            highlightthickness=0, bd=0)
            cv.pack(fill="both", expand=True)
            cv.create_rectangle(2, 2, aw - 2, ah - 2,
                                 outline="#dc143c", width=3)
        except Exception:
            self.anel = None

    def _criar_bubble(self, passo, alvo):
        if self.bubble is not None:
            try:
                self.bubble.destroy()
            except Exception:
                pass

        self.bubble = tk.Toplevel(self.root)
        self.bubble.overrideredirect(True)
        try:
            self.bubble.attributes("-topmost", True)
        except Exception:
            pass

        c = C()
        frame = tk.Frame(self.bubble, bg=c["bg"], bd=1, relief="solid")
        frame.pack(fill="both", expand=True)

        head = tk.Frame(frame, bg=c["btn_primary"])
        head.pack(fill="x")
        tk.Label(head, text=T(passo["titulo"]),
                 bg=c["btn_primary"], fg=c["btn_primary_fg"],
                 font=("Segoe UI", 11, "bold"),
                 anchor="w").pack(fill="x", padx=12, pady=8)

        txt_wrap = 340
        tk.Label(frame, text=T(passo["texto"]),
                 bg=c["bg"], fg=c["fg"],
                 font=("Segoe UI", 10), wraplength=txt_wrap,
                 justify="left").pack(anchor="w", padx=14, pady=(12, 10))

        nav = tk.Frame(frame, bg=c["bg"])
        nav.pack(fill="x", padx=10, pady=(0, 12))

        tk.Label(nav, text=f"{self.idx + 1}/{len(self.passos)}",
                 bg=c["bg"], fg="#888").pack(side="left", padx=4)

        ttk.Button(nav, text=T("onb_pular"),
                   command=self._fechar,
                   style="Danger.TButton",
                   width=9).pack(side="right", padx=2)

        ultimo = (self.idx == len(self.passos) - 1)
        txt = T("onb_comecar") if ultimo else T("onb_proximo")
        ttk.Button(nav, text=txt, command=self._proximo,
                   style="Success.TButton",
                   width=13).pack(side="right", padx=2)

        if self.idx > 0:
            ttk.Button(nav, text=T("onb_anterior"),
                       command=self._anterior,
                       width=9).pack(side="right", padx=2)

        self.bubble.update_idletasks()
        bw = self.bubble.winfo_reqwidth()
        bh = self.bubble.winfo_reqheight()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        if alvo:
            x, y, w, h = alvo
            bx = x + w // 2 - bw // 2
            by = y + h + 20
            if by + bh > sh - 20:
                by = y - bh - 20
            if by < 20:
                by = 20
            if bx < 20:
                bx = 20
            if bx + bw > sw - 20:
                bx = sw - bw - 20
        else:
            bx = sw // 2 - bw // 2
            by = sh // 2 - bh // 2

        self.bubble.geometry(f"+{bx}+{by}")

    def _anterior(self):
        if self.idx > 0:
            self.idx -= 1
            self._mostrar_passo()

    def _proximo(self):
        self.idx += 1
        self._mostrar_passo()

    def _fechar(self):
        self._ativo = False
        self._destruir_anel()
        if self.bubble is not None:
            try:
                self.bubble.destroy()
            except Exception:
                pass
            self.bubble = None
        try:
            self.root.unbind("<Escape>")
        except Exception:
            pass


# =====================================================================
# APP PRINCIPAL
# =====================================================================
class App:
    def __init__(self, root):
        self.root = root
        root.geometry("1180x740")
        root.minsize(960, 600)

        self.config = carregar_config()
        self.covers_ignorados = carregar_skip_covers()

        # Inicializa idioma ANTES de qualquer texto
        try:
            definir_idioma(self.config.get("idioma", IDIOMA_PADRAO))
        except Exception as e:
            print(f"Erro ao definir idioma: {e}")

        # Agora sim pode traduzir o titulo
        root.title(T("app_titulo"))

        TEMA["escuro"] = bool(self.config.get("modo_escuro", False))
        TEMA["auto"] = bool(self.config.get("tema_automatico", False))
        if TEMA["auto"]:
            d = detectar_tema_sistema()
            if d is not None:
                TEMA["escuro"] = d

        self.perfis = carregar_perfis()
        self.perfil_atual_nome = tk.StringVar(
            value=list(self.perfis.keys())[0] if self.perfis else "")

        self.pastas_salvas = [p for p in self.config.get("pastas_salvas", [])
                              if os.path.isdir(p)]
        self.pasta = tk.StringVar(
            value=self.pastas_salvas[0] if self.pastas_salvas else "")

        self.incluir_subpastas = tk.BooleanVar(value=False)
        self.arquivos = []
        self.capa_tk = None
        self.capa_bytes_atual = None
        self._thumb_cache = {}
        self._info_cache = {}

        self.busca_var = tk.StringVar()

        self.pl_playlist_atual = tk.StringVar()
        self.pl_caminho_atual = ""
        self.pl_arquivos = []
        self.pl_playlists = []
        self.pl_busca_var = tk.StringVar()

        self._sort_col = None
        self._sort_reverse = False

        self.var_modo_escuro = tk.BooleanVar(value=bool(
            self.config.get("modo_escuro", False)))
        self.var_tema_auto = tk.BooleanVar(value=bool(
            self.config.get("tema_automatico", False)))
        _tam_pt = self.config.get("tamanho_capa_override",
                                   "Padrão do perfil")
        self.tamanho_capa_var = tk.StringVar(
            value=_tam_para_display(_tam_pt))
        _filtro_pt = self.config.get("filtro_atual", "Mostrar todas")
        self.filtro_var = tk.StringVar(
            value=_filtro_para_display(_filtro_pt))

        self.player = Player()
        _PLAYER_REF["player"] = self.player

        # Barra superior com status + botao configuracoes
        barra_topo = ttk.Frame(root)
        barra_topo.pack(fill="x", padx=4, pady=(4, 0))

        criar_botao_canvas(barra_topo, "gear",
                            self._abrir_configuracoes,
                            T("tooltip_config"),
                            size=34, lado="right", padx=4)

        self.status_global = StatusLabel(barra_topo,
                                          text=T("st_pronto"),
                                          anchor="w")
        self.status_global.pack(side="left", fill="x",
                                 expand=True, padx=(4, 8))
        self.status_global.set_idle(T("st_pronto"))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=4, pady=(4, 0))

        self.tab_inicio = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_inicio, text="  " + T("aba_inicio") + "  ")
        self._ui_inicio(self.tab_inicio)

        self.tab_play = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_play, text="  " + T("aba_playlist") + "  ")
        self._ui_playlist(self.tab_play)

        self._janela_config = None

        self._aplicar_tema_agora()
        self._loop_seek()

        # Restaura geometria salva da ultima sessao
        try:
            geom = self.config.get("janela_geometry", "")
            if geom and "x" in geom and "+" in geom:
                self.root.geometry(geom)
            if self.config.get("janela_zoom", False):
                try:
                    self.root.state("zoomed")
                except Exception:
                    pass
        except Exception:
            pass

        # Salva estado da janela ao fechar
        self.root.protocol("WM_DELETE_WINDOW", self._ao_fechar)

    def _ao_fechar(self):
        try:
            self.config["janela_geometry"] = self.root.geometry()
            try:
                self.config["janela_zoom"] = (
                    self.root.state() == "zoomed")
            except Exception:
                self.config["janela_zoom"] = False
            salvar_config(self.config)
        except Exception:
            pass
        try:
            self.player.parar()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    # ---------- tema ----------
    def _aplicar_tema_agora(self):
        escuro = bool(TEMA["escuro"])
        aplicar_tema_global(escuro)
        _aplicar_em_tk(self.root, escuro)
        c = C()
        try:
            self.frame_preview.configure(bg=c["preview_bg"])
            self.lbl_preview.configure(bg=c["preview_bg"])
        except Exception:
            pass
        try:
            self.menu_ctx.configure(
                bg=c["entry_bg"], fg=c["entry_fg"],
                activebackground=c["select_bg"],
                activeforeground=c["select_fg"], bd=0)
        except Exception:
            pass
        try:
            self.tree.tag_configure("frozen",
                                    background=c["row_frozen_bg"],
                                    foreground=c["row_frozen_fg"])
            self.tree.tag_configure("placeholder", foreground="#888888")
        except Exception:
            pass
        try:
            self.player_inicio.atualizar_cores()
        except Exception:
            pass
        try:
            self.player_playlist.atualizar_cores()
        except Exception:
            pass
        try:
            self.player_inicio.seek_bar._redesenhar()
        except Exception:
            pass
        try:
            self.player_playlist.seek_bar._redesenhar()
        except Exception:
            pass
        try:
            aplicar_barra_escura_windows(self.root, escuro)
        except Exception:
            pass
        try:
            atualizar_botoes_canvas()
        except Exception:
            pass
        self.root.update_idletasks()

    def _trocar_idioma(self, event=None):
        nome = self.var_idioma.get()
        codigo = codigo_do_nome(nome)
        self.config["idioma"] = codigo
        salvar_config(self.config)
        try:
            definir_idioma(codigo)
        except Exception:
            pass
        messagebox.showinfo(T("cfg_idioma"),
                             T("idioma_alterado"))

    def _toggle_modo_escuro(self):
        if self.var_tema_auto.get():
            return
        TEMA["escuro"] = self.var_modo_escuro.get()
        self.config["modo_escuro"] = TEMA["escuro"]
        salvar_config(self.config)
        self._aplicar_tema_agora()

    def _toggle_tema_auto(self):
        auto = self.var_tema_auto.get()
        TEMA["auto"] = auto
        self.config["tema_automatico"] = auto
        salvar_config(self.config)
        if auto:
            d = detectar_tema_sistema()
            if d is not None:
                TEMA["escuro"] = d
                self.var_modo_escuro.set(d)
                self.config["modo_escuro"] = d
                salvar_config(self.config)
        self._aplicar_tema_agora()
    def _abrir_configuracoes(self):
        # Evita abrir varias janelas de config ao mesmo tempo
        if self._janela_config is not None:
            try:
                self._janela_config.lift()
                self._janela_config.focus_force()
                return
            except Exception:
                self._janela_config = None

        jan = tk.Toplevel(self.root)
        jan.title(T("btn_configuracoes"))
        jan.geometry("760x820")
        jan.minsize(640, 600)
        jan.transient(self.root)
        jan.configure(bg=C()["bg"])
        jan.grab_set()
        aplicar_barra_escura_windows(jan, TEMA["escuro"])

        def fechar():
            self._janela_config = None
            jan.destroy()

        jan.protocol("WM_DELETE_WINDOW", fechar)

        self._ui_config(jan)

        aplicar_tema_janela(jan)
        # Botao fechar no rodape
        rodape = ttk.Frame(jan, padding=8)
        rodape.pack(side="bottom", fill="x")
        ttk.Button(rodape, text=T("cfg_fechar"), command=fechar,
                   style="Danger.TButton", width=12).pack(side="right",
                                                          ipady=4)
        
    def _trocar_tamanho_override(self, event=None):
        display = self.tamanho_capa_var.get()
        pt = _display_para_tam(display)
        self.config["tamanho_capa_override"] = pt
        salvar_config(self.config)
        self._trocar_perfil()

    def _perfil_ativo(self):
        nome = self.perfil_atual_nome.get()
        p = dict(self.perfis.get(
            nome, PERFIS_DEFAULT["Universal (maxima compatibilidade)"]))
        tam = self.tamanho_capa_var.get()
        if tam and tam != T("tam_padrao"):
            try:
                p["cover_size"] = int(tam.split(" ")[0])
            except Exception:
                pass
        return p

    def _trocar_perfil(self, event=None):
        nome = self.perfil_atual_nome.get()
        p = self.perfis.get(nome, {})
        desc = p.get("descricao", "")
        tam = self.tamanho_capa_var.get()
        if tam and tam != T("tam_padrao"):
            desc = f"[capa {tam}] " + desc
        try:
            self.lbl_perfil_desc.config(text=desc[:70])
        except Exception:
            pass

    def _abrir_gerenciar_perfis(self):
        PerfisWindow(self.root, on_change=self._recarregar_perfis)

    def _recarregar_perfis(self):
        self.perfis = carregar_perfis()
        self.combo_perfil["values"] = list(self.perfis.keys())
        if self.perfil_atual_nome.get() not in self.perfis:
            self.perfil_atual_nome.set(list(self.perfis.keys())[0])
        self._trocar_perfil()

    def _normcase(self, caminho):
        return os.path.normcase(os.path.abspath(caminho))

    def _capa_ignorada(self, caminho):
        return self._normcase(caminho) in self.covers_ignorados

    def _toggle_ignorar_capa(self, caminho, ativo=None):
        nc = self._normcase(caminho)
        if ativo is None:
            ativo = nc not in self.covers_ignorados
        if ativo:
            self.covers_ignorados.add(nc)
        else:
            self.covers_ignorados.discard(nc)
        salvar_skip_covers(self.covers_ignorados)

    def _obter_thumb(self, capa_bytes, caminho):
        if caminho in self._thumb_cache:
            return self._thumb_cache[caminho]
        photo = thumb_pequena(capa_bytes)
        self._thumb_cache[caminho] = photo
        return photo

    def _invalidar_thumb(self, caminho):
        self._thumb_cache.pop(caminho, None)

    def _info_de(self, caminho):
        if caminho not in self._info_cache:
            self._info_cache[caminho] = ler_info(caminho)
        return self._info_cache[caminho]

    def _invalidar_info(self, caminho):
        self._info_cache.pop(caminho, None)

    # ---------- pastas ----------
    def escolher_pasta(self):
        p = filedialog.askdirectory(title=T("dlg_escolher_pasta"))
        if not p:
            return
        if p not in self.pastas_salvas:
            self.pastas_salvas.append(p)
            self.config["pastas_salvas"] = self.pastas_salvas
            salvar_config(self.config)
            self._atualizar_combo_pastas()
        self.pasta.set(p)
        self._recarregar_tudo()

    def _atualizar_combo_pastas(self):
        try:
            valores = [nome_curto_pasta(p) for p in self.pastas_salvas]
            self.combo_pastas["values"] = valores
        except Exception:
            pass

    def _trocar_pasta_pelo_combo(self, event=None):
        idx = self.combo_pastas.current()
        if idx < 0 or idx >= len(self.pastas_salvas):
            return
        self.pasta.set(self.pastas_salvas[idx])
        self._recarregar_tudo()

    def _remover_pasta_atual(self):
        p = self.pasta.get()
        if p in self.pastas_salvas:
            self.pastas_salvas.remove(p)
            self.config["pastas_salvas"] = self.pastas_salvas
            salvar_config(self.config)
        if self.pastas_salvas:
            self.pasta.set(self.pastas_salvas[0])
        else:
            self.pasta.set("")
        self._atualizar_combo_pastas()
        self._recarregar_tudo()

    def _recarregar_tudo(self):
        self._thumb_cache.clear()
        self._info_cache.clear()
        self.carregar_lista()
        self.pl_carregar_playlists()

    def _on_enter_pasta(self, event=None):
        self._recarregar_tudo()

    # ---------- busca ----------
    def _on_busca_mudou(self, *args):
        self._rebuild_view()

    # ---------- ordenação ----------
    def _setup_sorting(self):
        for col in ("musica", "album", "ano", "sub", "capa"):
            self.tree.heading(col, command=lambda c=col: self._sort_by(c))

    def _sort_by(self, col, forcar_direcao=None):
        if col == "capa":
            return
        if forcar_direcao is None:
            if self._sort_col == col:
                self._sort_reverse = not self._sort_reverse
            else:
                self._sort_col = col
                self._sort_reverse = False
        else:
            self._sort_col = col
            self._sort_reverse = forcar_direcao

        idx = {"musica": 0, "album": 1, "ano": 2, "sub": 3}[col]
        items = list(self.tree.get_children())

        def key(iid):
            vals = self.tree.item(iid, "values")
            v = vals[idx] if idx < len(vals) else ""
            if col == "ano":
                try:
                    return (0, int(v))
                except (ValueError, TypeError):
                    return (1, 0)
            return str(v).lower()

        items.sort(key=key, reverse=self._sort_reverse)
        for i, iid in enumerate(items):
            self.tree.move(iid, "", i)

        cabecalhos = {"musica": "Artista — Música", "album": "Álbum",
                      "ano": "Ano", "sub": "Subpasta", "capa": "Capa"}
        for col, txt in cabecalhos.items():
            if col == self._sort_col:
                arrow = " ▼" if self._sort_reverse else " ▲"
                self.tree.heading(col, text=txt + arrow)
            else:
                self.tree.heading(col, text=txt)

    def _passa_filtro(self, info, filtro):
        if filtro == "Mostrar todas" or not filtro:
            return True
        sem_capa = not info.get("capa")
        sem_artista_titulo = (not info.get("artista")
                              or not info.get("titulo"))
        sem_album = not info.get("album")
        sem_ano = not info.get("ano")
        if filtro == "Só sem capa":
            return sem_capa
        if filtro == "Só sem artista/título":
            return sem_artista_titulo
        if filtro == "Só sem álbum":
            return sem_album
        if filtro == "Só sem ano":
            return sem_ano
        if filtro == "Só incompletas (qualquer)":
            return (sem_capa or sem_artista_titulo
                    or sem_album or sem_ano)
        return True

    def _passa_busca(self, info, termo):
        if not termo:
            return True
        t = termo.lower()
        return (t in (info.get("titulo") or "").lower()
                or t in (info.get("artista") or "").lower()
                or t in (info.get("album") or "").lower()
                or t in (info.get("ano") or "").lower()
                or t in (info.get("genero") or "").lower())

    def _trocar_filtro(self, event=None):
        display = self.filtro_var.get()
        pt = _display_para_filtro(display)
        self.config["filtro_atual"] = pt
        salvar_config(self.config)
        self._rebuild_view()

    def _rebuild_view(self, sel_para_restaurar=None):
        if sel_para_restaurar is None:
            sel_anterior = list(self.tree.selection())
        else:
            sel_anterior = list(sel_para_restaurar)

        self.tree.delete(*self.tree.get_children())

        if not self.arquivos:
            self.lbl_status_pequeno.config(text="")
            return

        pasta = self.pasta.get()
        filtro_disp = self.filtro_var.get()
        filtro = _display_para_filtro(filtro_disp)
        termo = self.busca_var.get().strip()
        visiveis = 0
        for caminho in self.arquivos:
            info = self._info_de(caminho)
            if not self._passa_filtro(info, filtro):
                continue
            if not self._passa_busca(info, termo):
                continue
            rel = os.path.relpath(caminho, pasta) if pasta else \
                os.path.basename(caminho)
            sub = os.path.dirname(rel) or "."
            thumb = self._obter_thumb(info["capa"], caminho)
            tags = ("frozen",) if self._capa_ignorada(caminho) else ()
            self.tree.insert("", "end", iid=caminho, text="", image=thumb,
                             values=self._vals_row(info, sub, caminho),
                             tags=tags)
            visiveis += 1

        for caminho in sel_anterior:
            if self.tree.exists(caminho):
                self.tree.selection_add(caminho)

        if self._sort_col:
            direcao = self._sort_reverse
            self._sort_by(self._sort_col, forcar_direcao=direcao)

        total = len(self.arquivos)
        partes = []
        if visiveis != total:
            partes.append(T("st_v_de_n_filtro", v=visiveis, n=total))
        else:
            partes.append(T("st_n_musicas", n=total))
        if termo:
            partes.append(T("st_busca", termo=termo))
        if filtro != "Mostrar todas":
            partes.append(T("st_filtro", filtro=filtro_disp))
        self.lbl_status_pequeno.config(text=" — ".join(partes))

        if sel_anterior:
            for caminho in sel_anterior:
                if self.tree.exists(caminho):
                    self.tree.selection_set(caminho)
                    break
        self._on_select()

    # =================================================================
    # ABA INÍCIO
    # =================================================================
    def _ui_inicio(self, parent):
        l1 = ttk.Frame(parent)
        l1.pack(fill="x", padx=8, pady=4)
        ttk.Label(l1, text=T("lbl_perfil")).pack(side="left")
        self.combo_perfil = ttk.Combobox(l1,
                                         textvariable=self.perfil_atual_nome,
                                         values=list(self.perfis.keys()),
                                         state="readonly", width=26)
        self.combo_perfil.pack(side="left", padx=4)
        self.combo_perfil.bind("<<ComboboxSelected>>",
                                self._trocar_perfil)
        ttk.Button(l1, text=T("btn_perfis"),
                   command=self._abrir_gerenciar_perfis).pack(side="left",
                                                              padx=4)
        ttk.Checkbutton(l1, text=T("chk_incluir_subpastas"),
                        variable=self.incluir_subpastas,
                        command=self.carregar_lista).pack(side="left",
                                                          padx=12)

        l2 = ttk.Frame(parent)
        l2.pack(fill="x", padx=8, pady=2)
        ttk.Label(l2, text=T("lbl_tamanho_capa")).pack(side="left")
        self.combo_tamanho = ttk.Combobox(
            l2, textvariable=self.tamanho_capa_var,
            values=[_tam_para_display(k) for k in TAMANHOS_CAPA_UI],
            state="readonly", width=18)
        self.combo_tamanho.pack(side="left", padx=4)
        self.combo_tamanho.bind("<<ComboboxSelected>>",
                                self._trocar_tamanho_override)

        ttk.Label(l2, text=T("lbl_mostrar")).pack(side="left", padx=(12, 2))
        self.combo_filtro = ttk.Combobox(
            l2, textvariable=self.filtro_var,
            values=[_filtro_para_display(k) for k in FILTROS_UI],
            state="readonly", width=22)
        self.combo_filtro.pack(side="left")
        self.combo_filtro.bind("<<ComboboxSelected>>",
                                self._trocar_filtro)

        l3 = ttk.Frame(parent)
        l3.pack(fill="x", padx=8, pady=2)
        ttk.Label(l3, text=T("lbl_buscar")).pack(side="left")
        e_busca = ttk.Entry(l3, textvariable=self.busca_var)
        e_busca.pack(side="left", fill="x", expand=True, padx=4)
        self.busca_var.trace_add("write", self._on_busca_mudou)
        criar_botao_canvas(l3, "trash",
                            lambda: self.busca_var.set(""),
                            T("tooltip_limpar_busca"),
                            size=34, lado="left", padx=2)

        corpo = ttk.Frame(parent)
        corpo.pack(fill="both", expand=True, padx=8, pady=4)

        esq = ttk.LabelFrame(
            corpo,
            text=T("lblframe_musicas"))
        esq.pack(side="left", fill="both", expand=True)
        cols = ("musica", "album", "ano", "sub", "capa")
        self.tree = ttk.Treeview(esq, columns=cols, show="tree headings",
                                 selectmode="extended")
        self.tree.heading("#0", text="🎨")
        self.tree.column("#0", width=56, anchor="center", stretch=False)
        self.tree.heading("musica", text=T("col_musica"))
        self.tree.heading("album", text=T("col_album"))
        self.tree.heading("ano", text=T("col_ano"))
        self.tree.heading("sub", text=T("col_sub"))
        self.tree.heading("capa", text=T("col_capa"))
        self.tree.column("musica", width=260)
        self.tree.column("album", width=160)
        self.tree.column("ano", width=50, anchor="center")
        self.tree.column("sub", width=130)
        self.tree.column("capa", width=55, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(esq, orient="vertical",
                           command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        self._setup_sorting()

        self.menu_ctx = tk.Menu(self.root, tearoff=0)
        self.menu_ctx.add_command(label=T("menu_editar_meta"),
                                  command=self.editar_metadados)
        self.menu_ctx.add_command(label=T("menu_sel_album"),
                                  command=self._selecionar_mesmo_album)
        self.menu_ctx.add_command(label=T("menu_sel_artista"),
                                  command=self._selecionar_mesmo_artista)
        self.menu_ctx.add_separator()
        self.menu_ctx.add_command(label=T("menu_congelar_capa"),
                                  command=self._menu_toggle_capa)
        self.menu_ctx.add_command(label=T("menu_capa_pc"),
                                  command=self.trocar_capa)
        self.menu_ctx.add_command(label=T("menu_buscar_capa"),
                                  command=self.buscar_online)
        self.menu_ctx.add_separator()
        self.menu_ctx.add_command(label=T("menu_normalizar_sel"),
                                  command=self.normalizar_selecionados)
        self.menu_ctx.add_separator()
        self.menu_ctx.add_command(label=T("menu_tocar"),
                                  command=self._tocar_selecionada)
        self.menu_ctx.add_separator()
        self.menu_ctx.add_command(label=T("menu_corrigir_nome"),
                                  command=self.corrigir_nomes_suspeitos)

        dir_ = ttk.LabelFrame(corpo, text=T("lblframe_preview"))
        dir_.pack(side="left", fill="y", padx=(6, 0), ipadx=6, ipady=6)

        self.frame_preview = tk.Frame(
            dir_, bg=C()["preview_bg"],
            width=LADO_PREVIEW, height=LADO_PREVIEW,
            highlightthickness=0, bd=0)
        self.frame_preview.pack(padx=6, pady=6)
        self.frame_preview.pack_propagate(False)
        self.lbl_preview = tk.Label(self.frame_preview,
                                    bg=C()["preview_bg"])
        self.lbl_preview.pack(fill="both", expand=True)

        self.lbl_info = ttk.Label(dir_, text=T("lbl_selecione_musica"),
                                  wraplength=LADO_PREVIEW, justify="left")
        self.lbl_info.pack(padx=6)

        ttk.Label(
            dir_,
            text=T("aviso_antes_editar"),
            foreground="#cc7000", wraplength=LADO_PREVIEW,
            justify="center", font=("Segoe UI", 8)
        ).pack(padx=4, pady=(4, 2))

        bt = ttk.Frame(dir_)
        bt.pack(pady=4)
        ttk.Button(bt, text=T("btn_editar_metadados"),
                   command=self.editar_metadados,
                   style="Primary.TButton").pack(fill="x", pady=1)
        ttk.Button(bt, text=T("btn_capa_do_pc"),
                   command=self.trocar_capa).pack(fill="x", pady=1)
        ttk.Button(bt, text=T("btn_colar"),
                   command=self.colar_capa).pack(fill="x", pady=1)

        if DND:
            ttk.Label(dir_, text=T("lbl_arraste"),
                      foreground="#0066cc").pack(pady=2)
            self.lbl_preview.drop_target_register(DND_FILES)
            self.lbl_preview.dnd_bind("<<Drop>>", self._on_drop_preview)

        ttk.Separator(dir_, orient="horizontal").pack(fill="x", pady=4)
        pf = ttk.LabelFrame(dir_, text="Player")
        pf.pack(fill="x", padx=0, pady=2)
        self.player_inicio = PlayerControl(pf, self, mostrar_capa=False)
        self.player_inicio.pack(fill="x")

        ttk.Separator(dir_, orient="horizontal").pack(fill="x", pady=4)
        pf2 = ttk.LabelFrame(dir_, text=T("lblframe_pasta_atual"))
        pf2.pack(fill="x", padx=0, pady=2)
        linha_pasta = ttk.Frame(pf2)
        linha_pasta.pack(fill="x", padx=4, pady=4)
        criar_botao_canvas(linha_pasta, "folder",
                            self.escolher_pasta,
                            T("btn_escolher_pasta"),
                            size=34, lado="left", padx=2)
        self.combo_pastas = ttk.Combobox(linha_pasta,
                                          state="readonly", width=18)
        self.combo_pastas.pack(side="left", padx=4, fill="x", expand=True)
        self.combo_pastas.bind("<<ComboboxSelected>>",
                                self._trocar_pasta_pelo_combo)
        self._atualizar_combo_pastas()
        criar_botao_canvas(linha_pasta, "trash",
                            self._remover_pasta_atual,
                            T("btn_recarregar"),
                            size=34, lado="left", padx=2)

        ttk.Separator(dir_, orient="horizontal").pack(fill="x", pady=4)
        self.btn_normalizar_todas = ttk.Button(
            dir_, text=T("btn_normalizar_todas"),
            command=self.normalizar_todas, width=24,
            style="Warning.TButton")
        self.btn_normalizar_todas.pack(pady=2)

        self.lbl_perfil_desc = ttk.Label(dir_, text="", foreground="gray",
                                          wraplength=LADO_PREVIEW,
                                          justify="left")
        self.lbl_perfil_desc.pack(padx=4, pady=(2, 0), fill="x")
        self._trocar_perfil()

        # Linha pequena de status (escondida — usamos o topbar)
        self.lbl_status_pequeno = ttk.Label(parent, text="",
                                            foreground="gray")
        # NÃO empacotar!
        # existindo para compatibilidade (evita erro nos .config())

        self.root.bind("<Control-v>", lambda e: self.colar_capa())

    # ---------- seek loop ----------
    def _loop_seek(self):
        try:
            self.player_inicio.tick_seek()
        except Exception:
            pass
        try:
            self.player_playlist.tick_seek()
        except Exception:
            pass
        self.root.after(250, self._loop_seek)

    def _on_trocar_musica(self):
        try:
            self.player_inicio.atualizar()
        except Exception:
            pass
        try:
            self.player_playlist.atualizar()
        except Exception:
            pass

    def _on_double_click(self, event):
        col = self.tree.identify_column(event.x)
        if col == "#0":
            sel = self.tree.selection()
            if sel:
                self._menu_toggle_capa()
            return
        if col == "#2":
            self._selecionar_mesmo_album()
            return
        self.editar_metadados()

    def _selecionar_mesmo_album(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            return
        info = self._info_de(sel[0])
        album = (info.get("album") or "").strip()
        artista = (info.get("artista") or "").strip()
        if not album:
            messagebox.showinfo(T("dialogo_aviso"),
                T("msg_sem_album"))
            return
        self.tree.selection_remove(*self.tree.selection())
        count = 0
        for caminho in self.arquivos:
            if not self.tree.exists(caminho):
                continue
            i = self._info_de(caminho)
            if ((i.get("album") or "").strip() == album and
                    (i.get("artista") or "").strip() == artista):
                self.tree.selection_add(caminho)
                count += 1
        self.status_global.set_ok(
            T("st_selecionadas_album", n=count, album=album))

    def _selecionar_mesmo_artista(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            return
        info = self._info_de(sel[0])
        artista = (info.get("artista") or "").strip()
        if not artista:
            messagebox.showinfo(T("dialogo_aviso"),
                T("msg_sem_artista"))
            return
        self.tree.selection_remove(*self.tree.selection())
        count = 0
        for caminho in self.arquivos:
            if not self.tree.exists(caminho):
                continue
            i = self._info_de(caminho)
            if (i.get("artista") or "").strip() == artista:
                self.tree.selection_add(caminho)
                count += 1
        self.status_global.set_ok(
            T("st_selecionadas_artista", n=count, artista=artista))

    def _menu_toggle_capa(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            return
        todos_ignorados = all(self._capa_ignorada(c) for c in sel)
        novo_ativo = not todos_ignorados
        for c in sel:
            self._toggle_ignorar_capa(c, novo_ativo)
        self._atualizar_tags_das_linhas(sel)
        n = len(sel)
        if novo_ativo:
            self.status_global.set_ok(
                T("st_capa_congelada_n", n=n))
        else:
            self.status_global.set_ok(
                T("st_capa_editavel_n", n=n))

    def _atualizar_tags_das_linhas(self, caminhos):
        pasta = self.pasta.get()
        for c in caminhos:
            if not self.tree.exists(c):
                continue
            info = self._info_de(c)
            rel = os.path.relpath(c, pasta) if pasta else \
                os.path.basename(c)
            sub = os.path.dirname(rel) or "."
            vals = self._vals_row(info, sub, c)
            tags = ("frozen",) if self._capa_ignorada(c) else ()
            self.tree.item(c, values=vals, tags=tags)

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item and item not in self.tree.selection():
            self.tree.selection_set(item)
        try:
            self.menu_ctx.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_ctx.grab_release()

    def _tocar_selecionada(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            messagebox.showinfo(T("dialogo_aviso"), T("msg_selecione_musica_aviso"))
            return
        self._tocar_caminho(sel[0], fonte="inicio")

    def _tocar_selecionada_para(self, player_control):
        if player_control is self.player_inicio:
            self._tocar_selecionada()
        else:
            self._pl_tocar_selecionada()

    def _tocar_caminho(self, caminho, fonte="inicio"):
        if not PLAYER_DISPONIVEL:
            messagebox.showerror(T("dlg_player_indisponivel"),
                                 T("dlg_instale_pygame"))
            return
        if fonte == "inicio":
            fila = list(self.tree.get_children())
            try:
                idx = fila.index(caminho)
            except ValueError:
                idx = 0
            self.player.definir_fila(fila, idx)
        elif fonte == "playlist":
            fila = list(self.pl_arquivos)
            try:
                idx = fila.index(caminho)
            except ValueError:
                idx = 0
            self.player.definir_fila(fila, idx)

        if self.player.tocar(caminho, inicio=0.0):
            self.status_global.set_ok(T("st_tocando", nome=os.path.basename(caminho)))
            self._on_trocar_musica()
        else:
            self.status_global.set_erro(T("st_erro_tocar"))

    def _vals_row(self, info, sub, caminho=None):
        capa_status = "OK" if info["capa"] else "—"
        if caminho and self._capa_ignorada(caminho):
            capa_status = "🔒 " + capa_status
        return (info["rotulo"], info["album"], info["ano"], sub,
                capa_status)

    def carregar_lista(self):
        sel_anterior = list(self.tree.selection())

        self.tree.delete(*self.tree.get_children())
        self.arquivos = []
        self._info_cache.clear()
        self._thumb_cache.clear()

        pasta = self.pasta.get()
        if not os.path.isdir(pasta):
            self.capa_tk = preview_quadrado(None, LADO_PREVIEW)
            self.lbl_preview.config(image=self.capa_tk, text="")
            self.lbl_info.config(text=T("lbl_selecione_musica"))
            return

        self.status_global.set_working(T("st_lendo_pasta"))
        self.root.update_idletasks()

        try:
            if self.incluir_subpastas.get():
                encontrados = []
                for raiz, _dirs, files in os.walk(pasta):
                    for f in sorted(files):
                        if f.lower().endswith(".mp3"):
                            encontrados.append(os.path.join(raiz, f))
                encontrados.sort()
            else:
                encontrados = [
                    os.path.join(pasta, f)
                    for f in sorted(os.listdir(pasta))
                    if f.lower().endswith(".mp3")
                    and os.path.isfile(os.path.join(pasta, f))
                ]
        except Exception as e:
            self.status_global.set_erro(T("erro_generico", e=e))
            messagebox.showerror(T("dialogo_erro"), T("dlg_erro_ler", err=e))
            return

        if not encontrados:
            self.status_global.set_erro(T("st_sem_mp3"))
            self.tree.insert("", "end", iid="__placeholder__", text="",
                             values=(T("st_nenhum_mp3_pasta"),
                                     "", "", "", ""))
            return

        suspeitos = 0
        for caminho in encontrados:
            self.arquivos.append(caminho)
            self._info_cache[caminho] = ler_info(caminho)
            if nome_arquivo_suspeito(caminho):
                suspeitos += 1

        self._rebuild_view(sel_para_restaurar=sel_anterior)

        n = len(self.arquivos)
        marcados = sum(1 for c in self.arquivos
                       if self._capa_ignorada(c))
        visiveis = len(self.tree.get_children())
        base_msg = T("st_n_musicas_carregadas", n=n)
        if visiveis != n:
            base_msg = T("st_v_de_n_filtro", v=visiveis, n=n)
        if suspeitos:
            self.status_global.set_aviso(
                base_msg + " — " + T("st_n_nomes_suspeitos", n=suspeitos))
        elif marcados:
            self.status_global.set_ok(
                base_msg + " — " + T("st_n_congeladas", n=marcados))
        else:
            self.status_global.set_ok(base_msg)

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            self.capa_tk = preview_quadrado(None, LADO_PREVIEW)
            self.lbl_preview.config(image=self.capa_tk, text="")
            self.lbl_info.config(text=T("lbl_selecione_musica"))
            self.status_global.set_idle("")
            return
        caminho = sel[0]
        info = self._info_de(caminho)
        self.capa_bytes_atual = info["capa"]
        self.capa_tk = preview_quadrado(info["capa"], LADO_PREVIEW)
        self.lbl_preview.config(image=self.capa_tk, text="")
        if len(sel) == 1:
            base_nome = os.path.basename(caminho)
            aviso = ("\n" + T("msg_capa_congelada_aviso")
                     if self._capa_ignorada(caminho) else "")
            self.lbl_info.config(
                text=f"{info['rotulo']}\n\nArquivo: {base_nome}{aviso}")
            self.status_global.set_idle(info["rotulo"])
        else:
            self.lbl_info.config(
                text=T("st_n_selecionadas", n=len(sel)))
            self.status_global.set_idle(
                T("st_n_selecionadas", n=len(sel)))

    def editar_metadados(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            messagebox.showinfo(T("dialogo_aviso"), T("msg_selecione_musica_aviso"))
            return
        ignorar = all(self._capa_ignorada(c) for c in sel)
        EditorMetadadosWindow(self.root, list(sel), self._perfil_ativo(),
                              on_done=self.carregar_lista,
                              ignorar_capa=ignorar)

    def trocar_capa(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            messagebox.showinfo(T("dialogo_aviso"), T("msg_selecione_musica_aviso"))
            return
        efetivos = [c for c in sel if not self._capa_ignorada(c)]
        if not efetivos:
            messagebox.showinfo(
                T("dialogo_aviso"),
                T("msg_todas_congeladas"))
            return
        c = filedialog.askopenfilename(
            title=T("dlg_escolher_imagem"),
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp"),
                       ("Todos", "*.*")])
        if not c:
            return
        with open(c, "rb") as f:
            self._aplicar_capa_selecionados(f.read(), apenas=efetivos)

    def colar_capa(self):
        sel = self.tree.selection()
        if not sel:
            return
        efetivos = [c for c in sel if not self._capa_ignorada(c)]
        if not efetivos:
            return
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                buf = io.BytesIO()
                img.convert("RGB").save(buf, "PNG")
                self._aplicar_capa_selecionados(buf.getvalue(),
                                                apenas=efetivos)
            elif isinstance(img, list) and img:
                with open(img[0], "rb") as f:
                    self._aplicar_capa_selecionados(f.read(),
                                                    apenas=efetivos)
        except Exception as e:
            self.status_global.set_erro(T("erro_colar", e=e))

    def _on_drop_preview(self, evento):
        c = evento.data.strip("{}")
        sel = self.tree.selection()
        efetivos = [x for x in sel if not self._capa_ignorada(x)]
        if not efetivos:
            return
        try:
            with open(c, "rb") as f:
                self._aplicar_capa_selecionados(f.read(),
                                                apenas=efetivos)
        except Exception as e:
            self.status_global.set_erro(T("erro_drop", e=e))

    def _aplicar_capa_selecionados(self, imagem_bytes, apenas=None):
        sel = (apenas if apenas is not None
               else list(self.tree.selection()))
        if not sel or sel[0] == "__placeholder__":
            messagebox.showinfo(T("dialogo_aviso"), T("msg_selecione_musica_aviso"))
            return

        try:
            if self.player.musica_atual and self.player.musica_atual in sel:
                self.player.parar()
                self._on_trocar_musica()
        except Exception:
            pass

        profile = self._perfil_ativo()
        self.status_global.set_working(
            T("st_capa_aplicada", n=len(sel)))
        self.root.update_idletasks()
        ok = 0
        for caminho in sel:
            try:
                info = self._info_de(caminho)
                aplicar_completo(caminho, info, imagem_bytes, profile)
                ok += 1
                self._invalidar_thumb(caminho)
                self._invalidar_info(caminho)
            except Exception as e:
                self.log_msg(f"ERRO {os.path.basename(caminho)}: {e}")
        if ok == len(sel):
            self.status_global.set_ok(T("st_capa_aplicada", n=ok))
        else:
            self.status_global.set_erro(T("st_capa_aplicada_xy", ok=ok, total=len(sel)))
        self._rebuild_view(sel_para_restaurar=sel)

    def log_msg(self, texto):
        # Redireciona pro status do topo (o pequeno foi escondido)
        try:
            self.status_global.set_aviso(texto)
        except Exception:
            pass

    def buscar_online(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            messagebox.showinfo(T("dialogo_aviso"), T("msg_selecione_musica_aviso"))
            return
        if not ONLINE_OK:
            messagebox.showerror(T("dlg_faltam_bibs"),
                                 T("dlg_pip_install"))
            return
        ignorar = all(self._capa_ignorada(c) for c in sel)
        EditorMetadadosWindow(self.root, list(sel), self._perfil_ativo(),
                              on_done=self.carregar_lista,
                              ignorar_capa=ignorar)

    def normalizar_selecionados(self):
        sel = self.tree.selection()
        if not sel or sel[0] == "__placeholder__":
            return
        profile = self._perfil_ativo()
        self.status_global.set_working(T("st_normalizando_n", n=len(sel)))
        self.root.update_idletasks()
        erros = 0
        for caminho in sel:
            try:
                normalizar(caminho, profile)
                self._invalidar_thumb(caminho)
                self._invalidar_info(caminho)
            except Exception as e:
                erros += 1
                self.log_msg(f"ERRO {os.path.basename(caminho)}: {e}")
        if erros == 0:
            self.status_global.set_ok(T("msg_normalizadas_n", n=len(sel)))
        else:
            self.status_global.set_erro(T("msg_erros_n", n=erros))
        self._rebuild_view(sel_para_restaurar=sel)

    def corrigir_nomes_suspeitos(self):
        sel = self.tree.selection()
        alvos = list(sel) if (sel and sel[0] != "__placeholder__") else \
                [c for c in self.arquivos if nome_arquivo_suspeito(c)]
        alvos = [c for c in alvos if nome_arquivo_suspeito(c)]
        if not alvos:
            messagebox.showinfo(T("dialogo_aviso"), T("dlg_corrigir_zero"))
            return
        if not messagebox.askyesno(
                T("dialogo_confirmar"),
                T("dlg_corrigir_nomes", n=len(alvos))):
            return
        self.status_global.set_working(T("st_corrigindo"))
        self.root.update_idletasks()
        ok = 0
        for caminho in alvos:
            try:
                info = ler_info(caminho)
                base = sanitizar_nome(
                    info["titulo"] or info["artista"] or "sem-nome")
                dir_atual = os.path.dirname(caminho)
                novo = os.path.join(dir_atual, base + ".mp3")
                cont = 1
                while (os.path.exists(novo)
                       and novo.lower() != caminho.lower()):
                    novo = os.path.join(dir_atual,
                                        f"{base} ({cont}).mp3")
                    cont += 1
                if novo.lower() != caminho.lower():
                    os.rename(caminho, novo)
                ok += 1
            except Exception as e:
                self.log_msg(f"ERRO: {e}")
        self.status_global.set_ok(T("st_nomes_corrigidos", n=ok))
        self._recarregar_tudo()

    def normalizar_todas(self):
        if not self.arquivos:
            messagebox.showinfo(T("dialogo_aviso"), T("dlg_carregar_pasta"))
            return
        profile = self._perfil_ativo()
        tam = profile.get("cover_size", 250)
        if not messagebox.askyesno(
                T("dialogo_confirmar"),
                T("dlg_normalizar_todas", n=len(self.arquivos), tam=tam)):
            return

        try:
            self.player.parar()
            self._on_trocar_musica()
        except Exception:
            pass

        self.btn_normalizar_todas.config(state="disabled")
        self.status_global.set_working(
            T("st_normalizando_n", n=len(self.arquivos)))
        total = len(self.arquivos)
        sel_atual = list(self.tree.selection())

        def rodar():
            ok, erros = 0, 0
            for i, c in enumerate(self.arquivos):
                try:
                    normalizar(c, profile)
                    ok += 1
                    self._invalidar_thumb(c)
                    self._invalidar_info(c)
                except Exception:
                    erros += 1
                if i % 3 == 0 or i == total - 1:
                    self.root.after(0, lambda n=i+1:
                        self.status_global.set_working(
                            T("st_normalizando_xy", n=n, total=total)))

            def finalizar():
                self.btn_normalizar_todas.config(state="normal")
                msg = T("st_normalizadas_xy", ok=ok, total=total)
                if erros:
                    msg += f" ({erros} erro(s))"
                    self.status_global.set_erro(msg)
                else:
                    self.status_global.set_ok(msg)
                self._rebuild_view(sel_para_restaurar=sel_atual)

            self.root.after(0, finalizar)

        threading.Thread(target=rodar, daemon=True).start()

    # =================================================================
    # ABA PLAYLIST
    # =================================================================
    def _ui_playlist(self, parent):
        l1 = ttk.Frame(parent)
        l1.pack(fill="x", padx=8, pady=4)
        ttk.Label(l1, text=T("lbl_pasta")).pack(side="left")
        e = ttk.Entry(l1, textvariable=self.pasta, state="readonly",
                      foreground="#888")
        e.pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(l1, text=T("btn_escolher_pasta"),
                   command=self.escolher_pasta,
                   style="Primary.TButton").pack(side="left")
        ttk.Button(l1, text=T("btn_recarregar"),
                   command=self._recarregar_tudo).pack(side="left", padx=4)

        l2 = ttk.Frame(parent)
        l2.pack(fill="x", padx=8, pady=2)
        ttk.Label(l2, text=T("lbl_buscar_playlist")).pack(side="left")
        e2 = ttk.Entry(l2, textvariable=self.pl_busca_var)
        e2.pack(side="left", fill="x", expand=True, padx=4)
        self.pl_busca_var.trace_add("write",
                                     lambda *a: self.pl_redesenhar())
        criar_botao_canvas(l2, "trash",
                            lambda: self.pl_busca_var.set(""),
                            T("tooltip_limpar_busca"),
                            size=34, lado="left", padx=2)

        corpo = ttk.Frame(parent)
        corpo.pack(fill="both", expand=True, padx=8, pady=4)

        esq_pl = ttk.LabelFrame(corpo, text=T("lblframe_ordem_playlists"))
        esq_pl.pack(side="left", fill="y", padx=(0, 8))
        self.pl_lista_ordem = tk.Listbox(esq_pl, width=26, height=18)
        self.pl_lista_ordem.pack(padx=6, pady=6, fill="y", expand=True)
        btord = ttk.Frame(esq_pl)
        btord.pack(fill="x", padx=6, pady=(0, 6))
        criar_botao_canvas(btord, "subir",
                            lambda: self._pl_ordem_mover(-1),
                            T("tooltip_mover_subir"),
                            size=34, lado="left", padx=2)
        criar_botao_canvas(btord, "descer",
                            lambda: self._pl_ordem_mover(1),
                            T("tooltip_mover_descer"),
                            size=34, lado="left", padx=2)
        criar_botao_canvas(btord, "save",
                            self._salvar_ordem_playlists,
                            T("st_ordem_salva"),
                            size=34, lado="right", padx=2)

        esq = ttk.LabelFrame(corpo, text=T("lblframe_musicas_playlist"))
        esq.pack(side="left", fill="both", expand=True)

        topo_pl = ttk.Frame(esq)
        topo_pl.pack(fill="x", padx=6, pady=4)
        ttk.Label(topo_pl, text="Playlist:").pack(side="left")
        self.pl_combo = ttk.Combobox(topo_pl,
                                     textvariable=self.pl_playlist_atual,
                                     state="readonly", width=42)
        self.pl_combo.pack(side="left", padx=6)
        self.pl_combo.bind("<<ComboboxSelected>>",
                            self.pl_trocar_playlist)

        self.pl_tree = ttk.Treeview(esq, columns=("num", "nome"),
                                    show="headings",
                                    selectmode="extended")
        self.pl_tree.heading("num", text="#")
        self.pl_tree.heading("nome", text=T("col_nome_arquivo"))
        self.pl_tree.column("num", width=50, anchor="center")
        self.pl_tree.column("nome", width=500)
        self.pl_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(esq, orient="vertical",
                           command=self.pl_tree.yview)
        sb.pack(side="right", fill="y")
        self.pl_tree.config(yscrollcommand=sb.set)
        self.pl_tree.bind("<Double-1>", self._pl_duplo_clique)

        dir_ = ttk.LabelFrame(corpo, text=T("lblframe_mover"))
        dir_.pack(side="left", fill="y", padx=(8, 0), ipadx=6, ipady=6)

        btm = ttk.Frame(dir_)
        btm.pack(fill="x", pady=4)
        for _i in range(4):
            btm.columnconfigure(_i, weight=1)

        # Botoes de mover (Canvas + seta desenhada)
        f_topo = ttk.Frame(btm)
        f_topo.grid(row=0, column=0, sticky="we", padx=1)
        criar_botao_seta(f_topo, "topo",
                          lambda: self.pl_mover(-9999),
                          T("tooltip_mover_topo"))

        f_subir = ttk.Frame(btm)
        f_subir.grid(row=0, column=1, sticky="we", padx=1)
        criar_botao_seta(f_subir, "subir",
                          lambda: self.pl_mover(-1),
                          T("tooltip_mover_subir"))

        f_descer = ttk.Frame(btm)
        f_descer.grid(row=0, column=2, sticky="we", padx=1)
        criar_botao_seta(f_descer, "descer",
                          lambda: self.pl_mover(1),
                          T("tooltip_mover_descer"))

        f_fim = ttk.Frame(btm)
        f_fim.grid(row=0, column=3, sticky="we", padx=1)
        criar_botao_seta(f_fim, "fim",
                          lambda: self.pl_mover(9999),
                          T("tooltip_mover_fim"))

        ttk.Separator(dir_, orient="horizontal").pack(fill="x", pady=6)

        ttk.Button(dir_, text=T("btn_aplicar_renomear"),
                   command=self.pl_renomear,
                   style="Success.TButton").pack(fill="x", pady=3)

        ttk.Separator(dir_, orient="horizontal").pack(fill="x", pady=6)

        pf = ttk.LabelFrame(dir_, text="Player")
        pf.pack(fill="x")
        self.player_playlist = PlayerControl(pf, self, mostrar_capa=True)
        self.player_playlist.pack(fill="x")

    def _pl_duplo_clique(self, event):
        item = self.pl_tree.identify_row(event.y)
        if not item:
            return
        try:
            idx = int(item) - 1
            if 0 <= idx < len(self.pl_arquivos):
                self._tocar_caminho(self.pl_arquivos[idx], fonte="playlist")
        except Exception as e:
            print(f"Erro duplo clique playlist: {e}")

    def _pl_tocar_selecionada(self):
        sel = self.pl_tree.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma música na playlist.")
            return
        try:
            idx = int(sel[0]) - 1
            if 0 <= idx < len(self.pl_arquivos):
                self._tocar_caminho(self.pl_arquivos[idx], fonte="playlist")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao tocar: {e}")

    def _pl_ordem_mover(self, delta):
        sel = self.pl_lista_ordem.curselection()
        if not sel:
            return
        idx = sel[0]
        itens = list(self.pl_lista_ordem.get(0, "end"))
        novo = idx + delta
        if novo < 0 or novo >= len(itens):
            return
        itens[idx], itens[novo] = itens[novo], itens[idx]
        self.pl_lista_ordem.delete(0, "end")
        for it in itens:
            self.pl_lista_ordem.insert("end", it)
        self.pl_lista_ordem.selection_set(novo)

    def _salvar_ordem_playlists(self):
        ordem = list(self.pl_lista_ordem.get(0, "end"))
        self.config["ordem_playlists"] = ordem
        salvar_config(self.config)

        # Se ha pastas (nao apenas "(raiz)"), oferece renomear no disco
        nomes_pastas = [n for n in ordem if n != "(raiz)"]
        if nomes_pastas:
            exemplo = "\n".join(
                f"    {str(i).zfill(2)}-{self._sem_prefixo_num(n)}"
                for i, n in enumerate(nomes_pastas[:5], 1))
            if len(nomes_pastas) > 5:
                exemplo += f"\n    ... (+{len(nomes_pastas)-5} pasta(s))"
            msg = (
                "Ordem salva.\n\n"
                "Deseja tambem renomear as PASTAS no disco com "
                "prefixo numerico (01-, 02-, ...)?\n\n"
                "Isso faz a ordem persistir em qualquer aparelho "
                "(ex: Flip Vita), mesmo fora deste programa.\n\n"
                "Novos nomes:\n" + exemplo)
            if messagebox.askyesno(T("dlg_renomear_pastas"), msg):
                self._renomear_pastas_com_prefixo(ordem)

        self.pl_carregar_playlists()
        self.status_global.set_ok(T("st_ordem_salva"))

    @staticmethod
    def _sem_prefixo_num(nome):
        """Remove prefixo tipo '01-' ou '02.' do nome da pasta."""
        return re.sub(r'^\d+[-_. ]+', '', nome).strip() or nome

    def _renomear_pastas_com_prefixo(self, ordem):
        """Renomeia as pastas da playlist com prefixo numerico
        (01-, 02-, ...) na ordem escolhida."""
        pasta_pai = self.pasta.get()
        if not os.path.isdir(pasta_pai):
            return

        nomes_pastas = [n for n in ordem if n != "(raiz)"]
        if not nomes_pastas:
            return

        padding = max(2, len(str(len(nomes_pastas))))

        # Fase 1: renomeia tudo pra nomes temporarios (evita colisao)
        temps = []
        for i, nome in enumerate(nomes_pastas, 1):
            origem = os.path.join(pasta_pai, nome)
            if not os.path.isdir(origem):
                continue
            limpo = self._sem_prefixo_num(nome)
            tmp = os.path.join(pasta_pai, f"__tmp_pl_{i:04d}__{limpo}")
            try:
                os.rename(origem, tmp)
                temps.append((tmp, limpo, i))
            except Exception as e:
                self.log_msg(f"ERRO ao preparar '{nome}': {e}")

        # Fase 2: aplica prefixo numerico
        renomeados = 0
        for tmp, limpo, i in temps:
            final_nome = f"{str(i).zfill(padding)}-{limpo}"
            final = os.path.join(pasta_pai, final_nome)
            try:
                os.rename(tmp, final)
                renomeados += 1
            except Exception as e:
                self.log_msg(f"ERRO: {e}")

        # Atualiza a config com os novos nomes
        nova = []
        contador = 0
        for nome in ordem:
            if nome == "(raiz)":
                nova.append(nome)
            else:
                contador += 1
                limpo = self._sem_prefixo_num(nome)
                nova.append(f"{str(contador).zfill(padding)}-{limpo}")
        self.config["ordem_playlists"] = nova
        salvar_config(self.config)

        if renomeados:
            self.status_global.set_ok(
                T("st_pastas_renomeadas", n=renomeados))
        else:
            self.status_global.set_ok(T("st_nenhuma_pasta_renomeada"))

    def pl_carregar_playlists(self):
        pasta = self.pasta.get()
        if not os.path.isdir(pasta):
            return
        self.status_global.set_working(T("st_procurando_playlists"))
        self.root.update_idletasks()

        nomes_encontrados = []
        tem_raiz = any(
            f.lower().endswith(".mp3")
            and os.path.isfile(os.path.join(pasta, f))
            for f in os.listdir(pasta))
        if tem_raiz:
            nomes_encontrados.append("(raiz)")
        for nome in sorted(os.listdir(pasta)):
            caminho = os.path.join(pasta, nome)
            if not os.path.isdir(caminho):
                continue
            if pasta_tem_mp3(caminho):
                nomes_encontrados.append(nome)

        ordem_salva = self.config.get("ordem_playlists", [])
        nomes_ordenados = [n for n in ordem_salva
                           if n in nomes_encontrados]
        nomes_ordenados += [n for n in nomes_encontrados
                            if n not in ordem_salva]

        self.pl_lista_ordem.delete(0, "end")
        for n in nomes_ordenados:
            self.pl_lista_ordem.insert("end", n)

        self.pl_playlists = []
        for nome in nomes_ordenados:
            if nome == "(raiz)":
                self.pl_playlists.append(("(raiz)", pasta))
            else:
                self.pl_playlists.append(
                    (nome, os.path.join(pasta, nome)))

        self.pl_combo["values"] = nomes_ordenados
        if not nomes_ordenados:
            self.pl_playlist_atual.set("")
            self.pl_arquivos = []
            self.pl_caminho_atual = ""
            self.pl_redesenhar()
            self.status_global.set_idle(T("st_nenhuma_playlist"))
            return
        anterior = self.pl_playlist_atual.get()
        if anterior not in nomes_ordenados:
            self.pl_playlist_atual.set(nomes_ordenados[0])
        self.pl_trocar_playlist(None)
        self.status_global.set_ok(
            T("st_n_playlists", n=len(nomes_ordenados)))

    def pl_trocar_playlist(self, event=None):
        nome = self.pl_playlist_atual.get()
        caminho = next((c for n, c in self.pl_playlists if n == nome), "")
        if not caminho:
            return
        self.pl_caminho_atual = caminho
        try:
            arquivos = []
            for raiz, _dirs, files in os.walk(caminho):
                for f in files:
                    if f.lower().endswith(".mp3"):
                        arquivos.append(os.path.join(raiz, f))
            arquivos.sort(key=lambda p: os.path.relpath(p, caminho).lower())
            self.pl_arquivos = arquivos
        except Exception as e:
            messagebox.showerror(T("dialogo_erro"), T("dlg_erro_ler", err=e))
            return
        self.pl_redesenhar()
        n = len(self.pl_arquivos)
        self.status_global.set_ok(
            T("st_playlist_n_musicas", nome=nome, n=n))

    def pl_redesenhar(self):
        self.pl_tree.delete(*self.pl_tree.get_children())
        pasta_base = self.pl_caminho_atual
        termo = ""
        try:
            termo = self.pl_busca_var.get().strip().lower()
        except Exception:
            termo = ""
        for i, caminho in enumerate(self.pl_arquivos, 1):
            nome = (os.path.relpath(caminho, pasta_base)
                    if pasta_base else os.path.basename(caminho))
            if termo and termo not in nome.lower():
                continue
            self.pl_tree.insert("", "end", iid=str(i), values=(i, nome))

    def pl_mover(self, delta):
        sel = self.pl_tree.selection()
        if not sel:
            return
        indices = sorted([int(s) - 1 for s in sel])
        nomes_sel = [self.pl_arquivos[i] for i in indices]
        if delta == -1:
            for i in indices:
                if i > 0:
                    self.pl_arquivos[i], self.pl_arquivos[i - 1] = \
                        self.pl_arquivos[i - 1], self.pl_arquivos[i]
        elif delta == 1:
            for i in reversed(indices):
                if i < len(self.pl_arquivos) - 1:
                    self.pl_arquivos[i], self.pl_arquivos[i + 1] = \
                        self.pl_arquivos[i + 1], self.pl_arquivos[i]
        else:
            movidos = [self.pl_arquivos[i] for i in indices]
            restantes = [f for j, f in enumerate(self.pl_arquivos)
                         if j not in indices]
            self.pl_arquivos = (movidos + restantes if delta < 0
                                else restantes + movidos)
        self.pl_redesenhar()
        for i, nome in enumerate(self.pl_arquivos, 1):
            if nome in nomes_sel:
                self.pl_tree.selection_add(str(i))

    def pl_renomear(self):
        if not self.pl_arquivos:
            messagebox.showwarning(T("dialogo_aviso"), T("msg_selecione_musica_aviso"))
            return
        pastas = set(os.path.dirname(c) for c in self.pl_arquivos)
        if len(pastas) > 1:
            messagebox.showinfo(
                T("dialogo_aviso"),
                T("msg_subpastas_diff"))
            return
        pasta = pastas.pop() if pastas else None
        if not pasta:
            return
        total = len(self.pl_arquivos)
        padding = len(str(total))
        nome_pl = self.pl_playlist_atual.get()
        if not messagebox.askyesno(T("dialogo_confirmar"),
                                   T("dlg_renomear_arquivos", n=total)):
            return
        self.status_global.set_working(T("st_normalizando_n", n=total))

        try:
            if self.player.musica_atual:
                self.player.parar()
                self._on_trocar_musica()
        except Exception:
            pass

        def base_de(caminho):
            nome = os.path.basename(caminho)
            sem = re.sub(r'^\d+[-_.\s]+', '', nome, count=1).strip()
            stem = os.path.splitext(sem)[0].strip()
            if (stem.lower() in NOMES_SUSPEITOS
                    or not re.search(r'\w', stem)):
                info = ler_info(caminho)
                stem = (info["titulo"] or info["artista"] or "sem-nome")
            return sanitizar_nome(stem) + ".mp3"

        try:
            temps = []
            for i, caminho in enumerate(self.pl_arquivos):
                novo_base = base_de(caminho)
                temp = os.path.join(pasta,
                                    f"__tmp_{i:04d}__{novo_base}")
                os.rename(caminho, temp)
                temps.append((temp, novo_base))
            for i, (temp, base) in enumerate(temps, 1):
                final = os.path.join(
                    pasta, f"{str(i).zfill(padding)}-{base}")
                os.rename(temp, final)
            self.status_global.set_ok(T("st_n_renomeados", n=total))
            self._recarregar_tudo()
            messagebox.showinfo(T("dialogo_pronto"), T("st_n_renomeados", n=total))
        except Exception as e:
            self.status_global.set_erro(T("erro_generico", e=e))
            messagebox.showerror("Erro", f"Erro: {e}")

    # =================================================================
    # ABA CONFIGURAÇÕES
    # =================================================================
    def _ui_config(self, parent):
        # Secao de idioma (vem primeiro)
        f0 = ttk.LabelFrame(parent, text=T("cfg_idioma"))
        f0.pack(fill="x", padx=8, pady=6)

        linha_idioma = ttk.Frame(f0)
        linha_idioma.pack(fill="x", padx=8, pady=6)

        ttk.Label(linha_idioma, text=T("cfg_idioma")).pack(side="left")

        nomes_idiomas = [nome for _, nome in IDIOMAS_DISPONIVEIS]
        self.var_idioma = tk.StringVar(
            value=nome_do_idioma(idioma_atual()))
        self.combo_idioma = ttk.Combobox(
            linha_idioma, textvariable=self.var_idioma,
            values=nomes_idiomas, state="readonly", width=22)
        self.combo_idioma.pack(side="left", padx=8)
        self.combo_idioma.bind("<<ComboboxSelected>>",
                                self._trocar_idioma)

        f1 = ttk.LabelFrame(parent, text=T("cfg_aparencia"))
        f1.pack(fill="x", padx=8, pady=6)
        ttk.Checkbutton(
            f1, text=T("cfg_tema_auto"),
            variable=self.var_tema_auto,
            command=self._toggle_tema_auto
        ).pack(anchor="w", padx=8, pady=4)
        ttk.Checkbutton(
            f1, text=T("cfg_modo_escuro"),
            variable=self.var_modo_escuro,
            command=self._toggle_modo_escuro
        ).pack(anchor="w", padx=8, pady=4)
        ttk.Label(f1, text=T("cfg_hint_auto"),
                  foreground="gray").pack(anchor="w", padx=24,
                                          pady=(0, 6))

        f2 = ttk.LabelFrame(parent, text=T("cfg_capa"))
        f2.pack(fill="x", padx=8, pady=6)
        ttk.Label(f2, text=T("cfg_tamanho_padrao")).pack(side="left", padx=8,
                                                    pady=6)
        cb = ttk.Combobox(f2, textvariable=self.tamanho_capa_var,
                          values=TAMANHOS_CAPA_UI, state="readonly",
                          width=18)
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>", self._trocar_tamanho_override)

        f2b = ttk.Frame(f2)
        f2b.pack(fill="x", padx=8, pady=4)
        ttk.Button(f2b, text=T("cfg_desmarcar_congeladas"),
                   command=self._limpar_congeladas).pack(side="left")

        f3 = ttk.LabelFrame(parent, text=T("cfg_player"))
        f3.pack(fill="x", padx=8, pady=6)
        if PLAYER_DISPONIVEL:
            ttk.Label(f3,
                      text=T("cfg_player_ativo"),
                      foreground=COR_OK).pack(anchor="w", padx=8, pady=6)
        else:
            ttk.Label(f3,
                      text=T("cfg_player_inativo"),
                      foreground=COR_AVISO).pack(anchor="w", padx=8,
                                                 pady=6)

        f4 = ttk.LabelFrame(parent, text=T("cfg_log"))
        f4.pack(fill="x", padx=8, pady=6)
        self.log_grande = scrolledtext.ScrolledText(f4, height=8,
                                                    wrap="word")
        self.log_grande.pack(fill="both", expand=True, padx=6, pady=6)
        ttk.Button(f4, text=T("cfg_limpar_log"),
                   command=lambda: self.log_grande.delete("1.0", "end")
                   ).pack(anchor="e", padx=6, pady=(0, 6))

        f5 = ttk.LabelFrame(parent, text=T("cfg_sobre"))
        f5.pack(fill="x", padx=8, pady=6)
        info = (T("cfg_sobre_arquivos") + "\n"
                f"  • {CONFIG_PATH}\n"
                f"  • {PERFIS_PATH}\n"
                f"  • {COVER_SKIP_PATH}\n\n"
                + T("cfg_sobre_bibs") + " mutagen, Pillow"
                f"{', tkinterdnd2' if DND else ''}"
                f"{', musicbrainzngs + requests' if ONLINE_OK else ''}"
                f"{', pygame' if PLAYER_DISPONIVEL else ''}")
        ttk.Label(f5, text=info, justify="left").pack(anchor="w", padx=8,
                                                      pady=6)

    def _limpar_congeladas(self):
        if not self.covers_ignorados:
            return
        if not messagebox.askyesno(
                T("dialogo_confirmar"),
                T("dlg_desmarcar_congeladas", n=len(self.covers_ignorados))):
            return
        self.covers_ignorados.clear()
        salvar_skip_covers(self.covers_ignorados)
        self._rebuild_view()
        self.status_global.set_ok(T("st_capas_descongeladas"))


# =====================================================================
# MAIN
# =====================================================================
def _montar_passos_tour(app):
    """Lista de passos do tutorial interativo."""
    def _voltar_inicio():
        try:
            app.notebook.select(app.tab_inicio)
        except Exception:
            pass
    def _ir_playlist():
        try:
            app.notebook.select(app.tab_play)
        except Exception:
            pass
    return [
        {"widget": None,
         "titulo": "onb_slide1_titulo",
         "texto": "onb_slide1_texto"},
        {"widget": lambda: app.combo_perfil,
         "titulo": "onb_slide5_titulo",
         "texto": "onb_slide5_texto"},
        {"widget": lambda: app.tree,
         "titulo": "onb_slide2_titulo",
         "texto": "onb_slide2_texto"},
        {"widget": lambda: app.btn_normalizar_todas,
         "titulo": "onb_slide4_titulo",
         "texto": "onb_slide4_texto"},
        {"widget": lambda: app.pl_tree,
         "pre_hook": _ir_playlist,
         "titulo": "onb_slide3_titulo",
         "texto": "onb_slide3_texto"},
        {"widget": lambda: app.btn_config,
         "pre_hook": _voltar_inicio,
         "titulo": "onb_slide5_titulo",
         "texto": "onb_slide5_texto"},
    ]


def main():
    root = TkinterDnD.Tk() if DND else tk.Tk()
    aplicar_icone_janela(root)
    root.withdraw()

    cfg = carregar_config()
    mostrar_tour = False
    if cfg.get("primeira_execucao", True):
        cfg["primeira_execucao"] = False
        salvar_config(cfg)
        mostrar_tour = True
        try:
            onb = OnboardingWindow(root)
            root.wait_window(onb.janela)
            if onb.idioma_escolhido:
                cfg["idioma"] = onb.idioma_escolhido
            if onb.tema_escolhido:
                if onb.tema_escolhido == "auto":
                    cfg["tema_automatico"] = True
                elif onb.tema_escolhido == "escuro":
                    cfg["tema_automatico"] = False
                    cfg["modo_escuro"] = True
                else:
                    cfg["tema_automatico"] = False
                    cfg["modo_escuro"] = False
            salvar_config(cfg)
        except Exception as e:
            print(f"Erro no onboarding: {e}")

    app = App(root)
    root.deiconify()

    if mostrar_tour:
        def _abrir_tour():
            try:
                passos = _montar_passos_tour(app)
                tour = TutorialOverlay(root, app, passos)
                tour.iniciar()
            except Exception as e:
                print(f"Erro no tour: {e}")
        try:
            root.after(700, _abrir_tour)
        except Exception as e:
            print(f"Erro ao agendar tour: {e}")

    root.mainloop()


if __name__ == "__main__":
    main()