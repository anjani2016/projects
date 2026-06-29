# 1. The Architectural Process

To deliver real-time monitoring, price projection, and hedging as a scalable service, the system should be divided into three distinct operational layers:

**[Ingestion Layer] → [Analytics & Projection Engine] → [Hedging & Decision Suite]**

- **Ingestion Layer:** IESO APIs, Web Services, Weather  
- **Analytics & Projection Engine:** ML/Statistical Modeling of Real-Time & DAM LMPs  
- **Hedging & Decision Suite:** Risk Optimization, VaR, Portfolio Position Simulation  

---

## The Ingestion Layer
An event-driven pipeline that constantly aggregates:
- Multi-zonal pricing  
- Intertie schedules  
- Generation mixes  
- Weather realities  

---

## The Analytics & Projection Engine
A dual-horizon forecasting framework that predicts:

- **5-minute Real-Time Market (RTM)** intervals  
- **Hourly Day-Ahead Market (DAM)** prices  

Using:
- Structural models (grid physics, stack curves)  
- Statistical / ML models (gradient-boosted trees, neural networks for spatial-temporal data)  

---

## The Hedging & Decision Suite
An optimization framework that uses projected price distributions to evaluate hedging positions.

Includes:
- Value at Risk (VaR)  
- Financial derivative recommendations (swaps, options)  
- Virtual Trades for exposure mitigation  

---

# 2. Core Data Sources

Following the MRP transition, the IESO data architecture uses modernized endpoints:

### **Public Reports Engine**
Real-time demand, system adequacy, pre-dispatch forecasts, and final zonal/intertie LMPs.  
Access via:
- IESO Public Reports API: https://reports.ieso.ca/api/v1.4/files  
- IESO SFTP server  

### **Market Information Management (MIM2)**
Used for programmatic data exchange regarding physical or financial schedules.  
Endpoint: https://webservices.ieso.ca/mim2  

### **Exogenous Inputs**
- High-resolution weather feeds (Environment Canada, NOAA)  
- Natural gas spot pricing (Dawn Hub)  
Used to estimate marginal cost of gas-fired generation.  

---

# 3. Permissions & Accreditations

Your regulatory path depends on your business model:

| Business Model | IESO Requirement | Technical Requirement |
|----------------|------------------|------------------------|
| **Informational / Advisory SaaS** (App provides insights; client executes independently) | None — only public APIs used | Standard internet-facing infrastructure; corporate data compliance |
| **Automated / Direct Trading Platform** (App executes trades/virtual bids on behalf of clients) | Must register as IESO Market Participant (Virtual Trader, Financial Marketer, Trader) | Participant Authorization, EMI2/MIM2 connectivity testing, secure VPNs |

---

# 4. Associated Costs

### **Infrastructure (Low–Moderate)**
- Time-series databases (TimescaleDB)  
- Cloud compute (AWS/GCP) for pipelines & ML inference  

### **Commercial Data Feeds (Variable)**
- Proprietary weather models  
- Natural gas forward curves  

### **Prudential Capital (High, Conditional)**
If acting as a direct market participant (Virtual Trader), you must post financial collateral (letters of credit or cash deposits) based on trading volumes.

---

# 5. Critical System Limitations

### **SCED Algorithm Opacity**
The IESO uses the Security-Constrained Economic Dispatch (SCED) tool to calculate LMPs:



\[
LMP = \lambda_{ref} + L_j + C_j
\]



Where:
- \( \lambda_{ref} \): reference bus price  
- \( L_j \): marginal loss component  
- \( C_j \): congestion component  

External platforms cannot perfectly model:
- Real-time line ratings  
- Forced outages  
- Loop flows  

Thus, structural unpredictability is unavoidable.

---

### **Operator Discretion (Manual Intervention)**
IESO operators may issue manual dispatch instructions or declare system states for reliability.  
This can create:
- Sudden price spikes  
- Price floors  
- Non-modelable anomalies  

---

### **Reporting Latency**
“Real-time” public reports often have **5–15 minute delays**.  
High-frequency physical asset optimization requires:
- Direct telemetry  
- Not just public API scraping  

---

# 5-minute ingestion process


# IESO 5-Minute Ingestion Pipeline Architecture

To build a production-grade ingestion pipeline for IESO’s 5-minute public XML/CSV engine, we have to look past simple `requests.get()` loops. The IESO public reporting portal (`reports-public.ieso.ca`) can experience brief server hangs, file release latencies, or sudden structural schema changes.

If your ingestion drops for even 15 minutes during a tight supply hour, your downstream pricing models and hedging risk metrics lose their real-time accuracy.

Here is a resilient, low-latency data ingestion architecture designed to pull, validate, and store IESO data smoothly.

---

## 1. High-Level Pipeline Architecture

The optimal design uses a decoupled, event-driven architecture rather than a monolithic script. This ensures that a failure in parsing an XML file won't crash your scheduler or block the downloading of subsequent files.

```text
 [Cloud Scheduler]  ──(Trigger)──>  [Producer: Orchestrator Lambda / Container]
                                                        │
                                                 (Polls Endpoint)
                                                        ▼
 [TimescaleDB / Postgres] <── [Consumer: Parser] <── [Kafka / SQS] <── [S3 Raw Bucket]

```



2. Pipeline Execution StepsStep 1: Trigger & High-Frequency PollingLayer: Ingestion TriggerFrequency: Every 60 secondsMechanic: A serverless scheduler (like AWS EventBridge or GCP Cloud Scheduler) triggers an ingestion worker every 60 seconds. Even though the files are published at "5-minute" intervals, the actual publication timestamp varies. Polling once per minute ensures you capture the file within seconds of its release.Step 2: Idempotent Check & Raw S3 StorageLayer: Network & Storage LayerMechanic: The worker issues an HTTP HEAD request to check the Last-Modified header or specific file suffix (e.g., PUB_RealtimeTotals.xml). If the file is new, it downloads the raw object and writes it directly to an S3 or Cloud Storage "landing zone" bucket using a strict date-partitioned prefix (s3://ieso-raw/yyyy/mm/dd/).Step 3: Event DecouplingLayer: Message Queue BrokerMechanic: The moment the file hits the raw storage bucket, an event notification drops a message onto a queue or streaming platform (like AWS SQS or Apache Kafka). The message contains only the file metadata and bucket path. This ensures that even if downstream parsers are temporarily overwhelmed, the raw data is safely isolated and buffered.Step 4: Stream Parsing & Schema ValidationLayer: Processing LayerMechanic: A dedicated consumer service picks up the queue message. It streams the XML/CSV out of storage—never loading large historic files fully into RAM. The parser validates the document elements against predefined schema structures (like the official RealtimeTotals_r1.xsd).Step 5: Time-Series UpsertLayer: Database LayerMechanic: Validated values are written to your production engine. Using a SQL ON CONFLICT DO UPDATE (upsert) command bound to the primary key combination of (Timestamp, Node_ID/Zone_ID, Metric_Name) prevents duplicate rows if a report is re-run or double-fetched by the polling script.3. Handling Critical Edge Cases & Fault ToleranceBuilding this effectively means writing code to survive the real-world operational quirks of the grid:Redundant FormatsThe IESO often publishes the same market metrics in both .xml and .csv variations across its directory.Strategy: Configure your ingestion worker to prioritize the XML endpoint for its structural integrity. If the XML request returns a 504 Gateway Timeout or a corrupted file payload, the pipeline should instantly fall back to download the corresponding CSV asset.Schema Shifts (Post-MRP Realities)The Market Renewal Program fundamentally overhauled report layouts to accommodate three distinct pricing pillars:$$LMP = \text{Reference Price} + \text{Congestion Component} + \text{Loss Component}$$If an unannounced system update modifies an XML element name, a traditional parser will crash.Mitigation: Your consumer must wrap structural parsing logic in a try/except block. If a schema violation occurs, the worker pushes the raw file to a Dead Letter Queue (DLQ), posts a high-priority alert to your team, and allows the loop to continue tracking the next 5-minute interval without grinding the entire infrastructure to a halt.4. Technology Stack RecommendationFor an engineering-driven advisory application, this stack balances high performance with low maintenance overhead:LayerRecommended TechnologyWhy it FitsCompute / WorkerAWS Lambda (Python / Go)Scales down to zero cost between 5-minute intervals.Message QueueAWS SQS or RabbitMQGuarantees at-least-once message delivery with zero server maintenance.Storage (Time-Series)TimescaleDB (Postgres extension)Perfect for grid applications. It allows complex SQL window functions across time intervals while keeping standard relational features for client metadata.