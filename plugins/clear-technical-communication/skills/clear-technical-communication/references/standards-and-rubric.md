# Standards and evaluation rubric

This skill combines a reader-outcome standard with controlled-English
mechanics. The combination matters: sentence rules cannot repair missing
context, absent analysis, or an unclear reader action.

## ISO 24495-1:2023 Plain language

Use its four governing outcomes at the document or message level:

1. **Relevant** — readers get what they need.
2. **Findable** — readers can easily find what they need.
3. **Understandable** — readers can easily understand what they find.
4. **Usable** — readers can easily use the information.

Apply these outcomes to the intended reader, their knowledge, and the context
in which they will use the communication. Do not substitute readability scores
for reader success.

Official source:
<https://www.iso.org/standard/78907.html>

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

Use selected mechanics as strong technical-writing controls:

- Write short, clear sentences.
- Use one topic or primary assertion per sentence.
- Use a maximum of 25 words for descriptive sentences and 20 words for
  procedural sentences when performing a formal STE pass.
- Use one instruction per procedural sentence except for simultaneous actions.
- Use vertical lists for complex material.
- Replace ambiguous pronouns with the noun they refer to.
- Use controlled, consistent meanings and parts of speech.
- Avoid contractions and potentially confusing Latin abbreviations in formal
  technical text.

Official standard:
<https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf>

Official history and ownership:
<https://www.asd-ste100.org/about_STE.html>

## Limits of ASD-STE100

STE is useful but not sufficient for this skill's purpose. It does not by
itself determine:

- which information the reader needs;
- whether essential context or evidence is missing;
- whether the author has analyzed the available options;
- whether a table is better than prose for a particular comparison;
- whether facts, requirements, proposals, and estimates are distinguishable;
- whether a decision request includes effects and a recommendation;
- whether the final communication lets the reader act.

Therefore, use ISO 24495-1 for message-level outcomes and STE for sentence- and
terminology-level controls.

## Operational evaluation

### Critical failures

Rewrite before sending if any answer is no:

- Can the intended reader state the message's purpose?
- Are required local terms, identifiers, and symbols defined?
- Are causes, contrasts, constraints, and consequences explicit?
- Can the reader distinguish known facts from proposals and open decisions?
- Does the reader know the conclusion or exact response required?

### Strong review signals

Inspect closely when any are present:

- a descriptive sentence longer than approximately 25 words, counting each code
  span, identifier, path, and quoted output as one word;
- three or more unfamiliar local identifiers in one paragraph;
- several comparison dimensions described only in prose;
- essential information inside parentheses;
- two or more semicolons or em dashes carrying logical relationships;
- an approximate quantity without a basis or implication;
- a decision request without option effects or a recommendation;
- phrases such as `only you can answer`, `obviously`, `meaningless`, `dead
  code`, or `N/A` without supporting criteria;
- an embedded code block, configuration, or diagram with no lead-in stating why
  it is present or no reading stating what to take from it;
- a quantity stated with no unit or no reference point that makes it
  interpretable.

Signals are not automatic defects. Verify the actual reader burden and preserve
technical precision.
