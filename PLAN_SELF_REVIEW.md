# Revisão crítica dos planos Amanda TFG BIM

**Data:** 2026-09-15. **Escopo:** os quatro Markdown indicados, materiais locais de apoio e ZIP recebido durante a revisão.

**Conclusão:** revisão documental concluída com correções de estrutura, fontes e contratos. O antigo “PASS pronto para execução” foi retirado. Implementação, instalação de provedores, testes do software do agente e validação real no Revit: **NOT_RUN**. A revisão estática não comprova viabilidade integral da automação.

## 1. Material examinado

- Leitura dos quatro Markdown e comparação com `amanda-tfg-bim-agent-superpowers-plan.zip`.
- Extração somente leitura dos 13 PDF/DOCX/XLSX disponíveis, com páginas, parágrafos, tabelas, células e fórmulas. Leitura focal das partes relacionadas a programa, tipologia, terreno, normas, cálculos e entregas; não foi uma revisão integral do conteúdo acadêmico nem da diagramação de todos os arquivos.
- Inventário dos 21 arquivos de `TFG_Amanda_2026`; inspeção do cabeçalho/unidades do IFC HIPÓTESE. Sem abertura em Revit, avaliação integral da geometria ou execução de HTML.
- Documentação primária de Autodesk, Horizun, RevitCortex, Blender MCP e Shapely; conferência local de `codex mcp add --help`. Nenhuma instalação ou compilação de provedor.

Evidências: [ZIP](docs/review/archive-comparison.json), [checagem inicial](docs/review/validation-before.json), [checagem final](docs/review/validation-after.json) e [handoff](docs/notes/2026-09-15-revisao-planos-handoff.md).

## 2. Estrutura real e correção do diagnóstico inicial

Inicialmente havia quatro Markdown soltos na raiz, com instruções apontando para `docs/superpowers`. O ZIP recebido depois contém o mestre e nove planos separados. Os quatro documentos coincidem byte a byte com os originais da raiz, as dez seções correspondem ao COMBINED e os 15 hashes declarados conferem. Portanto, os filhos não faltavam no pacote original; faltavam na disposição inicial da pasta.

A revisão mantém os quatro documentos da raiz como canônicos e gera dez arquivos por fase em `docs/superpowers/plans/`. São derivados do COMBINED, com origem e links corrigidos. Editar o combinado e regenerar evita divergência. O ZIP original permanece preservado; o pacote revisado tem nome próprio.

## 3. Achados e correções

| ID | Prioridade | Problema | Correção |
|---|---|---|---|
| R01 | Alta | Entrada pressupunha outra disposição dos arquivos | Links reais, âncoras, filhos gerados e distinção pasta/ZIP |
| R02 | Alta | Approved/PASS confundiam revisão com aprovação/execução | REVISED_DOCUMENT, REVIEW_ONLY, NOT_RUN e aprovação arquitetônica separada |
| R03 | Crítica | Só dois PDFs e programa conflitante ignorado | Inventário multimodal; PROGRAM_BASELINE entre 20 pessoas e hipótese de 42 |
| R04 | Alta | Documento transformava afirmação em fato aceito | verification_status e adoption_status; hipótese documentada continua hipótese |
| R05 | Alta | Área de 24.135 m² e quatro frentes fixadas sem conciliação | SITE_BOUNDARY/SITE_OCCUPANCY, polígono/norte calibrados e premissa de realocação |
| R06 | Alta | Apoios chamados verificação podiam alimentar normas automaticamente | Fonte primária, vigência, mapa/anexo e aplicabilidade antes da restrição |
| R07 | Alta | Revit/SDK bloqueavam também ingestão e solver | Gates por ramo; 03 após 01 e 04 sem dependência Revit |
| R08 | Alta | Segurança/continuidade chegavam depois das instalações | 07A antes de 02; 07B para integração após 06; grafo acíclico |
| R09 | Alta | APS só após GOLDEN, embora pudesse resgatar bloqueios anteriores | Exceção de avaliação em sandbox sem transformar gate local em PASS |
| R10 | Alta | Teste CLI só rodava depois da implementação | RED comportamental primeiro; stubs encerram com código 2 |
| R11 | Alta | Replace atômico ainda permitia perder atualizações | Lock, revision/CAS, temporário único, fsync e recuperação |
| R12 | Crítica | Lock por worktree não impede outro worktree | Recurso compartilhado, fencing, identidade e reconciliação |
| R13 | Crítica | Registry aceitava PASS sem evidências/build | Hashes, tested_scope, tool_schema_hash e persistência na promoção |
| R14 | Alta | C# via Cortex parecia independente do próprio Cortex | transport_provider e domínio de falha explícitos |
| R15 | Alta | Aprovação desde R01 impedia massas antes da seleção | CONCEPT_ONLY até R04, SYNTHETIC_LAB e approval_hash na produção detalhada |
| R16 | Crítica | Timeout podia repetir escrita ainda ativa | Journal, claim/record-result, IN_DOUBT e reconciliação |
| R17 | Alta | BIM build não correspondia ao executor descrito | CLI plan/verify-plan/claim/record-result e fronteira MCP explícita |
| R18 | Alta | Proteção só por palavras no nome do arquivo | Allowlist, identidade, originais protegidos e testes de escapes |
| R19 | Alta | Snapshot podia expor segredos ou perder restauração ao ser redigido | Backup privado íntegro e relatório sanitizado separados |
| R20 | Alta | Worktree tratado como isolamento de add-in/config global | Distingue código de instalação compartilhada; sandbox/manutenção própria |
| R21 | Alta | Conversão metros/pés ignorava unidade do MCP | Unidade por ferramenta, UnitUtils e teste de conversão dupla |
| R22 | Alta | Polígonos de salas podiam duplicar paredes/áreas | Topologia compartilhada, área líquida/bruta e reconsulta após R08 |
| R23 | Alta | Validador de salas rejeitaria a macroescala | Validação MACRO/BLOCK/ROOM e NOT_EVALUATED |
| R24 | Alta | Seed sozinho prometia determinismo/diversidade | Worker único, budget determinístico, solver status e deduplicação |
| R25 | Alta | Scores sem direção/unidade/normalização | Contratos de métricas e tratamento transparente de ausências |
| R26 | Alta | Adjacência podia ser tomada como rota acessível | Grafo derivado de portas, circulação, obstáculos e permissões |
| R27 | Alta | GOLDEN selado antes dos relatórios | Staging completo, hashes, revisão visual e publicação sem sobrescrita |
| R28 | Alta | Limitação de topografia/norma podia parecer conclusão final | STUDY/FINAL e TFG_COMPLETE separado do release técnico |
| R29 | Média | SDK genérico, primeiro/mais novo executável e versões flutuantes | Pré-requisito do commit escolhido, manifestos e locks reproduzíveis |
| R30 | Média | Adiamento/suspensão fora dos enums | SUSPENDED em TaskStatus; DEFERRED_OPTIONAL fora de CapabilityStatus |
| R31 | Alta | Entregas acadêmicas fora da conclusão | Registro de responsáveis/evidências para caderno, visitas, memoriais e defesa |
| R32 | Média | Ler JSON era chamado verificar hashes | release verify recalcula integridade dos artefatos |

## 4. Decisões do usuário e pesquisa delegada ao agente

| Decisão | Evidência disponível | Efeito enquanto pendente |
|---|---|---|
| Programa/capacidade | PDF: 20 pessoas; XLSX Premissas!C15:C16 e C27: hipótese de 42 | PROGRAM_BASELINE = RESOLVED: usuário escolheu 20 pessoas conforme o PDF em 2026-09-15; planilha de 42 não adotada |
| Tipologia/sigilo | Caderno e apoio discutem casa-abrigo/centro e visibilidade | Agente pesquisa e adota política justificada, revisável por Amanda depois |
| Lote/norte/confrontações | Área textual, ilustrações e hipóteses | Agente pesquisa fontes e prossegue em cenário STUDY provisório se necessário; confirmação do lote real segue rastreável |
| Ocupação/realocação | CPChoque mencionada nos documentos | Registrar premissa acadêmica; não assumir liberação real |
| Normas/topografia | Referências secundárias, parâmetros provisórios e cotas faltantes | Bloqueia checks dependentes e FINAL |
| Arquitetura finalista | Pesquisa e seleção delegadas pelo usuário em 2026-09-15 | AGENT_DELEGATED + decisão/hash permite R05–R16; Amanda revisa posteriormente sem gate prévio |
| Calendário acadêmico | Plano de apoio com semanas relativas | Confirmar regulamento/coordenação; não inventar datas |

Os apoios foram preservados. As fontes permanecem intactas. Por instrução posterior do usuário, o agente deve pesquisar e escolher premissas/soluções revisáveis, registrando sua autoria e incertezas, sem atribuir endosso pessoal a Amanda. Fonte documentada, adoção projetual e comprovação normativa são decisões distintas.

## 5. Conferência técnica primária

Consulta em 2026-09-15; revalidar no commit/build efetivamente escolhido:

- Revit 2027 usa .NET 10 em runtime; isso não impõe universalmente um patch de SDK. [Autodesk](https://help.autodesk.com/view/RVT/2027/ENU/?guid=f7165618-24c9-4160-a7a4-09979fe4a981).
- Horizun documenta suporte 2023–2027, source build com SDK 10.0.400 e installer publicado recomendado para uso comum. Source-first permanece uma opção justificada e fixada por commit. [Horizun](https://github.com/HorizunGroup/horizun-revit-mcp), [global.json](https://github.com/HorizunGroup/horizun-revit-mcp/blob/main/global.json).
- RevitCortex documenta build por ano, deploy 2027 e ativação do Cortex Switch. Caminho/versão instalados precisam de evidência própria. [RevitCortex](https://github.com/LuDattilo/RevitCortex).
- Blender MCP documenta uvx e install-addon; pacote/executável/addon devem ter versões controladas na execução. [Blender MCP](https://github.com/ahujasid/blender-mcp).
- A distribuição Shapely consultada expõe 2.1.2 e wheel Windows CPython 3.12; mínimo 2.2 não deve ser presumido disponível. Faixa candidata revisada para >=2.1,<3, com resolução e lock antes de uso. [Shapely](https://pypi.org/project/shapely/).
- `codex mcp add NAME -- COMMAND...` foi conferido no CLI instalado, sem modificar configuração.

Não foi feita auditoria jurídica do terreno, normas ABNT ou licenciamento. Referências legais nos apoios são questões a validar, não pareceres desta revisão.

## 6. Validações e limites

[validate_documents.py](docs/review/validate_documents.py) executa 21 verificações estáticas: links/âncoras, entrada, caminho da especificação, status, conflito de programa, hipóteses, aprovação, suspensão, stubs, journal, capabilities, solver, backups, SDK, sintaxe de exemplos Python, cercas Markdown, grafo e IDs, além da delegação de seleção e tratamento de premissas revisáveis.

- Antes: 19 verificações; 3 passaram; 16 falharam por lacunas documentais.
- Depois: **21 verificações; 21 passaram; 0 falharam**. validation-after.json identifica os arquivos finais por hash.
- 159 IDs permitem retomada por fase; contagem/unicidade verificadas automaticamente.
- Pacote revisado: dez planos derivados, 15 Markdown com links locais verificados, 23 entradas no ZIP e 22 hashes conferidos; zero links locais quebrados. Os 13 hashes das fontes PDF/DOCX/XLSX continuam iguais aos registrados antes da revisão.
- Scripts de revisão não são implementação do agente. Exemplos Python foram analisados sintaticamente, não executados contra uma aplicação inexistente.
- Inspeção visual das duas páginas do programa confirma os dados utilizados; não houve QA visual integral do TFG ou das pranchas/modelos.
- Instalação/build, suíte do futuro agente, E2E Revit, solver real, exportação IFC/DWG, cold reopen, seleção arquitetônica e upload APS: NOT_RUN.

## 7. Retomada

Começar por [START_HERE_FOR_CODEX.md](START_HERE_FOR_CODEX.md) e pelo [handoff](docs/notes/2026-09-15-revisao-planos-handoff.md). Próxima implementação: M1/01, se solicitada. PROGRAM_BASELINE está resolvido por decisão do usuário: adotar o PDF de 20 pessoas. Registrar essa seleção com hash na futura ingestão; resolver as demais decisões antes das tarefas dependentes. A instrução posterior delega ao agente pesquisa/decisões e permite desenvolver BIM sem aprovação estética prévia, quando a execução do plano ocorrer. Esta tarefa apenas atualizou os documentos; não implementou o sistema.

## 8. Delegação posterior de decisões

Em 2026-09-15, o usuário determinou que o agente pesquise e tome decisões, deixando Amanda mudar depois o que não gostar. A seção 6.15 do design é o contrato canônico: seleção AGENT_DELEGATED, decision-register, hipóteses provisórias e revisão posterior não bloqueante. Essa instrução substitui o gate anterior de escolha humana; o programa de 20 pessoas continua adotado. Fontes, fatos, normas verificadas e hipóteses permanecem separados.

Validação documental antes dessa mudança: 21 verificações, 19 passaram e 2 falharam pelas regras de delegação ausentes (validation-delegation-before.json). Depois, 21/21; exemplos e contratos de implementação continuam sem teste runtime. A futura implementação deve testar decisão delegada, hash inválido, hipótese não verificada e feedback de Amanda conforme as tarefas atualizadas.
