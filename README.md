# Guiding Index Tuning Exploration with Potential Estimation (GITEE)

This repository contains the implementation of **GITEE**, a novel learning-based index advisor designed to improve the efficiency and effectiveness of index tuning by intelligently guiding the exploration of large search spaces for candidate indexes. GITEE leverages query-aware potential estimation and Monte Carlo Tree Search (MCTS) to optimize index configurations for complex workloads.

## Overview

**GITEE** addresses the inefficiencies in existing index advisors by:
1. Estimating the maximum improvement that indexes can bring to individual queries using a deep learning model named **NPE** (Normalized Potential Estimator).
2. Filtering out queries with minimal impact to reduce the workload, thus focusing the tuning budget on queries with the highest potential for performance improvement.
3. Utilizing **Monte Carlo Tree Search (MCTS)** to rapidly explore high-quality index configurations.

Extensive experiments demonstrate that GITEE outperforms state-of-the-art index advisors by reducing tuning overhead by 1-2 orders of magnitude while achieving superior tuning performance.

## Key Components

### 1. Normalized Potential Estimator (NPE)
NPE is a deep learning model that estimates the maximum potential improvement an index can bring to a query. It uses query plan and predicate information to generate accurate estimates without actually building indexes.

### 2. Workload Filtering
By estimating the gain of each query, GITEE filters out redundant queries, significantly reducing the search space and focusing on essential queries that contribute most to performance improvements.

### 3. MCTS-Based Index Selection
GITEE uses Monte Carlo Tree Search to efficiently explore the space of possible index configurations, incorporating incremental updates to refine the index selection process continuously.

## Installation

To install the required dependencies, run:

```bash
python index_advisor_workload.py 5432 indexselection_tpch___10 --db-host 127.0.0.1 --db-user postgres hyper.sql --schema public --max-index-num 10 --max-index-storage 3000 --multi-iter-mode --min-improved-rate 0.000002 --driver
