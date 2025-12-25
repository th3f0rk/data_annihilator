    ______      _           ___              _ _     _ _       _             
    |  _  \    | |         / _ \            (_) |   (_) |     | |            
    | | | |__ _| |_ __ _  / /_\ \_ __  _ __  _| |__  _| | __ _| |_ ___  _ __ 
    | | | / _` | __/ _` | |  _  | '_ \| '_ \| | '_ \| | |/ _` | __/ _ \| '__|
    | |/ / (_| | || (_| | | | | | | | | | | | | | | | | | (_| | || (_) | |   
    |___/ \__,_|\__\__,_| \_| |_/_| |_|_| |_|_|_| |_|_|_|\__,_|\__\___/|_|

# Data Annihilator v2.0 — Engineering Roadmap

**Primary goals**
- Ship a stable, polished v2.0 desktop application
- Replace Faker-driven generation with spec + LLM–driven generation
- Generate vision-ready datasets (images + ground truth)
- Preserve reproducibility, stability, and ease of use
- Optimize for education, research, and internal tooling (not enterprise)

**Later Goals (v2.0)**
- Non-vision oriented data capabilities (audio, tabular, etc.)
- Proprietary Overfitting Distribution model that checks data against different preset distrutions to determine if the text data is overconcetrated and will result in overfitting (this will be limited and designed for like general OCR and vision for the benefit of students)
- Built in NeoVim terminal instance to edit the yaml files and such. Very important to the core design philosophy. Important as a flex and to indoctrinate the next generation of students to using the superior text editor.
- UX improvements as needed. This thing needs to be very satisfying and easy to use.

---

## System Philosophy (design constraints)

- Image-first rendering (PNG/JPEG)
- PDFs are optional export artifacts, really just for user convienience since PDFs are not necessary for vision model training.
- All user customization flows through **validated specs**, not arbitrary code
- Core engine must be deterministic and reproducible
- UI must expose the pipeline clearly and visibly but only in a manner where the user can edit the structure, variance, and ground_truth through something like YAML files. The user should not be able to edit code.
- Dependencies should be minimal and well-isolated. Reportlab should be the only dependecy and I want to rewrite the api so it is more readable for students and users to call easily (something like renderer.function rather than reportlab.function)

---

## 1. Core Engine (no UI)

### 1.1 Internal data model
Define the **in-memory contract** everything else depends on.

- `DocumentSpec`
  - page size (pixels)
  - Dots Per Inch (DPI)
  - margins
  - blocks (ordered)
- `LayoutBlock`
  - type (paragraph, header, table, image, line)
  - bounding box (absolute or relative)
  - style reference
  - content reference
- `Style`
  - font family
  - font size
  - spacing
  - alignment
- `GroundTruth`
  - word-level boxes
  - line-level boxes
  - block-level boxes
  - reading order
  - metadata
- `Sample`
  - image path(s)
  - ground truth path(s)
  - seed
  - spec hashes

**Acceptance**
- Able to serialize `Sample` → `manifest.json`
- Able to load it back losslessly

---

### 1.2 Renderer abstraction
Isolate rendering behind a **single stable interface**.

**Renderer interface**

**RenderResult**
- page images (pixel arrays or file paths)
- exact pixel coordinates used
- font metrics used
- page metadata

#### Backends
- ReportLab-backed renderer (vendored/frozen if desired)
- Future image-first renderer (Pillow / Skia / Cairo)

#### Rules
- Only renderer modules may import rendering libraries
- Core engine never imports ReportLab directly
- Renderer selection happens via config

#### Acceptance criteria
- Swapping backend does not require engine changes
- GT boxes align pixel-perfectly with rendered output

---

## 2. Spec System (User-editable Surface)

### 2.1 Structure spec (`structure.yaml`)

Defines **layout and variance**, not text content.

#### Responsibilities
- Page dimensions and DPI
- Margins and gutters
- Block templates
- Repetition and conditional rules
- Variance distributions
- Multi-page document logic

#### Features
- Deterministic randomness (seeded)
- Optional and conditional blocks
- Weighted block inclusion
- Distribution constraints (min/max)

#### Validation
- Schema validation
- Field-level error messages
- Line-number error reporting

#### Acceptance criteria
- Valid YAML → DocumentSpec
- Invalid YAML → actionable errors
- Same seed → same layout

---

### 2.2 Ground truth spec (`groundtruth.yaml`)

Defines **what labels exist and how they are written**.

#### Responsibilities
- Granularity selection (word/line/block)
- Output formats
- Coordinate systems
- Label naming
- Metadata inclusion

#### Output formats

This will ultimately be defined by the user but default presets will be provided in documentation or something
- JSON
- JSONL
- COCO-style
- Custom structured formats

#### Acceptance criteria
- GT aligns exactly with rendered pixels
- GT format is renderer-independent
- One sample produces complete, consistent labels
- GT consistent across all samples unless users want GT variance (idk why they would though)

---

### 2.3 Ruleset spec (`ruleset.yaml`)

Defines **LLM behavior**, not model choice.

#### Responsibilities
- System instructions
- Output schema
- Field constraints
- Banned patterns
- Length limits
- Domain presets (invoice, letter, form, etc.)

#### Design
- User never writes prompts directly (though the user could theoretically edit this ruleset.yaml if they want different rulesets for their LLM)
- Engine enforces strict structured output
- Schema-based validation

#### Acceptance criteria
- LLM output always parses or is repaired
- Invalid outputs never crash the pipeline

---

## 3. Content Generation (LLM Layer)

### 3.1 Provider abstraction


#### Initial provider
- OpenAI-compatible HTTP API
- Compatible with local inference servers:
  - Ollama
  - vLLM
  - LM Studio
  - Similar

#### Configurable parameters
- model name
- temperature
- top_p
- max tokens
- retries
- timeout

---

### 3.2 Structured output enforcement

#### Pipeline
1. Request structured JSON
2. Validate against schema
3. If invalid:
   - Issue repair prompt
   - Retry N times
4. If still invalid:
   - Fallback deterministic generator

#### Acceptance criteria
- Dataset generation never fails due to LLM output
- Worst case: degraded but valid content

---

## 4. Dataset Generation Pipeline

### 4.1 Generation flow
load specs
->
generate structure
->
generate content (LLM)
->
layout engine
->
render image(s)
->
emit ground truth
->
update manifest

### 4.2 Metadata and reproducibility

Each dataset run records:
- structure spec hash
- groundtruth spec hash
- ruleset hash
- renderer backend + version
- provider config
- seeds

#### Acceptance criteria
- Entire dataset reproducible from manifest alone

---

## 5. UI Application

### 5.1 Project management
- New project
- Open project
- Project directory layout:
  - structure.yaml
  - groundtruth.yaml
  - ruleset.yaml
  - output/

---

### 5.2 Embedded editor (v2.0)
- Basic text editor
- Syntax highlighting (optional)
- Validate button
- Error panel
- Save state automatically

(Long-term: vim motions / advanced editor)

---

### 5.3 Preview & inspection
- Generate single sample
- Image preview panel
- Thumbnail navigation
- GT overlay toggle
- Visual reading order inspection

#### Acceptance criteria
- User can iterate quickly:
  edit YAML → preview → inspect → adjust

---

### 5.4 Batch generation
- Set sample count
- Progress indicator
- Cancel / resume
- Open output directory

---

## 6. Settings System

### 6.1 Persistent config
Stored in:
- `~/.data_annihilator/config.yaml` or `.toml`

#### Settings include
- Output defaults
- Renderer backend
- DPI/page size
- Provider endpoint
- Performance limits
- Retry policies

#### Acceptance criteria
- Settings persist across restarts
- Changes apply without restarting app

---

## 7. Export Formats

### 7.1 Canonical outputs
- PNG (default)
- JPEG / WebP optional

### 7.2 Optional PDF export
- Image-only PDFs
- Optional dependency
- Feature-gated

#### Acceptance criteria
- Core engine functions without PDF
- PDF is convenience only

---

## 8. Packaging and Updates

### 8.1 Packaging
- Single executable per OS
- Assets and templates bundled
- Stable path handling

### 8.2 Auto-updater
- Version manifest
- Download
- Verify
- Atomic replace
- Restart

#### Acceptance criteria
- Update without reinstall
- Rollback on failure

---

## 9. Repo Hygiene & Credibility

Required files:
- LICENSE (custom non-commercial / educational)
- THIRD_PARTY_LICENSES/
- NOTICE
- CHANGELOG.md
- examples/
- minimal tests

Tests include:
- Spec validation
- Golden sample generation

#### Acceptance criteria
- Fresh clone → dataset generation < 5 minutes

---

## 10. Planned Directory Structure
    data_annihilator_v2/
    ├── app/
    │ ├── gui/
    │ ├── css/
    ├── core/
    │ ├── pipeline/
    │ ├── specs/
    │ ├── generation/
    │ ├── layout/
    │ ├── renderers/
    │ ├── groundtruth/
    │ └── utils/
    ├── templates/
    ├── examples/
    ├── assets/
    ├── docs/
    │ └── ROADMAP_V2.md
    ├── THIRD_PARTY_LICENSES/
    ├── LICENSE
    ├── README.md
    └── pyproject.toml


---

## 11. Planned Build Order

1. Internal data model + manifest
2. Structure YAML → layout engine
3. Renderer abstraction + backend
4. Single-sample rendering + GT
5. Preview UI
6. LLM provider + ruleset
7. Batch generation
8. Settings UI
9. Updater
10. Polish, docs, tests

---

## 12. Definition of “v2.0 Shipped”

v2.0 is complete when:

- YAML-defined datasets generate reproducibly
- Images + ground truth are emitted correctly
- Preview and inspection work
- LLM failures are handled gracefully
- UI is stable and understandable
- Updater works
- Repo reads as a maintained, intentional tool
