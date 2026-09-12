# -*- coding: utf-8 -*-
"""
Sistema de internacionalizacao (i18n).
Carrega traducoes de arquivos JSON na pasta i18n/.
"""

import os
import sys
import json

_IDIOMA_ATUAL = "pt_BR"
_CACHE = {}

IDIOMAS_DISPONIVEIS = [
    ("pt_BR", "Português (Brasil)"),
    ("en",    "English"),
    ("es",    "Español"),
    ("ja",    "日本語"),
    ("ko",    "한국어"),
]

IDIOMA_PADRAO = "pt_BR"


def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _pasta_i18n():
    base = _base_dir()
    p1 = os.path.join(base, "i18n")
    if os.path.isdir(p1):
        return p1
    if hasattr(sys, "_MEIPASS"):
        p2 = os.path.join(sys._MEIPASS, "i18n")
        if os.path.isdir(p2):
            return p2
        p3 = os.path.join(sys._MEIPASS, "_internal", "i18n")
        if os.path.isdir(p3):
            return p3
    return p1


def _carregar(idioma):
    if idioma in _CACHE:
        return _CACHE[idioma]
    pasta = _pasta_i18n()
    caminho = os.path.join(pasta, f"{idioma}.json")
    if not os.path.exists(caminho):
        _CACHE[idioma] = {}
        return _CACHE[idioma]
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        _CACHE[idioma] = dados
        return dados
    except Exception as e:
        print(f"Erro ao carregar idioma {idioma}: {e}")
        _CACHE[idioma] = {}
        return _CACHE[idioma]


def definir_idioma(idioma):
    global _IDIOMA_ATUAL
    _IDIOMA_ATUAL = idioma if idioma else IDIOMA_PADRAO
    _carregar(_IDIOMA_ATUAL)
    _carregar(IDIOMA_PADRAO)


def idioma_atual():
    return _IDIOMA_ATUAL


def T(chave, **kwargs):
    """Retorna o texto traduzido. Se nao achar, cai pra pt_BR.
    Se ainda nao achar, devolve a propria chave."""
    trad = _carregar(_IDIOMA_ATUAL)
    texto = trad.get(chave)
    if texto is None:
        padrao = _carregar(IDIOMA_PADRAO)
        texto = padrao.get(chave, chave)
    if kwargs:
        try:
            return texto.format(**kwargs)
        except Exception:
            return texto
    return texto


def recarregar():
    _CACHE.clear()
    _carregar(_IDIOMA_ATUAL)
    _carregar(IDIOMA_PADRAO)


def nome_do_idioma(codigo):
    for cod, nome in IDIOMAS_DISPONIVEIS:
        if cod == codigo:
            return nome
    return codigo


def codigo_do_nome(nome):
    for cod, n in IDIOMAS_DISPONIVEIS:
        if n == nome:
            return cod
    return IDIOMA_PADRAO