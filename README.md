# Lab de SOC — Wazuh + Zabbix + GLPI

Laboratório de operações de segurança que integra três ferramentas de código aberto num fluxo único: **detecção → resposta → registro**. Um alerta de segurança ou de infraestrutura vira, sozinho, um chamado classificado no service desk.

Rodando inteiramente em uma VM de **5 GB de RAM**, custo zero de licenciamento.

![arquitetura](docs/arquitetura.png)

---

## A ideia

A maioria dos labs de SIEM para em "instalei o Wazuh, olha o dashboard". Detecção sem tratativa é log caro. Este projeto fecha o ciclo:

- **Wazuh** detecta o evento, correlaciona e responde (bloqueio de IP no firewall)
- **Zabbix** cobre disponibilidade e capacidade
- **GLPI** recebe os dois como chamado, com categoria e urgência definidas na origem
- Um operador analisa, resolve e registra a ação preventiva

## Stack

| Ferramenta | Versão | Papel |
|---|---|---|
| Wazuh | 4.14.7 | SIEM / XDR — detecção, FIM, resposta ativa |
| Zabbix | 7.0 LTS | Monitoramento de disponibilidade |
| GLPI | 10.0.26 | Service desk (destino das integrações) |
| Docker + Ubuntu Server | 24.04 | Base do laboratório |

## O que este repositório contém

- `core/`, `zabbix/`, `wazuh/` — os arquivos de composição e configuração
- `integrations/` — o script Python que liga o Wazuh ao GLPI e o webhook JavaScript que liga o Zabbix ao GLPI
- `wazuh/local_rules.xml` — regra de correlação própria (força bruta SSH)
- `docs/` — relatórios técnicos de cada uma das cinco fases

## Como funciona a integração

**Wazuh → GLPI:** o módulo `integrator` executa um script Python a cada alerta que satisfaz o filtro por `rule_id`, abrindo um chamado via API REST. O filtro aponta para regras específicas — incluindo a de correlação — para gerar um chamado por incidente, não por evento.

**Zabbix → GLPI:** um *media type* do tipo webhook, em JavaScript nativo, executado pelo próprio servidor Zabbix. Credenciais em macro protegida, sem depender de nada instalado no container.

## Resultados

- 1.149 eventos processados em um período de teste, com 2 incidentes de nível 12 destacados
- Bloqueio automático de origem em ataque de força bruta, aplicado **durante** o ataque
- Detecção mapeada ao framework MITRE ATT&CK
- Chamados de segurança e de infraestrutura convergindo no mesmo service desk, separados por categoria

## Cinco fases documentadas

| Fase | Tema | Relatório |
|---|---|---|
| 1 | Host, GLPI e API REST | [docs/relatorio-fase1.pdf](docs/relatorio-fase1.pdf) |
| 2 | Zabbix, agentes e triggers | [docs/relatorio-fase2.pdf](docs/relatorio-fase2.pdf) |
| 3 | Wazuh, FIM e regra de correlação | [docs/relatorio-fase3.pdf](docs/relatorio-fase3.pdf) |
| 4 | Integração das três ferramentas | [docs/relatorio-fase4.pdf](docs/relatorio-fase4.pdf) |
| 5 | Dashboards e validação por simulação | [docs/relatorio-fase5.pdf](docs/relatorio-fase5.pdf) |

## Lições registradas

O trabalho difícil não foi instalar as ferramentas. Foi decidir o que vira chamado, o que é ruído e onde a resposta precisa ser automática. Os relatórios documentam os problemas reais encontrados — dimensionamento de disco, consumo sem limite de módulos, permissões de execução, e a amplificação de chamados quando uma regra dispara em massa — porque é neles que está o aprendizado.

---

*Projeto de estudo desenvolvido por Kauan Trinchetti. As credenciais e tokens exibidos em qualquer captura de tela dos relatórios foram regenerados após a documentação.*
