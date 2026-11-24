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

## 2026-11-17
- Revisão: Philae publicado (vídeo 12/11 20:00 https://www.youtube.com/watch?v=nutPX0Efv84; Short 13/11 12:00 https://www.youtube.com/shorts/m7xwV5oSj3I). Nenhum erro no Metricool nos últimos dias.
- Windsor.ai (youtube, últimos 14 dias): Short do Philae 311 views / 9 likes (o melhor até agora); Short Citicorp 58/1; Short Apollo 34/0; vídeos longos: Apollo 25/2, Citicorp 21/2, Philae 8/1. Os Shorts puxam bem mais que os vídeos longos.
- Tema: o mouse de Douglas Engelbart (aniversário da patente, 17/11/1970). Primeiro protótipo de madeira (Bill English, 1964), duas rodinhas, nome de origem incerta, demo de 9/12/1968 em San Francisco (~90 min, >1.000 pessoas), patente do SRI, licença à Apple por ~US$ 40 mil, patente vencida em 1987, Engelbart sem royalties. Fatos checados em computinghistory.org.uk, greatpatent, SRI, Computer History Museum, dougengelbart.org e IPKat. De fora: tamanho exato da plateia (fontes dizem 1.000 ou 2.000), distância até o laboratório, Turing Award, nº de botões do primeiro protótipo.
- Primeiro episódio no formato "humanizado" (narrador conversando, humor leve, comentário fixado).
- make.py: 1ª geração QA OK (188,7 s), mas a folha mostrou a lista das rodinhas com pílulas cortadas/sobrepostas; encurtei os itens das duas listas. 2ª geração: QA OK (189,3 s; short 75,6 s; −14,1 LUFS).
- Branch videos: ep-20261117 (commit normal por cima).
- Metricool: vídeo hoje 20:00 (uuid -6786672992015070213, com thumb própria e primeiro comentário), Short amanhã 12:00 (uuid 4052884119274737441); mídia baixada (static.metricool.com) nos dois. Só YouTube conectado → sem Instagram/TikTok.

## 2026-11-19
- Revisão: mouse de madeira publicado (vídeo 17/11 20:00 https://www.youtube.com/watch?v=vEyc2IVV9Lo; Short 18/11 12:00 https://www.youtube.com/shorts/kiAHrSsHm4Y). Nenhum erro no Metricool. Nada agendado para hoje antes desta execução.
- Windsor.ai (youtube, últimos 14 dias): Short Philae 316/9; Short Citicorp 58/1; Short Apollo 13 35/0; vídeos longos: Apollo 13 28/2, Citicorp 22/2, Philae 9/1. Mouse (vídeo e Short) ainda sem dados sincronizados.
- Tema: Apollo 12 (aniversário do pouso, 19/11/1969) — decolagem sob chuva em 14/11/1969, raios aos ~36 s e 52 s, luzes de alerta, três células de combustível fora, telemetria embaralhada; John Aaron reconheceu o padrão de uma simulação ("SCE to AUX"); Alan Bean sabia onde ficava a chave; pouso no Oceano das Tempestades a <200 m da Surveyor 3 (abril/1967); primeira frase de Conrad; câmera de TV queimada apontada pro Sol; ~8 h em 2 caminhadas; câmera e peças da Surveyor trazidas de volta. Checado em NASA (2 páginas), AmericaSpace, Live Science, Sky at Night. De fora (fonte única ou conflito): medo dos paraquedas, aposta com Oriana Fallaci, altura de Conrad, distância exata (538 ft / 600 ft / 182 m → "menos de 200 m"), data do amerrissagem, 4 km de erro da Apollo 11. Falas de personagens só com controladores genéricos; frases de pessoas reais apenas pelo narrador.
- make.py: QA OK na 1ª tentativa (196,1 s; short 92,5 s; −14,3/−14,5 LUFS). Folhas e thumb conferidas: nada cortado/sobreposto.
- Branch videos: ep-20261119 (commit normal por cima).
- Metricool: vídeo hoje 20:00 (uuid 4844718927233761459, thumb própria + primeiro comentário), Short amanhã 12:00 (uuid -2865097289912859678); mídia baixada (static.metricool.com) nos dois. Só YouTube conectado → sem Instagram/TikTok.

## 2026-11-20 (pedido do dono, fora da rotina)
- Dono pediu vídeo de GTA 6 (lançado 19/11) com avatar dele em pixel. Decidiu: sem cortes de gameplay (risco de direitos), só animação; alternar histórias e games.
- Criado `engine/pixel.py` (apresentador pixel art, cenários neon/quarto/stats/news, trilha chiptune original, legenda karaokê). Avatar feito a partir de 4 fotos dele (`marca/avatar.json`).
- Fatos (2+ fontes): US$ 3,79 bi no 1º dia (Take-Two/Forbes/ABC), 32,5 mi de cópias pré-lançamento, Metacritic 99 (empate com Ocarina of Time), Twitch ~3,3 mi simultâneos (recorde, LoL 3,1 mi), ~7,6–8 mi somando plataformas, recorde de tráfego DE-CIX, PSN caiu no lançamento, 30 fps nos consoles, sem PC, R$ 449,90/549,90, legendado sem dublagem. De fora: estimativa de US$ 2,36 bi (só digital, Sensor Tower), comparação com Homem-Aranha (fonte única), minutos jogados (Circana, fonte única).
- QA OK (151,1 s; short 86,8 s; −15,4 LUFS). Branch videos: ep-20261121-gta6.
- Metricool: vídeo 20/11 21:40 (uuid 4599102999830875879, thumb + 1º comentário), Short 20/11 21:55 (uuid 926716543223481331); mídia baixada nos dois.
- Voz do dono: mandou áudio de 10 s; não deu pra transcrever/clonar (precisa de link público; compartilhar no Drive foi bloqueado). Vídeo saiu com a voz gerada.
- Atualização 21:40: dono deixou o áudio dele público no Drive; voz clonada no Speko (Cartesia, vc_7f48589f1c174050). Vídeo refeito com a voz dele (QA OK, 155,6 s; short 89,8 s). Branch videos: ep-20261121-gta6-voz. Posts no Metricool trocados para os arquivos novos: vídeo 20/11 21:55, Short 20/11 22:10 (mesmos uuids).

## 2026-11-24
- Revisão: nada agendado nem com erro no Metricool entre 23 e 26/11 antes desta execução (o GTA 6 de 20/11 saiu: vídeo e Short aparecem no Windsor).
- Windsor.ai (youtube, últimos 14 dias): Short Philae 320/9; Short mouse 136/5; Short Apollo 12 96/3; Short Citicorp 60/1; Short GTA 6 47/1; Short Apollo 13 37/0; vídeos longos: GTA 6 28/0, Apollo 13 24/0, Citicorp 22/2, Philae 10/1, Apollo 12 9/1, mouse 3/1. Shorts continuam puxando bem mais.
- Formato: história (último foi pixel). Tema: Lucy (aniversário da descoberta, 24/11/1974). Johanson e Tom Gray voltando pro Land Rover depois de uma manhã quente, passaram por uma ravina e viram um fragmento de cotovelo; depois fêmur, mandíbula, crânio, costelas, bacia; 2 semanas, centenas de fragmentos, 47 ossos, ~40%; joelho achado perto em 1973; festa com "Lucy in the Sky with Diamonds" tocando sem parar; ~3,2 mi de anos; ~1,1 m, ~27 kg; cérebro do tamanho do de chimpanzé mas bípede (andar em pé antes do cérebro grande); Museu Nacional da Etiópia; mesma data da Origem das Espécies (1859). Checado em IHO/ASU, ASU News (entrevista Johanson), Britannica, History, Live Science, The Conversation, Wikipedia. De fora (fonte única ou conflito): quem sugeriu o nome (Pamela Alderman × "ninguém lembra"), Dinkinesh, 110 °F ao meio-dia, idade ao morrer, marca de dente de carnívoro, "First Family", turnê nos EUA, hipótese da queda da árvore. Personagens só genéricos (pesquisadora, estudante, geólogo); Johanson e Gray só pelo narrador.
- make.py: 1ª geração QA OK (186,2 s), mas a thumb pegou o personagem piscando e cortou o texto, e os `compare` mostravam "≠" onde não cabia (AL 288-1 ≠ Lucy). Adicionei `thumb_line`/`thumb_t` opcionais no make.py, encurtei o thumb_text e troquei os compare por pill/list. 2ª geração: QA OK (186,5 s; short 91,7 s; −14,3/−14,5 LUFS). Folhas e thumb conferidas.
- Branch videos: ep-20261124 (commit normal por cima).
- Metricool: YouTube vídeo hoje 20:00 (uuid -7889984984128732721, thumb + 1º comentário), Short amanhã 12:00 (uuid -8699809073554306935), TikTok amanhã 13:00 (uuid -5712525270450486196, isAigc). Mídia baixada (static.metricool.com) nos três. Novidade: TikTok (joaopetb) agora conectado na brand; Instagram continua não conectado → sem Reel.
