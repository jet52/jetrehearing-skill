# jetrehear-skill: Petition for Rehearing Analyzer

## Context

After the ND Supreme Court decides a case, a party may file a petition for rehearing under N.D.R.App.P. 40 arguing the Court "overlooked or misapprehended" a point of law or fact. This skill analyzes such petitions and produces a recommendation memo. It is a separate skill from jetmemo because the analytical task is fundamentally different: rehearing is evaluative (checking the Court's own work against the petition's claims) rather than extractive (framing a case for initial decision).

---

## Project Structure

```
jetrehear-skill/
├── README.md
├── VERSION                             # "1.0.0"
├── Makefile
├── install.py
├── install.sh
├── .gitignore
└── skill/
    ├── SKILL.md                        # Core workflow (new)
    ├── references/
    │   ├── rehearing-format.md         # Output template (new)
    │   └── style-spec.md              # Copy from jetmemo
    └── scripts/
        ├── verify_citations.py         # Copy from jetmemo
        ├── extract_docx.py            # New — docx paragraph extraction
        ├── check_update.py            # Adapt from jetmemo
        └── splitmarks.py             # Copy from jetmemo
```

## Input Documents

| Type | Format | Required | Classification Signal |
|------|--------|----------|----------------------|
| Petition for rehearing | PDF | Yes | "Petition for Rehearing" |
| Court's opinion | docx, PDF, or md | Yes | Opinion header, [para N] style, "Filed" date |
| Response to petition | PDF | No | "Response to Petition for Rehearing" |
| Appellant brief | PDF | No | "Brief of Appellant" |
| Appellee brief | PDF | No | "Brief of Appellee" |
| Record items | PDF (may need splitting) | No | Record documents, appendix |

Opinion handled three ways: docx via `extract_docx.py`, PDF via `pdftotext`, markdown read directly.

## Recommendation Logic

Always recommend. Four possible outcomes:

1. **Deny** — Court did not overlook or misapprehend; petitioner merely disagrees with the outcome.
2. **Request response** — Close question on whether something was overlooked/misapprehended AND no response has been received yet.
3. **Correction** — Petition identifies an error (factual, citation, etc.) that should be fixed but does not change the result.
4. **Oral argument** — Response has been received but the answer remains uncertain.

Decision tree:
```
All points = mere disagreement → DENY
Any genuine oversight that doesn't change result → CORRECTION
Any genuine oversight that could change result:
  No response received → REQUEST RESPONSE
  Response received, still uncertain → ORAL ARGUMENT
Close call (could be oversight, uncertain):
  No response received → REQUEST RESPONSE
  Response received → DENY (with notation)
```

## Pipeline

### Phase 1: Preparation (Orchestrator, Sequential)

**Step 0: Scan & Classify**
- Scan working directory for .pdf, .docx, .md files
- Classify each document (petition, opinion, response, brief, record, other)
- Handle opinion format: docx → `extract_docx.py`, PDF → `pdftotext`, md → direct read
- Split large record PDFs via `splitmarks.py`
- Build manifest with `{path, type, format, page_count}`
- Set `has_response` flag based on whether a response document is found

**Step 1: Extract & Prepare**
- Read reference files (style-spec.md, rehearing-format.md)
- Extract text from all documents
- Run `verify_citations.py` separately on:
  - Petition → `petition_citations.json`
  - Opinion → `opinion_citations.json`
  - Briefs (if provided) → `briefs_citations.json`
- Compute new authorities: `petition_citations - opinion_citations - briefs_citations` (by normalized field)
- Determine which conditional agents to launch

### Phase 2: Parallel Analysis (Subagents)

**Agent A: Petition Extraction** (always)
- Extract each claimed point: heading, law vs. fact, specific claim, opinion cites, record cites, authority cites, preservation assertion
- Extract compliance data: page count, filing date
- All record citations listed with supporting assertions

**Agent B: Opinion Mapping** (always)
- Paragraph-by-paragraph map: number, topic, key holding, citations
- Issue structure with paragraph ranges
- Holdings per issue, disposition
- Concurrence/dissent summaries (if any)
- Does NOT receive petition claims — keeps mapping unbiased

**Agent C: Record Verification** (conditional — if record items provided)
- Content verification of each record citation from petition
- Read cited page, compare against petition's characterization
- Report: Verified / Partially verified / **NOT VERIFIED** / Could not check
- **Bold-flag all failures**

**Agent D: Precedent Lookup** (conditional — if new authorities detected)
- Same pattern as jetmemo Agent D
- Focuses on citations NOT in original briefs/opinion
- Notes what each is cited for and whether it was available at time of original briefing

**Agent E: Preservation Check** (conditional — if original briefs provided)
- For each petition claim asserting preservation, read the cited brief location
- Report: Preserved / Partially preserved / Not preserved

**Agent F: Response Analysis** (conditional — if response provided)
- Point-by-point extraction of response arguments
- Procedural objections, new arguments

### Phase 3: Synthesis (Orchestrator, Sequential)

**Step 2: Collect & Cross-Reference**
- Wait for all agents (5-min timeout, same as jetmemo)
- Map each petition claim to opinion paragraphs (Addressed / Partially addressed / Not addressed)
- Compile new authorities table with flags
- Compile record verification results (bold failures)
- Merge preservation results
- Integrate response arguments

**Step 3: Issue-by-Issue Assessment**
For each claimed point:
- Category: overlooked law, overlooked fact, misapprehended law, misapprehended fact
- Merit: Overlooked/Misapprehended, Mere disagreement, or Correction warranted
- Record support status
- Preservation status
- New authorities assessment

**Step 4: Determine Recommendation** (apply decision tree above)

**Step 5: Generate Memo** per rehearing-format.md

**Step 6: Self-Review Checklist**
- All petition claims addressed
- Sequential paragraph numbering
- Each claim maps to specific opinion paragraphs
- Record verification results included (bold failures)
- New authorities flagged
- Preservation checked (if briefs provided)
- Response integrated (if provided)
- Recommendation stated with reasoning
- No placeholders, correct citation format

**Step 7: Write Output** — `{case_number}_rehearing_memo.md`

**Step 8: Citation Verification** (optional, same as jetmemo)

## Output Format (rehearing-format.md)

```
# PETITION FOR REHEARING — RECOMMENDATION MEMO
Header: case number, case name, opinion date, petition date, response status, author

## RECOMMENDATION
[para 1] Bold recommendation + 2-3 sentence reasoning

## RULE 40 COMPLIANCE
[para 2] Timeliness (14-day check), page limit (10 pages), form (Rule 32), particularity

## PETITION SUMMARY
[para 3] Overview of claims raised

## ISSUE-BY-ISSUE ANALYSIS
### Point N: {Petition's characterization}
- Petition's Claim (with petition page cite)
- Opinion's Treatment (with pinpoint opinion para cites)
- Record Support (**BOLD** failures)
- Preservation (if briefs provided)
- Assessment (overlooked/misapprehended, mere disagreement, correction warranted)
- Response (if provided)

## NEW AUTHORITIES (if any)
Table + assessment of propriety

## CONCLUSION
Restate recommendation with summary reasoning
```

## New Script: extract_docx.py

Extracts text from .docx opinions using python-docx:
- Preserves [para N] paragraph numbering
- Detects heading styles → markdown headings
- Handles footnotes
- CLI: `python3 extract_docx.py opinion.docx > opinion.txt`
- Optional `--json` for structured output: `[{para_num, text, style, footnotes}]`
- Dependency: python-docx

## Shared Infrastructure

| Resource | Approach |
|----------|----------|
| `style-spec.md` | Copy from jetmemo (identical) |
| `verify_citations.py` | Copy from jetmemo (identical) |
| `splitmarks.py` | Copy from jetmemo (identical) |
| `jetcite` | Pip dependency (same as jetmemo) |
| `~/refs/` | Same read-only access |
| `check_update.py` | Adapt (change REPO/SKILL_NAME) |
| `install.py` | Adapt (change SKILL_NAME, add python-docx check) |

## Implementation Order

1. **Scaffolding**: repo structure, .gitignore, VERSION, install.sh, adapted install.py/Makefile/check_update.py
2. **Copy shared files**: style-spec.md, verify_citations.py, splitmarks.py
3. **New components**: extract_docx.py, rehearing-format.md, README.md
4. **Core SKILL.md**: Phase 1 → Phase 2 agents → Phase 3 synthesis (largest piece of work)
5. **Validate**: make test, manual test with Rath v. Rath petition + opinion

## Verification

- `make test` — structural validation (all files exist, Python files compile)
- Manual test with Rath v. Rath (petition PDF + opinion docx):
  - Minimal test: petition + opinion only → should get Agents A+B, recommendation
  - Extended: add record items, original briefs → full pipeline
- Verify four recommendation paths work with appropriate inputs
- Verify docx, PDF, and markdown opinion formats all produce usable text
