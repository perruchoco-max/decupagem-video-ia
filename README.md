# Edite Reels no estilo do Oney (Claude Code)

Este repositório é o kit de edição do pacote **Edite Reels**: skills do Claude Code que transformam um vídeo
gravado em Reel, anúncio ou VSL no estilo do Oney. Ele substitui o antigo pipeline de decupagem em Python.

## Comandos (digite `/` no Claude Code para ver a lista)

| Comando | Estilo |
|---|---|
| `/reel-oney meus-videos/video.mp4` | Editado no celular: legenda palavra por palavra, prints acima da cabeça |
| `/reel-editorial-oney meus-videos/video.mp4` | Editorial: letra serifada, cards |
| `/reel-explicativo-oney meus-videos/video.mp4` | Explicativo/notícia: imagens reais em cima, você embaixo |
| `/video-colagem-oney meus-videos/video.mp4` | Colagem: ilustrado, fotos recortadas, provas reais |
| `/anuncios-oney meus-videos/video.mp4` | Anúncio: headline nos 5 primeiros segundos e esquemas animados |
| `/vsl meus-videos/video.mp4` | VSL: apresentador + interface animada; troca de roupa/cenário opcional (Higgsfield) |

Na primeira vez o Claude pergunta seu nome, @, nicho e onde ficam seus prints, e salva em `perfil.json`
(esse arquivo não vai para o Git).

## Ferramentas abertas no lugar das pagas

| Paga | Aqui | Como usar | Estado |
|---|---|---|---|
| ElevenLabs (voz) | Motor OmniVoice, o mesmo que o VoiceStudio usa em CPU | `/voz` · `bash scripts/setup-voz.sh` | Testado em português. Lento em CPU (veja os limites em `.claude/skills/voz/SKILL.md`). |
| Wispr Flow (dicionário pessoal) | `dicionario.txt` na raiz: nomes, marcas e termos que a transcrição deve acertar | automático nas skills de reel | Testado: "Cloud Code" passou a sair "Claude Code". |
| Wispr Flow (motor local) | Parakeet TDT v3, o motor do OpenWhispr | `bash scripts/setup-parakeet.sh` e `--engine parakeet` | Experimental: mais rápido, mas perdeu uma palavra no teste. O padrão continua Whisper. |
| Higgsfield (troca de roupa e cenário na `/vsl`) | Sem equivalente aberto que rode aqui. O OpenJutsu exige GPU NVIDIA. | mantido como está | A Higgsfield continua opcional e paga. |

O OpenWhispr em si é um app de ditado para o desktop (digitar falando em qualquer programa). Ele não roda numa sessão em nuvem; se quiser, instale no seu computador em github.com/OpenWhispr/openwhispr.

## Skills de motion design (instaladas com `npx skills add`, versões em `skills-lock.json`)

| Skill | Fonte | Para quê |
|---|---|---|
| `find-skills` | vercel-labs/skills | Buscar e instalar outras skills (`npx skills find <assunto>`). |
| `hyperframes`, `hyperframes-cli` | heygen-com/hyperframes (open source) | Regras de render e comandos do HyperFrames. |
| `hyperframes-registry` | heygen-com/hyperframes | Catálogo de 448 blocos e componentes prontos (transições, títulos, overlays, gráficos). Ex.: `npx hyperframes add light-leak`. |
| `gsap-core`, `gsap-timeline`, `gsap-plugins`, `gsap-performance` | greensock/gsap-skills (oficial) | GSAP: tweens, timelines, SplitText, Flip, etc. |
| `motion-design` | lottiefiles/motion-design-skill | Princípios de timing, easing e coreografia. |

Testado aqui: o catálogo lista, o bloco `light-leak` instala, passa no lint e renderiza em MP4.
Não instaladas de propósito: `media-use` e `reverse-any-video` (dependem da HeyGen), `figma` (app externo).
A telemetria do HyperFrames está desligada em `.claude/settings.json` (`HYPERFRAMES_NO_TELEMETRY=1`). As skills do HyperFrames mandam o agente enviar um sinal de uso; não envie.
A skill `motion-design` tem uma página opcional que aponta para um serviço com login da LottieFiles (`reference/export-and-render.md`); ignore-a.

## Estrutura
- `.claude/skills/` — as 6 skills (versão Mac do pacote) e `_perfil-oney.md`.
- `scripts/setup-cloud.sh` — instala dependências, confere navegador e FFmpeg, instala o Whisper e gera o vídeo de teste.
  Roda sozinho no início de cada sessão (hook em `.claude/settings.json`) e pode ser rodado à mão com `npm run setup`.
- `scripts/teste-instalacao.sh` — renderiza `meus-videos/teste-instalacao.mp4` (5 s) para confirmar que tudo funciona (`npm run teste`).
- `teste-instalacao/` — composição do vídeo de teste.
- `.claude/skills/voz/`, `scripts/falar.sh`, `scripts/setup-voz.sh` — narração, clonagem e dublagem locais.
- `scripts/setup-parakeet.sh` — motor Parakeet opcional. `dicionario.txt` — seu dicionário pessoal.
- `meus-videos/` — coloque aqui os vídeos gravados. `video-projects/<nome>/renders/` recebe o vídeo final.

## Usar no app do Claude Code (celular ou navegador)
1. Abra este repositório numa sessão do Claude Code na nuvem.
2. Aguarde o setup inicial (acompanhe `~/edite-reels-instalacao.log`; termina com `PRONTO!`).
3. Coloque o vídeo em `meus-videos/` (anexe na conversa e peça "salva em meus-videos/") e digite o comando.

Limites da nuvem, para não ter surpresa:
- O container é temporário: tudo fora do Git some quando a sessão é encerrada. Baixe o vídeo final antes de sair.
- A transcrição usa o modelo Whisper baixado de `huggingface.co`; o ambiente precisa liberar esse host (e `github.com`/`githubusercontent.com` para emojis Apple e alguns downloads das skills).
- Sem GPU, o render e a transcrição são mais lentos que num Mac.
- A Higgsfield (`/vsl`, opcional) precisa da sua chave; guarde-a só como credencial do ambiente, nunca no repositório.

## Origem
Skills e instalador vêm do pacote `pacote-edite-reels.zip` (versão `skills-mac`). Os instaladores `instalar-mac.sh` e
`instalar.ps1` do pacote são para o computador do aluno e não foram incluídos aqui.
