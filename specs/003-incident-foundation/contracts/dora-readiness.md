# Contrato: qualidade / elegibilidade de métricas DORA

## Distinção de estado

```ts
type MetricReadiness = {
  metric: 'changeLeadTime' | 'deploymentFrequency' |
          'failedDeploymentRecoveryTime' | 'changeFailRate' | 'deploymentReworkRate';
  serviceKey: string;
  periodStart: string; // UTC inclusive
  periodEnd: string;   // UTC exclusive
  status: 'unavailable' | 'partial' | 'certified';
  reasons: string[];
  verifiedSources: string[];
  missingSources: string[];
  reviewedAt?: string;
  rulesVersion: string;
  coverageId?: string;
};
```

Regras de UX: se `status !== 'certified'`, o KPI oficial exibe **Não mensurável** e a explicação das lacunas. Se houver amostra parcial, ela pode aparecer em seção específica rotulada **amostra não consolidada**, nunca com badge de certificação.

## Gates por métrica

| Métrica | Conjunto mínimo de fontes | Condição de bloqueio |
| --- | --- | --- |
| Change Lead Time | commit/change ID, deployment finalizado em PROD, associação temporal | ausência de link individual ou ambiente inequívoco |
| Deployment Frequency | lista completa de deployments elegíveis em PROD / serviço / período | dados parciais ou sem reconciliação |
| Change Fail Rate | deployments PROD + incidentes relacionados + vínculos causais verificados + escopo certificado | causa não revisada, múltiplos incidentes contando uma mudança >1x, ausência de cobertura |
| Failed Deployment Recovery Time | causa por deployment verificada, início de impacto, restauração, timezone | timestamp ausente/inválido, indisponibilidade não causada pela mudança |
| Deployment Rework Rate | deployments PROD + identificação de remediação não planejada ligada a incidentes | cannot identify unplanned corrective deployments reliably |

## Cenários de aceitação obrigatórios

- 0 incidentes encontrados e cobertura não certificada ⇒ **Não mensurável**, nunca 0% validado.
- Deployment sandbox falha e nenhum impacto PROD ⇒ não aumenta Change Fail Rate.
- Um deployment em PROD causa três incidentes confirmados ⇒ numerador Change Fail Rate aumenta em **um**, não três.
- Incidente por rede sem evidência de mudança ⇒ excluído dos indicadores de falha de mudança.
- Rollback registrado manualmente, sem evento deployment confirmado ⇒ não aumenta frequência/rework por inferência.
- Hotfix emergencial implantado em produção, vinculado a incidente e classificado não planejado ⇒ elegível para rework se população certificada.
- Incidente restaurado antes de impacto ⇒ bloqueio de duração; corrigir a fonte, não calcular valor negativo.
- Falta de `commitAt` em um deployment ⇒ não fabricar Lead Time; manter o evento apenas nas métricas cujo contrato é atendido.
- Múltiplas fontes trazem o mesmo deployment ⇒ deduplicar por chave auditável, não por nome.
- Correção retroativa de vínculo/horário ⇒ invalida e refaz certificação/cálculo do período.

## Evidências a registrar

Para cada valor certificado: fórmula/versão, serviço, janela, timezone, IDs fonte, contagens brutas, excluídos, razões de exclusão, revisão, data e resultado. Nunca armazenar secrets/logs brutos no objeto de incidente.
