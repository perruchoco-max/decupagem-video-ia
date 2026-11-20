#!/usr/bin/env python3
"""Gera legenda ASS palavra a palavra (estilo editorial) a partir de tempos por palavra.

Entrada: JSON lista de {"word","start","end"} (segundos).
Sem glow: borda 0, sombra suave. Corte seco, sem animação.
"""
import argparse
import json
import sys

FUNCIONAIS = {"a", "o", "e", "de", "do", "da", "em", "no", "na", "um", "uma", "que", "me", "te",
              "se", "eu", "ou", "com", "por", "pra", "para", "até", "os", "as", "dos", "das"}


def ts(t):
    t = max(t, 0)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def norm(w):
    return w.strip().strip(".,!?;:…").lower()


def agrupar(palavras, max_gap=0.12):
    """Une palavras funcionais curtas coladas na fala a vizinhas (máx. 3 palavras)."""
    out = []
    for p in palavras:
        if out:
            a = out[-1]
            colado = p["start"] - a["end"] <= max_gap
            pequeno = len(a["words"]) < 3
            if colado and pequeno and (norm(a["words"][-1]) in FUNCIONAIS and norm(p["word"]) not in FUNCIONAIS
                                       or norm(p["word"]) in FUNCIONAIS and len(norm(p["word"])) <= 3
                                       and norm(a["words"][-1]) in FUNCIONAIS):
                a["words"].append(p["word"].strip())
                a["end"] = p["end"]
                continue
        out.append({"words": [p["word"].strip()], "start": p["start"], "end": p["end"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("saida")
    ap.add_argument("--largura", type=int, default=1080)
    ap.add_argument("--altura", type=int, default=1920)
    ap.add_argument("--fonte", default="Montserrat")
    ap.add_argument("--impacto", nargs="*", default=[])
    ap.add_argument("--chave", nargs="*", default=[])
    ap.add_argument("--agrupar", action="store_true")
    ap.add_argument("--modo-gancho-ate", type=float, default=0.0,
                    help="segundos iniciais em modo frase acumulada (0 = desligado)")
    a = ap.parse_args()

    palavras = json.load(open(a.entrada, encoding="utf-8"))
    impacto = {norm(x) for x in a.impacto}
    chave = {norm(x) for x in a.chave}
    W, H = a.largura, a.altura
    corpo = round(W * 0.067)
    grande = round(W * 0.14)
    cy = round(H * 0.62)
    sombra = max(2, round(W / 360))

    # Pesos: ASS escolhe o nome de família; "Bold" liga \b1. Variantes via nome da família.
    f = a.fonte
    estilos = [
        f"Style: Leve,{f} Light,{corpo},&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,0,0,0,0,100,100,-1,0,1,0,{sombra},5,40,40,0,1",
        f"Style: Chave,{f},{corpo},&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,-1,0,0,0,100,100,-1,0,1,0,{sombra},5,40,40,0,1",
        f"Style: Impacto,{f} Black,{grande},&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,0,0,0,0,100,100,-2,0,1,0,{sombra},5,40,40,0,1",
    ]
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\nWrapStyle: 2\n\n"
            "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
            "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
            "MarginL,MarginR,MarginV,Encoding\n" + "\n".join(estilos) +
            "\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")

    linhas = []
    pos = f"{{\\an5\\pos({W // 2},{cy})}}"

    def estilo_de(w):
        n = norm(w)
        if n in impacto:
            return "Impacto"
        if n in chave:
            return "Chave"
        return "Leve"

    gancho = [p for p in palavras if p["start"] < a.modo_gancho_ate]
    corpo_p = [p for p in palavras if p["start"] >= a.modo_gancho_ate]

    # Modo gancho: acumula palavras; limpa bloco em pausa >= 0.4 s
    bloco = []
    for i, p in enumerate(gancho):
        bloco.append(p)
        prox = gancho[i + 1] if i + 1 < len(gancho) else None
        fim = (prox["start"] if prox and prox["start"] - p["end"] < 0.4 else p["end"])
        texto = ""
        n_linha = 0
        for q in bloco:
            st = estilo_de(q["word"])
            w = q["word"].strip().lower()
            if st == "Impacto":
                texto = texto.rstrip() + f"\\N{{\\rImpacto}}{w}\\N"
                n_linha = 0
            else:
                if n_linha >= 3:  # quebra de linha a cada 3 palavras para formar o bloco empilhado
                    texto = texto.rstrip() + "\\N"
                    n_linha = 0
                texto += f"{{\\r{st}}}{w} "
                n_linha += 1
        linhas.append(f"Dialogue: 0,{ts(p['start'])},{ts(fim)},Leve,,0,0,0,,{{\\an5\\pos({W // 2},{round(H * 0.55)})}}{texto.strip()}")
        if prox is None or prox["start"] - p["end"] >= 0.4:
            bloco = []

    # Modo corpo: palavra por vez, some nas pausas, corte seco
    itens = agrupar(corpo_p) if a.agrupar else [
        {"words": [p["word"].strip()], "start": p["start"], "end": p["end"]} for p in corpo_p]
    for i, it in enumerate(itens):
        nxt = itens[i + 1]["start"] if i + 1 < len(itens) else None
        fim = min(it["end"] + 0.08, nxt) if nxt is not None else it["end"] + 0.08
        st = max((estilo_de(w) for w in it["words"]), key=["Leve", "Chave", "Impacto"].index)
        txt = " ".join(it["words"]).lower()
        linhas.append(f"Dialogue: 0,{ts(it['start'])},{ts(fim)},{st},,0,0,0,,{pos}{txt}")

    open(a.saida, "w", encoding="utf-8").write(head + "\n".join(linhas) + "\n")
    print(f"{len(linhas)} eventos escritos em {a.saida}", file=sys.stderr)


if __name__ == "__main__":
    main()
