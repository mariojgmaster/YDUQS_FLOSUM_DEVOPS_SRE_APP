# PNGs originais — fontes aprovadas

Os 14 **conceitos originais gerados** estão identificados em [visual-manifest.json](../visual-manifest.json) pelo nome e checksum SHA-256. A pasta `visual/` contém reconstruções vetoriais navegáveis (não são cópias dos PNGs).

A versão completa dos PNGs é distribuída como `branch-monitor-componentes-14-originais.zip`. Em um checkout local deste repositório, execute:

```sh
python scripts/docs/import_componentes_originals.py ./branch-monitor-componentes-14-originais.zip
git add docs/branch-monitor/componentes/originals
git commit -m "docs: version 14 original Componentes visual references"
git push
```

O importador confere todos os SHA-256 antes de gravar os arquivos e não publica sozinho.

**Status:** enquanto estes arquivos PNG não existirem na branch, o catálogo vetorial e o manifesto são a referência versionada. Não afirmar que os PNGs originais foram enviados ao GitHub.
