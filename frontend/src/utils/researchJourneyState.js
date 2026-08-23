/**
 * Frontend helper utility for determining student research journey stage states
 * and navigating between workspace tabs.
 */

export const JOURNEY_STAGE_DEFINITIONS = [
  { id: 1, key: 'PAPERS', title: '1. Research Papers', question: 'What research do I already have?', tab: 'papers' },
  { id: 2, key: 'LANDSCAPE', title: '2. Research Landscape', question: 'What are these papers doing?', tab: 'map' },
  { id: 3, key: 'GAPS', title: '3. Research Gaps', question: 'What appears to be missing?', tab: 'gaps' },
  { id: 4, key: 'OPPORTUNITY', title: '4. Research Opportunity', question: 'What could I investigate?', tab: 'directions' },
  { id: 5, key: 'VALIDATION', title: '5. Idea Validation', question: 'Is this idea worth investigating further?', tab: 'directions' },
  { id: 6, key: 'PLAN', title: '6. Research Plan', question: 'How should I conduct this research?', tab: 'plan' },
  { id: 7, key: 'EXPERIMENTS', title: '7. Experiments', question: 'Have I actually tested the idea?', tab: 'experiments' },
  { id: 8, key: 'RESULTS', title: '8. Results Analysis', question: 'What did my experiments actually show?', tab: 'results-analysis' },
  { id: 9, key: 'PROPOSAL', title: '9. Research Proposal', question: 'Can I turn this into a structured proposal?', tab: 'proposals' },
  { id: 10, key: 'REPORT', title: '10. Research Report', question: 'Can I document the complete research journey?', tab: 'report' },
];

export function getStageColor(status) {
  switch (status) {
    case 'COMPLETED':
      return 'emerald';
    case 'IN_PROGRESS':
    case 'AVAILABLE':
      return 'indigo';
    case 'BLOCKED':
      return 'rose';
    default:
      return 'slate';
  }
}
