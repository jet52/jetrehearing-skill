---
name: jetrehearing
description: 'Analyze petitions for rehearing and produce recommendation memos for the North Dakota Supreme Court. Use when the user provides a petition for rehearing and the Court''s opinion and asks to analyze the petition, draft a rehearing memo, or review a petition for rehearing. Triggers: analyze rehearing petition, rehearing memo, jetrehearing, review petition for rehearing, petition for rehearing analysis.'
---

# Petition for Rehearing Analyzer

Analyze petitions for rehearing under N.D.R.App.P. 40 and produce recommendation memos. Uses a three-phase pipeline — Preparation, Parallel Analysis, Synthesis — to evaluate whether the Court overlooked or misapprehended points of law or fact.

## Fixed Paths

| Resource               | Path                                                         |
| ---------------------- | ------------------------------------------------------------ |
| This skill             | `~/.claude/skills/jetrehearing/`                                |
| ND opinions (markdown) | `~/refs/opin/markdown/`                                      |
| ND Century Code        | `~/refs/ndcc/`                                               |
| ND Admin Code          | `~/refs/ndac/`                                               |
| ND Court Rules         | `~/refs/rule/`                                               |
| Style reference        | `~/.claude/skills/jetrehearing/references/style-spec.md`        |
| Memo format reference  | `~/.claude/skills/jetrehearing/references/rehearing-format.md`  |
| Citation checker       | `~/.claude/skills/jetrehearing/scripts/verify_citations.py`     |
| splitmarks             | `~/.claude/skills/jetrehearing/scripts/splitmarks.py`           |
| extract_docx           | `~/.claude/skills/jetrehearing/scripts/extract_docx.py`         |

> **Dependencies:**
> - splitmarks.py requires `pypdf` (`pip install pypdf`)
> - extract_docx.py requires `python-docx` (`pip install python-docx`)
> - verify_citations.py requires `jetcite` — install as a Claude skill from [github.com/jet52/jetcite](https://github.com/jet52/jetcite) or via `pip install git+https://github.com/jet52/jetcite.git`

### ~/refs directory layout

All local reference material lives under `~/refs/`. This directory may or may not exist for a given user; always check before relying on it and fall back to web lookups when absent.

**ND opinions** — `~/refs/opin/markdown/<year>/<year>ND<number>.md` (e.g., `2022/2022ND210.md`). Paragraphs are marked `[¶N]`.

**ND Century Code (N.D.C.C.)** — `~/refs/ndcc/title-<T>/chapter-<T>-<CC>.md` where `<T>` is the title number and `<CC>` is the chapter number (with leading zero). Examples:
- N.D.C.C. § 14-07.1-01 → `~/refs/ndcc/title-14/chapter-14-07.1.md`
- N.D.C.C. § 12.1-02-02 → `~/refs/ndcc/title-12.1/chapter-12.1-02.md`

Each chapter file contains all sections in that chapter as `### § T-CC-SS` headings. To verify a specific section, read the chapter file and search for the section number.

**ND Administrative Code (N.D.A.C.)** — `~/refs/ndac/title-<T>/article-<T>-<AA>/chapter-<T>-<AA>-<CC>.md` where `<T>` is the title, `<AA>` is the article, and `<CC>` is the chapter. Some small articles are a single file: `~/refs/ndac/title-<T>/article-<T>-<AA>.md`. Examples:
- N.D.A.C. § 75-02-01.2-01 → `~/refs/ndac/title-75/article-75-02/chapter-75-02-01.2.md`
- N.D.A.C. § 75-07-01 → `~/refs/ndac/title-75/article-75-07.md` (single-file article)

Each chapter file contains all sections as `### § T-AA-CC-SS` headings.

**ND Court Rules** — `~/refs/rule/<category>/rule-<number>.md`. Categories map from citation abbreviations:

| Citation prefix | Directory |
| --------------- | --------- |
| N.D.R.App.P. | `ndrappp/` |
| N.D.R.Civ.P. | `ndrcivp/` |
| N.D.R.Crim.P. | `ndrcrimp/` |
| N.D.R.Ev. | `ndrev/` |
| N.D.R.Ct. | `ndrct/` |
| N.D.R.Juv.P. | `ndrjuvp/` |
| N.D.Sup.Ct.Admin.R. | `ndsupctadminr/` |
| N.D.R.Prof.Conduct | `ndrprofconduct/` |
| N.D.Code.Jud.Conduct | `ndcodejudconduct/` |

Example: N.D.R.Civ.P. 12(b) → `~/refs/rule/ndrcivp/rule-12.md`. N.D.R.App.P. 35.1 → `~/refs/rule/ndrappp/rule-35.1.md`. The parenthetical (e.g., `(b)`) refers to a subsection within the rule file — read the whole file and search for the subsection.

**READ-ONLY access to `~/refs/` is pre-authorized.** All agents (including subagents) may read files from this directory without additional permission. Never modify, delete, or write to any file in this directory.

---

## Input Documents

| Type | Format | Required | Classification Signal |
|------|--------|----------|----------------------|
| Petition for rehearing | PDF | Yes | "Petition for Rehearing" |
| Court's opinion | docx, PDF, or md | Yes | Opinion header, [¶N] style, "Filed" date |
| Response to petition | PDF | No | "Response to Petition for Rehearing" |
| Appellant brief | PDF | No | "Brief of Appellant" |
| Appellee brief | PDF | No | "Brief of Appellee" |
| Record items | PDF (may need splitting) | No | Record documents, appendix |

## Recommendation Logic

Always state a likely outcome, framed as a prediction based on precedent and the Court's rules — never as a personal recommendation. Use hedged, predictive language ("would likely," "appears to," "under the Court's practice"). Four possible outcomes:

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

---

## Phase 1: Preparation (Orchestrator, Sequential)

### Step 0: Scan & Classify

**Update check:** Run `python3 ~/.claude/skills/jetrehearing/scripts/check_update.py` silently. If it prints output indicating an update, include it as a note to the user.

1. **Scan** the working directory for `.pdf`, `.docx`, and `.md` files.

2. **Classify** each document — read just the first 2 pages (use the Read tool) to determine document type:

   | Type | Look for |
   | ---- | -------- |
   | `petition` | "Petition for Rehearing" |
   | `opinion` | Opinion header with case number, [¶N] paragraph numbering, "Filed" date; or .docx with opinion formatting |
   | `response` | "Response to Petition for Rehearing" |
   | `appellant-brief` | "Brief of Appellant" |
   | `appellee-brief` | "Brief of Appellee", "Brief of State" |
   | `record` | Record documents, appendix |
   | `other` | Anything else |

3. **Handle opinion format:**
   - `.docx` → extract with `python3 ~/.claude/skills/jetrehearing/scripts/extract_docx.py opinion.docx > opinion.txt`
   - `.pdf` → extract with `pdftotext opinion.pdf opinion.txt`
   - `.md` → read directly

4. **Split large record PDFs** via `splitmarks.py` (same pattern as jetmemo):

   ```bash
   python3 ~/.claude/skills/jetrehearing/scripts/splitmarks.py record.pdf --dry-run -vv
   python3 ~/.claude/skills/jetrehearing/scripts/splitmarks.py record.pdf -o .split_records --no-clobber -v
   ```

   After the first pass, check if any output file is still large (>30 pages) and has sub-bookmarks. If so, run `splitmarks` again on that file. Repeat until every output file is a single record item or has no further bookmarks.

5. **Build manifest:** `{path, type, format, page_count}` for every document. Set `has_response` flag based on whether a response document is found.

6. If **no petition or no opinion** is found, ask the user.

### Step 1: Extract & Prepare

1. **Read references** into main context:
   - `~/.claude/skills/jetrehearing/references/style-spec.md`
   - `~/.claude/skills/jetrehearing/references/rehearing-format.md`

2. **Extract text** from all PDFs using `pdftotext`:

   ```bash
   pdftotext <file>.pdf <file>.txt
   ```

3. **Quality check:** Mark a document as `needs_visual_read: true` in the manifest if **any** of these conditions are met:
   - The `.txt` file is nearly empty (< 100 characters) for a multi-page PDF
   - The average words per line is < 3 (indicates OCR degradation)
   - The text contains a high ratio of garbled characters or encoding artifacts

   Quick check for line-to-word ratio:

   ```bash
   awk '{words+=NF; lines++} END {if(lines>0) printf "%.1f words/line\n", words/lines}' file.txt
   ```

   When `needs_visual_read` is set, the agent prompt **must** receive the PDF path (not the `.txt` path) with explicit instructions: "Use the Read tool on this PDF directly, reading page by page."

4. **Extract citation lists:** Run the citation checker separately on petition, opinion, and briefs (if provided):

   ```bash
   python3 ~/.claude/skills/jetrehearing/scripts/verify_citations.py --file petition.txt --refs-dir ~/refs --json > petition_citations.json
   python3 ~/.claude/skills/jetrehearing/scripts/verify_citations.py --file opinion.txt --refs-dir ~/refs --json > opinion_citations.json
   ```

   If briefs are provided:
   ```bash
   cat appellant_brief.txt appellee_brief.txt | python3 ~/.claude/skills/jetrehearing/scripts/verify_citations.py --refs-dir ~/refs --json > briefs_citations.json
   ```

5. **Compute new authorities:** Compare petition citations against opinion and briefs citations. Any citation in the petition that does NOT appear (by normalized field) in the opinion or briefs is a "new authority." This determines whether Agent D launches.

6. **Determine which conditional agents to launch:**
   - Agent C (Record Verification): if record items are in the manifest
   - Agent D (Precedent Lookup): if new authorities were detected
   - Agent E (Preservation Check): if original briefs are in the manifest
   - Agent F (Response Analysis): if a response document is in the manifest

---

## Phase 2: Parallel Analysis (Subagents)

Launch all applicable agents **simultaneously** using the Agent tool (`subagent_type: general-purpose`). Each agent gets:

- Paths to relevant `.txt` files (or PDF paths if `needs_visual_read`)
- Focused extraction instructions
- Expected output format (structured markdown)

### Agent A: Petition Extraction (always)

**Reads:** petition text

**Prompt template:**

> **Petition for Rehearing Extraction**
>
> Read: `[path to petition .txt or .pdf]`
>
> Extract the following in structured markdown:
>
> **1. Compliance Data**
> - Filing date
> - Page count
> - Whether it states points with particularity
>
> **2. Claimed Points**
> For each point the petition raises:
> - Point number and heading (use petition's own numbering/headings)
> - Category: overlooked law, overlooked fact, misapprehended law, or misapprehended fact
> - Specific claim: what exactly does the petition say the Court overlooked or misapprehended?
> - Opinion citations: which opinion paragraphs does the petition reference?
> - Record citations: which record items does the petition cite, with the assertion each supports?
> - Authority citations: which cases, statutes, or rules does the petition cite?
> - Preservation assertion: does the petition claim this was raised in the original briefing? If so, where?
>
> **3. All Record Citations**
> List every record citation in the petition with the assertion it supports.
>
> **4. All Authority Citations**
> List every case, statute, or rule citation in the petition.
>
> **Citation precision:** For every assertion, provide the petition page cite.
>
> Return only the structured extraction. Do not analyze or recommend.

### Agent B: Opinion Mapping (always)

**Reads:** opinion text (from .txt extraction, .md, or PDF)

**Important:** Agent B does NOT receive the petition's claims. This keeps the mapping unbiased.

**Prompt template:**

> **Opinion Mapping**
>
> Read: `[path to opinion .txt, .md, or .pdf]`
>
> Extract the following in structured markdown:
>
> **1. Case Metadata**
> - Case number, case name
> - Opinion date
> - Author (justice writing the opinion)
> - Joined by (other justices)
>
> **2. Paragraph-by-Paragraph Map**
> For each paragraph [¶N]:
> - Paragraph number
> - Topic (1-2 word label)
> - Key holding or finding (1 sentence)
> - Citations in that paragraph
>
> **3. Issue Structure**
> - List each issue the opinion addresses with its paragraph range
> - Standard of review stated for each issue
>
> **4. Holdings**
> - Per-issue holding (affirm, reverse, remand, etc.)
> - Overall disposition
>
> **5. Concurrence/Dissent**
> If any separate writings exist:
> - Author, type (concurring, dissenting, concurring specially)
> - Key points of disagreement
> - Paragraph range
>
> Return only the structured extraction. Do not analyze or recommend.

### Agent C: Record Verification (conditional — if record items provided)

**Reads:** record item PDFs/texts cited by the petition

**Prompt template:**

> **Record Verification**
>
> The petition for rehearing cites the following record items. For each, read the cited page and compare against the petition's characterization.
>
> Record citations from petition:
> [Insert record citations with assertions from Agent A output]
>
> Record files available:
> [Insert paths to record item files]
>
> For each citation:
> 1. Read the cited record page
> 2. Compare the petition's characterization against what the page actually says
> 3. Report:
>    - **Verified** — the record supports the petition's characterization
>    - **Partially verified** — the record partially supports but the characterization is incomplete or slightly inaccurate
>    - **NOT VERIFIED** — the record does not support the petition's characterization (**bold this**)
>    - **Could not check** — the cited page/document was not available
>
> **Bold-flag all failures.** This is critical for the recommendation memo.
>
> Return the results as a table:
>
> | Record Cite | Petition's Claim | Actual Content | Status |
> |-------------|-----------------|----------------|--------|
>
> Return only the verification results. Do not analyze or recommend.

### Agent D: Precedent Lookup (conditional — if new authorities detected)

**Reads:** local opinion markdown files (preferred), web sources via jetcite-provided URLs (fallback)

**Input:** Pass Agent D the list of new authority citations (those in the petition but NOT in the original briefs or opinion). Each entry includes `cite_type`, `local_path`, `local_exists`, `url`, and `search_hint`.

**Prompt template:**

> **New Authority Verification**
>
> The petition for rehearing cites the following authorities that did NOT appear in the original briefs or opinion. For each, look up the authority and assess its relevance.
>
> **Citation data format:** Each citation entry includes:
> - `cite_text` / `normalized`: the citation string
> - `cite_type`: type of citation
> - `local_path` / `local_exists`: path in `~/refs/` and whether the file exists
> - `url`: source URL
> - `search_hint`: text to match within the file
>
> **Lookup strategy:**
>
> **ND cases (`nd_case`):**
> 1. If `local_exists` is `true`, use the Read tool on `local_path`. Paragraphs are marked `[¶N]`.
> 2. If `local_exists` is `false`, use WebFetch on the `url`. Fall back to:
>    `https://www.ndcourts.gov/supreme-court/opinions?cit1=YYYY&citType=ND&cit2=NNN&pageSize=10&sortOrder=1`
> 3. CourtListener search API: `https://www.courtlistener.com/api/rest/v4/search/?q=%22YYYY+ND+NNN%22&type=o`
>
> **Other citation types:** Use `local_path` if `local_exists`, otherwise WebFetch on `url`.
>
> **Citations to verify:**
> [Insert new authority citation entries]
>
> **For each citation:**
> 1. Locate the authority
> 2. Extract the holding or relevant text
> 3. Assess: does it support the proposition the petition cites it for?
> 4. Note whether this authority was available at the time of original briefing (compare its date against the original brief filing dates)
>
> Return:
>
> | Citation | Cited For | Holding/Key Rule | Supports Petition? | Available at Briefing? |
> |----------|-----------|------------------|--------------------|----------------------|
>
> Return only the verification results. Do not analyze or recommend.

### Agent E: Preservation Check (conditional — if original briefs provided)

**Reads:** original appellant and appellee briefs

**Prompt template:**

> **Preservation Check**
>
> The petition for rehearing claims the following points were raised in the original briefing. For each, check whether the argument was actually raised.
>
> Claims from petition:
> [Insert preservation assertions from Agent A output, with cited brief locations]
>
> Brief files:
> - Appellant brief: `[path]`
> - Appellee brief: `[path]`
>
> For each preservation claim:
> 1. Read the cited location in the brief
> 2. Compare against the petition's characterization of what was argued
> 3. Report:
>    - **Preserved** — the argument was clearly raised in the original briefing
>    - **Partially preserved** — a related argument was raised but the specific point in the petition was not
>    - **Not preserved** — the argument does not appear in the original briefing at the cited location (or at all)
>
> Return as a table:
>
> | Petition Point | Claimed Location | Actual Brief Content | Status |
> |---------------|-----------------|---------------------|--------|
>
> Return only the verification results. Do not analyze or recommend.

### Agent F: Response Analysis (conditional — if response provided)

**Reads:** response to petition for rehearing

**Prompt template:**

> **Response to Petition Analysis**
>
> Read: `[path to response .txt or .pdf]`
>
> Extract the following in structured markdown:
>
> **1. Point-by-Point Response**
> For each point the response addresses:
> - Which petition point it responds to
> - The response's argument (with page cites)
> - Any procedural objections (timeliness, scope, etc.)
>
> **2. New Arguments**
> Any arguments the response raises that go beyond responding to the petition's claims.
>
> **3. Procedural Objections**
> Any arguments that the petition is procedurally defective (untimely, exceeds page limit, fails to state with particularity, raises new arguments, etc.).
>
> Return only the structured extraction. Do not analyze or recommend.

---

## Phase 3: Synthesis (Orchestrator, Sequential)

### Step 2: Collect & Cross-Reference

**GATE: Do not begin synthesis until ALL launched agents have returned or timed out (5-minute timeout).** Use `TaskOutput` with `block: true` for each agent to wait for completion. If an agent exceeds the timeout, treat it as failed and apply fallback handling.

Collect results from all agents. Then:

1. **Map each petition claim to opinion paragraphs:**
   - Using Agent A's claims and Agent B's paragraph map, determine for each claim whether the opinion:
     - **Addressed** — the opinion directly addressed the point (cite specific ¶¶)
     - **Partially addressed** — the opinion touched on the topic but did not address the specific claim
     - **Not addressed** — the opinion did not discuss this point at all

2. **Compile new authorities table** from Agent D results (if launched), with flags for whether each was available at time of briefing.

3. **Compile record verification results** from Agent C (if launched). **Bold all failures.**

4. **Merge preservation results** from Agent E (if launched).

5. **Integrate response arguments** from Agent F (if launched).

**Fallback handling:** If any subagent fails or times out, read the relevant document(s) directly in main context and perform that analysis step here. If >50% of documents failed text extraction in Step 1, abandon the parallel approach entirely and fall back to sequential multimodal reads of the PDFs.

### Step 3: Issue-by-Issue Assessment

For each claimed point in the petition:

1. **Category:** Classify as overlooked law, overlooked fact, misapprehended law, or misapprehended fact (use the petition's own characterization as a starting point, but verify).

2. **Merit assessment:** Apply one of three labels:
   - **Overlooked/Misapprehended** — The petition identifies a genuine point the Court overlooked or misapprehended. This could change the result.
   - **Mere disagreement** — The petition reargues the same position presented in the original briefing, which the Court considered and rejected. The Court addressed the point; the petitioner simply disagrees with the outcome.
   - **Correction warranted** — The petition identifies an error (factual, citation, typographical) that should be fixed but does not affect the result.

3. **Record support status:** From Agent C results — are the petition's factual assertions supported by the record?

4. **Preservation status:** From Agent E results — was this argument raised in the original briefing?

5. **New authorities assessment:** From Agent D results — are the new citations relevant, and were they available at time of briefing?

### Step 4: Determine Recommendation

Apply the decision tree:

```
All points = mere disagreement → DENY
Any genuine oversight that doesn't change result → CORRECTION
Any genuine oversight that could change result:
  No response received (has_response = false) → REQUEST RESPONSE
  Response received (has_response = true), still uncertain → ORAL ARGUMENT
Close call (could be oversight, uncertain):
  No response received → REQUEST RESPONSE
  Response received → DENY (with notation that the question was close)
```

### Step 5: Generate Memo

Write the complete recommendation memo in markdown per `rehearing-format.md`:

1. **Header** — case number, case name, opinion date, petition date, response status
2. **RECOMMENDATION** [¶1] — bold likely outcome + 2-3 sentence predictive reasoning
3. **RULE 40 COMPLIANCE** [¶2] — timeliness, page limit, form, particularity
4. **PETITION SUMMARY** [¶3] — overview of claims
5. **ISSUE-BY-ISSUE ANALYSIS** — for each point:
   - Petition's Claim (with petition page cite)
   - Opinion's Treatment (with pinpoint [¶N] cites)
   - Record Support (**bold failures**)
   - Preservation (if briefs provided)
   - Assessment
   - Response (if provided)
6. **NEW AUTHORITIES** — table if any new citations detected
7. **CONCLUSION** — restate likely outcome with summary reasoning

### Step 6: Self-Review Checklist

Review the memo against this checklist before presenting:

- [ ] All petition claims addressed
- [ ] Sequential paragraph numbering [¶1], [¶2], etc. throughout
- [ ] Each claim maps to specific opinion paragraphs with [¶N] cites
- [ ] Record verification results included (**bold failures**)
- [ ] New authorities flagged (if any)
- [ ] Preservation checked (if briefs provided)
- [ ] Response integrated (if provided)
- [ ] Likely outcome stated with predictive reasoning in [¶1] and CONCLUSION
- [ ] Rule 40 compliance section complete
- [ ] No placeholders, correct citation format
- [ ] Only "the Court" for ND Supreme Court, "the district court" for lower court
- [ ] No "I" or "we"

Fix any issues found before presenting the memo to the user.

### Step 7: Write Output

Write the memo to a file in the current working directory:

- Default filename: `{case_number}_rehearing_memo.md`
- If the user specifies a different output path, use that

### Step 8: Citation Verification (Optional)

If the user requests verification, run the citation checker on the finished memo:

```bash
python3 ~/.claude/skills/jetrehearing/scripts/verify_citations.py --file {memo_file} --refs-dir ~/refs
```

For JSON output, add `--json`.

After verification, append a summary to the memo:

```
## CITATION VERIFICATION

Verified: X | Unverified: Y | Skipped: Z

### Unverified Citations
- [list any citations that could not be confirmed]
```

Record citations (R##) reference the appellate record and are not checked by the script.

---

## Token Efficiency

| Content           | Strategy                                  | Rationale                            |
| ----------------- | ----------------------------------------- | ------------------------------------ |
| Petition (10pp)   | `pdftotext` -> `.txt`, agent reads text   | ~50% token savings vs multimodal PDF |
| Opinion (docx)    | `extract_docx.py` -> `.txt`               | Preserves [¶N] numbering            |
| Opinion (PDF)     | `pdftotext` -> `.txt`                     | Efficient text extraction            |
| Opinion (md)      | Read directly                             | Already markdown                     |
| Large record PDFs | `splitmarks` first, then extract per-file | Agents load only relevant documents  |
| Scanned PDFs      | Agent uses `Read` on PDF directly         | Fallback when text extraction fails  |
| Reference files   | Orchestrator reads directly               | Small, needed for synthesis          |

## Fallback Handling

- If a subagent fails or times out: orchestrator reads the document directly in main context and performs that analysis step itself
- If `pdftotext` produces empty output or poor quality (avg < 3 words/line): mark `needs_visual_read` and pass the PDF path to the subagent with explicit instructions to use the Read tool on the PDF directly
- If `splitmarks` finds no bookmarks: document stays intact, processed as-is
- If `extract_docx.py` is not available (python-docx missing): fall back to reading the .docx with the Read tool directly
- If >50% of documents fail text extraction: abandon parallel approach, fall back to sequential multimodal reads

## Important Rules

- **Never fabricate citations.** Only cite cases and authorities that appear in the petition, opinion, or original briefs.
- **Never use placeholder brackets** like [Date], [page], [County]. If information is unavailable, omit it or write "not specified in the record."
- **Always state a likely outcome.** Every rehearing memo must include a predicted outcome (deny, request response, correction, or oral argument), framed as what the Court would likely do based on precedent and rules — never as a personal recommendation. Use hedged, predictive language; never first person; never emphatic or certain.
- **Record citations are critical.** Bold-flag any record citation that does not support the petition's characterization.
- **Use "the Court"** when referring to the ND Supreme Court; **"the district court"** for the lower court.
- **Pinpoint opinion paragraph cites** are mandatory when discussing the opinion's treatment of a point. Always use [¶N] format.
- **Rule 40 standard only.** The analysis is limited to whether the Court overlooked or misapprehended points of law or fact. Do not re-analyze the merits de novo.
