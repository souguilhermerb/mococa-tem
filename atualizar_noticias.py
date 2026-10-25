#!/usr/bin/env python3
"""Coleta notícias de Mococa e região em feeds RSS/Atom e atualiza noticias.json.

Uso: python3 atualizar_noticias.py
Só usa a biblioteca padrão do Python (3.9+).
Guarda título, fonte, data e link. Não guarda o texto das matérias.
"""
import json, hashlib, sys, unicodedata
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

# ---------------- CONFIGURAÇÃO ----------------
# Abra cada URL no navegador para confirmar que é um feed válido.
# Feed que falhar é ignorado e o script segue com os demais.
# Para incluir Mococa 24h e Jornal Meio Dia, troque COLE_AQUI pelo endereço do feed.
FEEDS = [
    {"fonte": "g1 Ribeirão Preto e Franca", "url": "https://g1.globo.com/rss/g1/sp/ribeirao-preto-franca/"},
    {"fonte": "g1 Campinas e região",       "url": "https://g1.globo.com/rss/g1/sp/campinas-regiao/"},
    {"fonte": "g1 São Carlos e Araraquara", "url": "https://g1.globo.com/rss/g1/sp/sao-carlos-regiao/"},
    {"fonte": "R7 São Paulo",               "url": "https://noticias.r7.com/sao-paulo/feed.xml"},
    {"fonte": "Encontra Mococa",            "url": "https://www.encontramococa.com.br/feed/"},
    {"fonte": "Portal Rio Pardo",           "url": "https://portalriopardo.com.br/feed/"},
    {"fonte": "Mococa 24h",                 "url": "COLE_AQUI"},
    {"fonte": "Jornal Meio Dia",            "url": "COLE_AQUI"},
]
CIDADES_REGIAO = ["sao jose do rio pardo", "casa branca", "caconde", "tapiratiba",
                  "divinolandia", "sao sebastiao da grama", "itobi", "aguai"]
DIAS_MANTER = 30
MAXIMO = 80
INCLUIR_POLICIAL_AUTOMATICO = False  # títulos policiais podem citar nomes; deixe False e inclua à mão, sem nomes
ARQUIVO = "noticias.json"

CATEGORIAS = [  # a ordem importa: vale a primeira que combinar
    ("Segurança e trânsito", ["policia", "preso", "presa", "acidente", "morre", "homicidio", "assalto",
                              "roubo", "furto", "trafico", "delegacia", "colisao", "atropel"]),
    ("Saúde e educação", ["saude", "hospital", "santa casa", "upa", "vacina", "escola", "aluno",
                          "educacao", "faculdade", "enfermag", "dengue"]),
    ("Prefeitura e política", ["prefeit", "camara", "vereador", "eleic", "candidat", "decreto", "licitacao"]),
    ("Economia e emprego", ["emprego", "vaga", "empresa", "comercio", "restaurante", "industria",
                            "economia", "negocio", "agro", "leite", "cafe"]),
    ("Cultura, esporte e eventos", ["festa", "show", "cultura", "teatro", "esporte", "futebol",
                                    "natacao", "campeonato", "torneio", "evento", "exposicao"]),
    ("Utilidade pública", ["chuva", "tempo", "alerta", "interdit", "campanha", "falta de agua",
                           "energia", "defesa civil"]),
]
# ------------------------------------------------

def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()

def categoria_de(texto):
    t = norm(texto)
    for nome, palavras in CATEGORIAS:
        if any(p in t for p in palavras):
            return nome
    return "Cidade e serviços"

def lembrar_data(txt):
    if not txt:
        return None
    try:
        d = parsedate_to_datetime(txt)
    except Exception:
        try:
            d = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone(timedelta(hours=-3)))

def texto(el, *nomes):
    for filho in el:
        marca = filho.tag.split("}")[-1]
        if marca in nomes and (filho.text or "").strip():
            return filho.text.strip()
    return ""

def ler_feed(xml_bytes, fonte):
    """Devolve a lista de itens (título, link, data, descrição) do feed."""
    raiz = ET.fromstring(xml_bytes)
    itens = []
    for el in raiz.iter():
        marca = el.tag.split("}")[-1]
        if marca not in ("item", "entry"):
            continue
        link = texto(el, "link")
        if not link:  # Atom guarda o link em atributo
            for filho in el:
                if filho.tag.split("}")[-1] == "link" and filho.get("href"):
                    link = filho.get("href"); break
        itens.append({
            "titulo": texto(el, "title"),
            "url": link,
            "data": lembrar_data(texto(el, "pubDate", "published", "updated", "date")),
            "descricao": texto(el, "description", "summary"),
            "fonte": fonte,
        })
    return itens

def filtrar(itens):
    """Mantém só o que cita Mococa ou cidades da região e já classifica."""
    saida = []
    for it in itens:
        if not it["titulo"] or not it["url"] or not it["data"]:
            continue
        base = norm(it["titulo"] + " " + it["descricao"])
        if "mococa" in base:
            escopo = "Mococa"
        elif any(c in base for c in CIDADES_REGIAO):
            escopo = "Região"
        else:
            continue
        cat = categoria_de(it["titulo"] + " " + it["descricao"])
        if cat == "Segurança e trânsito" and not INCLUIR_POLICIAL_AUTOMATICO:
            continue
        saida.append({
            "id": hashlib.sha1(it["url"].encode()).hexdigest()[:10],
            "titulo": it["titulo"], "resumo": "", "categoria": cat, "escopo": escopo,
            "fonte": it["fonte"], "url": it["url"], "data": it["data"].date().isoformat(),
            "auto": True,
        })
    return saida

def baixar(url):
    req = Request(url, headers={"User-Agent": "MococaEmDia/1.0 (leitor de RSS)"})
    with urlopen(req, timeout=20) as r:
        return r.read()

def main():
    try:
        with open(ARQUIVO, encoding="utf-8") as f:
            atuais = json.load(f).get("noticias", [])
    except Exception:
        atuais = []
    por_url = {n["url"]: n for n in atuais}
    novos = 0
    for feed in FEEDS:
        if feed["url"].startswith("COLE"):
            continue
        try:
            achados = filtrar(ler_feed(baixar(feed["url"]), feed["fonte"]))
        except Exception as e:
            print(f"[aviso] {feed['fonte']}: {e}", file=sys.stderr)
            continue
        for n in achados:
            if n["url"] not in por_url:
                por_url[n["url"]] = n; novos += 1
    limite = (datetime.now() - timedelta(days=DIAS_MANTER)).date().isoformat()
    lista = [n for n in por_url.values() if n["data"] >= limite]
    lista.sort(key=lambda n: (n["data"], not n.get("auto", False)), reverse=True)
    saida = {"atualizado": datetime.now(timezone(timedelta(hours=-3))).isoformat(timespec="seconds"),
             "noticias": lista[:MAXIMO]}
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print(f"{novos} nova(s); {len(saida['noticias'])} no total.")

if __name__ == "__main__":
    main()
