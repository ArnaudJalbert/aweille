# Aweille

Aweille plans training and keeps planned targets separate from actual results.

## Language

**Training block**:
One independently planned occurrence of training, such as a run, stretching routine, strength workout, or yoga practice. Several blocks can share a day, with each scheduled, moved, or skipped independently.
_Avoid_: Section, training cycle

**Training kind**:
The activity a training block represents, such as running, stretching, strength training, or yoga. A training kind is distinct from the run type of a running block.

**Strength training**:
Training using resistance, including bodyweight exercises or equipment. This is the specific activity meant by a strength workout, rather than a name for all training.

**Planned run**:
A training block for running, planned for a date with an optional start time, one run type, and an ordered list of sections. Its targets describe the intended run, separately from any actual results.

**Planned-run edit**:
A partial change to an existing planned run's date, start time, run type, ordered sections, or user and trainer notes, preserving any fields not supplied. The run keeps its identity when edited, including when rescheduled.

**Planned-run deletion**:
Permanent removal of a planned run, whose identity cannot be reused. Deletion leaves no workout in training history and is separate from skipping a workout.

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
