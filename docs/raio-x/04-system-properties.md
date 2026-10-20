# Scan 4 — System Properties

**48 propriedades `ro.*`/`persist.*`/`sys.*`/`net.*` referenciadas em bytecode.** Lista do que o shipping lê ou escreve via `SystemProperties.get()`/`.set()`.

## Como foi coletado

```bash
grep -rhE 'const-string .*"(sys\.|ro\.|persist\.|init\.|dev\.|net\.)' bulk-smali/*/ \
  | grep -oE '"(sys\.|ro\.|persist\.|init\.|dev\.|net\.)[^"]+"' \
  | sort -u
```

**Limites:** props cujo nome é concatenado via `StringBuilder` (ex: `"sys.hmi_" + state`) escapam. Olhando o output, não há evidência de nenhum caso desses nesta ROM — todos os setters/getters usam literal direto.

## Por prefixo

### `sys.*` (8) — estado volátil do carro 🎯

| Prop | Significado inferido | Quem usa |
|---|---|---|
| **`sys.hmi_service_started`** | Flag que o PowerManager seta quando os HMI services estão vivos | `PowerManagerApService` principalmente |
| **`sys.hmi_service_start_cause`** | Causa textual do último start: `ColdBoot`, `ExitLP0`, `AccOnRestart` | idem |
| **`sys.hmi_service_keyoff`** | Flag de key-off em curso | idem |
| **`sys.hmi_reboot_reservation`** | Reserva de reboot (reboot pendente após keyoff) | idem |
| `sys.lowbat_stat` | Status de bateria baixa | diag/power |
| `sys.settings_global_version` | Versão do SettingsProvider.Global | AOSP |
| `sys.settings_secure_version` | Versão do SettingsProvider.Secure | AOSP |
| `sys.settings_system_version` | Versão do SettingsProvider.System | AOSP |

**Para o AutoOk:** `sys.hmi_service_started` + `sys.hmi_service_start_cause` já são usados indiretamente pelo nosso `HmiServiceReceiver` (via broadcast). Lê-los direto por `SystemProperties.get()` seria redundante — o broadcast chega com os mesmos dados.

### `persist.*` (13) — persistido entre reboots

Props que sobrevivem a reboot (escritas em `/data/property/persist.*`):

| Prop | O que faz |
|---|---|
| **`persist.sys.keyoff_reboot`** 🎯 | **0 = não reinicia no keyoff; 1 = reinicia**. Vale testar — mudar isso pode forçar cold boot ao desligar o carro, útil pra evitar o estado "aviso persiste" |
| `persist.sys.hdcp_checking` | HDCP (HDMI content protection) ligado/desligado |
| `persist.sys.strictmode.visual` | Debug: strict mode visual |
| `persist.sys.ui.hw` | Hardware UI rendering on/off |
| `persist.sys.` | prefix "nu" (provavelmente artefato de StringBuilder) |
| `persist.radio.imsallowmtsms` | IMS mobile-terminated SMS |
| `persist.radio.imsregrequired` | IMS registration required |
| `persist.radio.otaspdial` | OTASP dial habilitado |
| `persist.radio.ramdump` | ramdump do radio stack |

Também aparecem strings "literais de log" como `persist.sys.keyoff_reboot is 0`, `persist.sys.keyoff_reboot set 1` — essas são **mensagens de log** com o nome da prop embutido, não props em si. Deixaram marca no grep porque o filtro só olha o prefixo.

### `ro.*` (18) — read-only, imutáveis após boot

| Prop | O que informa |
|---|---|
| `ro.build.id` | DA version — nosso valor é `1.F187.16` |
| `ro.build.selinux` | SELinux status build-time |
| `ro.cdma.ecmexittimer` | CDMA emergency callback mode timer |
| `ro.com.android.dataroaming` | Roaming default |
| `ro.com.android.mobiledata` | Mobile data default |
| `ro.com.android.wifi-watchlist` | Watchlist WiFi |
| `ro.config.license_path` | Path pra arquivo de licença |
| **`ro.debuggable`** | **0 em prod, 1 em debug**. Nosso provavelmente 0 — vale confirmar |
| `ro.kernel.qemu` | é emulador? |
| `ro.lockscreen.disable.default` | Default lockscreen (desabilitado no carro) |
| `ro.ril.fccid` | FCC ID do rádio |
| `ro.allow.mock.location` | Mock location permitido |
| `ro.screenreader.market` | Market pra screenreader |
| **`ro.serialno`** | Serial number do device — já conhecemos (`androidboot.serialno` em kernel cmdline) |
| `ro.setupwizard.mode` | Modo do setup wizard |
| `ro.telephony.default_network` | Rede default (RIL) |
| `ro.url.safetylegal` | URL legal |

### `net.*` (9) — networking

| Prop | O que faz |
|---|---|
| `net.gsm.attempt-gprs`, `net.gsm.succeed-gprs` | Contadores GPRS |
| `net.gsm.radio-reset` | Flag reset do rádio |
| `net.ppp0.dns1`, `net.ppp0.dns2` | DNS do PPP (dial-up TCU) |
| `net.ppp.reset-by-timeout` | Reset PPP por timeout |
| `net.tcp.buffersize.wifi` | Buffer TCP via WiFi |
| `net.tethering.noprovisioning` | Tethering sem provisão |
| `net.wimax.mac.address` | MAC WiMAX |

Tudo relacionado a telefonia celular/WiFi — safra US/Acura inclusa (há TCU/CDMA cadastrados mesmo não ativos no BR).

## Highlights

### Propriedades HMI (as 4 que importam)

As únicas propriedades vendor-específicas da plataforma são os 4 flags `sys.hmi_*`. Dão o estado atual sem precisar escutar broadcasts:

```java
boolean started = "1".equals(SystemProperties.get("sys.hmi_service_started"));
String cause    = SystemProperties.get("sys.hmi_service_start_cause");   // "ColdBoot" | "ExitLP0" | "AccOnRestart"
boolean keyoff  = "1".equals(SystemProperties.get("sys.hmi_service_keyoff"));
boolean reboot  = "1".equals(SystemProperties.get("sys.hmi_reboot_reservation"));
```

**Para o AutoOk**, dois usos possíveis:
1. **No boot**, antes de iniciar o watcher: ler `sys.hmi_service_start_cause`. Se for `ColdBoot`, usar delay longo (sistema inteiro subindo). Se for `ExitLP0`, delay curto (volta rápida). Economiza bateria/CPU no cenário comum.
2. **No watchdog**, checar se `sys.hmi_service_started == "0"` significa "sistema vai dormir" e reduzir atividade preventivamente.

### `persist.sys.keyoff_reboot`

Esta é a propriedade que decide se o carro faz **cold boot ao desligar** vs. **suspend/resume**. Hoje nossa safra default faz suspend — o combo `AUDIO 5s + confirmar reiniciar` é o que força cold boot. 

**Se setarmos `persist.sys.keyoff_reboot=1`**, teoricamente todo keyoff vira cold boot. Isso tem três implicações potenciais:

1. **Pode resolver tudo o que a v0.4.0 trata** — se cada "ignição on" é cold boot, o aviso aparece do zero sem o LP0 bizarro.
2. **Impacto em UX**: o Honda liga mais devagar (3-5s de boot vs. instantâneo do suspend).
3. **Impacto em consumo**: cold boot gasta mais energia que resume — pode esgotar bateria em dias parado.

Vale a pena pesquisar sem commitar antes. Baixo custo: `su -c "setprop persist.sys.keyoff_reboot 1"` + testar + reverter com `0`.

### `ro.debuggable`

Se `ro.debuggable=1` por mágica em algum vendor-config, abriria **adb shell com acesso irrestrito** sem precisar do EvilValet. Vale verificar via `getprop ro.debuggable` no carro — baixo custo zero (só leitura).

## Observações metodológicas

- **Entradas "falso-positivo"**: `persist.sys.keyoff_reboot is 0`, `persist.sys.keyoff_reboot set 1` etc são **strings de log** com o nome da prop embutido. Deixaram pegadas no grep. Para script futuro, filtrar strings sem espaço.
- **Props Honda-specific raras**: a plataforma usa principalmente **broadcasts e binder** para comunicação. SysProps são reservadas pra estado persistido ou lido por binários nativos (ex: `init.rc` consultando `sys.hmi_service_started` pra decidir se deve iniciar algo).

## Próximos passos sugeridos

1. **Dump completo via `getprop`** no carro — próxima vez que estiver com acesso, rodar `su -c getprop | tee /sdcard/getprop-full.txt`. Vai pegar inclusive props que são lidas por binários nativos (não só pelo que está no bytecode Java).
2. **Testar `persist.sys.keyoff_reboot=1`** como experimento com rollback preparado. Mais arriscado — fica como follow-up da Fase 9.
