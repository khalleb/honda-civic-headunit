# Fase 1 — Reconhecimento no carro, sessão 2 (2026-10-15 à tarde)

Segunda ida ao carro no mesmo dia. Objetivo primário era habilitar ADB via passcord com as 3 variações do `docs/fase3-adb/passcord-pesquisa.md`. Como todas falharam, aproveitamos a janela para explorar os menus de serviço que a sessão 1 (manhã) não abriu.

Continuação do `achados-2026-10-15.md`.

## 1. Resultado das 3 tentativas de passcord

Pré-condição constante: Settings → Sobre o dispositivo → 7 toques rápidos no `Número da versão` disparam o toast `Please enter a passcord` (confirmado nas 3 tentativas, então o detector dos 7 toques funciona).

| # | Variação | Hipótese | Resultado |
|---|---|---|---|
| 1 | Sequência 1-4-2-3 (Modelo → Kernel → Android → Baseband) com cadência ~3 toques/s, iniciada antes do toast sumir | 2.2 (timing engolindo os toques) | ❌ nada acontece além do toast |
| 2 | Mesma sequência com cadência 1 toque/s, aguardando o toast quase sumir | 2.2 variante lenta | ❌ nada acontece |
| 3 | Sequência do vídeo brasileiro (Kernel → Modelo → Build → Status) com cadência 1 toque/s | 2.1 variante (ordem alternativa do BR) | ❌ nada acontece |

Combinadas com as tentativas da sessão 1 (sequência XDA 1-4-2-3 em cadência padrão + variação do vídeo), **5 variações distintas, todas falharam**. A hipótese 2.4 (`1.F187.16` BR é pós-patch) **se confirma** — a rota do passcord via toques no Settings do Android está morta nessa safra.

Isso bate com os relatos públicos:

- A doc do `@codeage` explicitamente diz "Honda has changed the password to enter the developer mode in new vehicle models so the old method described in this thread may not work any longer".
- O próprio `@codeage` começou a cobrar US$25 pelo "web-based installation" porque muita gente parou de conseguir a sequência manual.
- Nossa unidade (`1.F187.16`, build do kernel de Apr/2016) está no grupo pós-patch.

**Status final da rota passcord via Settings:** encerrada. Próximas rotas a avaliar estão na seção 3 do `docs/fase3-adb/passcord-pesquisa.md`.

## 2. Estrutura detalhada do Self-Diagnosis Mode

Combo correto do EXL BR (ver 4.1a do KB): `DAY/NIGHT + AUDIO + MENU` por 2s com áudio off.

```
Self-Diagnosis Mode (fase 1 sessão 1)
└─ Detail Information & Setting
   ├─ Monitor Check            → testes de display (sessão 2)
   ├─ Unit Check               → 18 componentes (sessão 2)
   ├─ Audio Check              → 1 teste (sessão 2)
   ├─ Guideline Setup          → 2 câmeras (sessão 2)
   ├─ Functional Setup         → coberto na sessão 1
   ├─ B-CAN                    → RX Error ~20+ sinais (sessão 2)
   ├─ F-CAN                    → TIME OUT 2 sinais sem motor (sessão 2)
   ├─ Version                  → inventário de pacotes (sessão 1)
   ├─ Vehicle status           → valores decodificados ao vivo (sessão 2)
   └─ GPS Information          → status GPS (sessão 2)
```

### 2.1 Monitor Check

7 testes de display (todos read-only de UI):

```
RGB Colour · Grey Tone · White Raster · Black Raster ·
Colour Pattern · Touch Panel Check · Touch Panel Adjustment
```

Nada acionável para dev mode. Útil se precisar validar display defeituoso.

### 2.2 Unit Check — componentes mapeados

18 componentes individuais com status health check. Lista scrollada do topo ao fim:

```
HMI Unit · F-CAN · B-CAN · USB · Vehicle Status · HFT/Mic ·
Hard Key · Error History · Rear wide camera · LaneWatch ·
Remote tuner · CD · Centre display · Meter Display · GPS Antenna ·
Traffic Information · Gyro Sensor · A/C
```

**Nenhum componente** com nome `Developer`, `ADB`, `Debug`, `USB mode`, `Service`, `Factory`, `Dealer`, `Diag`. Confirma que a rota "dev mode via Unit Check" está fechada.

Observação útil para o KB: **"USB"** aparece como componente testável no Unit Check — provavelmente roda um self-test que pode ser interessante explorar numa visita futura (não entrei por segurança nessa visita, pois a doc dessa família de testes pode mudar modos). "Error History" também pode render dados valiosos sobre erros persistentes.

### 2.3 Audio Check

Só uma opção: `Speaker Check`. Teste read-only. Não acionável.

### 2.4 Guideline Setup

Calibração de guias das câmeras:

```
Corner Camera · Rear wide camera
```

Não aplicável.

## 3. B-CAN RX ERROR — Lista semântica de sinais consumidos pela central

**Achado principal desta sessão.** A tela B-CAN mostra tabela de status "RX ERROR" com nomes semânticos dos sinais que a central escuta. O KB (seção 4bis) lista isso como "lacuna documental: não há lista pública de IDs CAN do infotainment do G10" — essa tela entrega **os nomes semânticos** (não IDs numéricos) para o EXL BR.

Status de cada sinal:

- **OK** (verde): sinal recebido recentemente, dentro de janela de watchdog
- **NG amarelo**: sinal recebido mas com warning (atraso ou valor fora de intervalo)
- **NG vermelho**: time-out (não recebido na janela esperada)

### 3.1 Lista completa (ordem de aparição no scroll)

```
VSPNE       → Vehicle Speed             [OK]
AT          → Automatic Transmission    [OK]
ILLUMI      → Illumination (farol→dim)  [OK]
ST_SW_PAD   → Steering Wheel Switch Pad [OK]
VINNO       → VIN Number                [OK]
ACSTATE     → AC State                  [NG — AC desligado, esperado]
STRG_ANG    → Steering Angle            [OK]
ODO_TRIP    → Odometer / Trip           [OK]
TRICOM1     → Trip Computer 1           [OK]
TRICOM2     → Trip Computer 2           [OK]
TRICOM3     → Trip Computer 3           [OK]
TRICOM4     → Trip Computer 4           [OK]
PARKSENS    → Parking Sensors           [NG amarelo — sem obstáculo, esperado]
METER_RMD   → Meter Reminder            [OK]
ACFB        → AC Feedback               [NG — AC off, esperado]
HLSW_BCM/ICU → Headlight Switch         [OK]
MICU_BCM/ICU → Multiplex ICU            [OK]
MET_CUSTOM  → Meter Custom              [OK]
MAINTENANCE → Maintenance reminders     [OK]
```

### 3.2 Observações

- **Os `NG` são coerentes com o estado do carro parado** (AC off, sem obstáculo nos sensores de ré). Não indicam falha real.
- Nenhum sinal específico de infotainment aqui (ex.: fonte de áudio atual, volume) — isso provavelmente trafega em barramento interno da própria HMI, não via CAN.
- **ST_SW_PAD** confirma que os botões do volante chegam na central via B-CAN — útil para projetos de remapping (algumas unidades Honda permitem redefinir ação de botões).
- **VINNO** confirma que o VIN é transmitido via B-CAN pelo cluster, não é fixo no firmware da central.

### 3.3 F-CAN sem motor

Com motor desligado, F-CAN mostra apenas:

```
ENG1        → Engine 1                  [NG vermelho — time out]
EPB1        → Electronic Parking Brake  [NG amarelo]
```

E a mensagem na tela: `Must have engine running for this test`. Documentado: **F-CAN só é observável com motor rodando**; para a próxima visita, se quisermos mapear F-CAN precisamos deixar o motor em marcha lenta num local arejado.

## 4. Vehicle Status — valores decodificados ao vivo

Nome dos campos (valores omitidos por conter dado identificável — o VIN):

```
VSP                      → Vehicle Speed Pulse
BACK                     → marcha ré (0/1)
IG                       → Ignition on (0/1)
C_METER_ILL_STATUS       → status da iluminação do painel
C_METER_ILL_CANCEL       → bit de cancel
C_METER_ILL_STEP         → passo atual de dim do painel (0-N)
Speed                    → velocidade decodificada em km/h
TV-PARK                  → trava DD para TV com carro parado (0/1)
NAVI-PARK                → trava DD para nav com carro parado (0/1)
Current received VIN     → VIN recebido do CAN agora
Initial registered VIN   → VIN que a central registrou na primeira inicialização
Last registered VIN      → VIN mais recente registrado
```

Observações:

- **TV-PARK e NAVI-PARK** confirmam a existência das travas DD VSS (seção 3 do KB, trava "b"). O menu "Operation Restriction" (dentro de Functional Setup → Other, sessão 1) controla essas duas flags.
- **Initial / Current / Last registered VIN** — a central guarda histórico de qual VIN apareceu. Isso é usado como **antifurto** (se a central detectar um VIN diferente, pode travar). Possível vetor de problema se trocar a central entre carros.
- **Com motor desligado (IG=0)**, `Current received VIN` fica `00------` enquanto `Initial registered VIN` persiste.

## 5. GPS Information

Estrutura da tela (valores omitidos — geolocalização):

```
Number of Satellites    → ícones + contagem
Measuring Status        → 2D / 3D / No Fix
Time                    → UTC
Current Position        → lat / lon
Altitude                → m
In Use / Search         → mapa de céu com satélites ativos
```

Tempo é **UTC**, não local — para converter: `BRT = UTC - 3`. Isso é relevante se quisermos sincronizar relógio do nosso APK auto-OK com o GPS (não é o caso agora, mas vale catalogar).

## 6. Teste do cabo USB — resultado + ressalva

Pluguei o cabo (USB-A na central, USB-C no notebook Fedora) em modo "central ACC, menu normal, áudio ligado em qualquer fonte":

```
lsusb                      → sem linha nova (idêntico à linha base)
journalctl -k -n 40        → sem evento USB nos últimos minutos
adb devices                → lista vazia
```

**Conclusão imediata:** sem dev mode habilitado, a central em modo host USB e o PC em modo host USB resultam em conflito host-host; nenhum negocia como device. Esperado.

**Ressalva importante levantada pelo dono:** o cabo pode **não ter data lines** (ser "só carrega"). Nesse caso o teste é inconclusivo — mesmo que a central fosse em modo device, nada enumeraria porque os pinos D+/D- do USB não chegam.

**Para falsificar essa ressalva** (fazer antes da próxima tentativa):

- Pluga o cabo entre o notebook e um pendrive, com o pendrive do lado USB-A e o notebook do lado USB-C.
- Se o notebook monta o pendrive e consegue listar os arquivos, o cabo tem data lines (a conclusão da sessão fica firme).
- Se nada acontece, o cabo é "só power" — a conclusão de "central engole o cabo" não vale, precisa cabo com data e testar de novo.

## 7. Dados para o KB consolidar

Edits a aplicar no `central-multimidia-civic-g10-kb.md`:

- **Seção 4bis** (CAN bus): adicionar os ~20 sinais B-CAN mapeados; adicionar nota sobre F-CAN precisar motor on; adicionar flow do Vehicle Status.
- **Seção 4.4** (dev mode): fechar definitivamente a rota do passcord via Settings do Android; apontar para o `docs/fase3-adb/passcord-pesquisa.md` para rotas abertas restantes.
- **Nova subseção dentro de 4.1a**: estrutura detalhada dos sub-menus de Detail Information & Setting.
- **Seção 7** (perguntas em aberto): registrar que a rota do passcord está encerrada; adicionar nova pergunta sobre o teste do cabo.

## 8. Fontes

- Doc interno sessão 1: `achados-2026-10-15.md`
- Doc interno passcord: `../fase3-adb/passcord-pesquisa.md`
- Observação do dono sobre data lines do cabo: conversa interna 2026-10-15 após o teste no carro
