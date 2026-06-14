# Addocu TFM — AI Agent Briefing & Critical Review Guide

**For:** AI agents working on `addocu-keygraph` and/or `addocu-pro`  
**Context:** These two projects form the technical foundation of a TFM (Master's thesis) at Universidad Complutense de Madrid — Master en Big Data, Data Science e IA.  
**Owner:** Javier Rodeiro Rodríguez  
**Stakes:** 20-page academic thesis + prize competition. The examiner (Carlos Ortega) explicitly rejected a previous proposal for being "too architectural and abstract." He wants DS aplicabilidad and concrete, evaluatable results.

Read this entire document before touching any code. Your job is not to build features. Your job is to make a thesis that wins.

---

## 1. What These Projects Are

### addocu-keygraph
Keyword intelligence platform with GEO/AEO visibility. Integrates Google Search Console, Google Ads, GA4, and LLM visibility signals (via prompt farming across 10+ models) into a unified `keyword_lemma` entity. DS methods: HDBSCAN clustering, pymc-marketing Bayesian MMM, Prophet/skforecast forecasting, GLiNER NER on farming responses.

### addocu-pro
Knowledge graph of the entire Google Marketing ecosystem. Discovers entities (campaigns, properties, audiences, keywords, tags) across 13+ Google platforms and connects them with 13 relationship types (`FEEDS_INTO`, `TRACKS`, `DEPENDS_ON`...). Stores in FalkorDB (Cypher) + DuckDB. Includes Text2Cypher with Qwen 3 0.6B via llama.cpp for natural language querying.

### The Hypothesis (OneSearch)
> Search behavior is fragmenting into three correlated but distinct channels: organic (GSC), paid (Google Ads), and LLM-mediated (GEO/AEO). We measure whether LLM visibility is an independent predictor of traffic and conversions, and whether a knowledge graph of the marketing ecosystem makes that attribution queryable in natural language.

That hypothesis is the thesis. Not the code. Not the architecture.

---

## 2. Hard Questions You Must Answer Before Writing Any Code

These are not rhetorical. If you cannot answer them with data or a concrete plan, stop building and surface the gap to the user.

### 2.1 Data Validity

**Q: Is your GEO/AEO signal actually signal, or is it noise?**

LLM responses vary by model version, prompt phrasing, temperature, time of day, and geographic routing. A keyword that appears in a Gemini response today may not appear tomorrow — not because visibility changed, but because the model sampled differently. If you have not controlled for this variability, your Bayesian MMM is fitting noise.

What you need before claiming GEO visibility as a channel:
- Minimum 3 independent runs of the same prompt per keyword per model
- Variance measurement across runs (not just presence/absence)
- Temporal stability analysis: does visibility score for the same keyword correlate across weeks?

If you have not done this, your farming data is decorative.

**Q: Do you have enough time series for Bayesian MMM?**

pymc-marketing's MMM requires minimum 1 year of weekly data to estimate media saturation curves reliably. With less, you get wide credible intervals that cannot distinguish signal from prior.

- How many weeks of GSC + Google Ads data do you have for this brokerage?
- If < 52 weeks: document this as a limitation and use a simpler linear attribution model with explicit uncertainty quantification instead of full MMM.
- If < 26 weeks: MMM is invalid. Use correlation analysis + Granger causality tests only.

Do not use pymc-marketing if you cannot defend the data volume to an examiner.

**Q: Is `keyword_lemma` entity resolution actually working?**

Unifying keywords across GSC, Google Ads, and GA4 sounds simple. It is not. GSC returns queries in lowercase, GA4 may have (not provided), Google Ads has broad match variants that don't map 1:1 to organic queries. Your `keyword_lemma` column is either (a) correctly resolving cross-source entities or (b) silently creating false matches that inflate apparent correlations.

Audit required:
- Sample 100 `keyword_lemma` values and manually verify the cross-source joins are correct
- Measure: what % of GSC queries have a matching Google Ads keyword? What's the expected rate?
- If using spaCy lemmatization: test on domain-specific insurance terms ("seguro de coche" vs "seguros coche" vs "seguro coche barato")

**Q: Do you have explicit permission to use the brokerage's data for a public academic thesis?**

Google's ToS for GSC and Ads API data does not prohibit academic use, but the brokerage's data is their commercial data. If the thesis is published (UCM repository), the brokerage's keyword performance data becomes public. This is a legal and ethical question, not a technical one. Answer it now.

---

### 2.2 Methodology Validity

**Q: Is your HDBSCAN clustering stable?**

HDBSCAN is sensitive to `min_cluster_size` and `min_samples`. A clustering that changes dramatically between `min_cluster_size=5` and `min_cluster_size=10` is not a finding — it is a parameter artifact.

Required before presenting clusters as results:
- Stability analysis across 3-5 `min_cluster_size` values
- DBCV score (Density-Based Clustering Validation) reported, not just visual inspection
- Cluster size distribution: if >60% of keywords fall into noise class (-1), your feature space is wrong

**Q: Is Prophet the right forecasting model here?**

Prophet assumes: (1) trend stationarity or slow change, (2) regular seasonality, (3) no structural breaks. The introduction of ChatGPT (Nov 2022), Google AI Overviews (May 2024), and Perplexity growth represents structural breaks in search behavior. Prophet will interpolate through these breaks and produce confident-looking but misleading forecasts.

Consider: skforecast with a gradient boosting regressor (LightGBM) + explicit regime features (binary indicators for AI search milestones). That is both more defensible and more aligned with the thesis argument that AI search created a new channel.

**Q: What is the null hypothesis for your OneSearch analysis?**

You need a null: "LLM visibility score is uncorrelated with organic CTR and paid ROAS, controlling for keyword volume and competition." If you cannot reject that null with your data, that is still a valid academic finding — it means GEO/AEO is not yet a significant channel for this brokerage, and you explain why (industry vertical, brand size, content quality). A negative result, rigorously reached, is better than a positive result built on thin data.

Do not overfit to confirm the hypothesis. The examiner will check.

---

### 2.3 addocu-pro Specific

**Q: Is FalkorDB the right graph database for this use case?**

FalkorDB is a Redis module. It is fast for read-heavy graph traversal but has limited support for complex graph ML pipelines. If you plan to run GNN training on this graph, you will need to export the adjacency matrix and node features to PyTorch Geometric anyway — FalkorDB is then just a serving layer.

Questions to answer:
- How many nodes and edges does the graph currently have for the brokerage?
- If < 500 nodes: NetworkX in memory is sufficient. FalkorDB is over-engineering.
- If you plan GNN: does FalkorDB's export format integrate cleanly with PyTorch Geometric?

**Q: What is Qwen 3 0.6B's actual Text2Cypher accuracy on your schema?**

0.6B parameter models have limited instruction-following capability for complex graph schemas. A Cypher query like `MATCH (k:Keyword)-[:FEEDS_INTO]->(c:Campaign)-[:TRACKS]->(p:Property) WHERE k.geo_score > 0.5 RETURN k, c, p` requires the model to understand your schema, Cypher syntax, and the join logic simultaneously.

Required before claiming Text2Cypher as a working feature:
- Benchmark: 20 manually written natural language questions → generated Cypher → execution result vs expected result
- Report exact-match accuracy and semantic accuracy separately
- If accuracy < 60%: either fine-tune, use a larger model via API (Gemini Flash is free tier), or drop the claim from the thesis

**Q: Are your 13 relationship types analytically meaningful or just API structure mirrored?**

`FEEDS_INTO(Campaign → Keyword)` makes sense analytically. But does `DEPENDS_ON(GTM Container → GA4 Property)` add attribution value or just reflect implementation topology? Relationship types that mirror technical dependencies without behavioral meaning inflate graph complexity without improving analysis.

For the thesis: reduce to the 5-7 relationship types that have direct attribution meaning. Justify each one with: "This relationship explains variance in [metric] because..."

---

### 2.4 The Integration Between Projects

**Q: How exactly does addocu-pro enrich addocu-keygraph clustering? Write the data flow, not the concept.**

"The graph enriches the clusters" is not an answer. This is an answer:

```
addocu-pro discovers: keyword "seguro de coche"
  → appears in Campaign ID 12345 (TARGETS)
  → Campaign 12345 FEEDS_INTO GA4 Property 98765
  → GA4 Property 98765 has GSC Connection for domain mso.es

addocu-keygraph receives:
  keyword_lemma = "seguro coche"
  + feature: campaign_count (how many campaigns target this lemma)
  + feature: property_hop_distance (graph distance from keyword to GA4 property)
  + feature: is_cross_channel (appears in both paid and organic data)

HDBSCAN then clusters on:
  [semantic_embedding, geo_score, ctr, roas, campaign_count, property_hop_distance, is_cross_channel]
```

If you cannot write the equivalent of that for your actual schema, the integration does not exist yet. Write it before building it.

**Q: What is the ground truth for evaluating GNN node predictions?**

You plan to train a GNN to predict which keyword nodes will gain/lose LLM visibility. Ground truth requires: (1) historical LLM visibility scores (farming data from T-1, T-2...) and (2) actual traffic outcomes (GSC clicks at T+1).

- How many weeks of farming history do you have?
- Is that enough for a train/test split with temporal ordering? (Never random split time series.)
- If < 8 weeks: GNN is premature. Use node2vec embeddings as static features instead.

---

## 3. Harsh Structural Criticism

### addocu-keygraph

The dev log from May 24 lists 8 hours of work installing dependencies, configuring MLflow, evaluating 19 repos, and setting up pre-commit hooks. That is 8 hours of scaffolding with zero DS output. This is a recurring pattern in AI-assisted coding sessions: the agent optimizes for setup completeness, not research progress.

**The question is not "is the pipeline configured?" The question is "what do the clusters show?"**

Before adding any new library, component, or configuration: run the existing clustering on real data, plot the results, and identify what is wrong with them. Setup is not research. Clustering results that reveal something unexpected about search behavior IS research.

### addocu-pro

The project README describes inventory, graph, vigilance, LLM, and cloud as five components. That is five engineering systems in a TypeScript monorepo. For a 20-page thesis, you need one of them to produce a finding. Which one?

**Pick one output artifact that constitutes a thesis result.** Candidate: "the graph community detection on marketing entities reveals N distinct attribution clusters, and keywords in cluster X show 3x higher GEO visibility than cluster Y." That is a finding. "We built a graph that stores 13 relationship types" is not.

### General

Both projects suffer from the same disease: **premature productization**. You have a commercial mindset (deployable, scalable, CLI, API, MCP server) applied to what should be a research mindset (falsifiable, reproducible, interpretable). A thesis examiner does not care if it runs on HuggingFace Spaces. They care if the methodology is valid and the results are surprising.

For the next 60 days: delete the deployment chapter from your mental model. Build for a Jupyter notebook that tells a story, not a Docker container that runs in production.

---

## 4. What the Examiner Will Actually Evaluate

Carlos Ortega's feedback in exact words: *"las decisiones de arquitectura suelen estar muy acopladas al caso de uso y de las capacidades futuras que se esperan de la arquitectura propuesta"* and *"el trabajo le veo mucho de arquitectura y eso suele ser bastante abstracto y difícil de evaluar."*

Translation for the AI agent: he cannot grade a system diagram. He can grade:

1. A research question with a measurable answer
2. A dataset with documented provenance, size, and limitations
3. A methodology with justified model choices and validation strategy
4. Results with uncertainty quantification (p-values, credible intervals, DBCV scores)
5. A conclusion that either confirms or rejects the hypothesis with an explanation

Every line of code you write should trace to one of those five things. If it does not, delete it or move it to an appendix.

---

## 5. The 15 UCM Modules — Coverage Map

| # | Module | How covered | Risk |
|---|--------|-------------|------|
| 1 | Business Intelligence | Marimo attribution dashboard | Low |
| 2 | SQL | DuckDB + dbt keyword_lemma pipeline | Low |
| 3 | Tableau | Add 2 Tableau dashboards on DuckDB | **Medium — must add** |
| 4 | Python | Entire codebase | Low |
| 5 | NoSQL | FalkorDB graph (addocu-pro) | Medium — depends on graph size |
| 6 | Statistics | Bayesian MMM, Granger causality, correlation tests | **High — depends on data volume** |
| 7 | Data Mining | HDBSCAN clustering + community detection | Low |
| 8 | ML | skforecast, scikit-learn pipelines | Low |
| 9 | Data Visualization | Marimo + Plotly cluster maps | Low |
| 10 | DL / LLMs | Prompt farming + GNN or node2vec + Text2Cypher | Medium — validate each claim |
| 11 | Spark | Historical BigQuery backfill processing | **High — weakest module** |
| 12 | Big Data | dlt incremental ingestion at keyword scale | Medium |
| 13 | Productivization | MLflow experiment tracking | Low |
| 14 | TFM | This project | — |
| 15 | Applied DS | End-to-end: ingest → cluster → attribute → recommend | Low |

Modules 3, 6, 10, 11 need explicit attention. Do not assume they are covered.

---

## 6. Minimum Viable Thesis — What Must Exist

If nothing else is built, these six artifacts constitute a defensible thesis:

1. **Dataset card:** documented provenance, date range, row counts, limitations, permission status for GSC + Ads + farming data
2. **EDA report:** distribution of `keyword_lemma` across channels, GEO score distribution, temporal trend plots
3. **Clustering analysis:** HDBSCAN results with DBCV score, stability analysis, interpretable cluster names with business meaning
4. **Attribution model:** correlation matrix (GSC rank × GEO score × ROAS), Granger causality test, Bayesian MMM if data volume permits
5. **Graph analysis:** degree distribution, community detection results, top-N influential entities by betweenness centrality
6. **Conclusion:** reject or fail to reject the OneSearch hypothesis with quantified confidence and explanation

Six analytical outputs that tell a story. Not six systems. Not six features.

---

## 7. Questions to Ask the User Before Every Work Session

Before starting any implementation task, ask the user:

1. "Which of the 6 minimum viable thesis artifacts does this task contribute to?"
2. "Do we have real data to validate this, or are we building on assumptions?"
3. "Is this a thesis result or a product feature? If product feature, should we defer it?"
4. "What would the result look like if this approach is wrong?"

If the user cannot answer question 1, push back. The task is likely premature.

---

## 8. Recommended 60-Day Focus

| Week | Priority |
|------|----------|
| 1–2 | Data audit: validate keyword_lemma entity resolution, measure GEO signal stability, document time series length |
| 3–4 | Clustering: HDBSCAN on real data, stability analysis, interpret clusters with domain knowledge |
| 5–6 | Attribution: correlation analysis, Granger causality, decide if MMM is justified by data volume |
| 7–8 | Graph: addocu-pro entity count for brokerage, community detection, enrich keygraph features with graph metrics |
| 9–10 | GNN or node2vec: only if graph has >200 nodes and >4 weeks farming history |
| 11–12 | Writing: dataset card, methodology chapter, results chapter — no new code in this period |

Every week that produces only code and no analysis output is a week wasted for the thesis.

---

## 9. What Success Looks Like

The thesis wins the prize if it produces one surprising finding — something that contradicts the obvious assumption. Examples:

- "GEO visibility is NOT correlated with organic CTR for high-competition insurance keywords, suggesting LLMs use different citation signals than Google's ranking algorithm"
- "Bayesian MMM reveals that GEO/AEO channel has negative attribution weight for this vertical — brand mentions in LLMs reduce paid click intent"
- "HDBSCAN identifies a cluster of 47 keywords with high organic rank but zero LLM visibility — these represent the highest-risk keywords for the zero-click transition"

A surprising finding with rigorous methodology beats a confirmed hypothesis with weak data every time.

---

*Maintained in SoloDShouse/docs/solodshouse/addocu-tfm-briefing.md. Update after each major thesis milestone.*
