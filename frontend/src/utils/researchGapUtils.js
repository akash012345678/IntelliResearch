/**
 * Filter research gaps strictly by QUALIFIED_POTENTIAL_GAP contract.
 * Rejects legacy, unclassified, insufficient-evidence, and malformed gaps.
 */
export function filterQualifiedGaps(rawGaps = []) {
  if (!Array.isArray(rawGaps)) return [];
  return rawGaps.filter((g) => {
    const status = g?.eligibility_status ?? g?.evidence?.eligibility_status;
    return status === "QUALIFIED_POTENTIAL_GAP";
  });
}
