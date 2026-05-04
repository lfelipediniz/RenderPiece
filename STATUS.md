# Status do Projeto 2 (Render Piece)

Acompanhamento do que ja esta implementado e do que falta para cumprir as
especificacoes em [projeto2.md](projeto2.md).

## Checklist de requisitos

| # | Requisito                                                                 | Status     | Onde / observacao                                                                                                                                                                                  |
|---|---------------------------------------------------------------------------|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | Ambiente interno + externo com objetivo definido                          | OK         | Externo: convés/proa do Going Merry sobre o oceano. Interno: cabine do navio (cama, mesa, Brook, Chopper). Tema One Piece: tripulação no convés + objetos pessoais na cabine.                       |
| 2 | >= 6 modelos 3D com textura                                               | OK         | 10 modelos texturizados em [renderpiece/scene.py](renderpiece/scene.py): Going Merry, Luffy, Nami, Franky, Barrel, Bitcoin pile, Bed, Brook, Chopper, Wooden table.                                |
| 3 | >= 3 internos e >= 3 externos                                              | OK         | Internos (4): Bed, Brook, Chopper, Wooden table. Externos (5): Luffy, Nami, Franky, Barrel, Bitcoin pile.                                                                                          |
| 4 | Cada modelo de um `.obj` distinto                                          | OK         | Cada `load_*` em `scene.py` aponta para um arquivo `.obj` exclusivo dentro de `modelos/`.                                                                                                          |
| 5 | Modelos ajustados de forma coerente (escala/posicao)                       | OK         | Escalas/posicoes calibradas individualmente em `compose_transform(...)` no `build_scene` de [renderpiece/scene.py](renderpiece/scene.py).                                                          |
| 6 | Pisos diferentes nos dois ambientes                                        | OK         | Externo: superficie do oceano animada em [renderpiece/ocean.py](renderpiece/ocean.py). Interno: tabuas do convés (parte do modelo Going Merry).                                                    |
| 7 | Escala, rotacao e translacao via teclado, cada uma em um modelo diferente  | **FALTA**  | Hoje so existem controles de camera/wireframe/pause/reset em [renderpiece/app.py](renderpiece/app.py) `key_callback`. Nada manipula transformacoes de objetos em tempo real. Detalhe abaixo.       |
| 8 | Skybox com textura                                                         | OK         | [renderpiece/skybox.py](renderpiece/skybox.py) gera um cubemap procedural (gradiente ceu/horizonte/oceano + sol).                                                                                  |
| 9 | Restricao da camera dentro do ceu/terreno                                  | OK         | `Camera.move` em [renderpiece/camera.py](renderpiece/camera.py) clipa XZ por `WORLD_HALF_SIZE` e Y por `SKY_CEILING_Y` / `OCEAN_Y` (config em [renderpiece/config.py](renderpiece/config.py)).      |
| 10| Tecla `P` alterna malha poligonal                                          | OK         | `KEY_P` -> `toggles.wireframe` em [renderpiece/app.py](renderpiece/app.py); `glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)` aplica em todos os objetos e no oceano.           |
| 11| Importacao de modelos via `.obj` (Wavefront)                               | OK         | Loader proprio em [renderpiece/obj_loader.py](renderpiece/obj_loader.py) (faces N-gono trianguladas em fan, materiais via `.mtl`, fallback de textura/diffuse).                                     |
| 12| Sem efeitos de iluminacao                                                  | OK         | Shaders ([renderpiece/shaders.py](renderpiece/shaders.py), `ocean.py`, `skybox.py`) usam apenas textura + cor difusa. Nada de Phong/Blinn/normal mapping.                                          |

Resumo: **11 de 12 requisitos completos**. Falta apenas o requisito 7.

## Pendencias para entrega

### 1. Implementar o requisito 7 (transformacoes via teclado) - **bloqueante para nota**

Escolher 3 modelos distintos da cena e ligar cada um a uma transformacao
diferente, controlavel por teclas independentes. Sugestao concreta:

| Transformacao | Objeto sugerido | Teclas sugeridas                       | Justificativa tematica                                                                                          |
|---------------|-----------------|----------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| Escala        | Luffy           | `1` / `2` (aumenta / diminui)          | Luffy tem a Akuma no Mi do Gomu Gomu: seu corpo é de borracha e ele pode esticar membros a vontade. Escalar o modelo inteiro remete visualmente a esse poder de deformacao corporal. |
| Rotacao       | Tony Tony Chopper | `3` / `4` (gira em torno de Y, +/-) | Chopper pode girar/mudar de forma com seus Rumble Balls; uma rotacao interativa reforca a ideia de movimento. |
| Translacao    | Barrel          | `5`/`6` (X +/-) e `7`/`8` (Z +/-)    | O barril e um objeto cenario; transladar ele pelo convés mostra a transformacao de forma intuitiva e coerente com o tema. |

> **Observacao sobre combinacoes**: o requisito 7 exige que escala, rotacao e translacao sejam aplicadas em modelos _diferentes_. No entanto, como as transformacoes sao compostas por multiplicacao de matrizes (`T * R * S`), e tecnicamente possivel combinar mais de uma delas em um mesmo objeto simultaneamente — por exemplo, rotacionar _e_ escalar o Luffy ao mesmo tempo. Isso pode ser explorado como demonstracao extra durante a apresentacao para evidenciar o entendimento do pipeline de transformacoes.

Pontos de implementacao:
- Adicionar parametros mutaveis em `SceneObject` (ou um wrapper) para guardar
  delta de rotacao/escala/translacao do usuario.
- Em [renderpiece/app.py](renderpiece/app.py) `key_callback` (e/ou `process_keyboard` para teclas continuas),
  atualizar esses deltas conforme a tecla.
- Em `SceneObject.model_matrix(elapsed)`, compor o `model_factory` com a matriz
  de delta antes de aplicar `anchor_to_base`.

### 2. Atualizar `README.md`

O README hoje tem so uma linha. Antes da apresentacao, adicionar:
- Como instalar (`pip install -r requirements.txt`).
- Como rodar (`python main.py`).
- Mapa completo de teclas: WASD/Space/Shift/Ctrl (movimento), mouse (olhar),
  `P` (wireframe), `R` (reset camera), `ESC` (pause + musica), e as teclas do
  requisito 7 quando implementadas.

### 3. Validacao visual durante a apresentacao

- Confirmar que o piso da cabine (tabua do Going Merry) esta visualmente
  distinto do oceano. Caso contrario, aumentar contraste de cor/textura.
- Verificar se nao ha modelos flutuando (Franky atualmente nao esta apoiado
  em superficie alguma; pode ser ajustado em `compose_transform(...)`).

## Nice-to-have

- Reduzir overlap visual entre Luffy e Nami na proa.
- Smoke test automatico em CI (script ja existe em formato local; ver
  comando usado pelo agente em chat).
- Documentar a estrutura de `modelos/` no README ou aqui em STATUS.md.

## Estrutura atual de `modelos/`

```
modelos/
  One Piece - Bink's Sake _ Piano [SeDyYtIuhsA].mp3   (musica de fundo)
  going-merry/{source,textures}/
  luffy/{source,textures}/
  nami/{source,textures}/
  franky/{source,textures}/
  bitcoin-pile/{source,textures}/
  barrel/{source,textures}/
  bed/{source,textures}/
  brook/{source,textures}/
  chopper/{source,textures}/
  wooden-table/{source,textures}/
```

Cada pasta segue o padrao `<nome-kebab-case>/source/<arquivos .obj/.mtl/texturas>`
e `<nome-kebab-case>/textures/<texturas extras curadas>` quando aplicavel.
