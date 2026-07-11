---
name: "<agent-name>"
description: "<When to use this agent, with 1-2 <example> blocks showing invocation context.>"
tools: Read, Grep, Glob, Bash
model: sonnet
memory: project
---

# <Agent Name>

## Role

<Clear one-paragraph description of what this agent does.>

## Scope

| Permission | Details                            |
| ---------- | ---------------------------------- |
| Read       | <What files this agent can read>   |
| Write      | <What files this agent can write>  |
| Execute    | <What commands this agent can run> |
| Forbidden  | <What this agent must NOT do>      |

## Capabilities

1. <Capability 1>
2. <Capability 2>

## Workflow

1. <Step 1>
2. <Step 2>

## Verification

This agent verifies its own output by:

- <Verification step 1>

## Context loading

- `.claude/BOOTSTRAP.md`
- <Relevant rules>
- <Relevant skills>
