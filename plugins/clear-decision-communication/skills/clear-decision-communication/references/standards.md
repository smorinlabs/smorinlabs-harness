# Standards behind the clarity rules

The brief combines a reader-outcome standard with controlled-English
mechanics. The combination matters: sentence rules cannot repair missing
context, absent analysis, or an unclear decision. Read this when a reader
disputes a wording rule, when the pre-send check fails on the four outcomes, or
when someone asks what the rules in `references/clarity.md` rest on.

## ISO 24495-1:2023 Plain language, Part 1: Governing principles and guidelines

Use its four governing outcomes at the level of the whole brief:

1. **Relevant**: readers get what they need. For a brief: the decision, the
   supported recommendation or explicit neutrality, the consequences, the
   evidence, and the next action, and
   nothing about drafting, queuing, or agent coordination.
2. **Findable**: readers can easily find what they need. For a brief: the
   question line is first, the recommendation or explicit neutrality is second,
   every section carries its label, and the options are a list with IDs.
3. **Understandable**: readers can easily understand what they find. For a
   brief: every identifier is described at first use, every claim carries its
   status, every artifact is framed, and the reader's own vocabulary is used.
4. **Usable**: readers can easily use the information. For a brief: the reply
   grammar lets the reader answer in a word, add a condition, skip, or ask.

Apply these outcomes to the intended reader, their knowledge, and the
situation in which they will read: an unattended run, some time after the
work happened, with no memory of the plan in front of them. Do not substitute
readability scores for reader success.

Official source: <https://www.iso.org/standard/78907.html>

## ASD-STE100 Simplified Technical English, Issue 9

ASD-STE100 is a controlled natural language for technical documentation, not a
general-purpose clarity checklist. European airlines asked the European
Association of Aerospace Industries (AECMA, now ASD) for a common controlled
form of English in 1979. AECMA led the development with participation from the
US Aerospace Industries Association (AIA), and the first guide was released in
1986. ASD owns the standard. The ASD Simplified Technical English Maintenance
Group (STEMG) develops and maintains it. Issue 9 was released on January 15,
2025 and changed the subtitle from a specification to a standard for technical
documentation.

The standard has two normative parts: writing rules and a controlled
dictionary. Formal compliance requires applying both parts, including the
approved vocabulary and the rules for permitted technical nouns and verbs.
This skill applies selected writing rules only and never claims compliance.

The mechanics the brief applies, as strong technical-writing controls:

- Write short, clear sentences.
- Use one topic or primary assertion per sentence.
- Treat 25 words for a descriptive sentence and 20 words for a procedural
  sentence as the review signal; code spans, identifiers, paths, and quoted
  output count as one word each.
- Use one instruction per procedural sentence, except for simultaneous
  actions. The "On Q1.A I will" line is procedural.
- Use vertical lists for complex material: options, ladders, and ledgers.
- Replace an ambiguous pronoun with the noun it refers to.
- Use controlled, consistent meanings and parts of speech: one name per thing
  for the whole brief.
- Avoid contractions and Latin abbreviations in the brief's own prose. Never
  restyle quoted or code text.

Official standard: <https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf>
Official history and ownership: <https://www.asd-ste100.org/about_STE.html>

## Limits of ASD-STE100 for a decision request

STE is useful but not sufficient. It does not by itself determine:

- whether a decision is needed at all, or whether a fact was asked instead;
- which information the reader needs, or how deep the brief should go;
- whether essential context, evidence, or an option is missing;
- whether the options exhaust the feasible set;
- whether a table, sequence, or diagram beats prose for this comparison;
- whether verified, inferred, assumed, and not verified are told apart;
- whether a supported recommendation says when it would flip, or neutrality
  names the preference needed to choose;
- whether the reader knows the exact action approval authorizes.

Therefore the gate, the axes, and the six questions decide what the brief
contains; ISO 24495-1 judges the brief as a whole; STE controls its sentences
and terms.

## Operational evaluation

### Critical failures

Do not send if any answer is no:

- Can the reader state the exact decision and the action approval authorizes?
- Are required local terms, identifiers, and symbols defined?
- Are causes, contrasts, constraints, and consequences explicit?
- Can the reader tell verified facts from inferences, assumptions, and
  unknowns, and proposals from decisions already taken?
- Does every option name its consequence? Does a supported recommendation say
  why it wins and when it would not, or does neutrality explain what preference
  would settle the choice without marking an option recommended?
- Does the reader know how to reply?

### Strong review signals

Inspect closely when any are present:

- a descriptive sentence longer than about 25 words, counting each code span,
  identifier, path, and quoted output as one word;
- three or more unfamiliar local identifiers in one paragraph;
- several comparison dimensions described only in prose;
- essential information inside parentheses;
- two or more semicolons or dashes carrying logical relationships;
- an approximate quantity without a basis, a date, or an implication;
- an option without an effect, or a supported recommendation without a
  runner-up condition when there is a meaningful alternative;
- phrases such as "only you can answer", "obviously", "should be fine",
  "probably", or "N/A" without supporting criteria;
- an embedded code block, table, or diagram with no lead-in stating why it is
  present or no reading stating what to take from it;
- a quantity stated with no unit or no reference point that makes it
  interpretable;
- a brief past its tier's length target.

Signals are not automatic defects or hard limits. Keep every material
consequence, uncertainty, and approval boundary visible even when the length
target is exceeded. Verify the actual reader burden and
preserve technical precision: never remove a name, an example, or a quoted
artifact in the name of simplification.
