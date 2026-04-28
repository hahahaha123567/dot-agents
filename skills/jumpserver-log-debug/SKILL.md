---
name: jumpserver-log-debug
description: Use when Codex needs to debug a deployed service by logging into a server through the user's local JumpServer zsh alias `js`, searching service logs by the interface or handler changed in the current git diff, extracting `log_id`, fetching the complete request-processing log, and comparing the result with local code changes. Trigger when the user says code has been deployed and provides a target server hostname, log directory, request time window, interface name, or asks to check deployment logs via JumpServer.
user-invocable: true
---

# Jumpserver Log Debug

## Overview

Debug deployed service behavior from server logs after code changes have been deployed. Prefer read-only investigation: infer the changed interface from local code, connect through JumpServer, find the request log, expand it by `log_id`, then explain whether the runtime behavior matches the code.

## Inputs

Collect or infer these values:

- Server hostname, for example `daily-acp-finance-02`.
- Service log directory, for example `/home/admin/ai-call-back/callout-job-provider/callout-job-provider-2.0.0-RELEASE/logs`.
- Approximate request time window, if available.
- Interface name, URL path, controller method, handler name, job name, trace id, or business keyword, if available.
- Expected and actual behavior, if the user knows them.

If the user omits the interface name, inspect the local repository first with `git status`, `git diff`, and targeted `rg` searches to infer the changed controller path, RPC method, job handler, or log keyword.

## Workflow

1. Inspect local changes before connecting:

   ```bash
   git status --short
   git diff --stat
   git diff
   ```

   Look for endpoint mappings, annotations, controller names, Feign/RPC interfaces, scheduled job handlers, log messages, constants, and request/response fields that can identify the deployed request.

2. Connect through JumpServer using the user's local zsh alias:

   ```bash
   zsh -ic 'js'
   ```

   Use an interactive terminal if JumpServer presents a menu. Select or search the target hostname the user provided. Do not ask for private keys, certificates, passwords, or tokens; rely only on the user's existing local configuration.

3. On the target server, enter the service log directory:

   ```bash
   cd /path/to/service/logs
   pwd
   ls -ltr
   ```

   Prefer recent log files first. Avoid unbounded searches across unrelated directories.

4. Search for the request using the most specific available keyword:

   ```bash
   grep -RIn --color=never 'interface-or-path-or-keyword' . | tail -n 80
   grep -RIn --color=never 'ERROR\|Exception\|interface-or-path-or-keyword' . | tail -n 120
   ```

   If logs are compressed, use `zgrep` against the relevant files. If the user gave a time window, search files whose modification time and log lines overlap that window.

5. Extract `log_id` from the matching request line, then fetch the complete request-processing log:

   ```bash
   grep -RIn --color=never 'log_id_value' . | sort
   ```

   Use a tighter file set when possible, for example the current `app.log` or the matching rolled log. Capture surrounding stack traces, downstream calls, request parameters, response payload summaries, and timing lines.

6. Compare logs with local code:

   - Map log messages and stack frames back to changed files and methods with `rg`.
   - Check whether request fields, branch conditions, validation, downstream calls, and error handling match the intended change.
   - Separate runtime/environment issues from code defects.
   - If a likely code issue is found, inspect the relevant local code and propose or implement the minimal fix requested by the user.

## Safety

Run read-only commands by default. Do not restart services, edit server files, delete logs, kill processes, run database writes, or change deployment state unless the user explicitly authorizes the exact operation and the risk is clear.

Keep outputs focused. Summarize only the useful log lines instead of dumping large logs, and redact secrets or sensitive identifiers if they appear.
