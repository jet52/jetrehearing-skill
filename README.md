# Jetrehearing Skill

Analyze petition for rehearing and produce recommendation memos for the Court. Skill evaluates whether the petition identifies points of law or fact the Court overlooked or misapprehended under N.D.R.App.P. 40, and recommends deny petition, request response, correction to opinion, or oral argument. Useful for generating draft to compare to memo prepare by law clerk or staff attorney.

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

Download the reference archives from [ndconst.org/tools](https://ndconst.org/tools) and install to `~/refs/`:

```bash
mkdir -p ~/refs
unzip opin.zip -d ~/refs/opin
unzip ndcc.zip -d ~/refs/ndcc
unzip ndac.zip -d ~/refs/ndac
unzip rule.zip -d ~/refs/rule
```

| Archive                                               | Contents                                 | Install to     | Purpose                                    |
| ----------------------------------------------------- | ---------------------------------------- | -------------- | ------------------------------------------ |
| [opin.zip](https://ndconst.org/_media/tools/opin.zip) | ND Supreme Court opinions (1997-present) | `~/refs/opin/` | Precedent lookup and citation verification |
| [ndcc.zip](https://ndconst.org/_media/tools/ndcc.zip) | North Dakota Century Code                | `~/refs/ndcc/` | Statutory text verification                |
| [ndac.zip](https://ndconst.org/_media/tools/ndac.zip) | North Dakota Administrative Code         | `~/refs/ndac/` | Administrative rule verification           |
| [rule.zip](https://ndconst.org/_media/tools/rule.zip) | North Dakota Court Rules                 | `~/refs/rule/` | Court rule verification                    |

## Other Dependencies

| Dependency                                  | Purpose                            | Required?   |
| ------------------------------------------- | ---------------------------------- | ----------- |
| pypdf                                       | Split PDF packets by bookmark      | Recommended |
| python-docx                                 | Extract text from .docx opinions   | Recommended |
| [jetcite](https://github.com/jet52/jetcite) | Citation extraction and resolution | Required    |

**jetcite** powers the citation checker (`verify_citations.py`). Install as a Claude skill from the GitHub repo, or via pip: `pip install git+https://github.com/jet52/jetcite.git`.
