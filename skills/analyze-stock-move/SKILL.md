---
name: analyze-stock-move
description: Analyze the latest rise or fall of an A-share stock with structured market, style, industry, peer, money-flow, announcement, and counterfactual evidence. Use when asked why a Chinese stock moved, whether a move came from high-to-low rotation, sector resonance, or stock-specific catalysts, or when reviewing a prior stock-move explanation.
---

# Analyze Stock Move

Use the deterministic stock-flow-lens attribution API before forming a narrative. Treat its output as observable evidence and rule-based attribution, not proof of each trader's intent.

## Workflow

1. Run `python scripts/analyze_stock.py <股票代码或名称>`.
2. If the local API is unavailable, report that the structured attribution service must be started. Do not replace missing data with a confident story.
3. Read `references/methodology.md` when interpreting scores, counterfactuals, missing fields, or confidence.
4. Inspect evidence in this order:
   - whole-market direction and breadth;
   - growth-versus-value rotation;
   - industry and peer co-movement;
   - stock-relative return, volume, turnover, and money flow;
   - same-day company announcements;
   - current authoritative news when the stock-specific residual remains large.
5. Distinguish three levels explicitly:
   - primary driver: explains why the move happened that day;
   - amplifier: explains why this stock moved more than peers;
   - background: medium-term fundamentals that made the stock selectable but did not trigger the day.
6. Apply every counterfactual returned by the API. Do not call an old announcement a direct catalyst when `sameDay` is false.
7. State the conclusion, evidence, rejected explanations, confidence, and data limitations.

## Output Rules

- Lead with one primary driver or say `mixed`/`insufficient`.
- Quote exact dates for market data and announcements.
- Label causal language as inference unless a same-day disclosure directly explains the move.
- Do not infer a medium-term technology top or cycle reversal from one trading day.
- Do not give personalized buy or sell instructions unless the user separately requests decision support.
- When fresh news is required, prefer exchange filings, company disclosures, government data, and primary research sources.

## Required Output

Use this compact structure:

```text
结论：<一级驱动>（<置信度>）

一级证据：
- <市场/风格事实>

二级放大因素：
- <行业/个股事实>

反事实：
- <同行是否同步、当日是否有公告、替代解释是否成立>

限制：
- <缺失数据或只能推断的部分>
```
