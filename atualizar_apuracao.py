#!/usr/bin/env python3
"""Baixa os resultados oficiais do TSE e grava apuracao.json (lido por apuracao.html).

Uso: python3 atualizar_apuracao.py
Só biblioteca padrão (3.9+). Não inventa dados: se a URL não estiver configurada
ou o TSE não responder, a página mostra "aguardando dados".

COMO ACHAR CADA URL (uma vez só):
1. Abra https://resultados.tse.jus.br e escolha 2026, turno, cargo e abrangência
   (Brasil ou Mococa).
2. F12 > aba Rede (Network) > filtre por "json" > recarregue a página.
3. Copie o endereço do arquivo terminado em "-r.json" e cole abaixo.
"""
import json, sys
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

ELEICOES = [
    {"titulo": "Presidente: Brasil",         "url": "COLE_AQUI"},
    {"titulo": "Presidente: Mococa",         "url": "COLE_AQUI"},
    {"titulo": "Governador (SP): Mococa",    "url": "COLE_AQUI"},
]
ARQUIVO = "apuracao.json"
BRT = timezone(timedelta(hours=-3))

def num(v):
    try:
        return float(str(v).replace(".", "").replace(",", "."))
    except Exception:
        return None

def baixar(url):
    req = Request(url, headers={"User-Agent": "MococaEmDia/1.0"})
    with urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))

def converter(titulo, d):
    cands = []
    for c in d.get("cand", []):
        votos = num(c.get("vap"))
        if not c.get("nm") or votos is None:
            continue
        cands.append({"nome": c["nm"].title(), "votos": int(votos),
                      "pct": num(c.get("pvap")), "eleito": str(c.get("e", "")).lower() == "s"})
    cands.sort(key=lambda c: c["votos"], reverse=True)
    return {"titulo": titulo, "status": "ok" if cands else "sem_dados",
            "secoes_pct": num(d.get("pst")), "candidatos": cands,
            "fonte_hora": f'{d.get("dg", "")} {d.get("hg", "")}'.strip()}

def main():
    saida = []
    for e in ELEICOES:
        if e["url"].startswith("COLE"):
            saida.append({"titulo": e["titulo"], "status": "nao_configurado", "candidatos": []})
            continue
        try:
            saida.append(converter(e["titulo"], baixar(e["url"])))
        except Exception as ex:
            print(f"[aviso] {e['titulo']}: {ex}", file=sys.stderr)
            saida.append({"titulo": e["titulo"], "status": "erro", "candidatos": []})
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump({"atualizado": datetime.now(BRT).isoformat(timespec="seconds"),
                   "eleicoes": saida}, f, ensure_ascii=False, indent=1)
    print("ok:", [(s["titulo"], s["status"]) for s in saida])

if __name__ == "__main__":
    main()
