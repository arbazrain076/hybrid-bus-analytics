# Viva Notes

Prep notes and anticipated questions, organized by report section. Fill in as decisions are made — don't
leave this until the week before the viva. Rehearse via `/viva-drill`.

## Problem Definition & Dataset Selection
- Why this stakeholder and problem framing? Regional Transport Authority was chosen as primary because
  the brief's own Authority stakeholder example ("monitoring operator compliance and service reliability")
  maps directly onto this project's reliability/delay-prediction focus, and naturally covers oversight
  across multiple operators rather than one operator's own fleet. Bus Operators are the secondary
  stakeholder — they benefit from the same delay predictions to improve scheduling, but aren't the primary
  driver of the analysis. See ADR-001 in `docs/architecture-decisions.md` for the full reasoning and the
  rejected alternatives (Bus Operator as primary, Commuter/Passenger App).
- Why these BODS catalogues / this augmentation strategy?
- <answers to be filled in>

## Data Collection & Preprocessing
- Why this cleaning approach for nulls/outliers?
- How was the 100k-record threshold met, and why that method?
- <answers to be filled in>

## Methodology / ML
- Why regression (not classification/clustering)?
- Why these 3 models specifically?
- Why a time-based split instead of random?
- How do the domain metrics (Travel Time Variability, Service Reliability) relate to the ML metrics?
- <answers to be filled in>

## System Design
- Why PySpark for X but Pandas for Y?
- Why this DB schema / this engine (SQLite vs Postgres)?
- How does caching/repartitioning show up in the Spark UI evidence?
- <answers to be filled in>

## Security
- How are SQL injection and credential exposure prevented, concretely?
- <answers to be filled in>

## Evaluation & Reflection
- What's the memory-vs-distributed trade-off, concretely, for this project?
- What are the ethical/GDPR/bias considerations specific to this data?
- What would you do differently with more time/data?
- <answers to be filled in>

## General
- Can you walk through the architecture diagram end to end from memory?
- What was the hardest technical decision, and why?
