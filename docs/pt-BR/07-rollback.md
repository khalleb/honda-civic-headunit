# 07 — Rollback (remover AutoOk + su)

Se precisar reverter a modificação — crash, instabilidade, atualização Honda pendente, qualquer motivo — este é o procedimento.

**Rollback é SIMÉTRICO ao deploy.** Mesmo pendrive, mesmo protocolo no carro, mas pacote diferente.

## Quando fazer rollback

- APK causando crashes/instabilidade (muito raro — nossa modificação é cirúrgica)
- Antes de aplicar atualização OTA oficial da Honda
- Vender o carro (deixar no estado original)
- Qualquer dúvida/arrependimento
- Diagnóstico — remover temporariamente para isolar se um problema vem da nossa mod

## Procedimento

### 1. Construir o pacote de rollback (se ainda não foi feito)

```bash
cd /caminho/do/projeto
python3 tooling/ota-build/build-rollback.py
```

Saída:

```
INFO: rollback mdt: tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt
```

### 2. Carregar pendrive

```bash
sudo ./tooling/scripts/prepare-pendrive-rollback.sh /dev/sdX
```

O script:
1. Confere que `/dev/sdX` é USB (guarda contra formatar o SSD)
2. Monta o pendrive
3. Apaga todo o conteúdo existente
4. Copia o pacote de rollback (busybox + sleep + updater-script de remoção)

### 3. Deploy no carro

Mesmo protocolo do deploy de instalação:

1. **Pendrive na porta USB-A frontal**
2. **Carro ligado**
3. **`AUDIO 5s`** → "Quer reiniciar?" → **confirma**
4. Fluxo "Software update → Copying" aparece
5. Central reinicia → recovery aplica → reboot normal
6. Quando central voltar à tela normal, **puxa o pendrive**

## O que o rollback faz

Internamente, o updater-script no recovery:

1. Monta `/system` via edify (partição `APP` = `mmcblk0p3`)
2. `rm -f /system/app/AutoOk.apk`
3. `rm -f /system/xbin/su`
4. Confirma remoção listando ambos (devem retornar "No such file or directory")
5. `sync` + unmount
6. Sleep 30s pra janela de retirada do pendrive

Grava `rollback-0040.log` no pendrive com o output de cada passo — para você verificar depois.

## Verificar que removeu

Depois do deploy, pluga pendrive no notebook, abre `rollback-0040.log`:

```
=== ROLLBACK START Fri Oct XX ... ===
-rw-r--r-- ... AutoOk.apk           ← tinha, foi removido
-rwsr-sr-x ... su                   ← tinha, foi removido
rm-done
removal-confirmed                   ← ambos removidos com sucesso
=== ROLLBACK END ... ===
```

Se tiver `removal-confirmed`, rollback funcionou.

Depois disso, se você voltar a ligar o carro:

- Aviso aparece normalmente, precisa clicar OK manual (como era antes).
- Nenhum sinal visual de que o APK/su existiram.
- Serviços Android (CarPlay, Bluetooth) continuam intactos.

## Rollback de emergência (central não boota)

Cenário raro: APK ou outro problema causa boot loop. Procedimento:

1. **NÃO entre em pânico.** O rollback via OTA ainda deve funcionar.
2. Pluga pendrive de rollback na porta frontal.
3. **Combo `AUDIO 5s`** para forçar reboot.
4. Fluxo deve aplicar — recovery pega o pacote.
5. Se funcionar, pronto.

Se nem o rollback via OTA funcionar (central em recovery loop permanente ou boot loop sem fim), opções:

- **Puxar fusível do radio** no fuse box interno por 15-20 minutos. Força a central a desligar completamente, pode destravar.
- **Desconectar bateria do carro** (negativo) por 30 minutos. Nuclear option — reset total.
- **Troca da central** — última opção, R$ 1.000-2.000.

Veja [`docs/fase7-deploy-2026-10-16/05-manutencao-e-futuro.md § Troubleshooting`](../fase7-deploy-2026-10-16/05-manutencao-e-futuro.md#troubleshooting) para troubleshooting detalhado.

## Depois do rollback — pode reinstalar?

Sim. Tudo que você fez para o deploy inicial funciona de novo. Mesmo pacote OTA de instalação, mesmo protocolo. Mas lembra:

- Se mudou algo no APK/updater-script desde a última vez, rebuild antes.
- Se mudou de pendrive, verifica se está FAT32 MSDOS correto.

## Rede de segurança: ter rollback pronto SEMPRE

**Regra:** nunca deployar o pacote INSTALL sem ter o pacote ROLLBACK já construído e acessível no notebook.

```
tooling/ota-build/output-rollback/<timestamp>/0040/SwUpdate.mdt
```

Se por qualquer motivo precisar reverter às pressas, você já tem.

Em casos de viagem/longa distância, considere ter um pendrive extra já carregado com rollback — guardado no porta-luvas, pronto se precisar.
