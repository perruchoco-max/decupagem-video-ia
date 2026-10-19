# Fase 1 — Auditoria (resultado real, testado nesta sessão)

## Ambiente de execução desta sessão (nuvem)
- Linux x86_64, 4 vCPUs, 15GB RAM, 30GB livres em disco.
- FFmpeg 6.1.1 já instalado (libx264, libopus, libvpx etc.) — motor de cortes pronto para uso.
- Python 3.13 + pip, com saída de rede liberada para PyPI. `faster-whisper` 1.2.1 instala e
  importa sem problema.
- **Rede corrigida com a ajuda do usuário.** O download do modelo Whisper não usa só
  `huggingface.co` — redireciona para CDNs variadas (`cas-server.xethub.hf.co`,
  `us.aws.cdn.hf.co` e outras). Liberar só o domínio principal não bastou; foi preciso ampliar o
  nível de acesso à rede do ambiente para "qualquer domínio" (Network access → nível amplo, não
  allowlist). Registrado aqui para quem for replicar: **não dá para resolver isso com uma lista
  de domínios individuais**, porque os hosts de CDN mudam.
- Também foi preciso fixar `av<14` (PyAV) — a versão 19.0.1 instalada por padrão quebra a
  chamada interna do `faster-whisper` para decodificar áudio (`metadata_errors` kwarg removido
  da API do PyAV novo). Já adicionado em `requirements-cloud.txt`.
- `espeak-ng` instalado via apt (usado só para gerar áudio sintético de teste, não faz parte do
  produto final).

## Capacidade real de "Modo Nuvem" (verificado, não presumido)
- **Não existe** nesta oferta um mecanismo de preview que exponha uma aplicação web pública
  (upload/processamento/download) para o público geral. Procurei explicitamente por uma
  ferramenta de túnel/exposição de porta e não há.
- Artifacts (a única forma de publicar algo com URL pública nesta conta) rodam como página
  sandboxed no navegador, sem backend — não executam ffmpeg nem whisper.
- **O caminho real e suportado**: anexar o arquivo de áudio/vídeo diretamente numa mensagem de
  uma sessão do Claude Code (web ou app), processar no container da sessão, devolver os
  resultados para download ali mesmo. Decisão confirmada com o usuário: esse é o fluxo adotado
  para "Modo Nuvem", sem contratar hospedagem externa.

## Modo Local (Mac M1) — núcleo validado aqui, Metal e seleção de pasta só no Mac
Esta sessão roda num container Linux isolado, sem qualquer acesso ao disco do Mac — não há como
"selecionar uma pasta no Finder" nem testar a aceleração Metal a partir daqui. Mas o
`whisper.cpp` é código-fonte único (muda só o backend de aceleração entre plataformas), então
compilei e rodei o binário real aqui (CPU) para validar a integração antes de mandar instruções
ao Mac. Isso revelou um bug real na suposição inicial: o JSON do whisper.cpp não tem uma chave
`"words"` — tem `"tokens"`, e só aparece com a flag `-dtw <preset>` (alinhamento por DTW); sem
ela não há timestamp por palavra, só por segmento. Corrigido em `core/transcribe.py` e
confirmado com `tests/test_local_logic.py` (pipeline completo: transcrição real → decisão →
corte com FFmpeg → relatórios, arquivo original intacto). Decisão confirmada com o usuário: ele
já usa o Claude Code localmente no Mac; a validação da aceleração Metal e da seleção de pasta via
Finder acontece lá — ver `docs/INSTALACAO_MAC.md`.

## Diferenças macOS ARM64 × Linux x86_64 que o código precisa respeitar
| Item | macOS M1 (local) | Linux x86_64 (nuvem) |
|---|---|---|
| Backend de transcrição | whisper.cpp (binário nativo, aceleração Metal) | faster-whisper (CTranslate2, CPU, int8) |
| Instalação do backend | compilar/baixar binário `whisper-cli` + modelo GGUF | `pip install faster-whisper` (já testado aqui) |
| FFmpeg | Homebrew (`brew install ffmpeg`) | pacote de sistema (já presente) |
| Sem GPU presumida | correto — M1 usa Metal via whisper.cpp, não CUDA | correto — CPU int8, sem presumir GPU |

## Ferramentas open source — triagem (Fase 1, não instalar sem necessidade)
- `whisper.cpp`: MIT, ativamente mantido — adotado para o Mac.
- `faster-whisper`: MIT, ativamente mantido — adotado para a nuvem. Já testado.
- `silero-vad`: dependeria de `torch` (pesado, não instalado aqui). **Decisão: não usar.**
  `faster-whisper` já embute um filtro de VAD (`vad_filter=True`, baseado em Silero via ONNX)
  sem precisar de `torch` — evita sobreposição de ferramentas, conforme instruído.
- `auto-editor`, `video-use`, `freecut`: referências de abordagem, não dependências diretas —
  a lógica de decupagem conservadora/editorial foi implementada diretamente no núcleo
  (`core/decoupage.py`) para manter controle total sobre a precisão dos cortes, que é o
  critério de qualidade prioritário do projeto.

## O que foi de fato testado nesta sessão (Fase 2, núcleo compartilhado)
Ver `tests/test_core_logic.py` — executado com sucesso, com FFmpeg real cortando um áudio
sintético real (vozes geradas com espeak-ng + silêncios reais inseridos com ffmpeg):
- Original permanece intocado (hash idêntico antes/depois).
- Silêncios longos (3.0s, 2.5s, 2.0s) são removidos; a duração cai de 28.59s para 12.74s.
- Uma "retomada" (mesma frase repetida) é detectada por similaridade de texto e apenas a
  segunda tentativa é mantida — **marcada como "duvidosa" para revisão humana**, porque decidir
  qual tomada é de fato a melhor exige ouvir o áudio, não só comparar texto.
- Um marcador de recomeço ("então, eh, deixa eu recomeçar") é detectado e o trecho inteiro é
  removido.
- O conteúdo real (as duas frases "boas") é preservado integralmente.
- `tests/test_e2e_cloud.py` cobre o mesmo cenário com transcrição real (`faster-whisper small`,
  modelo baixado de verdade, não mockado) — **testado e passando**: original intacto, duração
  caiu de 28,59s para 16,10s, retomada e marcador de recomeço removidos, conteúdo real preservado,
  1 trecho corretamente sinalizado como duvidoso para revisão humana. A segmentação de fala que o
  Whisper real produziu em cima da voz sintética (espeak-ng) ficou mais grosseira do que a do
  teste com dados sintéticos (3 segmentos em vez de 5) — esperado, já que espeak-ng não soa como
  voz humana real; isso não invalida o teste, mas significa que a precisão fina de corte por
  palavra só será confirmada de verdade com gravações humanas reais (Fase 3, no Mac).

## Dados enviados à Anthropic (Seção 6 do pedido)
Nenhum vídeo ou áudio bruto é enviado ao modelo Claude para a análise semântica — apenas texto
(transcrição + metadados de tempo) quando a etapa de decupagem editorial (modo B) for implementada.
A chamada à API de transcrição (whisper.cpp/faster-whisper) roda localmente/no container, sem
nenhuma chamada de rede para esse passo. No Modo Nuvem, o próprio arquivo de mídia trafega para
dentro do container da sessão do Claude Code quando você o anexa ao chat — isso é implícito ao
usar o produto, não uma chamada adicional feita pelo nosso código.
