# Eficiência de compressão de vídeo: codec AV1 frente ao H.264

Código e resultados do Trabalho de Conclusão de Curso apresentado ao curso de Sistemas de Informação da Multivix Serra (2026).

Autores: Pedro Henrick Gineli de Souza, Fernando Gonçalves Nogueira e Pedro Henrique Dal'Col Queiroz.
Orientador: André Bessa da Silva.

O experimento comparou cinco configurações de codificação em oito sequências 4K sem compressão:

| Configuração | Codificador | Execução | Preset |
|---|---|---|---|
| x264 medium | libx264 (H.264) | CPU | medium |
| x264 veryslow | libx264 (H.264) | CPU | veryslow |
| NVENC H.264 | h264_nvenc | GPU | p7 |
| SVT-AV1 | libsvtav1 (AV1) | CPU | 6 |
| NVENC AV1 | av1_nvenc | GPU | p7 |

Foram medidos a taxa de bits, o tempo e a energia de codificação e a qualidade visual por dez métricas objetivas. A partir desses dados, foram calculados o BD-Rate, a economia em iso-qualidade (VMAF 93 e 95), um teste de hipótese e uma projeção de custos de armazenamento, tráfego e codificação.

## Conteúdo do repositório

```
.
├── run_pipeline.py            Execução do experimento (codificação, métricas, BD-Rate, relatórios)
├── analise_complementar.py    Análises usadas no texto do TCC que não são geradas pelo run_pipeline.py
├── config.json                Codificadores, grade de CRF/CQ, amostras, testes e premissas de custo
├── requirements.txt
├── pipeline/                  Módulos do experimento
│   ├── encoder.py             Codificação com FFmpeg e medição de tempo e energia
│   ├── monitor.py             Telemetria de CPU e GPU (LibreHardwareMonitor e nvidia-smi)
│   ├── metrics.py             VMAF, VMAF NEG, PSNR, SSIM, MS-SSIM, XPSNR, SSIMULACRA2, Butteraugli e CVVDP
│   ├── bjontegaard.py         BD-Rate (PCHIP), interpolação em iso-qualidade e teste de Wilcoxon
│   ├── economics.py           Projeção de custos e ponto de equilíbrio
│   ├── siti.py                Informação espacial e temporal (ITU-T P.910)
│   ├── decode.py              Teste de decodificação (software e NVDEC)
│   ├── crops.py               Recortes visuais ampliados
│   ├── plots.py               Gráficos
│   ├── reporter.py            Relatório em Markdown, Excel, CSV e JSON
│   ├── hardware.py            Registro do ambiente de hardware e software
│   ├── synthetic.py           Sequências sintéticas para o teste rápido de validação
│   └── utils.py               Hash SHA-256, registro de comandos e tamanho do fluxo de vídeo
├── samples/                   Vazia: as sequências devem ser obtidas nas fontes originais
└── output/                    Resultados do experimento
    ├── relatorio_tcc.md       Relatório com todas as tabelas geradas pelo pipeline
    ├── analise_complementar.md Tabelas geradas pelo analise_complementar.py
    ├── resultados_tcc.xlsx    As mesmas tabelas em planilha
    ├── resultados_completos.json Todos os dados medidos (base para recalcular qualquer tabela)
    ├── comandos_executados.jsonl Cada comando do FFmpeg e do FFVship executado, com data e hora
    ├── csv/                   Tabelas em CSV
    ├── metrics/               Saídas por quadro do libvmaf, do XPSNR e do FFVship
    ├── graficos/              Curvas taxa-distorção, velocidade, estabilidade temporal, SI x TI, custos
    ├── recortes/              Recortes visuais de cada sequência em qualidade próxima de VMAF 93
    └── encoded/               Vazia: os 259 vídeos codificados (cerca de 19 GB) não foram incluídos
```

A numeração das tabelas em `relatorio_tcc.md` é a do relatório gerado pelo código e não coincide com a numeração do texto do TCC.

## Onde encontrar cada resultado do TCC

| Resultado no TCC | Arquivo |
|---|---|
| Complexidade das sequências (SI e TI) | `output/relatorio_tcc.md` (Tabela 2), `output/graficos/grafico5_dispersao_siti.png` |
| BD-Rate VMAF por sequência e sobreposição das curvas | `output/relatorio_tcc.md` (Tabela 4) |
| Teste de Wilcoxon com correção de Holm | `output/relatorio_tcc.md` (Tabela 4b) |
| BD-Rate por métrica de qualidade | `output/analise_complementar.md` (seção 1) |
| Correlação de Spearman entre SI e BD-Rate | `output/analise_complementar.md` (seção 2) |
| Taxa de bits, tempo e energia em iso-qualidade | `output/relatorio_tcc.md` (Tabelas 5, 5b e 6), `output/analise_complementar.md` (seção 3) |
| Estabilidade temporal do VMAF por quadro | `output/analise_complementar.md` (seção 3), `output/graficos/grafico4_*` |
| Velocidade de codificação e variação entre repetições | `output/relatorio_tcc.md` (Tabela 3), `output/analise_complementar.md` (seção 4) |
| Projeção econômica e ponto de equilíbrio | `output/relatorio_tcc.md` (Tabelas 5 e 6) |
| Sensibilidade ao volume de audiência | `output/analise_complementar.md` (seção 5) |
| Presets do SVT-AV1 | `output/relatorio_tcc.md` (Tabela 8) |
| Síntese de grão | `output/resultados_completos.json` (linha "SVT-AV1 (Film Grain 8)") |
| Decodificação | `output/relatorio_tcc.md` (Tabela 7) |
| Curvas taxa-distorção de todas as métricas | `output/graficos/grafico1_rd_*`, `output/graficos/grafico2_rd_psnr_*` |
| Recortes visuais | `output/recortes/` |

## Ambiente experimental

| Item | Especificação |
|---|---|
| CPU | AMD Ryzen 7 9800X3D (8 núcleos, 16 threads) |
| GPU | NVIDIA GeForce RTX 4070 SUPER, 12 GB (NVENC de 8ª geração, Ada Lovelace), driver 621.01 |
| Memória | 32 GB DDR5 5600 MT/s |
| Sistema operacional | Windows 11 Pro 64 bits (build 26300) |
| FFmpeg | 9.0.1 (build full de gyan.dev) |
| Bibliotecas | x264 core 165 r3223, SVT-AV1 v4.2.0-72-gae2658e53, dav1d 1.5.4, libvmaf v3 |
| Métricas por GPU | FFVship 5.1.0-a |
| Medição de energia da CPU | LibreHardwareMonitor (sensor de potência do pacote) |

O experimento foi executado em 27/10/2026. Tempos e energia dependem do hardware e não devem ser idênticos em outra máquina; taxa de bits e qualidade tendem a se repetir com as mesmas versões das bibliotecas.

## Requisitos para reproduzir

1. Python 3.10 ou superior e as dependências:

   ```
   pip install -r requirements.txt
   ```

2. FFmpeg no PATH, compilado com `libx264`, `libsvtav1`, `libdav1d`, `libvmaf` e o filtro `xpsnr`, e com suporte a NVENC e NVDEC. As builds "full" de https://www.gyan.dev/ffmpeg/builds/ atendem a esses requisitos no Windows.

3. GPU NVIDIA com codificação AV1 por hardware (arquitetura Ada Lovelace ou mais recente) e `nvidia-smi` no PATH. Sem ela, remova as configurações `h264-nvenc` e `nvenc-av1` de `config.json` (e as comparações que as usam) antes de executar.

4. FFVship (https://github.com/Line-fr/Vship), para SSIMULACRA2, Butteraugli e CVVDP. O executável deve ficar em `tools/FFVship/FFVship.exe` ou no PATH.

5. LibreHardwareMonitor (https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) aberto durante a execução, com o servidor web ativado na porta 8085 (Options > Remote Web Server). Sem ele, a energia da CPU é estimada por TDP x utilização, o que não corresponde ao método usado no TCC.

## Obtenção das sequências de vídeo

As sequências não são redistribuídas neste repositório. Elas devem ser baixadas das fontes originais e convertidas para Y4M na pasta `samples/`, com os nomes definidos em `config.json`.

| Arquivo em `samples/` | Sequência | Fonte |
|---|---|---|
| amostra1_cityalley.y4m | CityAlley, 3840x2160, 50 fps, 8 bits, 600 quadros | UVG Dataset |
| amostra2_flowerfocus.y4m | FlowerFocus | UVG Dataset |
| amostra3_flowerkids.y4m | FlowerKids | UVG Dataset |
| amostra4_flowerpan.y4m | FlowerPan | UVG Dataset |
| amostra5_racenight.y4m | RaceNight | UVG Dataset |
| amostra6_riverbank.y4m | RiverBank | UVG Dataset |
| amostra7_twilight.y4m | Twilight | UVG Dataset |
| amostra8_crowdrun.y4m | crowd_run_2160p50, 500 quadros | Xiph.org Video Test Media |

- UVG Dataset (Mercat; Viitanen; Vanne, 2020): https://ultravideo.fi/dataset.html. Usar as versões 3840x2160, 50 fps, 8 bits, YUV 4:2:0. As sequências usadas são de propriedade da Digiturk e licenciadas sob Creative Commons Attribution-NonCommercial 3.0 (arquivo de copyright distribuído com cada sequência).
- Xiph.org Video Test Media: https://media.xiph.org/video/derf/

Conversão de uma sequência do UVG (arquivo `.yuv`) para Y4M, sem perdas:

```
ffmpeg -f rawvideo -pix_fmt yuv420p -s:v 3840x2160 -r 50 -i CityAlley_3840x2160_50fps_8bit.yuv -f yuv4mpegpipe samples/amostra1_cityalley.y4m
```

A CrowdRun já é distribuída em Y4M e foi apenas renomeada para `amostra8_crowdrun.y4m`.

Hashes SHA-256 dos arquivos usados no experimento, para conferência (o pipeline os recalcula e registra em `resultados_completos.json`):

| Arquivo | SHA-256 |
|---|---|
| amostra1_cityalley.y4m | 030b4fd9c6fd6fd6e1977065993aa43824b4a27764c535785e1427241c2d69cc |
| amostra2_flowerfocus.y4m | 61577f858d57769d62634a21f4266320ce45a99063c2e83df2bf4d47df6c2abc |
| amostra3_flowerkids.y4m | e18b451dff2582bf70f5b143e393391a5c28223e595fbf0a4eda947a53c40956 |
| amostra4_flowerpan.y4m | ce7da73a2e73d13dc78a79a8944669ff2fb78f0f636c024bdc69556bb9538872 |
| amostra5_racenight.y4m | fb1a543ab8100f8dfca4e2bd670fa255416da8b55ca1f07331627d554c77c90c |
| amostra6_riverbank.y4m | 575c16b795b57866d980ebd8bbda0d976435e9e503de3b1ea46de58b1197cf6e |
| amostra7_twilight.y4m | ba5eda3b947d69260296aced147ffdb26cceaf6b1fefa894914ba5a9e6c3e434 |
| amostra8_crowdrun.y4m | 6a6bb03cdf499000a4c79fb0a5cd8dce6fef11830d9467be6b06bf62dfb5e1eb |

O hash depende do cabeçalho Y4M escrito pelo FFmpeg; uma versão diferente pode gerar um hash diferente com o mesmo conteúdo de vídeo.

## Execução

Teste rápido de validação do ambiente, com sequências sintéticas (não sobrescreve `output/`):

```
python run_pipeline.py --quick-test
```

Experimento completo, em duas fases, como executado no TCC (registro em `output/comandos_executados.jsonl`):

```
python run_pipeline.py --mode quality --skip-metrics --test-presets --test-grain
python run_pipeline.py --recompute-metrics --test-decode --generate-crops
python analise_complementar.py
```

A primeira fase codifica os 259 arquivos e mede tempo e energia (cerca de 7 horas no ambiente descrito acima). A segunda calcula as métricas de qualidade de todos os arquivos, gera os recortes, executa o teste de decodificação e produz as tabelas (cerca de 6 horas). Também é possível executar tudo de uma vez, com as métricas calculadas logo após cada codificação:

```
python run_pipeline.py --mode quality --test-presets --test-grain --test-decode --generate-crops
```

Recalcular tabelas e gráficos a partir de `output/resultados_completos.json`, sem codificar novamente (requer as sequências em `samples/`):

```
python run_pipeline.py --skip-encoding
```

O `analise_complementar.py` usa apenas os arquivos já presentes em `output/` e pode ser executado logo após clonar o repositório, sem as sequências e sem FFmpeg.

## Principais decisões metodológicas

- Varredura por qualidade constante (CRF no x264 e no SVT-AV1, CQ no NVENC) em seis níveis por codificador, calibrados para cobrir VMAF de aproximadamente 88 a 99.
- GOP fixo de 2 segundos (100 quadros), detecção de corte de cena desativada e 8 bits em todos os codificadores.
- No NVENC, taxa-alvo anulada e teto de taxa de 800 Mb/s, para evitar o limite implícito do codificador nos níveis de maior qualidade.
- Três repetições por codificação; o tempo é o tempo decorrido do processo do FFmpeg.
- Energia líquida: potência da CPU (LibreHardwareMonitor) e da GPU (nvidia-smi), amostradas a cada 0,25 s, menos a potência em repouso, multiplicadas pelo tempo.
- Taxa de bits efetiva: soma dos pacotes de vídeo dividida pela duração.
- BD-Rate com interpolação PCHIP sobre o logaritmo da taxa de bits; comparações com sobreposição das curvas inferior a 50% são excluídas.
- Teste de hipótese: Wilcoxon unilateral exato sobre o BD-Rate VMAF, com H0: mediana >= -30%, correção de Holm e alfa de 5%.

A descrição completa está na seção de metodologia do TCC.

## Como citar

SOUZA, Pedro Henrick Gineli de; NOGUEIRA, Fernando Gonçalves; QUEIROZ, Pedro Henrique Dal'Col. Eficiência de compressão de vídeo: codec AV1 frente ao H.264. Trabalho de Conclusão de Curso (Bacharelado em Sistemas de Informação) - Multivix Serra, Serra, 2026.
