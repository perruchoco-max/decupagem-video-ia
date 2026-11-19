---
name: layout-reel
description: Regras e verificação automática de espaçamento, alinhamento e hierarquia para Reels/vídeos verticais montados em HTML (HyperFrames). Use ANTES de montar e ANTES de renderizar qualquer Reel com vídeo, legendas, selos, dados e logos; e sempre que o usuário disser "espremido", "apertado", "desalinhado", "logos grandes", "título em duas linhas" ou pedir ajuste de espaço. Evita retrabalho: mede o resultado renderizado em vez de confiar no olho.
---

# Layout de Reels sem retrabalho

Origem: fica registrado aqui o que o usuário teve de pedir várias vezes (blocos espremidos, separadores desalinhados, logos grandes demais, títulos quebrados sem necessidade). Base teórica: skills `refactoring-ui` (escala de espaçamento, "espaço entre grupos > espaço dentro dos grupos", "comece com espaço demais"), `better-typography` (`text-box`, `text-wrap`, uma linha para rótulos) e `impeccable/layout` (ritmo = contraste entre intervalos curtos e generosos; verificar com evidência renderizada). Leia a `refactoring-ui` e a `better-typography` se for desenhar algo novo.

## 1. Antes de desenhar: grupos, hierarquia, orçamento vertical
1. **Liste os blocos e agrupe por significado** (ex.: cabeçalho = linha pequena + título; vídeo; legenda; dado em destaque; marcas). Blocos do mesmo grupo ficam perto; grupos diferentes ficam longe.
2. **Nomeie a hierarquia**: o que lidera (vídeo/animal e fala) e o que apoia (créditos, selos). O apoio fica menor e mais discreto. Marcas do cliente e do evento ficam maiores que créditos de transmissão/agência.
3. **Faça o orçamento vertical numa tabela** antes de escrever HTML: altura de cada bloco (tinta) + espaços. Zona segura do Instagram Reels: texto principal entre y 269–1248 e x 65–1015 (verificador do HyperFrames); rodapé de marcas pode ir até ≈1570 (340 px inferiores do Instagram). Se não couber, **reduza tamanho de bloco ou corte conteúdo, nunca o espaço**.

## 2. Escala de espaçamento (a única que vale)
Múltiplos de 8: `8 · 16 · 24 · 32 · 48 · 64 · 96`. Nenhum outro valor (nada de 22, 26, 13).
- **Dentro de um grupo**: 24 (ou 8–16 entre linha pequena e título).
- **Entre blocos de conteúdo** (cabeçalho · vídeo · legenda · dado): 48, o mesmo valor entre todos.
- **Entre o conteúdo e o bloco de marcas**: 96 (≥ 1,6× o espaço entre blocos).
- Conteúdo não pode ficar "colado": mínimo de 40 px entre blocos de conteúdo.

## 3. Meça pela tinta, não pela caixa do CSS
A caixa de um texto tem folga invisível (entrelinha). Use `text-box: trim-both cap alphabetic` + `line-height: 1` nos textos de uma linha para que a caixa seja do topo das maiúsculas à linha de base. Acentos (Ã, Ê) e pernas (J, Q) não contam para o alinhamento; logos e molduras contam pela tinta. Construa as posições a partir da escala (constantes derivadas), não com números soltos.

## 4. Alinhamento e separadores
- **Um eixo central (x = 540)** para tudo que é centralizado. Separadores verticais caem **exatamente** em x = 540, centralizados na altura do conteúdo que separam, com o mesmo comprimento relativo.
- Linhas de marcas **simétricas ao eixo**: colunas de larguras iguais, cada logo centrada na sua coluna (nunca "encostada" no separador).
- Borda esquerda do título = borda esquerda da moldura do vídeo.

## 5. Títulos e rótulos
- **Uma linha.** Meça a largura real (Cinzel 700, 36 px cabe em 916 px de 920 disponíveis). Subtítulo/pedigree vai **na mesma linha**, menor e em verde. Não quebre linha só porque o texto é longo: reduza um passo da escala ou reorganize.
- **A altura do cabeçalho é constante em todas as cenas** (o vídeo nunca "pula"). Se um texto excepcional precisar de outro tamanho, compense a altura (ex.: `margin-top`) para o fundo ficar na mesma linha.
- Rótulos e selos: `white-space: nowrap`. Legendas: `text-wrap: balance`, até 2 linhas, faixa própria.

## 6. Verificação obrigatória antes de renderizar
```bash
node .claude/skills/layout-reel/scripts/audit.mjs index.html
```
(ou o `layout-audit.mjs` do projeto). Ele renderiza o HTML em Chrome, mede a tinta em 12 momentos e falha se: título passar de uma linha; espaços entre blocos forem desiguais ou < 40 px; o espaço antes das marcas não for ≥ 1,6× os outros; os espaços do bloco de marcas não forem uniformes e menores; separadores fugirem do eixo ou do centro do conteúdo; algo sair da zona segura; o cabeçalho "pular" entre cenas. **Só renderize com "AUDITORIA OK"** e depois olhe 6–8 quadros em tamanho de celular (teste de apertar os olhos: dá para ver líder, apoio e grupos?).
Ajuste o script (seletores e constantes no topo e no `build.mjs`) ao projeto: ele espera `.hd/.kick/.ttl`, `.cap`, `.chip`, um rodapé `[id^=ft]` e a moldura do vídeo.

## 7. Ao receber "isso está espremido/desalinhado"
Não ajuste um número. Pergunte: qual **grupo** está quebrado? Rode a auditoria, leia a tabela de espaços e corrija pela escala. Mostre ao usuário a tabela de espaços medidos (tinta → tinta) junto com o resultado.
