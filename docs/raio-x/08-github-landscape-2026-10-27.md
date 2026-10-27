# Varredura do GitHub — ecossistema Honda e lições para o projeto (2026-10-27)

Varredura ampla do GitHub, feita a partir da pesquisa "Honda Hack" e refinada por diversos ângulos (plataforma Mitsubishi, família de carro, derivados do nosso stack, projetos de telemetria/HU, listas de RE automotivo). O objetivo é **catalogar o que já foi descoberto por outras pessoas** sobre o nosso HU — ou sobre partes vizinhas do mesmo veículo — puxar o que serve para o nosso projeto, e deixar registrado o que **não** cabe no nosso escopo. Baseado em metadados, READMEs, código legítimo e nas issues públicas do `librick/ic1101`.

> **Achado crítico desta varredura, resolvido em outro repo:** o `su` que já instalamos no carro é **KingoSU**, não SuperSU. A auditoria do `joshfng/root-honda` identificou isso e publicou a substituição pelo `su` oficial do Chainfire. Nós **ainda temos o KingoSU no binário local** (SHA-256 bate exatamente). Ver §4.

## 1. Panorama (33 repositórios inspecionados)

Agrupei por categoria. Estrelas são do dia da varredura; o que não tiver link direto para arquivo é por não haver conteúdo relevante além do metadado.

### 1.1 Mesmo HU que o nosso (vcm30t30, Android 4.2.2, Mitsubishi ADA)

| Repo | ★ | Papel | Relevância |
|---|---|---|---|
| [`librick/ic1101`](https://github.com/librick/ic1101) | **188** | Writeup EvilValet + `ota-builder` + `apk-rebuilder` + `aidl-rebuilder`. Autor: Eric McDonald. | **Base técnica.** Já no `setup.sh`. Issues #6, #20, #29 em §5. |
| [`alexpotv/Clusters`](https://github.com/alexpotv/Clusters) | 1 | App Android aberto que lê o veículo via Binder/Intent e desenha no cluster secundário. | **Fecha a RE Camada 2 §3/§4** — ver §3. |
| [`jersacct/2016PilotOneClick`](https://github.com/jersacct/2016PilotOneClick) | 58 | Rooteador do Honda Pilot 2016 (DirtyCOW + `su` + whitelist). Já no `setup.sh`. | Fonte do mecanismo que `codeage/root-honda` adaptou. |
| [`codeage/root-honda`](https://github.com/codeage/root-honda) | 129 | Fork simplificado do 2016PilotOneClick + SuperSU + whitelist Mitsubishi. Já no `setup.sh`. | **De onde veio o nosso `su` — e com `su` incorreto, ver §4.** |
| [`joshfng/root-honda`](https://github.com/joshfng/root-honda) | 0 | **Fork auditado do codeage/root-honda** (2026-10-13). | **Nosso achado principal. Resolve o KingoSU; ver §4.** |
| `madhunm`, `ring2003`, `z3tab`, `eral2001`, `hackers365`, `CrackerCat`, `evi1r0s3` — todos `ic1101` | 0-1 | Forks mirror; 0 commits próprios em todos. | Confirma que o ic1101 **não** tem derivados ativos (não precisamos vigiar nada). |
| [`cysin/honda_hacking_analysis`](https://github.com/cysin/honda_hacking_analysis) | 16 | Análise RE das ferramentas comerciais chinesas (HondaHack / AutoHack / VinciCar). | **Fora do nosso escopo.** Apenas o fato de existir confirma a prevalência do alvo. Ver §7. |

### 1.2 Mesma geração do carro (Civic 2016/2017), lado dos ECUs/CAN

| Repo | ★ | Papel | Relevância |
|---|---|---|---|
| [`commaai/opendbc`](https://github.com/commaai/opendbc) | 2k+ | Decodificação de DBC. Contém **`honda_civic_touring_2016_can.dbc`** e **`honda_civic_hatchback_ex_2017_can.dbc`**. | **Tabela canônica de B-CAN/F-CAN** do nosso veículo. §6. |
| [`commaai/openpilot`](https://github.com/commaai/openpilot) | 64k | Driver assistance aberto. Honda é uma das plataformas mais cobertas. | Fluxos de leitura CAN em cima do opendbc — não vamos usar isso em runtime, só como "oracle" na RE. |
| [`sunnypilot/sunnypilot`](https://github.com/sunnypilot/sunnypilot) | 2154 | Fork do openpilot com mais carros Honda. | Mesma fonte CAN. |
| [`commaai/panda`](https://github.com/commaai/panda) | 1707 | Firmware do gateway CAN (OBD2 → USB). | Útil se um dia quisermos ler CAN **sem** o HU no caminho (plano B pra Fase 9). |
| [`alexgaoth/awesome-reverse-engineered`](https://github.com/alexgaoth/awesome-reverse-engineered) | — | Lista curada; destaca o `ic1101` na seção Automotive. | Confirma a reputação do nosso projeto-base. |

### 1.3 Outras famílias Honda / plataformas vizinhas

| Repo | ★ | Papel | Para nós |
|---|---|---|---|
| [`enricobattocchi/myhondaplus-homeassistant`](https://github.com/enricobattocchi/myhondaplus-homeassistant) | 18 | Integra Home Assistant com Honda Connect Europe (My Honda+). | API **cloud**, não HU local. Útil se quisermos cruzar comandos remotos. |
| [`enricobattocchi/myhondaplus-desktop`](https://github.com/enricobattocchi/myhondaplus-desktop) | 10 | GUI desktop para a mesma API. | Idem. |
| [`daviddelahoz/ha-hondalink`](https://github.com/daviddelahoz/ha-hondalink), [`nickwilkie/ha-hondalink`](https://github.com/nickwilkie/ha-hondalink) | — | Integração HondaLink (North America) com HA. | Equivalente US ao de cima. |
| [`mitchellrj/kamereon-python`](https://github.com/mitchellrj/kamereon-python) | 24 | Plataforma Kamereon da aliança Renault-Nissan-Mitsubishi (connected cars). | **Mitsubishi corporativo, não ADA.** Não é a nossa stack. |
| [`yuxiuwen64-maker/HondaHUDdiy`](https://github.com/yuxiuwen64-maker/HondaHUDdiy) | 0 | HUD custom para Honda **mais novo** (Android 10 + Alpine, `com.alap.honda30ea.aochr.meterservice`). | **Não é a nossa safra**, mas o **PROTOCOL.md** é útil (ver §3.5): padrão de bind + 12 TX codes de `MeterService`. |
| [`flyandi/honda-fuel-tracker`](https://github.com/flyandi/honda-fuel-tracker) | 0 | App React Native rastreador de combustível. | Autor é referência (SDK Mazda); este repo em si é só um app React Native, pouco especial. |
| [`flyandi/mazda-custom-application-sdk`](https://github.com/flyandi/mazda-custom-application-sdk) | 213 | SDK Mazda Connect (plataforma vizinha). | **Padrão arquitetural** — micro-framework + simulator. Vale como inspiração se um dia virar "AutoOk SDK" (item futuro do PENDENCIAS). |
| [`mbhul/HondaLink_USB_Audio`](https://github.com/mbhul/HondaLink_USB_Audio), [`tahmidul612/hondalink-app-controller`](https://github.com/tahmidul612/hondalink-app-controller) | 0-1 | Workarounds pontuais, usos de HondaLink. | Pouca relação com HU. |

### 1.4 ECU/OBD/K-Line (ecossistema separado, mas no mesmo repositório temático)

| Repo | Papel |
|---|---|
| [`VIRUXE/ghidra-oki66207`](https://github.com/VIRUXE/ghidra-oki66207) | **Módulo processador do Ghidra** para a família OKI 66201/66207/66301 — MCUs de ECUs Honda OBD1 pré-1996. Decompila com XRefs e C legível. |
| [`aster94/Keyword-Protocol-2000`](https://github.com/aster94/Keyword-Protocol-2000) | KWP2000 (Honda HDS, Suzuki SDS, Kawasaki KDS). |
| [`andreibaw/Honda_K-Line_KWP2000`](https://github.com/andreibaw/Honda_K-Line_KWP2000), [`atoid/DashBle`](https://github.com/atoid/DashBle), [`kerpz/ArduinoHondaUNI`](https://github.com/kerpz/ArduinoHondaUNI), [`guilhermemecatronica/projectkline`](https://github.com/guilhermemecatronica/projectkline) | OBD/K-Line para motos e carros antigos. |
| [`gecekusu1979/honda`](https://github.com/gecekusu1979/honda), [`bouletmarc/Converter`](https://github.com/bouletmarc/Converter), [`hondabase/files-archive`](https://github.com/hondabase/files-archive) | ECU tuning (eCtune, Hondata, cal/bin). |

**Nenhum** destes tem contato com o HU — ficam aqui só para registro de que a comunidade Honda-RE tem duas correntes bem separadas (ECU/motor vs. infotainment).

### 1.5 Writeups, discussões e matrizes

| Fonte | Relevância |
|---|---|
| [`kristate/krackinfo`](https://github.com/kristate/krackinfo) — `ANDROID_H.md` | Matriz "fabricante × modelo × device SoC". Honda × `vcm30t30` = `MY17ADA` (nosso). Também lista `koelsch`/`e1853` para Pilot, Accord, Clarity, NSX, Ridgeline, Spirior. |
| [`ahastudio/til`](https://github.com/ahastudio/til) — `security/honda-civic-headunit-evil-valet.md` | Resumo em coreano do writeup do librick e da thread HN. §8. |
| [HN thread 48523080](https://news.ycombinator.com/item?id=48523080) | 342 pontos / 76 comentários. Discussão de supply chain security. §8. |
| [`Buildstarted/linksfordevs`](https://github.com/Buildstarted/linksfordevs), [`bobkingdom/TrendRadar`](https://github.com/bobkingdom/TrendRadar), vários `Tyaoo/picker`, `BruceFeIix/picker` | Agregadores que indexaram o writeup do librick em 2026-06. Sinal de alcance. |

## 2. Issues públicas do `librick/ic1101` (campo da comunidade)

Explorei as 7 issues abertas/fechadas do ic1101 que ainda dão sinal. As três que importam para nós:

### 2.1 Issue #6 — `IVideoManagerApService` (não estava no nosso radar)

Usuário `hackers365` fez RE no `HondaHack-7.0.1-release.apk` com JADX e postou **quais services o produto comercial faz bind**:

- `IAvApService`
- `IVehicleInfoManagerApService`
- `ICameraAPService`
- **`IVideoManagerApService`** ← novo para nós

Útil pra nós: `IVideoManagerApService` entra na lista de services candidatos a deodex futuro (se formos escrever um app com sobreposição de vídeo, estilo o Clusters no cluster).

### 2.2 Issue #20 — cadeia completa de USB mode (Device/Host)

Autor documentou `UI → JNI → sysfs`:

```
UsbCertActivity (menu secreto)
   → UsbCertJni.changeDeviceMode(listener, 0|1)   [Java]
   → libusbcert_jni.so                            [JNI]
   → property_set("persist.sys.usb1_mode", "device"|"host")
   → usbdetectd                                   [prop watcher]
   → /sys/devices/platform/tegra-otg/enable_device
   → /sys/devices/platform/tegra-udc.0/.../soft_connect
```

Combo físico para o menu: **Brightness + Phone + Volume/Power** → "Detail Information and Settings" → segurar **Phone**, depois segurar **Home** (três beeps, depois um). Via shell (com root):

```sh
echo 0 > /sys/devices/platform/tegra-otg/enable_host
echo 1 > /sys/devices/platform/tegra-otg/enable_device
echo connect > /sys/devices/platform/tegra-udc.0/udc/tegra-udc.0/soft_connect
setprop sys.usb.config mtp,adb
setprop persist.sys.usb1_mode device   # persistente
```

**Impacto para nós:** com AutoOk + `su` já instalados, dá para habilitar ADB via USB a partir do próprio script, sem combo físico, em investigações futuras — ótimo para pós-deploy da Fase 10 e para substituir OTAs de diagnóstico pontuais por sessões ADB.

### 2.3 Issue #29 — pacote OTA do CR-V China

Usuário `hybzhl` subiu um `SwUpdate.mdt` chinês do CR-V, Android 4.2.2, mesmo CPU, versão `1.F198.60`. `librick` confirmou que o formato é "muito parecido" com Civic → "muitas ferramentas provavelmente funcionam para o CR-V também".

**Para nós:** safras compatíveis vão além do Civic G10 US — **CR-V China** confirmado como mesma família. Nossa "matriz de compatibilidade" (`PENDENCIAS.md`) ganha pontos: Civic BR `1.F187.16` (nós), Civic US (librick), **CR-V China `1.F198.60`**. `kristate/krackinfo` ainda lista Pilot, Accord, Ridgeline, NSX, Spirior usando `koelsch` (SoC primo — não é o mesmo chip, mas é o mesmo stack Mitsubishi ADA).

## 3. `alexpotv/Clusters` — a mina de ouro da RE Camada 2

App Android aberto feito para o cluster do Civic G10 (mesma safra, mesmo HU). Instala via ADB depois que o HU está em USB Device mode. Confirma, com código vivo, **tudo** o que inferimos na nossa RE Camada 2 §3 (`VehicleInfoManager`) — e vai além.

### 3.1 Como o Clusters acessa o veículo

`VehicleDataSource.java` faz `bindService` em três services Mitsubishi, com `Intent.setComponent(new ComponentName(pkg, cls))`:

| Service | Package | Class |
|---|---|---|
| VehicleInfoManager | `com.mitsubishielectric.ada.appservice.vehicleinfomanager` | `.VehicleInfoManagerApService` |
| AvApService | `com.mitsubishielectric.ada.appservice.avapservice` | `.AvApService` |
| DiagService | `com.mitsubishielectric.ada.appservice.diag` | `.DiagService` |

Depois chama o Binder cru com `transact(txCode, data, reply, 0)` + `writeInterfaceToken(descriptor)` — exatamente como todo app privilegiado que fala com um service Mitsubishi faria. Nada de reflection quebrando `android.jar`; é bind normal, por nome.

### 3.2 Tabela de TX codes

Esses números são o que a nossa RE Camada 2 §3 não tinha. Guardar aqui porque é a chave para qualquer app nosso falar com o service sem o AIDL original (que o Mitsubishi não publica):

```
# IVehicleInfoManagerApService
TX_GET_VEHICLE_INFO       = 12
TX_GET_FOOT_BRAKE         = 102
TX_GET_TURN_SIGNALS       = 103
TX_REGISTER_BCAN_LISTENER = 25
TX_REGISTER_FCAN_LISTENER = 35
TX_NOTIFY_BCAN_RECEIVE    = 88

# Subkeys de getVehicleInfo(int)
VEHICLE_INFO_ILLUMINATION  = 0
VEHICLE_INFO_SHIFT         = 1
VEHICLE_INFO_PARKING_BRAKE = 6
VEHICLE_INFO_SPEED         = 8
VEHICLE_INFO_GEAR          = 9

# IAvApService
TX_AV_GET_VOLUME     = 22     (type MAIN = 0)
TX_AV_GET_VOLUME_MAX = 160
TX_AV_GET_MUTE       = 24
TX_AV_GET_SOURCE     = 72

# IDiagService
DIAG_TX_INITIALIZE    = 1
DIAG_TX_REQUEST       = 3
DIAG_CANDATA_GET_FCAN = 3998210
DIAG_CANDATA_GET_BCAN = 3998209
```

### 3.3 IDs internos do B-CAN do Mitsubishi

Resolvidos pela classe `ConstExt` interna. **Não** são CAN IDs de wire; são os IDs que o `IVehicleBcanInformationListener` recebe no campo `type`:

| ID interno | Chave simbólica | Conteúdo |
|---|---|---|
| `318263376` | `VSPNE` | velocidade + rotação |
| `318263632` | `AT` | transmissão / posição de câmbio |
| `318264400` | `ILLUMI` | iluminação (faróis) |
| `318337360` | `STEERING` | ângulo do volante |
| `184053784` / `184053776` | `HLSW_BCM` / `HLSW_ICU` | setas |
| `318246936` / `318246928` | `MICU_BCM` / `MICU_ICU` | **luz de ré**, one-touch |
| `318334800` | `MAINTENANCE` | óleo, intervalo de serviço |
| `318333520` | `TRICOM` | autonomia (`C_TRICOM_RANGE`, `..._UNIT`) |
| `318336336` | `MET_CUSTOM` | ADAS (CMBS, LKAS, RDM) |

### 3.4 Fluxo de registro (confirma a RE §3)

```
bindService(VehicleInfoManagerApService, ServiceConnection)
   → onServiceConnected(binder):
       transact(TX_REGISTER_BCAN_LISTENER, writeInterfaceToken + writeStrongBinder(BcanListener))
       transact(TX_REGISTER_FCAN_LISTENER, writeInterfaceToken + writeStrongBinder(FcanListener))
       for each canId em CanDefinitions.BCAN_MESSAGES:
           transact(TX_NOTIFY_BCAN_RECEIVE, writeInt(canId))   ← inscreve no frame
```

Os listeners chegam como `Binder.onTransact(code, data, …)` com descriptor `IVehicleBcanInformationListener` / `IVehicleFcanInformationListener`, `type` (int) e um `Bundle` com os sinais já decodificados.

> **Nota do próprio Clusters:** "the Mitsubishi middleware pre-decodes raw frames and only delivers integer Bundle values to app-level listeners — raw bytes are NOT forwarded". Ou seja, do lado Android dá para ler sinal decodificado; raw CAN só com biblioteca nativa ou socket CAN direto.

### 3.5 Padrão arquitetural (confirmado em outras plataformas)

O `HondaHUDdiy` (plataforma Honda **mais nova**, Android 10 + Alpine) usa **o mesmo esquema** com nomes diferentes:

```
Intent i = new Intent("com.alap.honda30ea.aochr.meterservice.MeterService");
i.setPackage("com.alap.honda30ea.aochr.meterservice");
bindService(i, conn, BIND_AUTO_CREATE);
// 12 TX codes do IMeterServiceManager (sendByte / sendBitmap / sendTBTInfo / getBCanState etc.)
```

Importante: o `HondaHUDdiy` observa que **não** se deve usar `setComponent` com o nome real da classe (`...service.MeterService`), e sim só `package + action`, porque a classe real tem subpacote `service` que a action não revela. **Lição para nós:** se escrevermos um bind usando só a action (sem `setComponent`), tem que confirmar com `cmp=` no logcat que o serviço resolvido é o esperado — o AVApService ou VideoManager podem ter estrutura parecida.

### 3.6 Impacto para o nosso projeto

- **Fase 9 (câmera de ré sem logcat).** Em vez do polling, dá para `bindService` no `VehicleInfoManagerApService`, registrar `BcanListener`, chamar `notifyBcanReceiveSetting` com `MICU_BCM`/`MICU_ICU` (luz de ré), e tratar o callback. É mais limpo e não depende de `am_create_activity`.
- **Alternativa já conhecida:** `ICameraAPServiceReverseSignalListener` (MAPA Raio-X §1). Comparar as duas antes de escolher.
- **AutoOk v0.6.0 hipotético** poderia expor um status via `IAvApService` (volume / mute / source) para o próprio watchdog saber se o CarPlay está em ligação, antes de qualquer tap. Fecha o buraco que o v0.5.4 resolveu só com needle filtrado.
- **Permissão.** O manifesto do VehicleInfoManager pede `com.mitsubishielectric.ada.permission.VEHICLE_RW`. O [`05-trust-map.md`](05-trust-map.md) confirma: é GID-only, 70/110 APKs declaram. Nosso AutoOk também pode declarar sem signature issue (foi parte da decisão da Fase 10).
- **Permissões Android 4.2.2 não precisam de grant em runtime** (`INSTALL.md` do Clusters). Qualquer app novo nosso herda isso.

## 4. 🚨 Achado crítico — o nosso `su` é **KingoSU**, não SuperSU

A auditoria do [`joshfng/root-honda`](https://github.com/joshfng/root-honda/blob/main/AUDIT.md) (publicada em 2026-10-13, 14 dias antes desta varredura) descobriu que o `su` do upstream `codeage/root-honda` **não é** o do Chainfire — é **KingoSU**. Vale literalmente para o nosso binário também:

| Fato | Evidência |
|---|---|
| **SHA-256 bate exatamente** | `tooling/ota-build/bin/su` → `4f399ccd4c53bf1a12cbcc7f1b2bd23354491111358937c2da51d3355333fa84` — mesma string citada no AUDIT.md. |
| **Strings identificam KingoSU** | `strings` revela `--- KingoSU notice ---`, `KingoSU v%d.%s%d Copyright (C) 2012-2015 - KingoSu`, paths em `/data/data/com.kingouser.com/`, broadcast `-n "com.kingouser.com/.NativeAccessReceiver"`. |
| **Comportamento diferente do SuperSU** | A cada chamada de `su`, dispara `am broadcast -a com.kingouser.com.NativeAccess ... -n com.kingouser.com/.NativeAccessReceiver` com UID, comando, código. Como o manager `com.kingouser.com` **não** está instalado no HU, o broadcast é no-op — mas é um broadcast público que o ActivityManager registra. |
| **Veio do 2016PilotOneClick** | Mesmo hash do `su` do `jersacct/2016PilotOneClick`. O `codeage/root-honda` só o rebateou. |

**O que isso significa para o nosso projeto, concretamente:**

1. **Não é falha funcional.** O `su` funciona — o AutoOk v0.5.4 chama `su` continuamente e os taps acertam. O broadcast "no-op" é cosmético.
2. **Pode encher `logcat.events` com `am_broadcast`** sempre que o AutoOk tapar — o próprio bug do mudo (§17.15) deu a dica de que o buffer events é sensível a `am_*` enquanto o nosso watcher lê dele.
3. **Suposição anterior quebrada.** O `MAPA.md` dizia "Setuid root ARM. Vindo do `codeage/root-honda` (versão SuperSU-adjacent 2.78 simples)". **É falso** — é KingoSU, não SuperSU-adjacent.
4. **Correção já existe.** O `joshfng/root-honda` publica o `su` correto do Chainfire SR1 (SHA-256 `67e4d251a8173b82f643aae45e53c5265ef4178d8c68c48f0429b38e2471155d`) extraído do zip oficial `download.chainfire.eu`.

**Plano técnico recomendado** (não aplicado nesta sessão; só documentado):

1. Baixar o `armv7/su` do zip oficial Chainfire SR1 pela URL que o joshfng documenta.
2. Validar SHA-256 contra `67e4d251…`.
3. Substituir `tooling/ota-build/bin/su` e regerar o `build.py` do AutoOk.
4. **Validar no carro** antes do deploy em prod — qualquer troca de `su` muda o caminho de contexto SELinux no Android 4.2.2, e o `AvisoMatcher` do v0.5.4 depende do `su` seguir rodando no mesmo contexto que roda hoje.
5. Mudar o modo no `nefarious.sh`-like do pacote: hoje nosso updater-script usa `chmod 06755` (correto); o upstream `codeage/root-honda` usava `6777` (world-writable, grave). Nós já temos o certo.

Impacto no AutoOk atual (v0.5.4) **é zero** — o `su` serve o `input tap` sem falhar há meses. Mas quando o próximo rebuild do AutoOk sair (quando `build.py` com `chown`/`chmod` do busybox for aplicado, §17.18), **esta é a janela natural** para trocar o `su` também.

### 4.1 Atualização obrigatória no MAPA

A §10.2 do MAPA diz "SuperSU-adjacent 2.78 simples". Vou corrigir para "KingoSU `v*`, do upstream `jersacct/2016PilotOneClick` via `codeage/root-honda` — ver auditoria `joshfng/root-honda` AUDIT.md e §4 de `raio-x/08-github-landscape-2026-10-27.md`. Substituição pelo `su` Chainfire SR1 pendente".

## 5. opendbc / openpilot — tabela canônica de CAN para o nosso Civic

[`commaai/opendbc`](https://github.com/commaai/opendbc) traz, no diretório `opendbc/dbc/generator/honda/`:

- `honda_civic_touring_2016_can.dbc` e `honda_civic_hatchback_ex_2017_can.dbc` — **a mesma geração do nosso veículo**
- Comuns importados: `_honda_common.dbc`, `_gearbox_common.dbc`, `_steering_sensors_a.dbc`, `_steering_control_a.dbc`, `_nidec_common.dbc`, `_lkas_hud_5byte.dbc`, `_bosch_2018.dbc`

Isso coincide **exatamente** com os `.dbc` que o `CanDefinitions.java` do Clusters cita como fonte. Em `_honda_common.dbc` as 23 mensagens relevantes incluem:

```
BO_ 388 HYBRID_BRAKE_ERROR
BO_ 420 VSA_STATUS
BO_ 427 STEER_MOTOR_TORQUE
BO_ 464 WHEEL_SPEEDS
BO_ 490 VEHICLE_DYNAMICS
BO_ 547 BRAKE_HOLD_HYBRID_ALT
BO_ 597 ROUGH_WHEEL_SPEED
BO_ 777 CAR_SPEED
BO_ 780 ACC_HUD
BO_ 804 CRUISE
BO_ 1029 DOORS_STATUS
BO_ 1302 ODOMETER
```

**Para nós:** se um dia escrevermos um app Android nosso que consuma o `BcanListener`/`FcanListener` do `VehicleInfoManagerApService`, estes IDs 11-bit são o decoder de referência para interpretar o `type` que chega no `Bundle`. A documentação do próprio Clusters já reconhece que o middleware pré-decodifica os frames e entrega `int`/`Bundle`, não raw bytes — então usaríamos opendbc como fonte de verdade sobre **o que** o campo decodificado significa, não para decodificar nós mesmos.

## 6. Família Honda × plataforma Mitsubishi

A matriz `kristate/krackinfo` ajuda a enxergar o escopo real da nossa descoberta:

| Modelo Honda | SoC/device | DA version | Compat técnica |
|---|---|---|---|
| **Civic 10a geração 2016/2017** | `vcm30t30` (Tegra 3) | `MY17ADA` | **Nosso HU**; CR-V China, Avancier/URV usam o mesmo. |
| Pilot, Accord, NSX, Clarity, Ridgeline, Spirior | `koelsch` | `MY15ADA`/`MY16ADA` | Stack Mitsubishi ADA, chip diferente. Issue #13 do ic1101 é dessa família (Clarity). Nossas descobertas de app-level podem valer; nossas descobertas de bootloader/kernel não. |
| Unit Assy AVN | `h16` | SiRFSoC Android | Diferente. |

Combinado com a issue #29 (CR-V China `1.F198.60`), isso dá 3 confirmados compatíveis com nossos pacotes OTA (BR Civic, US Civic, China CR-V), e 6 famílias "primas" onde a análise lógica do app vale, com adaptações de hardware.

## 7. `cysin/honda_hacking_analysis` — fora do escopo, mas um sinal

16★, criado em 2021. O repo documenta o ecossistema **comercial pago** chinês (HondaHack, AutoHack, VinciCar — produtos que vendem "destravamento" do HU). Contém:

- Loaders nativos (`.so` + `.c`) e scripts de instalação.
- Chaves AES e lógica de licenciamento comercial.
- Caminho web (via navegador) de persistência.
- Writeup detalhado em [52pojie.cn/thread-1376274-1-1.html](https://www.52pojie.cn/thread-1376274-1-1.html).

**Deliberadamente não incluí** nesta nota nada do mecanismo específico desses tools. Serve só como sinal de que:

1. O mesmo HU é alvo há 4+ anos.
2. Há produtos comerciais explorando-o (vendidos no mercado chinês).
3. Nossa escolha de **publicar aberto** o fluxo EvilValet não introduz risco novo — o conhecimento já estava disponível em canais pagos.

## 8. Supply chain e discussão pública (writeup librick 2026-06-13)

Reflexo em `ahastudio/til` (coreano) + HN thread (342 pts). Pontos relevantes para o nosso projeto:

- A **testkey AOSP continua aceita** em pacotes oficiais de 2026. Librick validou com `MRC_EU_SW_v12_4.zip` baixado de fórum público.
- Honda usa fork Mitsubishi do AOSP; o problema é de **supply chain security review**, não do carro individual.
- "assinado ≠ assinatura verificada" (padrão em firmware comercial, muito citado na thread HN).
- `hnav` levantou dúvida pública sobre o HU ser gateway para outras ECUs e sobre CarPlay/Android Auto como vetor — nós estamos no HU, não escalamos para fora dele.
- Órgãos de governo começaram a tratar como ameaça formal (comentário `bigfatkitten`).

**O que isso muda para nós:** nada no plano técnico. **Confirma** que a janela EvilValet continua aberta e que a nossa escolha de usar `testkey` pro pacote OTA do DaLauncher (Fase 10) segue válida por tempo indeterminado.

## 9. O que ficou **fora** desta varredura

Deliberadamente não detalhei nem reproduzi aqui:

- Mecanismos de injeção, loaders nativos, cracks de licenciamento, cadeia completa de root remoto por navegador, ou chaves/credenciais usadas por tools comerciais chineses (AutoHack / VinciCar / HondaHack).
- APKs assinados dos produtos comerciais (nem o Honda Hack obfuscado via Tencent Legu que o `joshfng/root-honda` menciona em `packages/`).
- Qualquer coisa que facilite abusar de HUs de terceiros sem autorização do dono.

O que de código externo o projeto já consome está em `tooling/references/` via `setup.sh` (ic1101 Apache 2.0, root-honda, 2016PilotOneClick) — segue como está. Pode mudar: ver §4.

## 10. Impacto consolidado — o que vai pro código / docs

| # | Fonte | O que fazer | Onde |
|---|---|---|---|
| 1 | `joshfng/root-honda` AUDIT.md | **Documentar o KingoSU no MAPA §10.2** e abrir item no PENDENCIAS para troca pelo `su` Chainfire SR1 no próximo rebuild do AutoOk. | §4 desta nota, MAPA §10.2, PENDENCIAS |
| 2 | Clusters: TX codes do `IVehicleInfoManagerApService` + IDs B-CAN | Atualizar [`07-services-re.md §3`](07-services-re.md) com os TX codes e os IDs internos. Candidato pra Fase 9. | `07-services-re.md`, MAPA §13 |
| 3 | Clusters: `IAvApService` TX codes (`setMute`/`getVolume`/`getSource`) | Fecha a lacuna da RE §4 (áudio) sem precisar deodexar o `AvApService`. | `07-services-re.md §4` |
| 4 | ic1101 issue #6: Honda Hack binda `IVideoManagerApService` | Adicionar à lista de services candidatos à deodex futura. | PENDENCIAS |
| 5 | ic1101 issue #20: cadeia de USB mode via sysfs | Script opcional para ligar ADB sem combo físico (depois do deploy da Fase 10). | PENDENCIAS |
| 6 | ic1101 issue #29: CR-V China é mesma família | Matriz de compatibilidade ganha mais uma linha. | `nova-safra.md`, ROADMAP |
| 7 | opendbc: Civic Touring 2016 + Hatchback EX 2017 DBCs | Nota técnica: usar como oracle para interpretar o `type` do BcanListener. | `07-services-re.md §3`, PENDENCIAS |
| 8 | HondaHUDdiy PROTOCOL.md | Lição de bind "só com `package + action`"; usar com cuidado se formos binder sem `setComponent`. | guia interno quando chegarmos no app novo |
| 9 | Writeup librick 2026-06: testkey ainda aceita | Confirmação; nenhuma mudança operacional. | esta nota, não precisa mexer em código |

Os 33 projetos ficam catalogados aqui para quem retomar a parte de RE depois — a maioria é "ler README e seguir", só o §4 pede ação concreta.
