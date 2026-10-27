# 08 — Backups e rollback

Catálogo completo do que temos de backup, para que serve, e o que **não** temos (riscos remanescentes).

## Matriz de backups

### ✅ Que temos no projeto

| Artefato | Local | Tamanho | Reconstruível? | Cenário de uso |
|---|---|---|---|---|
| **Pacote OTA INSTALL** | `tooling/ota-build/output/<ts>/0040/SwUpdate.mdt` | 1.6MB | ✅ Via `build.py` | Re-instalar AutoOk+su |
| **Pacote OTA ROLLBACK** | `tooling/ota-build/output-rollback/<ts>/0040/SwUpdate.mdt` | 1.6MB | ✅ Via `build-rollback.py` | Remover AutoOk+su |
| **APK compilado** | `our-apk/app/build/outputs/apk/release/AutoOk.apk` | 12.8KB | ✅ Via `./gradlew assembleRelease` | Reprodutibilidade do binário |
| **Fonte do APK** | `our-apk/app/src/` | ~5KB | — | Modificação futura do APK |
| **Dump do /system pré-deploy** | `tooling/apks-dumped/dump-0040/` | 192MB | ⚠️ Precisa dumpar via carro | Inspeção, comparação pós-deploy, achar coord/activity em safras adjacentes |
| **Logs install final** | `docs/fase7-deploy-2026-10-16/artefatos-deploy/install-0040-final.log` | <2KB | — | Prova de que deploy funcionou |

### ❌ Que NÃO temos — riscos remanescentes

| Falta | Risco | Mitigação possível |
|---|---|---|
| **Imagem raw da partição APP** (mmcblk0p3, ~1GB) | Se brickar e nossos arquivos removidos não bastarem, não dá para restaurar o `/system` inteiro | Dumpar via pacote OTA de backup raw (ver seção abaixo) |
| **Imagem raw da partição CAP** (mmcblk0p2, ~100MB) | Idem para `/system/vendor` | Idem |
| **Imagem do bootloader + recovery** (NOR flash) | Se corromper o bootloader/recovery, só JTAG resolve | Dumpar via `dd if=/dev/mtd1 of=...` dentro do updater-script (complexo) |
| **Backup do /data** | Perder configurações salvas (Bluetooth pareado, presets, etc.) | Dumpar via pacote OTA |

**Em outras palavras:** nosso rollback cobre o cenário "APK deu problema, quero voltar ao normal". **Não cobre** cenário "central brickou e preciso restaurar firmware inteiro".

Para safra `1.F187.16` BR, o risco de brick com nosso procedimento é baixo:
- Nunca modificamos arquivos existentes do `/system`
- Só adicionamos 2 arquivos novos (AutoOk.apk + su)
- Updater-script usa edify `mount`/`unmount` oficial do recovery AOSP
- Teste de deploy foi bem-sucedido 2026-10-16

Mas o risco **nunca é zero** com modificação de firmware em sistema automotivo. Se quer margem máxima, considere fazer backup raw (seção abaixo).

## Rollback simples

**Cenário:** você quer remover o `AutoOk.apk` e o `su` do `/system`. Central volta ao estado original.

### Pré-condições
- Pacote de rollback já construído em `tooling/ota-build/output-rollback/<ts>/0040/SwUpdate.mdt`.
- Pendrive FAT32 MSDOS disponível.
- Carro acessível + combo `AUDIO 5s` funciona.

### Procedimento
Detalhado em [`07-rollback.md`](07-rollback.md). Resumo:

```bash
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX
# Depois no carro: porta frontal + AUDIO 5s + confirmar reiniciar
```

Tempo: ~5 min no notebook + ~10 min no carro.

## Rollback de emergência

**Cenário:** central em boot loop, não boota normal, problema maior.

Veja [`07-rollback.md § Rollback de emergência`](07-rollback.md#rollback-de-emergência-central-não-boota).

Opções (ordem de nuclearidade):
1. Deploy do rollback via OTA (se central ainda chega no recovery)
2. Puxar fusível do radio por 15-20 min (força desligamento completo)
3. Desconectar bateria por 30 min (reset total)
4. Troca da central (R$ 1.000-2.000)

## Backup raw de partição (opcional, mas recomendado)

Para ter margem total de segurança, podemos construir um **pacote OTA que dumpa `APP` e `CAP` inteiras** para o pendrive. Isso daria:
- `app.img.gz` (~500MB-1GB gzipped) — imagem bootável de `/system`
- `cap.img.gz` (~50-100MB) — imagem de `/system/vendor`

Restauração seria via outro pacote OTA que faz `dd` do raw image de volta para a partição. Isso é a **única forma real** de ter recovery completo sem JTAG.

**Não construímos esse backup ainda.** Se quiser, posso criar o pacote de dump raw (dura ~5-10 min no carro + requer pendrive de 2GB+). O doc [`03-descobrindo-sua-safra.md`](03-descobrindo-sua-safra.md) tem a receita de modificar `build.py` para dumps — princípio é o mesmo.

Me avise se quer fazer.

## Verificar estado dos backups

Script helper que lista o que está presente:

```bash
./tooling/scripts/verificar-backups.sh
```

Saída mostra o que cada pasta tem, SHA-1 dos arquivos críticos, e alerta se faltar algo.

## Reprodutibilidade

Qualquer um desses backups pode ser reconstruído se perdeu:

### Reconstruir pacote INSTALL

```bash
cd our-apk
./gradlew clean assembleRelease
$ANDROID_SDK_ROOT/build-tools/33.0.2/apksigner sign \
  --ks ~/.android/debug.keystore --ks-pass pass:android \
  --out app/build/outputs/apk/release/AutoOk.apk \
  app/build/outputs/apk/release/app-release-unsigned.apk
cp app/build/outputs/apk/release/AutoOk.apk \
   ../tooling/ota-build/overlay/system/app/AutoOk.apk
cd ..
python3 tooling/ota-build/build.py
```

Resultado em `tooling/ota-build/output/<timestamp>/0040/SwUpdate.mdt`.

### Reconstruir pacote ROLLBACK

```bash
python3 tooling/ota-build/build-rollback.py
```

Resultado em `tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt`.

### Re-dumpar o /system

Procedimento em [`../fase7-deploy-2026-10-16/06-dumps-obtidos.md § Como re-dumpar`](../fase7-deploy-2026-10-16/06-dumps-obtidos.md#como-re-dumpar). Requer:
- Modificar `build.py` temporariamente para gerar updater-script de dump (não install)
- Deploy no carro via protocolo normal
- Pendrive volta com os 192MB de dumps

### Reproduzir o APK no mesmo SHA-1

**Não garantido.** APKs assinados com debug keystore têm SHA-1 que depende de timestamp interno e keystore local. Para reproduzir SHA-1 idêntico, você precisaria do mesmo `~/.android/debug.keystore`. Para sua tranquilidade, o SHA-1 do seu deploy final está no manifest de artefatos: `docs/fase7-deploy-2026-10-16/02-descobertas-tecnicas.md § Hardware version`.

## O que fazer AGORA para ter rollback 100% garantido

Checklist antes de qualquer modificação futura ou longa ausência:

- [ ] Pacote ROLLBACK construído e verificado via `verificar-backups.sh`
- [ ] Pendrive extra formatado FAT32 MSDOS carregado com ROLLBACK (deixe no porta-luvas)
- [ ] Imagem raw de APP+CAP dumpada e salva no notebook (opcional mas recomendado)
- [ ] Backup do `~/.android/debug.keystore` em local seguro (pra conseguir re-assinar APK compatível)

## Em caso de atualização OTA oficial da Honda

Se a Honda emitir OTA (improvável para safra 2017 mas possível):
1. **Antes de aplicar o OTA deles**: deploy do nosso ROLLBACK para limpar nossos arquivos.
2. Aplique a OTA Honda normalmente.
3. Pós-OTA: dumpar o novo `/system` para ver o que mudou (novo rom_type? novo layout do Aviso?).
4. Ajustar `build.py` e `AutoOkConfig.java` com valores novos.
5. Redeployar.

Procedimento em [`../fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Após atualização OTA Honda`](../fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#após-atualização-ota-honda).
