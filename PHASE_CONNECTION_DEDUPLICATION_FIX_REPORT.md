# Phase Report: Research Connections Deduplication & Self-Relationship Fix

**Project:** IntelliResearch — AI-Based Research Gap Discovery and Research Recommendation System  
**Module:** Research Connections & Pairwise Paper Similarity Engine  
**Status:** COMPLETE & VERIFIED (269 Backend Tests Passing, Frontend Build Clean)

---

## 1. Executive Summary & Root Cause Analysis

### Problem Description
In the IntelliResearch project intelligence view ("How Are Papers Related in This Collection?"), paper-to-paper relationships were displaying duplicate/mirrored pairs (e.g. `Paper A → Paper B` AND `Paper B → Paper A`) as well as invalid self-relationships (e.g. `Paper A → Paper A` with 100% similarity).

### Root Cause
1. **Un-deduplicated Project Paper Associations**: When assigned project paper IDs were retrieved from the database, duplicate join entries or non-unique paper ID queries resulted in duplicate `ResearchPaper` object instances in the array.
2. **Missing Canonical Pair Normalization**: Pairwise comparison loops generated relationships for both indices $(i, j)$ without canonical ordering `min(id1, id2):max(id1, id2)`.
3. **Lack of Self-Relationship Rejection**: The comparison loop did not explicitly reject pairs where `source_paper_id == target_paper_id`. When identical paper objects were compared, the cosine similarity produced `100.0%`, generating invalid $A \rightarrow A$ self-relationships.

---

## 2. Theoretical Paper Pair Bound ($N = 4$)

For $N$ unique research papers assigned to a project, the maximum number of unique unordered pairwise relationships is given by:

$$\frac{N \times (N - 1)}{2}$$

For a project containing **4 assigned papers**:

$$\frac{4 \times (4 - 1)}{2} = \frac{12}{2} = 6\text{ maximum unique paper-to-paper connections.}$$

| Paper Count ($N$) | Before Fix (With Dupes & Self-Pairs) | After Fix (Canonical Unique Pairs) |
| :--- | :--- | :--- |
| **4 Papers** | Up to 16-20 (Self + Mirrored) | **Maximum 6 Unique Connections** |

---

## 3. Backend & Frontend Implementation Summary

### A. Backend Intelligence Layer
Updated [`global_research_intelligence_service.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/services/global_research_intelligence_service.py) and [`project_intelligence_service.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/app/services/project_intelligence_service.py):

1. **Deduplication of Input Papers**:
   ```python
   unique_papers_dict = {p.id: p for p in papers_raw if p}
   papers = sorted(list(unique_papers_dict.values()), key=lambda x: x.id)
   ```
2. **Canonical Pair Key & Self-Relationship Guard**:
   ```python
   seen_pairs = set()
   for i in range(total_papers):
       for j in range(i + 1, total_papers):
           p1 = papers[i]
           p2 = papers[j]

           # Rule 1: Exclude self-relationships
           if p1.id == p2.id:
               continue

           # Rule 2: Canonical Pair Key min(id1, id2):max(id1, id2)
           low_id = min(p1.id, p2.id)
           high_id = max(p1.id, p2.id)
           pair_key = f"{low_id}:{high_id}"

           if pair_key in seen_pairs:
               continue
           seen_pairs.add(pair_key)
   ```

### B. Frontend Defensive & UX Layer
Updated [`ResearchProjectDetails.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/pages/ResearchProjectDetails.jsx):

1. **Defensive Filtering via `useMemo`**:
   ```javascript
   const uniquePaperRelationships = useMemo(() => {
     if (!relationships || !Array.isArray(relationships)) return [];
     const seen = new Set();
     const result = [];
     for (const r of relationships) {
       const srcId = r.source_paper_id || r.source_id;
       const tgtId = r.target_paper_id || r.target_id;
       if (!srcId || !tgtId || srcId === tgtId) continue;
       const lowId = Math.min(srcId, tgtId);
       const highId = Math.max(srcId, tgtId);
       const pairKey = `${lowId}-${highId}`;
       if (seen.has(pairKey)) continue;
       seen.add(pairKey);
       result.push(r);
     }
     return result;
   }, [relationships]);
   ```

2. **UX Enhancements**:
   - **Student-Friendly Heading**: `🔗 How Are These Papers Related?`
   - **Helper Subtext**: `Each card compares two different papers from your project. A paper is shown only once per pair.`
   - **Connection Count Badge**: `Showing 6 unique paper connections`
   - **Card Presentation**:
     ```
     [Paper A #12]
           ↕
     76.3% Similar
           ↕
     [Paper B #27]
     Shared concepts: CNN • Computer Vision • Deep Learning
     ```
   - **100% Similarity Warning Badge**:
     If `similarity_score >= 99.9%` between two *different* papers:
     `"⚠️ 100% Similarity Warning: These papers have extremely similar extracted concepts/content. Review both papers to determine whether they are duplicates or closely related."`

---

## 4. Verification & Test Results

### A. Dedicated Backend Unit Test Suite
Created [`test_paper_relationship_deduplication.py`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/backend/tests/test_paper_relationship_deduplication.py) covering all 9 required test specifications:

| Test ID | Test Description | Result |
| :--- | :--- | :---: |
| **TEST 1** | 4 papers produce at most 6 unique pairs ($4 \times 3 / 2 = 6$) | **PASSED** |
| **TEST 2** | A-B and B-A collapse into one canonical relationship | **PASSED** |
| **TEST 3** | A-A self-relationship is never created or returned | **PASSED** |
| **TEST 4** | Duplicate titles do not cause incorrect deduplication | **PASSED** |
| **TEST 5** | Different paper IDs with identical titles remain separate papers | **PASSED** |
| **TEST 6** | 100% similarity between two different papers is allowed | **PASSED** |
| **TEST 7** | 100% similarity of a paper with itself is never returned | **PASSED** |
| **TEST 8** | Project-scoped connections only use papers assigned to that project | **PASSED** |
| **TEST 9** | Global intelligence remains global and is not accidentally restricted | **PASSED** |

### B. Full Test Suite Status
- **Backend Pytest**: `269 passed, 1 skipped in 24.36s` (0 failures across all 34 test modules).
- **Frontend Production Build**: `npm run build` compiled in **586ms** with 0 errors.

---

## 5. Conclusion
The paper-to-paper relationship deduplication and self-relationship exclusion pipeline is fully implemented, defensively layered, and verified across both backend services and frontend components.
