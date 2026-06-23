---
name: to-design
description: Generate or improve engineering design documents from PRDs, feature requests, issues, architecture notes, or rough implementation ideas. Use when the user asks to write a design doc, technical proposal, implementation design, architecture design, RFC, Go-style proposal, or asks for "to-design", "设计文档", "技术方案", "方案设计", "架构方案", "RFC", or "proposal".
---

# To Design

## Purpose

Turn incomplete requirements or implementation ideas into a clear engineering design document. Optimize for shared decision-making: make the problem, proposal, constraints, tradeoffs, compatibility risks, and rollout plan explicit enough that reviewers can agree or disagree on the same facts.

## Core Workflow

1. Read the source material first: PRD, issue, code context, existing architecture, related APIs, constraints, and discussion links.
2. Identify the document scope: the user-visible change, affected systems, non-goals, compatibility boundary, migration needs, and unresolved questions.
3. Draft the document in this order:
   - Metadata
   - Abstract
   - Background / Motivation
   - Design / Proposal
   - Rationale
   - Compatibility
   - Implementation / Transition
   - Appendix / FAQ
4. Prefer concrete examples over abstract claims. Use real code, request/response examples, schema snippets, state transitions, or before/after behavior wherever possible.
5. Surface tradeoffs and rejected alternatives proactively. A design doc is not a sales pitch; it records why this path is preferable under current constraints.
6. Be honest about costs: performance, operational complexity, behavior changes, compatibility, migration burden, security, observability, and testing gaps.
7. Finish with a review checklist and unresolved questions instead of hiding uncertainty.

## Document Skeleton

Use this skeleton unless the project already has a stronger local template:

```markdown
Title: Proposal: <one sentence saying what changes>
Author(s): <name(s)>
Last updated: <date>
Status: Draft | Reviewing | Accepted | Rejected | Implemented
Discussion: <issue / PR / doc link>

## Abstract
<One paragraph: what will change, roughly how it works, and the most important promise or constraint.>

## Background / Motivation
<Show the pain with concrete examples: bug, confusing behavior, operational issue, duplicated code, scaling limit, or user workflow problem.>

## Design / Proposal
<Explain from simple to complex. For each API or behavior, include declaration/shape, example usage, before/after behavior, and boundaries.>

## Rationale
<Explain why this design was chosen. List rejected alternatives and why they were rejected.>

## Compatibility
<State whether this breaks existing behavior. Describe migration path, opt-in/opt-out strategy, rollout controls, and known costs.>

## Implementation / Transition
<Break implementation into phases. Include tools, data migration, flags, monitoring, rollback, tests, and owner responsibilities.>

## Appendix / FAQ
<Move full API references, extended examples, edge cases, and common objections here.>
```

## Section Guidance

### Metadata

Write a title that is already a conclusion: "Proposal: Add idempotent order import retries" is better than "Order Import Design". Include author, date, status, and a discussion link when available so the document is not detached from the decision trail.

### Abstract

Write one paragraph that lets a busy reviewer understand the whole proposal. Include the most important promise early, such as backward compatibility, no data migration, opt-in rollout, or expected latency budget.

### Background / Motivation

Make the reader feel the problem before presenting the solution. Prefer:

- A failing or confusing code example
- A concrete production incident
- A repeated support or operations workflow
- A before/after request, response, SQL, or event example
- A measurable cost, failure rate, or latency impact

Avoid vague claims like "current design is poor" unless they are immediately backed by evidence.

### Design / Proposal

Teach progressively. Start with the simplest happy path, then add edge cases, extension points, failure handling, and operational boundaries.

For every important API, protocol, schema, or behavior, provide the "shape + example + boundary" trio:

- Shape: method signature, JSON schema, SQL table, message format, config key, or state machine.
- Example: minimal realistic usage or before/after behavior.
- Boundary: what is intentionally unsupported, invalid, deferred, or out of scope.

### Rationale

Separate "what the design is" from "why this design". Include rejected alternatives using this format:

```markdown
### Alternative: <name>

We considered <approach>. It was rejected because <specific reason: compatibility, complexity, performance, operational risk, unclear semantics, migration cost, or poor ergonomics>.
```

This prevents repeated debate and makes the decision more credible.

### Compatibility

If the proposal changes published behavior, say so directly. Cover:

- Existing users and old data
- API, schema, protocol, or config compatibility
- Performance and resource impact
- Security and privacy implications
- Migration path and fallback
- Feature flags, version gates, or gradual rollout

### Implementation / Transition

Make the plan executable. Include phases, owners when known, test strategy, monitoring, rollout, rollback, and cleanup. Use data and tools where possible to justify that the change can be landed safely.

### Appendix / FAQ

Move details that would interrupt the main argument here: full API reference, long examples, rejected edge cases, FAQ, compatibility tables, or benchmark details.

## Style Rules

- Use "we" for decisions and tradeoffs.
- Let code, systems, and data be the subject when describing behavior.
- Use "you" only when explaining what the reader or operator will do.
- Put the conclusion first in each section or paragraph.
- Use short sentences for decisions; use longer sentences only to explain mechanisms.
- Keep one paragraph to one point.
- Use plain, restrained language. Facts, examples, and measured costs are more persuasive than adjectives.
- Do not hide uncertainty. Mark unresolved questions explicitly.

## Self-Review Checklist

Before finalizing, verify:

- The title says what is changing.
- The abstract explains the proposal without requiring later sections.
- The motivation uses concrete evidence, not only adjectives.
- The design includes examples and clear boundaries.
- Rejected alternatives are documented with real reasons.
- Compatibility and migration are handled directly.
- Failure paths, observability, rollback, and tests are covered.
- Open questions are visible instead of buried.
- Appendix material does not interrupt the main argument.
