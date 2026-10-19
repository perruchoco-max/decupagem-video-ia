# Handoff — decupagem inteligente de vídeos (estado real, para continuar em outra ferramenta)

Repositório: https://github.com/perruchoco-max/decupagem-video-ia (privado, conta perruchoco-max)
Último commit relevante: `35ca07a`

## O que o sistema é

Núcleo compartilhado de decupagem para Reels, com dois backends de transcrição intercambiáveis:
`CloudFasterWhisperBackend` (Linux, faster-whisper, testado) e `LocalWhisperCppBackend`
(macOS M1, whisper.cpp, testado). Mesma lógica de decisão (`core/decoupage.py`) para os dois.
Modo conservador: remove silêncio real, remove retomadas de frase inteira repetida, remove
marcadores de recomeço por palavra-chave, gera relatório + JSON de cortes + SRT + transcrições,
nunca mexe no arquivo original.

## Problemas reais encontrados e já corrigidos (histórico, mais recente por último)

1. **MP4 não decodifica no whisper.cpp.** O decodificador embutido (miniaudio) só lê áudio bruto
   (wav/mp3/flac/ogg). Corrigido: `LocalWhisperCppBackend` extrai sempre para WAV 16kHz mono via
   FFmpeg antes de chamar o binário.
2. **Causa raiz de "nenhum silêncio era cortado" em vídeo real.** A primeira versão só removia o
   espaço *entre* os segmentos que o próprio Whisper decidia criar — e o Whisper costuma juntar
   várias frases com pausas reais entre elas num único segmento de texto longo, sem nunca
   dividi-lo. Corrigido com mudança de arquitetura: `core/vad.py` detecta silêncio acústico real
   via `ffmpeg silencedetect`; `core/decoupage.py` desmonta os segmentos em palavras e remonta
   "falas" nos pontos onde esse silêncio real confirma uma pausa — não nos limites que o modelo
   de linguagem escolheu para o texto.
3. **Preset de alinhamento DTW do whisper.cpp (`-dtw`) precisa bater com o tamanho do modelo.**
   Não dá erro quando não bate — só produz timestamps de palavra errados silenciosamente, o que
   fez o corte piorar sem aviso num teste. `LocalWhisperCppBackend` agora infere o preset do nome
   do arquivo do modelo e recusa combinações incompatíveis com erro explícito.
4. **Rede do ambiente de nuvem bloqueava CDNs do Hugging Face** (não só o domínio principal —
   `cas-server.xethub.hf.co`, `us.aws.cdn.hf.co` etc. mudam). Resolvido ampliando o nível de
   acesso de rede do ambiente (não dá pra resolver com allowlist de domínio por domínio).
5. **PyAV 19 incompatível com faster-whisper 1.2.1** (API mudou, `av.open()` perdeu um kwarg que
   a lib usa). Fixado `av<14` em `requirements-cloud.txt`.

## O limite real, ainda não resolvido (a trava atual)

Testado com a transcrição real de um vídeo do usuário (`C9147.MP4`, 18s, fala corrida sem
pausas reais) e com áudio sintético comparativo:

- **O Whisper "limpa" disfluências na transcrição.** Quando o locutor se autocorrige no meio da
  frase (ex: "...discos que se... berrr... eu separei alguns discos que podem..."), o modelo às
  vezes funde as duas tentativas numa frase "limpa" só, sem repetir o texto literalmente na
  saída. Qualquer detecção por repetição de texto falha aqui porque a informação da repetição já
  não existe na transcrição — não é possível recuperá-la só analisando o texto.
- **Marcadores curtos de início de gravação podem ser descartados.** No mesmo vídeo, "Um,
  valendo." (claquete) nunca apareceu na transcrição — o Whisper classificou como não-fala.
  Testei com áudio sintético equivalente e o modelo conseguiu transcrever quando havia contexto
  de fala real em seguida — então isso pode ser recuperável ajustando parâmetros de VAD/limiar,
  mas não confirmei ainda com o áudio real do usuário.
- **A única abordagem comprovadamente capaz de recuperar o caso da disfluência** é uma segunda
  passada com um modelo multimodal ouvindo o ÁUDIO/VÍDEO de verdade (não só o texto). Confirmado
  investigando a arquitetura do projeto open-source `kurbaitaev/ghost-editor`, que documenta
  exatamente este mesmo problema do Whisper e resolve enviando o corte provisório para o Gemini
  2.5 Pro pedindo uma "auditoria verbatim" (repetições, preenchimentos, palavras cortadas) — os
  timestamps do Gemini não são usados para cortar (não são confiáveis o suficiente), só os
  timestamps de palavra do Whisper, guiados pelo que o Gemini apontou.
- **Alternativa 100% local ainda não implementada nem validada:** autossimilaridade acústica —
  comparar a forma de onda consigo mesma pra achar uma frase real repetida sem depender da
  transcrição. Tecnicamente viável (técnica usada em análise de estrutura musical), mas não
  prototipado ainda; não há garantia de que funcione bem em fala antes de testar de verdade.
- Outros projetos avaliados e descartados: `autobroll` (usa WhisperX, mesma limitação de base,
  depende de Gemini pago pra B-roll que o usuário não quer); `auto-editor` (maduro, mas
  puramente acústico/sem transcrição — não exporta pra CapCut); `davinci-resolve-mcp` (muda o
  produto para "primeira montagem no DaVinci Resolve + humano finaliza", exige Resolve Studio
  pago ou bridge incerto na versão gratuita — mudança de direção grande, não um ajuste).

## Minhas intenções / o que espero no resultado final

- Sistema híbrido: mesmas regras editoriais rodando local (Mac M1, whisper.cpp) e na nuvem
  (faster-whisper), sem duplicar lógica.
- Decupagem conservadora deve remover de verdade: silêncio real, retomadas completas de frase,
  **e também autocorreções/gaguejos no meio da fala e marcadores de início de gravação** — esses
  dois últimos são o que ainda falta resolver de forma confiável.
- Nunca inventar fala, nunca cortar no meio de uma palavra, preservar pausas expressivas,
  sinalizar trechos duvidosos para revisão humana em vez de decidir sozinho quando a confiança é
  baixa.
- Saída final importável no CapCut: vídeo/áudio cortado, transcrição original e final, lista de
  cortes em JSON com timecodes, relatório de decisões, SRT.
- Preferência por não depender de serviços pagos adicionais — mas estou disposto a reconsiderar
  isso especificamente para o caso de disfluência, já que a investigação mostrou que esse caso
  específico parece exigir um modelo multimodal ouvindo áudio real (texto sozinho não basta).
- Decisão em aberto que preciso que você me ajude a resolver: (a) integrar uma segunda passada
  com Gemini (API, não a assinatura Pro de chat) para auditoria verbatim do corte provisório, ou
  (b) prototipar a rota 100% local de autossimilaridade acústica antes de aceitar a dependência
  externa, ou (c) aceitar que esse tipo específico de correção fica para revisão manual no
  CapCut e não tentar mais automatizar.
