# Catalogo de Assets

Este catalogo documenta onde cada asset fica e como ele deve ser usado no
projeto. A organizacao padrao e:

- `modelos/<asset>/source/`: arquivos `.obj` e `.mtl`.
- `modelos/<asset>/textures/`: texturas consumidas pelo loader.
- `modelos/<asset>/previews/`: imagens de referencia que nao entram no render.
- `modelos/<asset>/archives/`: pacotes originais baixados.
- `modelos/audio/`: trilhas e efeitos sonoros.
- `docs/project_specs/`: enunciados dos projetos.

## Assets Em Uso

| Asset | Papel na cena | Arquivos principais | Observacoes |
| --- | --- | --- | --- |
| Going Merry | Ambiente interno e externo | `modelos/going-merry/source/Going Merry.obj` | Modelo principal do navio. |
| Luffy | Personagem externo | `modelos/luffy/source/luffy.obj` | Fica na proa. |
| Nami | Personagem externo | `modelos/nami/source/Nami.obj` | Fica na proa. |
| Franky | Personagem externo | `modelos/franky/source/franky.obj` | Recebe luz externa. |
| Brook | Personagem externo | `modelos/brook/source/Brook.obj` | Recebe luz externa do sol. |
| Chopper | Personagem interno | `modelos/chopper/source/chopper.obj` | Nao recebe a luz externa nesta etapa. |
| Bed | Objeto interno | `modelos/bed/source/Bed.obj` | Nao recebe a luz externa nesta etapa. |
| Old wooden table | Objeto interno | `modelos/wooden-table/source/desk_UV02.obj` | Nao recebe a luz externa nesta etapa. |
| Firefly | Fonte de luz interna | `modelos/firefly/source/firefly.obj` | Instanciado como enxame pequeno ao redor da cabeca do Chopper; a ponta do abdomen emite luz interna controlada por `F`. |
| Lamp | Fonte de luz interna | `modelos/lamp/source/lamp.obj` | Fica em cima da mesa de madeira; a regiao da cupula/bulbo emite luz quente controlada por `O`. |
| Barrel | Objeto externo | `modelos/barrel/source/Barril.obj` | `Barril.mtl` aponta para a textura de madeira. |
| Bitcoin pile | Tesouro externo | `modelos/bitcoin-pile/source/coins.obj` | Instanciado varias vezes. |
| Sun | Fonte de luz externa | `modelos/sun/source/Sun.obj` | Controlado por `J`/`K`, textura em `modelos/sun/textures/sun_surface.png`. |
| Background music | Audio | `modelos/audio/One Piece - Bink's Sake _ Piano [SeDyYtIuhsA].mp3` | Usado por `renderpiece/app.py`. |

## Documentos Do Projeto

| Documento | Caminho |
| --- | --- |
| Enunciado Projeto 2 | `docs/project_specs/projeto2.md` |
| Enunciado Projeto 3 | `docs/project_specs/projeto3.md` |

## Observacoes

- O loader de OBJ procura texturas no diretorio do `.obj` e tambem em
  `modelos/<asset>/textures/`, entao novos assets devem seguir essa estrutura.
- Quando um upload nao trouxer `.mtl`, crie um arquivo minimo em `source/`
  apontando para as texturas de `textures/` para evitar fallback silencioso.
- Os parametros de iluminacao do Projeto 3 ficam em `renderpiece/scene.py` e
  `renderpiece/lighting.py`; os `.mtl` sao usados para textura/tint visual.
- Arquivos em `previews/` sao referencias visuais e nao devem ser carregados
  automaticamente pelo render.
