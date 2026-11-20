---
name: legenda-palavra-a-palavra
description: Gera legendas dinâmicas palavra a palavra para vídeos verticais de fala (Reels/TikTok/Shorts, depoimento ou talking head) no estilo "editorial escuro": fonte sans geométrica minúscula, uma palavra por vez no terço inferior do centro, hierarquia de peso (leve, negrito, black gigante) para a palavra de impacto, sem glow e sem caixa. Use sempre que o usuário pedir legenda estilizada, legenda dinâmica, legenda palavra por palavra, legenda "nessa pegada", gerar .ass/.srt com timing por palavra, queimar legenda no vídeo, ou mencionar o vídeo de referência da legenda, mesmo sem citar o estilo.
---

# Legenda palavra a palavra (estilo editorial)

Estilo extraído de um vídeo de referência de 55,8 s, 720x1280, 30 fps (depoimento em ambiente escuro). Os números abaixo foram medidos quadro a quadro, não estimados a olho. A única característica da referência que o usuário rejeitou é o **brilho fluorescente (outer glow)** em torno das letras; ele não faz parte deste estilo.

## Por que funciona (o racional)

- **Uma palavra por vez** acompanha o ritmo da fala e prende o olho no ponto exato onde o áudio está. Cada palavra dura em média 0,3 s (faixa observada: 0,15 a 0,6 s). Palavras mais longas ou faladas devagar ficam mais tempo; palavras funcionais curtas ficam menos.
- **A legenda some nas pausas.** Se a pessoa para de falar, o texto sai da tela. Isso mantém a respiração do vídeo e evita ruído visual. Nunca estenda uma palavra para "preencher" silêncio.
- **Hierarquia de peso e tamanho** diz ao espectador o que importa sem ele ler: palavras de ligação em peso leve, palavras-chave em negrito, a palavra de impacto da frase enorme e em black. Funciona como a entonação escrita.
- **Posição logo abaixo do rosto, no centro**, para o olhar não sair do rosto. Rosto fica no terço superior e central; a legenda fica entre o peito e as mãos.
- **Sem caixa, sem contorno grosso, sem glow.** O vídeo é escuro e de baixa luz; letra branca pura com sombra suave já tem contraste suficiente. O glow compete com o rosto e denuncia template.

## Especificação medida

Todas as posições em fração da altura (H) e da largura (W) do vídeo, para valer em qualquer resolução 9:16.

| Elemento | Valor |
|---|---|
| Cor | Branco puro `#FFFFFF` |
| Sombra | Preta, suave, deslocada para baixo (ASS: `Shadow` 2 a 3 px em 720 de largura, `BackColour` ~60% opaco, borda 0). Sem blur luminoso, sem contorno colorido |
| Caixa de fundo | Nenhuma |
| Caixa de texto | Minúsculas, mantendo pontuação (vírgula, ponto, interrogação) |
| Alinhamento horizontal | Centralizado em x = 0,5 W |
| Posição vertical (corpo) | Centro da palavra em ~0,62 H (faixa 0,60 a 0,65 H) |
| Tamanho (corpo) | Altura-x ~3,5% H; corpo de fonte ~6,7% de W (≈ 48 px em 720; ≈ 72 px em 1080) |
| Tamanho (palavra de impacto) | ~2x o corpo (≈ 14% de W; ≈ 105 px em 720) |
| Tracking | Levemente fechado (-1 a -2%) |
| Entrada/saída | Corte seco. Sem fade, sem slide. A palavra aparece em 1 quadro |

### Fonte e pesos

Família: sans geométrica de aparência Gotham/Montserrat (a de duplo andar, "t" curto, bojos circulares). **Use Montserrat** (Google Fonts, gratuita). Fallback: Inter.

| Papel | Peso | Exemplos na referência |
|---|---|---|
| Palavra de ligação | Montserrat Regular/Light | "seus", "você", "isso", "não" |
| Palavra-chave | Montserrat Bold ou Bold Italic | "talvez", "esteja", "vídeos" |
| Palavra de impacto | Montserrat ExtraBold/Black, ~2x | "pacientes", "fazendo", "pode" |

Itálico só em palavras-chave de dúvida ou ênfase leve ("talvez"). Não use itálico em tudo.

## Dois modos de composição

**Modo corpo (maior parte do vídeo): palavra por palavra.**
Uma palavra por vez, centralizada em ~0,62 H. Agrupe 2 a 3 palavras funcionais curtas quando forem ditas juntas e rápido (ex.: "sou a", "e faço", "com a do", "ou até", "me fala"). Substantivos, verbos de ação e números ficam sempre sozinhos.

**Modo gancho (primeiros ~5 s): frase que se acumula.**
Nos primeiros segundos as palavras se somam em um bloco de até 3 linhas centralizado em ~0,45 a 0,70 H (mais alto que o corpo, com mais respiro), e a frase inteira some junta antes da próxima. Exemplo da referência: "seus" → "seus vídeos" → "seus vídeos / não estão te trazendo" → linha 3 "pacientes" gigante. O bloco só é limpo quando a frase termina. Use o modo gancho só na abertura (a leitura da frase completa é o que segura quem chegou agora), depois mude para o modo corpo.

**Etiqueta contextual (opcional):** texto curto em caixa alta, negrito, com emoji de alerta, em ~0,11 H, centralizado, ex.: "⚠️ AVISO DE VÍDEO GENÉRICO". Corpo ~2,3% de H. Aparece de forma intermitente, só para comentar a cena. Use apenas se o roteiro pedir.

## Regras de decisão para a palavra de impacto

Escolha 1 palavra de impacto a cada 8 a 12 palavras faladas, ou cerca de 1 por frase de peso. Candidatas, em ordem de prioridade:

1. O objeto da dor ou do desejo ("pacientes", "dinheiro", "cliente").
2. A negação ou modal que vira a frase ("pode", "nunca", "não").
3. O verbo-ação central ("fazendo", "conectar").
4. Número ou prazo.

Nunca marque artigos, preposições ou conectivos. Marque no máximo 1 por grupo de 6 palavras para não diluir o efeito. Se a fala não tem palavra de peso evidente, não force: prefira zero impactos a impactos falsos.

## Fluxo de trabalho

1. **Obtenha os tempos por palavra.** O repositório já transcreve com timestamps por palavra (`core/transcribe.py`, faster-whisper ou whisper.cpp). Se só houver SRT por frase, peça a transcrição por palavra antes de seguir. Distribuir uma frase em partes iguais gera sincronia visivelmente errada.
2. **Defina palavras-chave e de impacto** usando as regras acima e mostre a lista ao usuário para aprovação quando o vídeo for importante.
3. **Gere o arquivo ASS** com o script:
   ```bash
   python3 .claude/skills/legenda-palavra-a-palavra/scripts/gerar_ass.py palavras.json saida.ass --largura 1080 --altura 1920 \
     --impacto pacientes fazendo pode --chave talvez esteja
   ```
   `palavras.json` é uma lista de `{"word": "...", "start": 0.0, "end": 0.0}` (formato do Whisper). Opções: `--fonte`, `--modo-gancho-ate SEGUNDOS`, `--agrupar` (agrupa palavras funcionais curtas).
4. **Queime no vídeo** (instale Montserrat antes, ou use `--fonte Inter`):
   ```bash
   ffmpeg -i entrada.mp4 -vf "ass=saida.ass" -c:a copy saida_legendado.mp4
   ```
5. **Confira 3 quadros** (um do gancho, um do corpo, um de impacto): texto centralizado, sem cortar nas bordas, contraste legível sobre mãos e roupa clara, sem brilho.

## O que não fazer

- Não adicione glow, neon, contorno colorido, caixa preta ou gradiente.
- Não use fundo animado, bounce, shake ou zoom pulsante nas palavras.
- Não coloque a legenda sobre os olhos ou a boca. Se o enquadramento mudar para close, mantenha ~0,62 H e confira.
- Não deixe palavra na tela durante silêncio.
- Não mude a fonte no meio do vídeo. Só peso e tamanho variam.

## Limites do que foi medido

Medido do vídeo: posição, tamanhos relativos, duração por palavra, modo acumulado no gancho, ausência de fade. **Inferido visualmente, não medido:** a família exata da fonte (identificada como equivalente a Gotham/Montserrat), o tracking e a intensidade da sombra. Se o usuário tiver o arquivo de fonte original, troque `--fonte`.
