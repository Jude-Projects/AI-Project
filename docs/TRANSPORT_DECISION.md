# Transport Decision Record — AI Data Assistant MCP Server

## Answers

1. **Who calls this server, and from where?** Claude Code, local — same machine.
2. **How many people or processes call it at the same time, realistically?** One.
3. **Does it need to run on more than one machine, now or within a year?** No — one machine, for now.
4. **Does anything about it have to survive between requests?** No. Nothing survives today (this was walked back from an initial "both ways" answer, clarified to mean "it could go either way eventually, but today, nothing does").
5. **What is the worst thing that happens if it is unavailable for an hour?** Nothing — it's easy to bring back online.

## Decision

**Transport: stdio.**
**State model: stateless per request** — no server-side session state persisted between tool calls.

## Rationale, in my own words

The caller is one Claude Code process on the same machine I'm on — there's no network between client and server to design for, so a network transport would be solving a problem I don't have. One caller at a time means no concurrency story is needed either. Nothing has to survive between requests, so there's nothing to persist, replicate, or recover — each tool call can just open what it needs (a SQL connection, a report render) and close it when done. And an hour of downtime costs nothing beyond restarting the process, so there's no case for redundancy or high availability. stdio — one process per client, spawned and torn down with the connection, no state kept beyond that process's lifetime — is the transport and state model that fits every one of those answers, and it's also exactly what's already implemented and registered (`mcp.run(transport="stdio")` in `src/mcp_server.py`, wired via `.mcp.json`).

## Option rejected

**streamable-http**, rejected because it solves problems this project doesn't have: it exists to let a server be reached over a network, by multiple clients, potentially from more than one machine, and to keep running independently of any one client's lifetime. None of that is true here — adopting it now would mean standing up a network-facing process (with the auth/security surface that implies) for a server one local process calls, one at a time, with nothing to keep alive between calls.

## Revisit condition

Revisit this if a second concurrent caller, a second machine, or a real need for state to survive between requests (e.g. STORY-007's follow-up-question session continuity, if it ever gets wired into *this* MCP server rather than just existing in `session_manager.py` unexposed) shows up.
