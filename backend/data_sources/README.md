# 📄 **README — Data Sources Directory**

This directory contains **all real-world data files** required to seed the baseline simulation world.

These files are used **only during the seeding process** (see `seed_baseline_world.py`) and **must never be loaded at runtime** by PFEE, Autonomy Engine, or any interactive system.
They provide the *initial* psychological, relational, and environmental facts used to construct the baseline world state.

---

## 🔒 **Authoritative Rules**

1. **These files define the initial state of the simulation world.**
   They must not be moved, renamed, re-formatted, or replaced without updating the mapping layer.

2. **The seed script and mapping functions MUST load data from this directory only.**
   No other directory may contain source-of-truth data for world seeding.

3. **PFEE and the Autonomy Engine must never read these files.**
   They operate *only* on the database state created by the seeding process.

4. **Paths must always be resolved dynamically**, using Python’s `pathlib`, never hardcoded.
   Example:

   ```python
   DATA_DIR = Path(__file__).resolve().parent
   path = DATA_DIR / "Rebecca_Fingerprint.json"
   ```

5. **Do not store processed or intermediate files here.**
   Only raw human-editable documents go in this directory.

---

## 📂 **Files in This Directory**

The following files must always exist here:

### **1. `Rebecca_Fingerprint.json`**

Structured psychological fingerprint for Rebecca Ferguson.
Used to generate:

* personality kernel
* drives
* mood baselines
* domain summaries
* archetype blend

### **2. `Rebecca Master Profile.csv`**

~500-row dataset of Rebecca’s biography, traits, values, tensions, and milestones.
Used to generate:

* memories
* arcs
* personality summaries
* domain summaries

### **3. `Rebecca Ferguson - Connections.csv`**

Detailed relationship graph with collaborators, family, friends.
Used to seed:

* relationship vectors for Rebecca → others
* baseline social graph

### **4. `Personalities.txt`**

List of 15 archetypes with behavioural signatures.
Used to derive:

* archetype_blend
* secondary trait weighting
* personality kernel scaffolds

### **5. `Sim Baseline.docx`**

Full baseline description of:

* the Cookridge house layout
* objects
* routines
* context
* initial world time
  Used to seed:
* locations
* objects
* initial positions
* calendar items

### **6. `George_Profile.txt`**

External, public-only facts about the real user (George).
Used to seed:

* George’s physical agent row
* public identity presence
  **Never used as internal psychological data.**

---

## 🧩 **How these files are used**

### During Seeding (`seed_baseline_world.py`):

1. Mapping layer loads these files into structured objects.
2. The seed script converts them into:

   * agents
   * relationships
   * memories
   * arcs
   * influence fields
   * calendars
   * physical world layout
3. The database is populated with a complete baseline world.

### After Seeding:

* These files are **never touched** by runtime code.
* PFEE uses only database state.
* Autonomy Engine uses only database state.
* The real user (George) is never simulated internally.

---

## 🛑 **Do Not Do This**

* ❌ Do not load these files inside PFEE modules.
* ❌ Do not put logs, outputs, or test artifacts in this folder.
* ❌ Do not rename files without updating mapping functions.
* ❌ Do not embed or duplicate these files elsewhere.

---

## 🧪 **For Testing**

Tests should rely on:

* test fixtures
* synthetic DB entries
* the seed script output

**Tests must never load these files directly.**

They verify the correctness of:

* mapping functions
* seeding output
* PFEE behaviour
* autonomy behaviour
* George-protection constraints

---

## ✔️ **Summary**

This directory is the **single, mandatory, canonical** location for:

* Rebecca’s psychological data
* Rebecca’s biography & connections
* Personality archetypes
* The physical world baseline
* George’s external profile

Every element of world seeding depends on these files being present and unchanged.

If you add new data (e.g., new characters), it must be placed here, and the mapping/seeding code updated accordingly.