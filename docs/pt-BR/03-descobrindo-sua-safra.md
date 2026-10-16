# 03 — Descobrindo sua safra

**Se você NÃO tem Civic 2017 EXL BR com DA version `1.F187.16`**, leia este doc antes de deployar. Precisa adaptar 2 coisas:

1. **`rom_type`** no `build.py` — chave do EvilValet; se errado, pacote OTA nem é reconhecido.
2. **Coordenadas do botão OK** no `AutoOkConfig.java` — se layout da sua tela for diferente, o tap pode errar.

Esse doc tem 2 caminhos:
- **Caminho rápido (sem risco):** só se adaptar algum dado conhecido publicamente da sua safra.
- **Caminho pleno:** rodar nosso pacote de diagnóstico pra descobrir tudo diretamente do seu HU.

---

## Passo 1 — Qual é a sua safra?

Para descobrir a DA version da sua central:

1. Carro em ACC, central ligada
2. Entre em: **Settings → System → About this Device** (ou "Sobre o dispositivo")
3. Procure por **"Software"**, **"Version"**, **"DA Version"** ou **"Build ID"**
4. Formato esperado: `1.F<X><YYY>.<Z>` (ex: `1.F187.16`, `1.F197.70`, `1.F1A5.15`)

Alternativa — menu de serviço:

1. Com áudio off, segure `DAY/NIGHT + AUDIO + MENU` por 2 segundos
2. Entra no menu de serviço Mitsubishi
3. Procure "Version Info" ou similar

Anote o valor.

## Passo 2 — Checar matriz de compatibilidade

Veja se sua safra já foi reportada:

| DA Version | Mercado | Rom type | Status | Fonte |
|---|---|---|---|---|
| `1.F187.16` | BR | `0040` | ✅ Deployado com sucesso | Este projeto, 2026-10-16 |
| `1.F1A5.15` | US | `1115` | ✅ EvilValet confirmado | ic1101 docs/updates.md |
| `1.F197.70` | EU | `2250` | ⚠️ Update file público, não deployado | ic1101 docs/updates.md |
| ...outras | — | — | ❓ Não reportado | — |

**Se sua safra está na tabela**: use o rom_type e as coordenadas listadas (quando disponíveis).

**Se não está**: siga o Passo 3.

Depois do deploy, por favor [abra uma issue](../../.github/ISSUE_TEMPLATE/nova-safra.md) reportando sua safra pra ajudar a comunidade.

## Passo 3 — Descobrir seu `rom_type` via pacote de diagnóstico

Esta é a parte importante: **não vamos adivinhar seu rom_type.** Vamos construir um pacote OTA que, quando aplicado, salva informação do seu HU pro pendrive. Zero risco de brick (modo diagnóstico puro, não escreve nada no `/system`).

### 3.1 Build do pacote de diagnóstico

**ATENÇÃO**: isso requer modificar temporariamente o `build.py` do projeto para gerar um range amplo de rom_types + updater-script de dump. Procedimento específico está em [`docs/fase7-deploy-2026-10-16/06-dumps-obtidos.md § Como re-dumpar`](../fase7-deploy-2026-10-16/06-dumps-obtidos.md#como-re-dumpar).

Resumo:

```python
# Em tooling/ota-build/build.py, trocar:
ROM_TYPES = ["0040"]
# Por:
ROM_TYPES = [f"{n:04d}" for n in range(0, 10000, 10)]  # 1000 valores
```

Build:

```bash
rm -rf tooling/ota-build/output/*
python3 tooling/ota-build/build.py
```

Pode levar vários minutos (vai gerar ~1000 pacotes assinados).

### 3.2 Carregar pendrive

```bash
sudo ./tooling/scripts/format-pendrive.sh /dev/sdX
sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sdX
```

### 3.3 Deploy no carro

1. Pendrive na porta USB-A frontal.
2. **Forçar cold boot** da central — segure `AUDIO` por 5 segundos até aparecer "Quer reiniciar?". Confirme.
3. Central reinicia. Se qualquer rom_type bater, o updater-script salva info no pendrive. Se nenhum bater, pendrive volta "vazio".

### 3.4 Após o deploy, extrair logs

Antes de puxar o pendrive do carro, salve os logs do sistema:

1. Com áudio off: `DAY/NIGHT + AUDIO + MENU` por 2 segundos.
2. `Detail Information & Setting → Error History → Save`.
3. Aguarda chegar 100%. Central salva `logcat.txt`, `kmsgcat.txt`, exception dumps + PowerLog no pendrive.

Puxa pendrive, plugar no notebook.

### 3.5 Analisar os logs

Procure por `daupdater` nos logcats:

```bash
grep "daupdater" /caminho/pendrive/logcat*
```

Vai aparecer algo como:

```
E daupdater: getNewDaVersion(228):Can't open /mnt/usbdrive1/0040/SwUpdate.mdt
```

**O número é o seu `rom_type`!**

Alternativamente, se algum rom_type do seu range bater, no pendrive volta um arquivo `MATCH-<rom>.txt` + `diag-<rom>-vendor-build.prop`. Esse último contém `custom_rom.type=<valor>` — valor exato.

### 3.6 Atualizar o `build.py` com o valor correto

```python
# tooling/ota-build/build.py
ROM_TYPES = ["<seu_rom_type>"]  # ex: ["0040", "1115", "2250"...]
```

Agora o pacote OTA real (de instalação do APK) vai usar o valor certo.

## Passo 4 — Descobrir as coordenadas do botão OK

### 4.1 Resolução da sua tela

Via menu de serviço: `DAY/NIGHT + AUDIO + MENU` 2s → `Detail Information & Setting → Unit Check → Display` (ou similar).

A nossa safra tem **800×480**. Se a sua é diferente, as coord do botão vão ser diferentes.

### 4.2 Via dump do DaLauncher

Depois que descobriu seu rom_type (Passo 3), use o pacote de dump completo (também em [`docs/fase7-deploy-2026-10-16/06-dumps-obtidos.md`](../fase7-deploy-2026-10-16/06-dumps-obtidos.md)) para extrair `DaLauncher.apk` do seu HU.

Decompile:

```bash
cd tooling/apks-decoded
apktool d -o DaLauncher tooling/apks-dumped/<seu-rom>/vendor-app/DaLauncher.apk
```

Procure o layout do Aviso:

```bash
grep -l "disclaimer" DaLauncher/res/layout/*.xml
```

Deve ser `mm_02_01_02.xml` (nosso) ou similar. Abra e procure o `btnOK`:

```xml
<... android:id="@id/btnOK"
     android:layout_width="354.0px"
     android:layout_height="44.0px"
     android:layout_x="223.0px"
     android:layout_y="328.0px">
```

Centro do botão: `(x + width/2, y + height/2)`. Nosso caso: `(223 + 354/2, 328 + 44/2) = (400, 350)`.

### 4.3 Atualizar `AutoOkConfig.java`

```java
public static final int BUTTON_OK_X = <centro_x>;
public static final int BUTTON_OK_Y = <centro_y>;
```

Rebuild APK:

```bash
cd our-apk
./gradlew assembleRelease
# ...sign com apksigner
cp AutoOk.apk ../tooling/ota-build/overlay/system/app/AutoOk.apk
```

Rebuild OTA, deploy, teste.

## Passo 5 — Confirmar nome da Activity

Se sua safra tem `com.mitsubishielectric.ada.app.dalauncher.OpeningDivideActivity` (igual à nossa), nada muda.

Se for diferente:

```bash
grep -rln "DisclaimerFragment" DaLauncher/smali/ | grep -v DisclaimerFragment\$
```

A classe que instancia `DisclaimerFragment` é a Activity do Aviso.

Atualizar `AutoOkConfig.AVISO_ACTIVITY_NAME` com formato `pkg/.ClassName` (barra-ponto):

```java
public static final String AVISO_ACTIVITY_NAME =
    "<package>/.<ClassName>";
```

---

## Checklist antes de deployar na sua safra

- [ ] DA version anotada
- [ ] Rom type descoberto (via diagnóstico ou matriz)
- [ ] `build.py` atualizado com seu rom_type
- [ ] Resolução da tela confirmada
- [ ] Coord do botão OK extraídas do seu DaLauncher.apk
- [ ] `AutoOkConfig.java` atualizado
- [ ] APK rebuildado e assinado
- [ ] Overlay atualizado com APK novo
- [ ] Pacote OTA buildado
- [ ] Pacote ROLLBACK buildado (sempre!)
- [ ] Reporta safra na matriz via issue 😊

---

**Dúvida?** Abra uma issue com template de nova safra. A comunidade cresce com dados reportados.
