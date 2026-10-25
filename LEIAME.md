# Mococa em Dia: atualização a cada hora

Arquivos
- `index.html`: o painel. Lê `noticias.json` ao abrir e a cada 1 hora.
- `noticias.json`: as notícias (começa com as 5 verificadas à mão).
- `atualizar_noticias.py`: lê os feeds RSS, filtra Mococa e região e atualiza o JSON.
- `.github/workflows/atualizar.yml`: agenda o script de hora em hora no GitHub.

Como publicar (gratuito)
1. Crie um repositório no GitHub e envie estes arquivos, mantendo a pasta `.github`.
2. Em Settings > Pages, escolha a branch principal e a pasta raiz. O painel fica no endereço que o GitHub mostrar.
3. Em Actions, abra "Atualizar notícias de Mococa" e clique em Run workflow para testar.

Ajustes no topo de `atualizar_noticias.py`
- `FEEDS`: confirme cada endereço no navegador. Troque `COLE_AQUI` pelos feeds do Mococa 24h e do Jornal Meio Dia.
- `INCLUIR_POLICIAL_AUTOMATICO`: fica `False` porque títulos policiais podem citar nomes. Inclua esses casos à mão, sem nomes.

Observações
- Itens automáticos entram sem resumo, só com título, fonte, data e link. Para resumos, edite o `noticias.json` e preencha `resumo` com palavras próprias.
- Os endereços de feed do g1 e do R7 não foram testados aqui. Se algum falhar, o script ignora e segue com os outros.
- O GitHub pode atrasar ou pular execuções agendadas em horários de pico.
