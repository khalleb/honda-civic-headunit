# 05 — Deploy no carro

Como transferir o pacote OTA do pendrive pra central e aplicar.

**Pré-requisito:** `SwUpdate.mdt` já gerado em `tooling/ota-build/output/<timestamp>/0040/`. Se ainda não, veja [`04-build-do-pacote.md`](04-build-do-pacote.md).

**Rede de segurança obrigatória:** antes do deploy do INSTALL, construa o pacote ROLLBACK. Se der problema, você precisa ter o rollback pronto na hora. Nunca deploy sem rollback no notebook.

**Tempo:** ~5 min no PC (preparar pendrive) + ~5-10 min no carro (deploy OTA).

---

## Parte 1 — No PC

### 1.1 Pluga o pendrive

```bash
lsblk -o NAME,SIZE,MODEL,TRAN
```

Identifica o device do pendrive. Ex:
```
NAME        SIZE MODEL                 TRAN
sda         29G  USB  DISK            usb      ← pendrive
nvme0n1     238G INTEL SSD              nvme   ← SSD do notebook, NÃO MEXE
```

**Confirma 3 vezes que é o pendrive!** Script errado em `/dev/nvme0n1` apaga todo o SSD do notebook.

### 1.2 Preparar pendrive (formato + copia pacote)

```bash
# Formata FAT32 MSDOS (destrói conteúdo!)
sudo ./tooling/scripts/format-pendrive.sh /dev/sda

# Copia o pacote INSTALL mais recente
sudo ./tooling/scripts/prepare-pendrive-install.sh /dev/sda
```

**O que o `prepare-pendrive-install.sh` faz:**
1. Confirma que `/dev/sda` tem transport `usb` (guarda contra `/dev/nvme`)
2. Monta temporariamente o pendrive
3. Limpa conteúdo anterior
4. Copia `SwUpdate2.txt` (trigger) + `0040/SwUpdate.mdt` (pacote)
5. Unmount + sync

Saída esperada:
```
=== Conteúdo final ===
drwxr-xr-x. 2 khalleb khalleb 16384 ... 0040
-rw-r--r--. 1 khalleb khalleb    28 ... SwUpdate2.txt

=== PRONTO ===
Pendrive em /dev/sda carregado com pacote INSTALL.
```

### 1.3 Puxa o pendrive do notebook

Sem umount manual — o script já fez. Pode arrancar.

---

## Parte 2 — No carro

### 2.1 Pendrive na porta USB-A frontal

A porta frontal fica perto do volante/console central (não a do console central secundário). Nos Civic BR, geralmente ao lado do botão de ligar/desligar o motor ou atrás da alavanca de câmbio.

**NÃO use porta USB-C** — essa é só pra carregar celular, o daupdater não escaneia ela.

### 2.2 Carro ligado em ACC ou ON

Chave em ACC (sem motor) ou ON (chave totalmente girada, motor desligado). O motor **não precisa estar rodando**.

Central ligada e normal: pode estar na tela principal, no CarPlay, no rádio, qualquer uma. Não importa.

### 2.3 Combo cold boot: AUDIO 5s

**Segure o botão AUDIO por 5 segundos** sem soltar. Depois de ~5s, aparece um diálogo:

```
┌─────────────────────────────┐
│                              │
│  Quer reiniciar o sistema?   │
│                              │
│       [ Cancelar ]  [ OK ]  │
│                              │
└─────────────────────────────┘
```

**Confirma OK.**

Se o diálogo **não aparecer** depois de 5s de AUDIO segurado:
- Pode ser que o botão esteja mal pressionado (segura firme no centro)
- Pode ser que o sistema esteja em suspend profundo — abra a porta pra "acordar" primeiro
- Pode ser que a safra tenha combo diferente — [`06-troubleshooting.md`](06-troubleshooting.md)

### 2.4 Central reinicia (shutdown real + cold boot)

A tela apaga por 1-2 segundos. Depois:

1. **Logo Honda** aparece
2. **Barra de progresso aparece** (acima do logo, pequena, pode ser rápida)
3. Pode aparecer a tela do "Software Update" ou "Copying..." — isso é o SystemUpdate.apk recebendo o pacote
4. **Central reinicia novamente** sozinha (segunda vez)
5. Pode aparecer barra do recovery (azul geralmente)
6. **Terceiro reboot** — volta ao modo normal
7. Tela de Aviso aparece normalmente (nessa primeira vez, você precisa clicar OK manual uma vez)

**Tempo total:** 3-10 minutos. Depende do tamanho do pacote. Pacotes INSTALL são pequenos (~870 KB) e aplicam em ~2-3 min.

### 2.5 Quando a central voltar à tela normal

**Puxa o pendrive.** Simples.

### 2.6 Clica OK uma vez manual

**IMPORTANTE:** nessa primeira vez pós-install, o APK **ainda não foi iniciado** (não houve `BOOT_COMPLETED` ainda — a OTA aconteceu durante o próprio boot). Clica OK manualmente nessa primeira aparição do aviso.

**No próximo boot** (quando você desligar e ligar o carro), o APK já estará ativo e vai dispensar o aviso automaticamente.

---

## Parte 3 — Testar

### 3.1 Desligar e ligar o carro

- Chave em OFF (desliga completamente)
- Espera 5 segundos
- Chave em ACC ou ON

Central liga.

### 3.2 Observar o aviso

- Aviso aparece normalmente (não há como fazê-lo não aparecer sem Xposed)
- **Aguarda ~5-10 segundos**
- Aviso deve sumir sozinho

Se sumir: **🎉 funcionou. Projeto completo.**

### 3.3 Repetir 2-3 vezes

- Desliga, liga. Deve interceptar.
- Desliga, liga. Deve interceptar.
- Pelo menos 3 ciclos sem falha pra ter confiança.

---

## Verificar os logs (opcional, mas útil pra confirmar)

Depois do deploy, pode ler o log do processo OTA que ficou no pendrive:

```bash
cat /run/media/<usuario>/HONDA_OTA/result.log
# Esperado: 2026/10/17 11:19:29 : OK

cat /run/media/<usuario>/HONDA_OTA/install-0040.log
# Esperado: tudo com exit=0, APK e su confirmados em /system
```

**Para ler o log do nosso APK** (depois do primeiro boot pós-install), precisa de acesso root via adb — se tiver essa rota ativa:

```bash
adb shell su -c "cat /data/data/com.khalleb.civichmi.autook/files/autook.log"
```

O log mostra:
```
2026-10-17 11:23:11 === session start versionCode=3 ===
2026-10-17 11:23:11 watcher iniciado needle=...OpeningDivideActivity
2026-10-17 11:23:14 aviso detectado
2026-10-17 11:23:16 tap ok=true coords=3
2026-10-17 11:23:28 rearmed (watcher reusado)
```

Se vir isso, APK está rodando perfeitamente.

---

## Checklist pós-deploy

- [ ] `result.log` do pendrive mostra `OK`
- [ ] Primeiro ciclo pós-install: aviso sumiu sozinho em ~5s
- [ ] Segundo ciclo: idem
- [ ] Terceiro ciclo: idem
- [ ] CarPlay/Bluetooth/áudio/navegação funcionam normalmente
- [ ] Nenhum crash/instabilidade observado
- [ ] Pacote ROLLBACK no notebook, acessível a qualquer momento
- [ ] (Opcional) Pendrive extra com ROLLBACK no porta-luvas

---

## Deu errado?

Veja [`06-troubleshooting.md`](06-troubleshooting.md) — tem decision tree pra cenários comuns:

- Diálogo "Quer reiniciar?" nunca aparece
- Fluxo OTA começa mas abort
- Barra de progresso trava
- APK não dispara após boot
- Central em boot loop

**Se brickar:** [`07-rollback.md`](07-rollback.md) — procedimento de recuperação.

---

## Próximo passo

Funcionou? Pode reportar sua safra via [issue](../../.github/ISSUE_TEMPLATE/nova-safra.md) ajudando a comunidade.

Pra entender o que o APK está fazendo em runtime: [`fase7-deploy-2026-10-16/04-apk-autook-detalhes.md`](../fase7-deploy-2026-10-16/04-apk-autook-detalhes.md).

Pra ter rede de segurança completa (dump raw bootable): [`08-backups-e-rollback.md`](08-backups-e-rollback.md).
