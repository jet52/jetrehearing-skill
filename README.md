# Jetrehearing Skill

Analyze petition for rehearing and produce memos for the Court. Skill focuses the Court's attention on any misapprehension of fact or law identified in the petition under N.D.R.App.P. 40, checking the cited record for factual assertions and the cited legal authorities for legal arguments. Useful for generating a draft to compare to the memo prepared by a law clerk or staff attorney.

## Not an Official Court Product

Jetrehearing is an independent, open-source project published by an individual
in a personal capacity as legal-educational software, consistent with Rule 3.1
of the North Dakota Code of Judicial Conduct. It is not authorized, endorsed, or
maintained by the North Dakota Supreme Court or the state court system, and is
being developed without court staff, equipment, or resources. It operates only
on publicly filed documents — do not input sealed, confidential, or other
non-public material. Its output, including any recommendation on a petition for
rehearing, is machine-generated and is neither the view of the Court or any
justice nor the Court's disposition of the petition. It is not legal advice.

**Best practice:** Run this tool as a *cross-check, not a substitute* — after a
staff attorney or law clerk has independently assessed the petition. Then compare
the two for any differences in content or recommendation and evaluate why they
diverge. The tool's value is in surfacing points an independent assessment may
have missed, not in replacing it.

## Caution: Privacy Settings Before Use (turn off use of training data)

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (CLI) installed
- `pypdf` — PDF processing library (`pip install pypdf`)
- `python-docx` — Word document extraction (`pip install python-docx`)
- Reference data (see [Reference Data](#reference-data) below)

## Installation

### Claude Code (CLI)

**Option A: From .zip**

1. Download and extract `jetrehearing-skill.zip`
2. Run the installer:
   ```bash
   python3 install.py
   ```

**Option B: From source**

```bash
git clone https://github.com/jet52/jetrehearing-skill.git
cd jetrehearing-skill
python3 install.py
```

**Option C: Manual**

Copy the `skill/` directory contents to `~/.claude/skills/jetrehearing/`:

```bash
mkdir -p ~/.claude/skills/jetrehearing
cp -r skill/* ~/.claude/skills/jetrehearing/
```

## Usage

Trigger phrases:

- "Analyze rehearing petition"
- "Rehearing memo"
- "Review this petition for rehearing"

Provide the petition PDF, the Court's opinion (docx, PDF, or markdown), and optionally a response, original briefs, and record items in the working directory.

## File Structure

```
jetrehearing-skill/
├── README.md
├── VERSION
├── Makefile
├── install.py
├── install.sh
├── .gitignore
└── skill/
    ├── SKILL.md
    ├── references/
    │   ├── rehearing-format.md
    │   └── style-spec.md
    └── scripts/
        ├── check_update.py
        ├── extract_docx.py
        ├── splitmarks.py
        └── verify_citations.py
```

## Reference Data

The skill uses local reference datasets for citation verification and precedent lookup. Without these, the memo will still generate but citation verification and precedent analysis will be limited.

Download the reference archives from [ndconst.org/tools](https://ndconst.org/tools) and install to `~/refs/nd/`:

```bash
mkdir -p ~/refs/nd
unzip opin.zip -d ~/refs/nd/opin
unzip ndcc.zip -d ~/refs/nd/code
unzip ndac.zip -d ~/refs/nd/regs
unzip rule.zip -d ~/refs/nd/rule
```

| Archive                                               | Contents                                 | Install to        | Purpose                                    |
| ----------------------------------------------------- | ---------------------------------------- | ----------------- | ------------------------------------------ |
| [opin.zip](https://ndconst.org/_media/tools/opin.zip) | ND Supreme Court opinions (1997-present) | `~/refs/nd/opin/` | Precedent lookup and citation verification |
| [ndcc.zip](https://ndconst.org/_media/tools/ndcc.zip) | North Dakota Century Code                | `~/refs/nd/code/` | Statutory text verification                |
| [ndac.zip](https://ndconst.org/_media/tools/ndac.zip) | North Dakota Administrative Code         | `~/refs/nd/regs/` | Administrative rule verification           |
| [rule.zip](https://ndconst.org/_media/tools/rule.zip) | North Dakota Court Rules                 | `~/refs/nd/rule/` | Court rule verification                    |

## Other Dependencies

| Dependency                                  | Purpose                            | Required?   |
| ------------------------------------------- | ---------------------------------- | ----------- |
| pypdf                                       | Split PDF packets by bookmark      | Recommended |
| python-docx                                 | Extract text from .docx opinions   | Recommended |
| [jetcite](https://github.com/jet52/jetcite) | Citation extraction and resolution | Required    |

**jetcite** powers the citation checker (`verify_citations.py`). Install as a Claude skill from the GitHub repo, or via pip: `pip install git+https://github.com/jet52/jetcite.git`.

## Contributing

On a fresh clone, activate the local pre-push sensitive-content check:

```bash
git config --local core.hooksPath .githooks
```

It scans commits being pushed for likely ND court dockets, confidential-case
captions, and committed binaries. Bypass once with `git push --no-verify`.
