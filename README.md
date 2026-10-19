# Decupagem Inteligente de Vídeos — Núcleo Compartilhado

Protótipo do núcleo compartilhado de decupagem (Fase 1 e 2 do plano), com os mesmos módulos
usados tanto no Modo Local (Mac M1, whisper.cpp) quanto no Modo Nuvem (Linux, faster-whisper).

Leia `docs/AUDITORIA.md` primeiro — tem o que foi verificado de verdade nesta sessão (o que
funciona, o que está bloqueado e por quê) antes de qualquer decisão de arquitetura.

## Estrutura
- `core/transcribe.py` — abstração de backend de transcrição (`CloudFasterWhisperBackend`,
  `LocalWhisperCppBackend`).
- `core/decoupage.py` — decisão editorial do modo conservador (silêncio, retomadas, repetições,
  margens de segurança por palavra).
- `core/cutter.py` — motor de cortes com FFmpeg (áudio e vídeo).
- `core/report.py` — exportações comuns (transcrições, JSON de cortes, relatório, SRT).
- `core/pipeline.py` — orquestra os passos acima.
- `tests/test_core_logic.py` — testado e passando nesta sessão (corte real via FFmpeg).
- `tests/test_e2e_cloud.py` — transcrição real via faster-whisper; bloqueado até liberar
  `huggingface.co` na rede do ambiente.

## Status (nesta sessão)
Fase 1 (auditoria) e Fase 2 (núcleo + testes do motor de corte) concluídas e testadas de
verdade. Fases 3 (validação no Mac) e 4 (transcrição real na nuvem) dependem de duas ações do
usuário — ver `docs/AUDITORIA.md`.
