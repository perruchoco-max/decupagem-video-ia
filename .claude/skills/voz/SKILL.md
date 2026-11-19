---
name: voz
description: Gera narração (texto para fala), clona a voz do próprio criador a partir de uma gravação de referência e dubla vídeos por arquivo SRT, tudo local e gratuito, com o motor OmniVoice (o mesmo que o VoiceStudio usa em CPU). Alternativa aberta à ElevenLabs. Use quando o usuário disser "/voz", "narra esse texto", "gera a voz", "clona minha voz", "dublar", "locução", ou quando um vídeo precisar de narração que o criador não gravou. Para editar vídeo gravado use reel-oney e as demais skills.
---

# Voz: narração, clonagem e dublagem locais

Motor: `omnivoice.cpp` (MIT) com os pesos OmniVoice GGUF, o mesmo caminho de CPU do VoiceStudio. Roda sem GPU e sem chave de API.
Instalação (uma vez, uns 5 min, ~660 MB): `bash scripts/setup-voz.sh` na raiz do kit. Se `scripts/falar.sh` disser que o motor não está instalado, rode isso e avise o usuário em uma linha antes.

## Limites que o usuário precisa saber (diga antes de começar)
- **Velocidade em CPU:** com 32 passos (padrão, melhor qualidade) leva ~22 s por segundo de áudio; com `--steps 10` leva ~8 s por segundo. Uma narração de 30 s leva de 4 a 11 min. Gere rascunho com `--steps 10` e o final com o padrão.
- **Qualidade:** testado em português; o resultado é compreensível, mas não houve comparação cega com a ElevenLabs. Nomes próprios e números podem sair com sotaque estranho (ex.: "Perrucho" saiu "Perúcho" em um teste). Escreva por extenso quando precisar (ex.: "doze mil") e ouça antes de usar.
- **Clonagem de voz:** só use a voz do próprio usuário ou de alguém que tenha dado autorização por escrito. Peça confirmação antes de clonar qualquer voz que não seja a dele.

## Uso
Narração a partir de texto ou arquivo:
```bash
bash scripts/falar.sh "Texto da narração." video-projects/<slug>/assets/narracao.wav --steps 10
bash scripts/falar.sh roteiro.txt video-projects/<slug>/assets/narracao.wav
```
Voz clonada (gravação limpa de 5 a 15 s, sem música, mais o texto exato do que foi dito num `.txt`):
```bash
bash scripts/falar.sh roteiro.txt saida.wav --ref-wav minha-voz.wav --ref-text minha-voz.txt
```
Dublagem: o `.srt` define o tempo de cada fala; sai um WAV na linha do tempo, pronto para juntar ao vídeo:
```bash
bash scripts/falar.sh --srt traducao.srt dublagem.wav --ref-wav minha-voz.wav --ref-text minha-voz.txt --lang English
```
Outras opções: `--seed N` (repetir o mesmo resultado), `--lang <idioma em inglês>` (padrão Portuguese), `--instruct "<estilo>"`.

## Depois de gerar
1. Ouça (ou transcreva de volta com `transcribe-local-whisper.py` e confira) antes de entregar. Corrija o texto e gere de novo se houver erro.
2. Para usar numa edição, coloque o WAV em `assets/` do projeto e trate como áudio de entrada das skills de reel (as skills transcrevem e legendam normalmente).
3. Para trocar o áudio de um vídeo: `ffmpeg -i video.mp4 -i narracao.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest saida.mp4`.

## VoiceStudio completo (opcional, no computador do usuário)
O aplicativo VoiceStudio (AGPL-3.0, github.com/debpalash/VoiceStudio) tem interface, vozes salvas, projetos e CLI (`voicestudio speak`, `transcribe`, `dub`), mas depende do backend Python completo (vários GB) e não foi instalado aqui. Se o usuário tiver GPU, vale instalá-lo no computador dele. Não copie o código dele para este repositório (a AGPL exigiria publicar o código de quem o modifica e oferece em rede); chame-o como programa separado.
