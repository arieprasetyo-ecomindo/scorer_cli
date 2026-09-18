## Response Style
- Be extremely concise. No pleasantries, no filler.
- When asked to write code, return code only unless explanation is explicitly requested.
- No sycophantic preambles ("Sure!", "Great question!", "Absolutely!").
- No "Here's a function that..." preambles.
- Don't restate the question before answering.
- No "Note:", "Tip:", or "Remember:" appendices unless asked.
- No usage examples unless asked.
- No unsolicited suggestions or improvements beyond what was asked.
- Use short variable names where meaning is clear from context.


## Context Retrieval Policy

Always retrieve the smallest amount of information necessary.
Escalate only when necessary. Stop escalating as soon as sufficient information has been obtained.

Preferred order:
1. Need code structure? `graphify-out/graph.json`.
2. Need directory structure? `rtk tree`
3. Need symbols? `ast-grep`.
4. Need implementation? Source files.
5. Use repository-wide search as last resort

Avoid reading entire directories or the whole repository unless explicitly requested.


<!-- rtk-instructions v2 -->
## RTK (Rust Token Killer) - Token-Optimized CLI

`rtk` is a CLI proxy that filters and compresses command outputs, saving 60-90% tokens.

**Always** prefix commands with `rtk`. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.


Instead of:
```
ls -la .
git status
git log -10
docker ps
```

Use:
```
rtk ls -la .
rtk git status
rtk git log -10
rtk docker ps
```

### RTK commands example

```bash
rtk ls <path>
rtk read <file>
rtk find <pattern>

rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values

rtk curl <url>          # Compact HTTP responses

rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
```

<!-- /rtk-instructions -->


## Graphify - Codebase context & knowledge graph protocol

A pre-computed AST knowledge graph (`graph.json`) is available at: `graphify-out/graph.json`
Use `graph.json` before searching or reading multiple source files.

Workflow:
1. Read `graph.json`.
2. Identify the relevant symbols, files, and dependency paths.
3. Read only the source files required for the task.
4. Avoid scanning unrelated files.

Use the graph for:
- dependency tracing
- call-path discovery
- identifying high-centrality modules
- impact analysis before refactoring
- locating symbol definitions

Never read an entire directory simply to locate a symbol. Use `graph.json` to locate the symbol first, then read only the relevant files.

The graph is generated from AST extraction and represents extracted structural relationships only. Treat graph edges as authoritative for structural relationships.
Do not infer dependencies that are absent from the graph.


## ast-grep

Prefer `ast-grep` over `grep` whenever searching source code.

Use `ast-grep` for:
- locating function definitions
- locating class definitions
- locating method implementations
- finding imports
- matching AST patterns
- performing structural search

Use `grep` only for:
- Markdown
- JSON
- YAML
- log files
- generated text
- plain-text configuration

Avoid using `grep` to search programming language source code when `ast-grep` can answer the query.