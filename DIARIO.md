# Diário do canal

## 2026-11-09
- Primeiro episódio: Apollo 13 (o filtro que não encaixava). Vídeo agendado hoje 21:35, Short amanhã 21:35, via Metricool.
- Motor genérico criado e testado (teste: ponte de Tacoma, não publicado).

## 2026-11-10
- Revisão: Apollo 13 (vídeo) publicado no YouTube em 09/11 21:35 (https://www.youtube.com/watch?v=nxRxR68I7CE). Short da Apollo 13 segue agendado para hoje 21:35 (pendente, sem erro).
- Windsor.ai (youtube): consulta OK, mas sem dados de vídeos nos últimos 7 dias (canal novo / dados ainda não sincronizados).
- Tema: Citicorp Center (1978) — ligações soldadas trocadas por parafusadas, vento diagonal, conserto noturno em segredo, furacão Ella. Fatos checados em Wikipedia + Damn Interesting (+ 6sqft). Detalhes com fonte única (espessura das chapas, nº de ligações, custo, peso do contrapeso) ficaram de fora.
- make.py: QA OK na 1ª tentativa (169 s), mas a folha mostrou "HOUSTON" no cenário `control` (cenário da Apollo) na cena do furacão; troquei para `city_night` e gerei de novo: QA OK (170 s; short 86 s; −14,3 LUFS).
- Branch videos: push forçado foi bloqueado pela permissão da sessão; publiquei com commit normal por cima (ep-20261110). O repositório vai crescer um pouco a cada episódio.
- Metricool: vídeo hoje 20:00 (uuid 7101481555783339035), Short amanhã 12:00 (uuid 9058288541645424141); mídia baixada (static.metricool.com) nos dois. Instagram não conectado na brand → sem Reel.

## 2026-11-12
- Revisão: Citicorp Center publicado (vídeo 10/11 20:00 https://www.youtube.com/watch?v=tikaeuooFxI; Short 11/11 12:00 https://www.youtube.com/shorts/d-sXaUL8sjw). Apollo 13 (vídeo e Short) também publicados. Nenhum erro no Metricool.
- Windsor.ai (youtube, últimos 7 dias): só a Apollo 13 aparece, 6 views / 2 likes (Citicorp ainda sem dados sincronizados).
- Tema: Philae (12/11/2014, aniversário do pouso) — arpões e propulsor falharam, primeiro salto ~1 km / quase 2 h, parou à sombra de um penhasco, bateria ~64 h, hibernação, contato jun–jul/2015, achado em set/2016. Fatos checados em ESA + NatGeo + collectSPACE + Astronomy + Wikipedia. De fora (fonte única): horas de sol no local (1,5 h vs 6–7 h), nº de compostos orgânicos, origem do nome.
- make.py: 1ª geração QA OK, mas a folha mostrou "CONTROLE DA MISSÃO · HOUSTON" no cenário `control` (errado para a ESA) e o título "Rosetta e Philae" sobreposto aos personagens. Corrigi o motor (cenário `control` agora diz só "CONTROLE DA MISSÃO"), movi o título para cena sem personagens e troquei o `compare` (mostrava "≠") por `list`. 2ª geração: QA OK (173,9 s; short 72 s; −14,3 LUFS).
- Branch videos: ep-20261112 (commit normal por cima).
- Metricool: vídeo hoje 20:00 (uuid 3082685333354859952), Short amanhã 12:00 (uuid 3158518523866271709); mídia baixada (static.metricool.com) nos dois. Só YouTube conectado na brand → sem Instagram/TikTok.
