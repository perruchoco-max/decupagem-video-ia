# Instalação no Mac (Modo Local)

Testado nesta sessão: compilei o `whisper.cpp` (mesmo código-fonte, build CPU em Linux em vez
de Metal no M1) e rodei o pipeline inteiro de ponta a ponta contra ele (`tests/test_local_logic.py`)
antes de escrever este guia — os comandos abaixo são os mesmos confirmados ali, só trocando a
aceleração de hardware.

## Pré-requisitos
- Homebrew (https://brew.sh) — se não tiver, instale primeiro.
- ~1GB livre em disco (modelo Small + build do whisper.cpp).

## Passo a passo

```bash
git clone https://github.com/perruchoco-max/decupagem-video-ia
cd decupagem-video-ia
bash local/instalar_mac.sh
```

Isso faz, nessa ordem:
1. Confere/instala `cmake` e `ffmpeg` via Homebrew (se já tiver, não reinstala).
2. Clona o `whisper.cpp` em `local/whisper.cpp/` e compila com `cmake` — no Apple Silicon, a
   aceleração Metal é ativada automaticamente pelo próprio build, não precisa de flag especial.
3. Baixa o modelo multilíngue **Small** em formato GGML (~500MB).

Ao final, o binário fica em `local/whisper.cpp/build/bin/whisper-cli` e o modelo em
`local/whisper.cpp/models/ggml-small.bin`.

## Testar com um arquivo seu

```bash
python3 cli.py --modo local \
  --whisper-cli local/whisper.cpp/build/bin/whisper-cli \
  --modelo local/whisper.cpp/models/ggml-small.bin \
  /caminho/para/seu_video.mp4 \
  /caminho/para/pasta_de_saida
```

O vídeo original em `/caminho/para/seu_video.mp4` não é alterado. Os resultados (vídeo decupado,
transcrições, lista de cortes, relatório, SRT) vão para a pasta de saída indicada.

## O que já foi validado de verdade, e o que ainda não
- **Validado nesta sessão** (build Linux do mesmo binário): o parsing do JSON do whisper.cpp, os
  flags de linha de comando (`-dtw`, `-ojf` etc.), a integração com `core/decoupage.py` e
  `core/cutter.py`, a geração do arquivo final e dos relatórios, com um binário `whisper-cli`
  de verdade.
- **Ainda não validado** (precisa ser feito por você, no Mac, com uma gravação real): a
  aceleração Metal em si (eu só testei em CPU), o tempo real de processamento num M1, e a
  qualidade da transcrição com voz humana real — os testes aqui usaram voz sintética
  (espeak-ng), que o modelo transcreve pior do que uma voz humana normal.

## Problemas conhecidos / se algo não funcionar
- Se o `cmake` reclamar de Xcode Command Line Tools ausentes: rode `xcode-select --install`.
- Se `whisper-cli` não compilar: confira a versão do Xcode (`xcodebuild -version`); o whisper.cpp
  precisa de um compilador C++17.
- O modelo Small multilíngue é maior e mais lento que o padrão `base.en` usado em muitos
  tutoriais — isso é intencional (seção 3 do pedido original: priorizar Small multilíngue se a
  memória permitir). Se o M1 for de 8GB e o desempenho ficar ruim, dá para trocar para o modelo
  `base` editando o nome passado a `download-ggml-model.sh` e ao `--modelo` do `cli.py`.
