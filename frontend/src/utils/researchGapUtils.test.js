import { filterQualifiedGaps } from './researchGapUtils.js';

export function runResearchGapUtilsTests() {
  console.log("Running researchGapUtils contract tests...");

  // Test Case 1: Standard response with 3 qualified gaps and 1 insufficient evidence candidate
  const mockResponse1 = [
    { eligibility_status: "QUALIFIED_POTENTIAL_GAP", gap_score: 0.8945, title: "Gap 1" },
    { eligibility_status: "QUALIFIED_POTENTIAL_GAP", gap_score: 0.8162, title: "Gap 2" },
    { eligibility_status: "QUALIFIED_POTENTIAL_GAP", gap_score: 0.8112, title: "Gap 3" },
    { eligibility_status: "INSUFFICIENT_EVIDENCE", gap_score: 0.7392, title: "Gap 4" }
  ];
  const qualified1 = filterQualifiedGaps(mockResponse1);
  if (qualified1.length !== 3) {
    throw new Error(`Test 1 failed: Expected 3 qualified gaps, got ${qualified1.length}`);
  }

  // Test Case 2: Backward compatibility for nested evidence.eligibility_status
  const mockResponse2 = [
    { evidence: { eligibility_status: "QUALIFIED_POTENTIAL_GAP" }, gap_score: 0.8945 },
    { evidence: { eligibility_status: "INSUFFICIENT_EVIDENCE" }, gap_score: 0.6983 }
  ];
  const qualified2 = filterQualifiedGaps(mockResponse2);
  if (qualified2.length !== 1) {
    throw new Error(`Test 2 failed: Expected 1 qualified gap, got ${qualified2.length}`);
  }

  // Test Case 3: Exclusion of objects with missing or malformed eligibility_status
  const mockResponse3 = [
    { title: "Malformed Gap with no status" },
    { eligibility_status: "REJECTED" },
    { evidence: {} }
  ];
  const qualified3 = filterQualifiedGaps(mockResponse3);
  if (qualified3.length !== 0) {
    throw new Error(`Test 3 failed: Expected 0 qualified gaps for malformed input, got ${qualified3.length}`);
  }

  console.log("ALL researchGapUtils contract tests PASSED SUCCESSFULLY!");
  return true;
}

if (typeof process !== 'undefined' && process.argv[1]?.includes('researchGapUtils.test.js')) {
  runResearchGapUtilsTests();
}
