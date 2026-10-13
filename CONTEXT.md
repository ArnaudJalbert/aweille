# Aweille

Aweille plans running training and keeps planned targets separate from actual results.

## Language

**Planned run**:
A running workout planned for a date, with an optional start time, one run type, and an ordered list of sections. Its targets describe the intended run, separately from any actual results.

**Section**:
One part of a planned run, with a distance and a target pace. Its position in the list defines when it comes within the run; repeated sections remain separate entries.

**Section distance**:
The positive distance planned for one section, measured in whole metres.

**Target pace**:
The intended pace for one section, measured in whole seconds per kilometre.

**Planned date**:
The local calendar day of a planned run in Montreal. A date alone does not imply a start time.

**Planned start time**:
The optional local clock time of a planned run on its planned date, in Montreal, with minute precision.

**Run type**:
One of `easy`, `hard`, `interval`, or `long`, describing a planned run. The type does not impose rules on its sections.

**User note**:
Optional plain text from the user about the whole planned run, separate from the trainer note.

**Trainer note**:
Optional plain text from the external trainer agent about the whole planned run, separate from the user note.
