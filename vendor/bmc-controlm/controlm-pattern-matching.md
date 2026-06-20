# Control-M Pattern-Matching Strings - Vendor Specifications

**Source:** BMC Software - Control-M SaaS Documentation  
**Document:** Pattern-Matching_Strings.htm  
**Date Scraped:** 2026-06-11  
**Purpose:** Pattern matching syntax, wildcards, and string comparison reference

⚠️ **VERSION NOTICE:** This documentation is sourced from Control-M SaaS (latest version) but is being applied to Control-M version 9.0.21.300. While the core functionality should be compatible, there may be differences in features, parameters, or behavior between SaaS and version 9.0.21.300. Consult version-specific documentation when encountering discrepancies.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content · **[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth). See SOURCE-MANIFEST default tier rule.

- **GROUNDED:** Wildcard set (`*`, `?`, `.`, `!`, `+`, `{n}`, `{n,m}`, `( )`, `,`); `\` escape; IF MATCHES operator; no-apostrophes-in-event-names / parenthesis-escaping constraints; "blank fields more efficient than `*`" performance note.
- **SYNTHESIZED:** All example tables, Notes for Planning Agents, Vendor Attributes table.

---

## Pattern Matching Overview

Control-M supports pattern-matching for "searching character patterns and symbols in filters."

**Primary Use Cases:**
- Search and filter operations
- Job name and parameter matching
- Condition evaluation in if-actions
- String comparison in prerequisites
- Application and folder filtering

**Scope:** Available in filters throughout Control-M (excludes Application Pack plug-ins and Control-M MFT)

---

## Supported Wildcards and Operators

### Basic Wildcards

| Symbol | Function | Examples |
|--------|----------|----------|
| **\*** | "Matches zero or more characters" - enables broad string matching | `a*` matches "a", "aa", "aab" |
| **? or .** | "Matches any single character in a string" | `S?ring` matches "Spring", "String", "S.ring" |
| **!** | "Matches all strings except for the string that immediately follows" | `!Host_A` excludes "Host_A" from results |

### Quantifier Operators

| Symbol | Function | Meaning | Examples |
|--------|----------|---------|----------|
| **+** | Matches one or more occurrences of preceding character | At least one | `ab+c` matches "abc", "abbc", "abbbc" |
| **{n}** | "Matches a defined number of occurrences of a preceding character" | Exact count | `a{3}` matches "aaa" exactly |
| **{n,m}** | Matches n to m occurrences (implied) | Range | `a{2,4}` matches "aa", "aaa", "aaaa" |

### Grouping and Logic

| Symbol | Function | Purpose |
|--------|----------|---------|
| **( )** | Groups characters; works with other symbols to define search scope | Grouping for operators |
| **,** | Separates multiple search criteria; represents Boolean OR | Multiple patterns |

---

## Pattern Matching Syntax Rules

### Character Classes and Escaping

| Syntax | Purpose | Notes |
|--------|---------|-------|
| **\\** | Escape character for special character literals | Required for special chars |
| **\\*** | Literal asterisk | Match exact * character |
| **\\(** | Literal parenthesis | Match exact ( character |
| **\\[** | Literal bracket | Match exact [ character |

### Special Characters Requiring Escape

The following special characters must be escaped with `\\` to match literally:

- `( )` — Parentheses
- `[ ]` — Square brackets
- `{ }` — Curly braces
- `. ` — Period/dot
- `+ ` — Plus
- `? ` — Question mark
- `^ ` — Caret
- `$ ` — Dollar sign
- `| ` — Pipe
- `< >` — Angle brackets
- `\ ` — Backslash

### Escape Examples
```
\\(MyJob\\)    → Matches literal "(MyJob)"
\\[Test\\]     → Matches literal "[Test]"
\\{Data\\}     → Matches literal "{Data}"
price\\.99     → Matches "price.99"
```

---

## Pattern Matching Examples

### Simple Wildcards

| Pattern | Matches | Doesn't Match |
|---------|---------|---------------|
| `a*` | "a", "aa", "aab", "apple" | "b", "ba" |
| `*test` | "test", "mytest", "pretest" | "testing", "tester" |
| `*test*` | "test", "mytest", "testing", "pretesting" | (matches all containing "test") |
| `S?ring` | "Spring", "String", "Saring" | "S1ring", "Sring" |

### Negation

| Pattern | Matches | Doesn't Match |
|---------|---------|---------------|
| `!Host_A` | "Host_B", "Host_C", "MyHost" | "Host_A" (excluded) |
| `!test*` | "prod", "dev", "stage" | "test", "testing", "test123" |

### Quantifiers

| Pattern | Matches | Notes |
|---------|---------|-------|
| `ab+c` | "abc", "abbc", "abbbc" | One or more b's |
| `a{3}` | "aaa" (exactly) | Exactly 3 a's |
| `a{2,4}` | "aa", "aaa", "aaaa" | 2 to 4 a's |

### Multiple Patterns (OR Logic)

| Pattern | Behavior |
|---------|----------|
| `host01,host02,host03` | Matches any of: host01, host02, host03 |
| `host01,host02,host03*` | Matches: host01, host02, host03, host034, host035... |
| `prod*,test*,dev*` | Matches any starting with: prod, test, or dev |

### Complex Patterns

| Pattern | Purpose | Matches |
|---------|---------|---------|
| `Job_[0-9]*` | Implied: digit pattern matching | "Job_1", "Job_123", "Job_456" |
| `\\(Batch\\)_*` | Job names with literal "(Batch)" prefix | "(Batch)_Job1", "(Batch)_Report" |
| `*_[A-Z]{3}` | Implied: 3 uppercase letters at end | "Report_ABC", "Daily_XYZ" |

---

## Pattern Matching Usage in Control-M

### In Search and Filter Operations

Pattern matching is used in:
- **Job Search:** Find jobs by name pattern
- **Folder Search:** Filter folders by naming pattern
- **Application Filter:** Match applications by pattern
- **Host Filter:** Filter by server/host name pattern

### In If-Action Conditions

Pattern matching enables conditional logic:

```
IF %%JOBNAME MATCHES "prod*"
  → Execute action only if job name starts with "prod"

IF %%COMPSTAT MATCHES "!OK"
  → Execute action if completion status is NOT "OK"
```

### In Prerequisites and Conditions

Used in job prerequisites to match:
- Job completion status values
- Event names with wildcards
- Resource requirements with pattern names

### In Variable Conditions

When comparing variable values:
```
IF %%MYVAR MATCHES "*test*"
  → True if MYVAR contains "test" anywhere

IF %%APPNAME MATCHES "[A-Z]*"
  → True if APPNAME matches pattern
```

---

## Constraints and Best Practices

### Performance Constraints

| Constraint | Impact | Recommendation |
|-----------|--------|----------------|
| **Blank fields** | More efficient than `*` | Leave filter fields blank instead of using `*` |
| **At least one value** | At least one filter field must contain a value | Cannot use all wildcards |
| **Whitespace after comma** | May cause pattern matching errors | Avoid spaces: use `host1,host2` not `host1, host2` |

### Syntax Constraints

- Special characters require escape sequences (`\\` prefix)
- Patterns are case-sensitive (unless documented otherwise for specific filter)
- Escape character is `\\` (backslash)
- Parentheses, brackets, braces must be escaped to match literally

### Best Practices

1. **Use Specific Patterns**
   - Prefer explicit patterns over broad wildcards
   - Use negation (`!`) for exclusion rather than broad matches
   - Document pattern purpose in job/folder descriptions

2. **Escape Special Characters**
   - Always escape special characters requiring literal match
   - Test patterns with escape characters before deployment
   - Document escape sequences used in patterns

3. **Multiple Pattern Logic**
   - Use commas for OR logic (multiple patterns)
   - Keep patterns simple and readable
   - Group related patterns together
   - Document complex pattern combinations

4. **Performance Optimization**
   - Leave filter fields blank instead of `*` for better performance
   - Use specific patterns rather than broad wildcards
   - Avoid leading wildcards when possible (`*test` slower than `test*`)
   - Test pattern performance on large datasets

5. **Testing and Validation**
   - Test patterns with sample data before deployment
   - Verify negation patterns match intended results
   - Test escaped characters in target system (z/OS may differ)
   - Document pattern behavior and edge cases

---

## Integration with Control-M Components

### With Variables System

Pattern matching used in variable conditions:
- Compare variable values against patterns
- Match system variables (%%JOBNAME, %%APPLIC)
- Evaluate dynamic variable substitution results

### With If-Actions

Conditional actions use pattern matching:
- IF conditions with MATCHES operator
- Status comparison (OK, NOT OK patterns)
- Dynamic condition evaluation

### With Job Filtering

Pattern matching in job operations:
- Search for jobs by name
- Filter job lists by pattern
- Exclude jobs using negation

### With Scheduling and Prerequisites

Pattern matching in prerequisites:
- Match status values
- Compare completion conditions
- Evaluate event name patterns

---

## Wildcard Summary Reference

### Quick Reference Table

| Symbol | Meaning | Usage |
|--------|---------|-------|
| `*` | Zero or more characters | Broad matching |
| `?` or `.` | Exactly one character | Single char replacement |
| `!` | Negation (NOT) | Exclusion |
| `,` | OR separator | Multiple patterns |
| `+` | One or more | Quantified matching |
| `{n}` | Exact count | Fixed repetitions |
| `\\` | Escape | Literal special chars |
| `( )` | Grouping | Scope definition |

### Common Pattern Examples

| Need | Pattern | Example |
|------|---------|---------|
| Start with text | `prefix*` | `prod*` matches "prod", "production", "product" |
| End with text | `*suffix` | `*_log` matches "job_log", "error_log" |
| Contains text | `*middle*` | `*_test_*` matches "pre_test_job" |
| Exclude text | `!pattern` | `!dev*` excludes dev jobs |
| Single char | `?` or `.` | `job?` matches "job1", "joba", etc. |
| Multiple patterns | `pat1,pat2` | `prod,test,dev` matches any three |
| Escape special | `\\char` | `\\(job\\)` matches literal "(job)" |

---

## Notes for Planning Agents

1. **Flexible Pattern Language:** Wildcards, quantifiers, negation, and escaping provide comprehensive matching
2. **Performance Consideration:** Blank fields more efficient than `*`; avoid leading wildcards
3. **OR Logic:** Comma-separated patterns use Boolean OR
4. **Case-Sensitive:** Patterns respect case (system may vary)
5. **Special Char Escaping:** Backslash (`\\`) required for literal special characters
6. **Integration Points:** Used in If-Actions, Prerequisites, Variables, Job filtering
7. **Naming Constraints Intersection:** Works with folder/job/calendar/variable naming rules
8. **No Leading Wildcards:** Best practice for performance (test* better than *test)
9. **Escape Examples Critical:** Parentheses, brackets, braces commonly need escaping in job names
10. **Multi-Pattern Logic:** Comma separates patterns; each treated as separate criterion

---

## Vendor Attributes

| Attribute | Value |
|-----------|-------|
| **Product** | Control-M |
| **Feature** | Pattern Matching & String Filtering |
| **Wildcards** | \*, ?, ., !, +, {n}, ( ), \, |
| **Operators** | MATCHES, equals, comparison |
| **Boolean Logic** | OR (comma), implicit AND |
| **Escape Char** | \\ (backslash) |
| **Case Sensitive** | Yes (unless documented otherwise) |
| **Scope** | Filters throughout Control-M (excludes MFT, plug-ins) |
| **Performance** | Blank fields preferred over \* |
| **Special Chars** | All listed chars require escape for literal match |
