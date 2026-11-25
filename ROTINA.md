# Rotina do canal (terças e quintas) do canal "A Peça que Faltava"

## FORMATO PADRÃO: AVATAR PIXEL + NOTÍCIA EM ALTA (decisão do dono, 24/11/2026 — vale para TODOS os episódios)

- Todo vídeo é apresentado pelo **avatar em pixel art do João Pedro** (`marca/avatar.json`: careca, barba cheia, óculos,
  headset), falando em 1ª pessoa com a voz clonada dele. Motor: `engine/pixel.py` (ver seção "Formato games (pixel)" no fim).
- Tema: **notícia em alta nos últimos dias** (games, lançamentos, tecnologia, cultura pop em tendência: Google Trends,
  YouTube em alta, sites de games). Checagem de 2 fontes por fato continua.
- **NÃO usar mais** o formato antigo de bonecos 2D/histórias ("neste dia na história", `engine/make.py`). A alternância de
  20/11 foi cancelada. Se o avatar pixel não estiver no repositório, não publicar no estilo antigo: parar e avisar o dono.
- Grave `"formato": "pixel"` em cada nova entrada de `historico.json`.
- As seções abaixo sobre bonecos/cenários/humanizado valem só como referência do motor antigo; o tom humanizado
  (conversa, frases curtas, sem clichês de IA) vale também para o apresentador pixel.

Canal de histórias reais animadas (ciência, engenharia, história, invenções, desastres que ensinaram algo,
"o detalhe que mudou tudo"). Bonecos 2D com volume, câmera de cinema, vozes geradas, legendas.

## Narração

O dono decidiu NÃO gravar a narração: usar sempre a voz gerada (narrador `cadu-medium`).
O motor ainda aceita `"narrator_audio"` caso ele mande uma gravação algum dia (pausa de 2 s entre as falas).

## Passo a passo de cada execução

1. **Preparar**: clonar este repositório, rodar `./setup.sh` (baixa Piper + vozes do GitHub).
2. **Revisar o dia anterior**:
   - Metricool `getScheduledPosts` dos últimos 2 dias (brand 7995588, fuso America/Sao_Paulo): algum post com status de erro?
     Se sim, tentar reagendar uma vez com o mesmo link e anotar.
   - Windsor.ai (connector `youtube`, conta 82613): visualizações/curtidas dos últimos vídeos, se disponível.
   - Registrar tudo em `DIARIO.md`.
3. **Escolher o tema** (pesquisa na web, em português e inglês):
   - O que está em alta em curiosidades/ciência/história (YouTube, Google Trends Brasil, notícias de ciência da semana,
     datas comemorativas do dia: "neste dia na história").
   - Preferir histórias com um **detalhe surpreendente** e uma virada clara (problema → engenhosidade → resultado).
   - **Proibido**: política partidária, religião, tragédias recentes (< 5 anos), crimes, pessoas privadas, temas médicos com
     conselho de saúde, personagens/marcas com direitos autorais, boatos sem fonte.
   - Não repetir temas de `historico.json`.
4. **Checar os fatos**: cada número, data e nome do roteiro precisa aparecer em pelo menos 2 fontes confiáveis
   (enciclopédias, NASA, universidades, museus, imprensa séria). Guardar as fontes no JSON (`fontes`).
   Na dúvida, deixar o detalhe de fora.
5. **Escrever o roteiro** em `stories/AAAA-MM-DD-slug.json` (formato abaixo). Alvo: 3 a 4 min, 25 a 40 falas.
   - Gancho forte nas 2 primeiras falas (é o que segura o público e vira o começo do Short).
   - Personagens falam como gente (frases curtas). Falas inventadas são ilustrativas: nunca colocar frase inventada na boca
     de uma pessoa real com nome; usar personagens genéricos (engenheira, repórter, operário, cientista) ou citar o fato pelo narrador.
   - Narrador: frases de até ~25 palavras.
   - **Jeito humano de contar (obrigatório, ver seção "Humanizado" abaixo).**
6. **Gerar**: formato pixel (`engine/voz_externa.py` + `engine/pixel.py`, ver fim do arquivo). O `make.py` é do formato antigo, não usar.
   Se o QA falhar, corrigir e rodar de novo (no máximo 2 tentativas).
7. **Olhar o resultado**: abrir `folha_16x9.jpg`, `folha_9x16.jpg` e `thumb.jpg` e conferir se nada está cortado, sobreposto ou vazio.
8. **Publicar os arquivos** (branch `videos`, sobrescrita a cada episódio para o repositório não crescer):
   ```
   D=$(mktemp -d); cd $D; git init -q; git checkout -q -b videos; mkdir ep-AAAAMMDD
   cp OUT/video_16x9.mp4 OUT/short_9x16.mp4 OUT/thumb.jpg OUT/legendas.srt ep-AAAAMMDD/
   git add -A; git -c user.name=Claude -c user.email=noreply@anthropic.com commit -qm "episódio AAAA-MM-DD"
   git remote add origin https://github.com/joaopedro2017vivo-sys/a-peca-que-faltava; git push -f origin videos
   ```
   Link público: `https://raw.githubusercontent.com/joaopedro2017vivo-sys/a-peca-que-faltava/videos/ep-AAAAMMDD/video_16x9.mp4`
   (o sandbox não consegue abrir esse link; quem baixa é o Metricool. Criar Releases não é permitido nesta sessão.)
9. **Agendar no Metricool** (blogId 7995588):
   - YouTube vídeo: hoje às 20:00 (America/Sao_Paulo), `type: video`, público, categoria GAMING (ou SCIENCE_TECHNOLOGY/ENTERTAINMENT conforme a notícia), madeForKids false,
     isAiGeneratedContent true, título/descrição/tags do JSON.
   - YouTube Short: amanhã às 12:00, `type: short`.
   - Instagram Reel com o short (se o Instagram estiver conectado na brand): amanhã às 12:30, `isAiGenerated: true`, legenda curta com 3 a 5 hashtags.
   - TikTok (se conectado): o short amanhã às 13:00, título curto, `isAigc: true`.
   - Se o horário de hoje já passou, usar o próximo horário livre (+15 min).
   - **Conferir**: na resposta do Metricool o campo `media` deve virar `https://static.metricool.com/...`
     (sinal de que ele baixou o vídeo). Se não virar, o link falhou: avisar o dono.
10. **Registrar**: adicionar o tema em `historico.json`, resumo em `DIARIO.md`, commit e push.
11. **Avisar o dono** (João Pedro) com uma mensagem curta: tema, horário, link do planner. Se algo falhou, dizer o que e o que foi feito.

## Formato do roteiro (JSON)

```json
{
 "slug": "ponte-tacoma",
 "title": "A ponte que dançou",
 "thumb_text": "A ponte que dançou com o vento",
 "channel": "A Peça que Faltava",
 "youtube": {"title": "...", "description": "...", "tags": ["..."],
             "short_title": "... #shorts", "short_description": "..."},
 "fontes": ["https://...", "https://..."],
 "pronounce": [["Tacoma", "Tacôma"]],
 "narrator": {"voice": "cadu-medium", "speed": 0.9},
 "cast": {
  "E": {"name": "Engenheira", "kind": "person", "outfit": "worker", "hat": "hardhat",
        "color": [230,120,40], "skin": [236,192,160], "hair": [90,50,30], "hairstyle": "long", "lashes": true,
        "shirt": [70,120,200], "voice": "dii-high", "speed": 0.92, "pitch": 0}
 },
 "scenes": [
  {"bg": "construction", "cast": ["E","R"], "mood": "calm", "expr": "neutral",
   "lines": [
    {"spk": "N", "text": "...", "show": {"year": "1940"}},
    {"spk": "E", "text": "...", "g": "talk", "e": "worried", "acts": {"R": ["idle","surprised"]}, "sfx": "boom", "sfx_at": 1.0}
   ]}
 ],
 "short": [0, 1, 2, 5, 6, 20, 21]
}
```

- **bg** (cenário): space, space_plain, spaceship (todos flutuam), control (sala de controle), ocean, studio (fundo neutro),
  lab, office, workshop, classroom, house, city_day, city_night, construction, countryside, desert.
- **cast**: até 3 por cena. `kind`: `astro` (astronauta, só cor/pele/cabelo) ou `person`.
  `outfit`: shirt, lab (jaleco), worker (colete), suit (terno). `hairstyle`: short, long, bun, bald. Extras: `glasses`, `beard`,
  `lashes`, `dress`, `hat: hardhat`, `headset`, `tie`, `badge`, `long_sleeve`, `shirt`/`pants` (cores).
  Cada personagem com cor diferente (é a marca dele na legenda).
- **vozes**: `cadu-medium` (grave, narrador), `jeff-medium`, `faber-medium` (masculinas), `dii-high` (mais aguda, usar para mulheres).
  `pitch` em semitons (−4 a +4) para diferenciar personagens com a mesma voz.
- **g** (gesto): idle, talk, pointR, pointL, shrug, cheer, hold, shiver, work, wave, open.
- **e** (expressão): neutral, happy, worried, surprised, determined, cold.
- **show** (elemento gráfico; pode ser lista): `{"title","sub"}`, `{"pill"}`, `{"year"}`, `{"big"}`, `{"icon"}`,
  `{"list": [...]}`, `{"compare": [a, b]}`. Ícones: bulb, gear, warning, check, cross, question, clock, money, globe, rocket,
  book, heart, bridge, building, atom. Cenas sem personagens precisam de `show` em quase toda fala (senão fica vazio).
- **mood** (música): calm, tense, hope, triumph. **sfx**: boom, alarm, chime, splash, applause, tape, clunk, buzz, boing, thud, static, rustle.
- **radio: true** numa fala = voz com efeito de rádio. **hold: 1.0** = segura a cena 1 s a mais.
- **short**: índices das falas (contando todas, na ordem) para o vertical; ~60–90 s. Sem isso, usa o começo + o fim.
- Números e siglas: escrever como se fala quando houver risco ("cê ó dois" já é automático para CO₂); usar `pronounce` para nomes estrangeiros.

## Humanizado (a partir de 14/11/2026)

O dono pediu o canal com menos "cara de IA". Valem para todo episódio novo:

### Roteiro e narrador
- O narrador conversa com quem assiste, como um amigo contando um causo: "Imagina…", "Olha só", "Repara nisso", "E aí vem o pior".
- Linguagem falada do Brasil: "pra", "tá", "a gente", "né", "uns mil metros". Nada de texto de enciclopédia.
- Misturar frases curtíssimas ("Num cometa.") com frases médias. Nunca três frases seguidas do mesmo tamanho.
- Personagens reagem como gente: "Peraí, peraí.", "Opa.", "Ué?", "Calma.". Um interrompe ou completa o outro de vez em quando.
- Pelo menos um momento de humor leve ou de opinião do narrador ("e, sinceramente, isso é genial").
- Proibido (soa robô): "Prepare-se", "Mas o que ninguém esperava", "fascinante", "incrível jornada", "uma verdadeira",
  "neste vídeo vamos", "você não vai acreditar", "mergulhe", "desvende".
- Os fatos continuam com a mesma checagem; humanizar é no jeito de falar, nunca inventar detalhe.
- Ritmo: use `…` (ou `...`) para uma pausa dramática no meio da fala; `"pause": 0.6` numa fala segura o silêncio depois dela.
  Perguntas e reticências já ganham uma pausa maior sozinhas; réplica entre personagens sai mais rápida.
- Use `e` (expressão) em toda fala de personagem: ela também muda o tom da voz (preocupado fala mais rápido e agudo,
  surpreso mais agudo, determinado mais firme e lento). Cenas `tense` deixam as falas um pouco mais rápidas.

### Motor (já automático)
- Voz: cada frase sai num ritmo levemente diferente, pausas variam, respiração baixinha antes de falas longas.
- Bonecos: piscar irregular (às vezes duplo), boca muda de formato pela vogal (a/o/e), corpo acompanha a força da voz,
  respiração parada, sobrancelha sobe no fim de pergunta, quem escuta acena com a cabeça.

### Títulos, descrições e comentário
- Título como alguém contaria pra um amigo, sem CAIXA ALTA forçada e sem fórmula repetida. Variar entre: pergunta,
  frase de efeito curta, "o dia em que…". Ex.: "O robô que saiu quicando num cometa (e mesmo assim deu certo)".
- Descrição começa com 2 ou 3 frases em tom de conversa ("Sabe aquela sensação de…?"), depois o resumo, depois
  "Dramatização animada baseada em fatos reais, com vozes geradas por computador. Os personagens são ilustrativos." e as fontes.
  O aviso de IA continua sempre (e `isAiGeneratedContent: true`).
- Terminar a descrição com uma pergunta sincera pra quem assistiu (ex.: "Você teria arriscado soltar o robô sem o propulsor?").
- Guardar no JSON `"youtube": {"pinned_comment": "..."}`: um comentário curto do canal, com opinião ou bastidor
  ("O que mais me pegou nessa história foi…") + uma pergunta. Se o Metricool tiver campo de primeiro comentário, usar;
  senão, incluir o texto no aviso ao dono para ele fixar.

## Formato games (pixel) — a partir de 20/11/2026

- Tema: a notícia de games mais comentada da semana (lançamento, recorde, anúncio grande, evento). Mesma checagem: 2 fontes por fato.
- Apresentador: avatar do dono em pixel art (`marca/avatar.json`, feito a partir das fotos dele: careca, barba cheia,
  óculos aviador, blusa preta com zíper, headset). Ele fala em 1ª pessoa, conversando com quem assiste ("Fala, galera!").
  Opinião leve pode; nunca inventar experiência pessoal específica dele (ex.: "eu joguei 10 horas").
- **Sem gameplay, trailer, logo, capa ou personagem dos jogos**: nem de streamers, nem oficiais (Content ID/strike).
  Nomes de jogos, empresas e números podem aparecer em texto. Cenários são pixel art original do motor (`neon`, `room`, `stats`, `news`).
- Roteiro: `stories/AAAA-MM-DD-slug.json` com `"format": "pixel"`, `"avatar"` (copiar de `marca/avatar.json`), `"voice"`,
  `scenes` (bg + lines com `text`, `show`, `sfx`), `short`, `thumb_lines`. Exemplo: `stories/2026-11-21-gta6-lancamento.json`.
  Alvo 2–3 min, 20–30 falas. `show`: title/sub, big/sub, pill, list, compare.
- Gerar: `python3 engine/pixel.py stories/ARQ.json out/ARQ` (≈5 min). Conferir folhas e thumb como no outro formato.
- YouTube: categoria GAMING, `isAiGeneratedContent: true`; descrição diz "apresentador em pixel art e voz gerada por computador"
  e "não usamos imagens do jogo".
- **Voz: a do dono, clonada** (Speko, voz `vc_7f48589f1c174050`, Cartesia, `provider_voice_id` 7d0a1565-4f11-4be6-8f32-3ac8a6c80c28).
  Para cada fala, na ordem: Speko `audio_synthesize` com body
  `{"text": FALA, "intent": {"language": "pt-BR"}, "voice": "7d0a1565-4f11-4be6-8f32-3ac8a6c80c28", "constraints": {"allowedProviders": {"tts": ["cartesia"]}}}`.
  O resultado vem salvo como .wav (o caminho aparece no texto do resultado). Depois:
  `python3 engine/voz_externa.py out/ARQ fala0.wav fala1.wav ...` e então `python3 engine/pixel.py stories/ARQ.json out/ARQ`.
  Gasta crédito Speko (conta tinha US$ 10 em 20/11; ~US$ 0,x por vídeo). Se o Speko falhar ou faltar crédito, use a voz Piper
  (cadu-medium, é só rodar o pixel.py direto) e avise o dono. Descrição: "a voz é a do João Pedro, recriada por IA".
