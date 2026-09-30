#!/usr/bin/env python3
# One-node shell_check: build, serve, run Playwright, and hand its verdict to
# the DAG repair edge. STOP suppresses a repair after the attempt/time budget.
# Usage: verify_node.py <tests_dir> <port> [--tag ID ...] [spec.ts ...]
#        verify_node.py --seed <deliverable_dir>
import json, os, re, shutil, signal, socket, subprocess, sys, tempfile, time, uuid
from pathlib import Path

STOP = "ARC_NO_MORE_REPAIRS"
PASSED = {"count": 0}               # tests the last check passed (for --best)
VERDICT = {"phase": "entered", "category": "application_failure", "reason": "unknown", "detail": ""}
INSTALL = "npm install --no-audit --no-fund --no-package-lock"


def mark_progress(phase: str) -> None:
    """Leave a small, secret-free breadcrumb while shell_check buffers output."""
    VERDICT["phase"] = phase
    try:
        (Path.cwd() / ".arc-verify-progress.json").write_text(
            json.dumps({"phase": phase, "at": time.time(), "pid": os.getpid()}), encoding="utf-8")
    except OSError:
        pass


def fail(category: str, reason: str, detail: str) -> int:
    VERDICT.update(category=category, reason=reason, detail=detail)
    return 1


def write_verdict(tag: str, attempt: int, elapsed: float, rc: int) -> None:
    """One immutable, atomically published result per shell check."""
    detail = str(VERDICT["detail"])
    for key, value in os.environ.items():
        if any(s in key.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD", "AUTH")) and len(value) >= 6:
            detail = detail.replace(value, "[REDACTED]")
    detail = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", detail)
    detail = " ".join(detail.split())[-800:]
    data = {"tag": tag, "attempt": attempt, "elapsed_s": round(elapsed, 2), "phase": VERDICT["phase"],
            "rc": rc, "category": "pass" if rc == 0 else VERDICT["category"],
            "reason": "passed" if rc == 0 else VERDICT["reason"], "detail": "" if rc == 0 else detail}
    folder = Path.cwd() / ".arc-verify-results"
    folder.mkdir(exist_ok=True)
    target = folder / f"{time.time_ns()}-{uuid.uuid4().hex[:8]}.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    temp.replace(target)


def configure_text_streams() -> None:
    """Keep browser output printable in Windows consoles with legacy codepages.

    Playwright's reporter can include Unicode glyphs in otherwise ordinary
    failure output.  If stdout is still using GBK/CP1252, printing that output
    raises UnicodeEncodeError and hides the actual test verdict.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                # Some captured/closed streams cannot be reconfigured; they
                # should not prevent the acceptance check from reporting.
                continue

# The harness owns the two manifests so the model never spends a turn on them
# (build copies src/* to dist; start runs server.js).
MANIFESTS = {
    "frontend/package.json": {"name": "f", "private": True, "scripts": {
        "build": "node -e \"const f=require('fs');f.rmSync('dist',{recursive:true,force:true});f.cpSync('src','dist',{recursive:true})\""}},
    "backend/package.json": {"name": "b", "private": True, "type": "commonjs",
                             "scripts": {"start": "node server.js"}},
}


def seed(src: Path) -> int:
    """Start the run dir from the existing app (evolution tasks, the platform
    template), else the bundle's own template: the model extends real files
    instead of rebuilding from nothing, and nothing stale survives collection."""
    out = Path.cwd()
    for base in (src, Path(__file__).resolve().parent / "template"):
        if (base / "frontend").is_dir() and not (out / "frontend").exists():
            for part in ("frontend", "backend"):
                if (base / part).is_dir():
                    shutil.copytree(base / part, out / part, dirs_exist_ok=True,
                                    ignore=shutil.ignore_patterns("node_modules", "dist", ".git"))
            print(f"[seed] workspace seeded from {base}")
    return 0


def free(port: int) -> bool:
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) != 0


def stop(proc) -> None:
    """Tolerant teardown: never die here and leave the app listening, or the
    next node's check would score this node's server."""
    if proc is None or proc.poll() is not None:
        return
    if os.name == "nt":
        # npm run start is launched through cmd.exe on Windows. Terminating only
        # that shell leaves npm/node descendants listening on the test port.
        try:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True, check=False, timeout=10)
            proc.wait(timeout=10)
            return
        except (OSError, subprocess.TimeoutExpired):
            pass
    attempts = ((lambda: os.killpg(os.getpgid(proc.pid), signal.SIGTERM)), proc.terminate, proc.kill) \
        if os.name != "nt" else (proc.terminate, proc.kill)
    for attempt in attempts:
        try:
            attempt(); proc.wait(timeout=10); return
        except (OSError, subprocess.TimeoutExpired):
            continue


def sh(cmd, cwd, env, timeout):
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, shell=isinstance(cmd, str),
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"") + (exc.stderr or b"")
        return 124, (out.decode(errors="replace") if isinstance(out, bytes) else out) + f"\n[timed out after {timeout}s]"


PLAYWRIGHT_VERSION = "1.63.0"   # never `latest`: an unpinned install broke cloud grading once


def playwright_command(root: Path, env: dict, *args: str) -> list[str]:
    """Run Playwright through Node instead of the POSIX-only .bin shim.

    The shim is executable on Linux/macOS but Windows rejects it with
    WinError 193. Calling the package CLI directly works on every platform.
    """
    node = shutil.which("node", path=env.get("PATH")) or "node"
    cli = root / "node_modules" / "@playwright" / "test" / "cli.js"
    return [node, str(cli), *args]


def playwright_root(env: dict) -> tuple[Path | None, dict]:
    """A directory holding node_modules/@playwright/test, plus the env its
    browsers need. The runner image ships one (/opt/arcbench on the platform,
    seen in every cloud run); a private pinned install through the mirrors is
    the fallback, cached for every later check."""
    private = Path(os.environ.get("TMPDIR", "/tmp")) / "arc-playwright"
    cands = [os.environ.get("OCTOS_ARC_PLAYWRIGHT_ROOT"), "/opt/arcbench", "/workspace", "/workspace/tests"]
    # The CLI file, not the package dir: a wiped cache once left an empty
    # @playwright/test behind, and every check then died on the dangling
    # .bin/playwright link -- a whole local keep run was verified by nothing.
    has = lambda root: (Path(root) / "node_modules" / "@playwright" / "test" / "cli.js").is_file()  # noqa: E731
    for cand in filter(None, cands):
        if has(cand):
            return Path(cand), {}
    # Prefer explicit local installations before consulting npm or walking `/`;
    # on Windows, invoking MSYS `find /` can traverse every mounted drive.
    try:
        rc, npm_root = sh(["npm", "root", "-g"], "/", env, 20)
    except OSError:
        rc, npm_root = 127, ""
    if rc == 0 and npm_root.strip():
        candidate = str(Path(npm_root.strip().splitlines()[-1]).parent)
        if has(candidate):
            return Path(candidate), {}
    browsers = {"PLAYWRIGHT_BROWSERS_PATH": str(private / "browsers")}
    if has(private):
        return private, browsers if (private / "browsers").is_dir() else {}
    if os.name != "nt":
        rc, hits = sh(["find", "/", "-maxdepth", "6", "-type", "d", "-path", "*/node_modules/@playwright/test",
                       "-not", "-path", "/proc/*", "-not", "-path", "/sys/*"], "/", env, 25)
        for hit in sorted(hits.split(), key=len):
            # find's own "Permission denied" lines land here too; only real hits count.
            if hit.endswith("/node_modules/@playwright/test") and has(Path(hit).parents[2]):
                return Path(hit).parents[2], {}
    if os.environ.get("OCTOS_ARC_INSTALL_PLAYWRIGHT", "1") != "1":
        return None, {}
    private.mkdir(parents=True, exist_ok=True)
    (private / "package.json").write_text('{"name": "arc-verify", "private": true}')
    mirror = dict(env, npm_config_registry="https://registry.npmmirror.com",
                  PLAYWRIGHT_DOWNLOAD_HOST="https://npmmirror.com/mirrors/playwright", **browsers)
    rc, log = sh(f"{INSTALL} @playwright/test@{PLAYWRIGHT_VERSION}", private, mirror, 600)
    if rc == 0:
        rc, log = sh(playwright_command(private, mirror, "install", "chromium"),
                     private, mirror, 600)
    if rc:
        print(f"[verify] private Playwright install failed:\n{log[-800:]}")
    return (private, browsers) if rc == 0 else (None, {})


NO_BROWSER = "Executable doesn't exist"


def install_browser(root: Path, env: dict) -> bool:
    """A Playwright whose browser build is missing (a wiped cache, a version
    bump) fails every spec in the same way -- a local run once burned 670
    nodes on that. Fetch chromium once, upstream then through the mirror."""
    for extra in ({}, {"PLAYWRIGHT_DOWNLOAD_HOST": "https://npmmirror.com/mirrors/playwright"}):
        install_env = dict(env, **extra)
        rc, log = sh(playwright_command(root, install_env, "install", "chromium"),
                     root, install_env, 600)
        if rc == 0:
            print("[verify] installed the missing Playwright browser")
            return True
    print(f"[verify] Playwright browser install failed:\n{log[-800:]}")
    return False


def check(tests: Path, port: int, specs: list[str]) -> int:
    out = Path.cwd()
    mark_progress("prepare")
    for rel, data in MANIFESTS.items():
        if not (out / rel).exists():
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            (out / rel).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env.pop("FORCE_COLOR", None)           # plain text for the model reading the failure
    if os.environ.get("NODE_BIN"):
        env["PATH"] = os.environ["NODE_BIN"] + os.pathsep + env.get("PATH", "")
    for executable in ("node", "npm"):
        if not shutil.which(executable, path=env.get("PATH")):
            print(f"[verify] {executable} unavailable; {STOP}: missing runtime")
            return fail("infrastructure_failure", f"{executable}_missing", f"{executable} is not on PATH")
    if not (out / "frontend" / "src").is_dir():
        print("[verify] no frontend/src: the implement node wrote nothing to verify")
        return fail("application_failure", "no_frontend", "frontend/src is missing")
    # Verify a disposable copy: the specs create, edit and delete records, and
    # a store they leave behind in the workspace ships with the app -- the
    # grader then starts from test debris instead of the seeded state (keep:
    # 15 requirements passed their own checks, 6/32 at grading).
    # Keep scratch data inside the pipeline workspace. The Octos shell-check
    # runs in a fenced workspace; some Windows hosts can stall when Python's
    # default TEMP points outside that writable area.
    app = Path(tempfile.mkdtemp(prefix=".arc-app-", dir=out))
    mark_progress("copy-app")
    for part in ("frontend", "backend"):
        if (out / part).is_dir():
            shutil.copytree(out / part, app / part, ignore=shutil.ignore_patterns("node_modules", "dist"))
    try:
        return run_app(app, out, env, tests, port, specs)
    finally:
        shutil.rmtree(app, ignore_errors=True)


def run_app(app: Path, out: Path, env: dict, tests: Path, port: int, specs: list[str]) -> int:
    for cwd, step in ((app / "frontend", f"{INSTALL} && npm run build"), (app / "backend", INSTALL)):
        mark_progress(f"build-{cwd.name}")
        rc, log = sh(step, cwd, env, 240)
        if rc:
            print(f"[verify] {cwd.name}: {step!r} failed\n{log[-1500:]}")
            return fail("application_failure", "build_failed", log)
    if not free(port):
        print(f"[verify] port {port} already serving; refusing to score another process")
        return fail("infrastructure_failure", "port_busy", f"port {port} is occupied")
    mark_progress("find-playwright")
    root, pw_env = playwright_root(env) if specs else (None, {})
    if specs and root is None:
        # Nothing the model can fix: stop, do not spend repair rounds on it.
        print(f"[verify] Playwright unavailable; cannot run the acceptance specs\n{STOP}: no test runner")
        return fail("infrastructure_failure", "playwright_unavailable", "Playwright runner is unavailable")

    server_log = out / ".arc-server.log"      # a file, not a pipe: a chatty server never blocks
    process_group = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"preexec_fn": os.setsid}
    mark_progress("start-server")
    with server_log.open("w") as log_file:
        srv = subprocess.Popen("npm run start", cwd=app / "backend", env=dict(env, PORT=str(port)),
                               shell=True, stdout=log_file, stderr=subprocess.STDOUT,
                               text=True, **process_group)
    try:
        for _ in range(60):
            if not free(port) or srv.poll() is not None:
                break
            time.sleep(0.5)
        if free(port):
            stop(srv)
            server_error = server_log.read_text(errors="replace")
            print(f"[verify] backend never bound port {port}\n{server_error[-1500:]}")
            return fail("application_failure", "server_start_failed", server_error)
        if not specs:
            # No public example for this requirement: the app must still build,
            # boot and serve its home page.
            import urllib.request
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                code = opener.open(f"http://127.0.0.1:{port}/", timeout=30).status
            except Exception as exc:  # noqa: BLE001 -- any failure is the verdict
                code = exc
            print(f"[verify] no public spec; GET / -> {code}")
            return 0 if code == 200 else fail("application_failure", "home_failed", str(code))
        # Specs `import '@playwright/test'` and Node resolves that upward from
        # the spec, so the copy sits under the install when it is writable
        # (NODE_PATH covers the temp-dir fallback).
        work = root / ".octos-acceptance" / "run"
        try:
            if work.exists():
                shutil.rmtree(work)
            (work / "tests").mkdir(parents=True)
        except OSError:
            work = Path(tempfile.mkdtemp(prefix=".arc-verify-", dir=out)) / "run"
            (work / "tests").mkdir(parents=True)
        # The node's specs plus the helpers they import (support/*.ts), at the
        # same relative paths so `../support/e2e` still resolves.
        helpers = [p.relative_to(tests) for p in tests.rglob("*")
                   if p.is_file() and "node_modules" not in p.parts and not p.name.endswith(".spec.ts")
                   and p.suffix in (".ts", ".js", ".mjs", ".cjs", ".json")]
        for rel in [*specs, *helpers]:
            if (tests / rel).is_file():
                (work / "tests" / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(tests / rel, work / "tests" / rel)
        # The platform grades with a 10 s per-test timeout; verify under the
        # same limit so a slow app fails here, where it can still be repaired.
        (work / "playwright.config.ts").write_text(
            "import { defineConfig } from '@playwright/test';\n"
            "export default defineConfig({ testDir: './tests', outputDir: './test-results', timeout: %s, retries: 0, workers: 4, "
            "reporter: [['list']], use: { headless: true, baseURL: process.env.E2E_BASE_URL } });\n"
            % os.environ.get("OCTOS_ARC_TEST_TIMEOUT_MS", "10000"))
        run_env = dict(env, E2E_BASE_URL=f"http://127.0.0.1:{port}", CI="1",
                       NODE_PATH=str(root / "node_modules"), **pw_env)
        run = lambda: sh(playwright_command(root, run_env, "test", "-c",
                                           str(work / "playwright.config.ts")), work, run_env,  # noqa: E731
                         int(os.environ.get("OCTOS_ARC_PLAYWRIGHT_TIMEOUT", "600")))
        mark_progress("run-playwright")
        rc, log = run()
        if rc and NO_BROWSER in log and install_browser(root, run_env):
            rc, log = run()
        mark_progress("playwright-finished")
    finally:
        stop(srv)
    if rc and NO_BROWSER in log:
        # The runner has no browser and none could be installed: nothing the
        # model can fix, so do not spend repair rounds on it.
        print(f"[verify] Playwright has no browser to run the specs\n{log[-800:]}\n{STOP}: no browser")
        return fail("infrastructure_failure", "browser_unavailable", log)
    # Playwright's exit code IS the verdict and its list reporter already names
    # every failing assertion; print that verbatim for the repair round.
    print(log[-6000:])
    counts = re.findall(r"(\d+) passed", log)
    PASSED["count"] = int(counts[-1]) if counts else 0
    if rc:
        fail("application_failure", "playwright_failed", log)
        # What the page actually showed when each test failed (Playwright's
        # ARIA snapshot): the difference between "not found" and why.
        for ctx in sorted((work / "test-results").rglob("error-context.md"))[:3]:
            page = ctx.read_text(errors="replace").partition("```yaml")[2].split("```")[0]
            if page.strip():
                print(f"\n----- page at failure: {ctx.parent.name} -----\n{page.strip()[:1500]}")
    return rc


def inventory(out: Path) -> str:
    """The app's source files with line counts. This output is the next
    implement node's input, so it starts oriented instead of spending its
    first turns on list_dir/glob."""
    rows = []
    for part in ("frontend", "backend"):
        for f in sorted((out / part).rglob("*")) if (out / part).is_dir() else []:
            rel = f.relative_to(out)
            if f.is_file() and not {"node_modules", "dist"} & set(rel.parts) and f.stat().st_size < 1_000_000:
                rows.append(f"{rel} ({len(f.read_bytes().splitlines())} lines)")
    return "Workspace files: " + ", ".join(rows[:80])


def snapshot(out: Path, dest: Path) -> None:
    shutil.rmtree(dest, ignore_errors=True)
    for part in ("frontend", "backend"):
        if (out / part).is_dir():
            shutil.copytree(out / part, dest / part, ignore=shutil.ignore_patterns("node_modules", "dist"))


def keep_best(out: Path, rc: int) -> None:
    """Snapshot the app when this full-suite check passed more tests than any
    before it. A repair that breaks more than it fixes, or a run cut off in
    the middle of one, must not ship: the adapter delivers the snapshot."""
    best = out / ".arc-best"
    score = best / "score.json"
    prev = json.loads(score.read_text())["passed"] if score.is_file() else -1
    if PASSED["count"] <= prev:
        return
    snapshot(out, best / "app")
    score.write_text(json.dumps({"passed": PASSED["count"], "rc": rc}))
    print(f"[verify] best full-suite state so far: {PASSED['count']} passed (kept)")


def parse_arguments(argv: list[str]) -> tuple[dict[str, str], list[str]]:
    """Parse verifier options anywhere around its required positionals.

    The Octos adapter may prepend ``--playwright-root`` before the tests dir
    and port, while older invocations place all options after them.
    """
    opts, positional = {}, []
    it = iter(argv)
    for arg in it:
        if arg.startswith("--"):
            try:
                opts[arg[2:]] = next(it)
            except StopIteration as exc:
                raise ValueError(f"missing value for {arg}") from exc
        else:
            positional.append(arg)
    if len(positional) < 2:
        raise ValueError("expected tests directory and port")
    return opts, positional


def main(argv: list[str]) -> int:
    configure_text_streams()
    mark_progress("entered")
    if argv[:1] == ["--seed"]:
        return seed(Path(argv[1]))
    opts, positional = parse_arguments(argv)
    tests_dir, port, *specs = positional
    tag = opts.get("tag", "UNTAGGED")
    counter = Path.cwd() / ".arc-attempts" / tag
    attempt = int(counter.read_text() or 0) + 1 if counter.is_file() else 1
    VERDICT.update(category="application_failure", reason="unknown", detail="")
    if opts.get("playwright-root"):
        os.environ["OCTOS_ARC_PLAYWRIGHT_ROOT"] = opts["playwright-root"]
    if "regress" in opts:
        # Regression checkpoint: also re-run the specs of earlier requirements
        # whose last verdict was a pass.
        status = Path.cwd() / ".arc-status"
        earlier = [rel for tag, rels in json.loads(Path(opts["regress"]).read_text()).items()
                   if tag != opts.get("tag") and (status / tag).is_file()
                   and (status / tag).read_text().strip() == "0" for rel in rels]
        extra = [rel for rel in dict.fromkeys(earlier) if rel not in specs]
        if extra:
            print(f"[verify] regression checkpoint: also re-running {len(extra)} spec(s) of earlier "
                  "requirements that passed; a failure there is a regression to fix now")
            specs = [*specs, *extra]
    started = time.monotonic()
    try:
        rc = check(Path(tests_dir).resolve(), int(port), specs)
    except Exception as exc:
        print(f"[verify] unexpected verifier error: {exc}")
        rc = fail("application_failure", "unexpected_error", str(exc))
    write_verdict(tag, attempt, time.monotonic() - started, rc)
    if rc and VERDICT["category"] == "infrastructure_failure":
        print(f"{STOP}: infrastructure failure ({VERDICT['reason']}); stopping run")
        return rc
    if "best" in opts:
        keep_best(Path.cwd(), rc)
    if rc == 0 and "tag" in opts:
        # Latest state a check passed: the adapter copies it into the output
        # dir as the run goes, so a run killed from outside still delivers.
        snapshot(Path.cwd(), Path.cwd() / ".arc-good" / "app")
        (Path.cwd() / ".arc-good" / "stamp").write_text(str(time.time()))
    print(inventory(Path.cwd()))
    if "tag" in opts:                           # the adapter reads the last verdict
        (Path.cwd() / ".arc-status").mkdir(exist_ok=True)
        (Path.cwd() / ".arc-status" / opts["tag"]).write_text(str(rc))
    if rc and "tag" in opts:
        counter.parent.mkdir(exist_ok=True)
        attempts = int(counter.read_text() or 0) + 1 if counter.is_file() else 1
        counter.write_text(str(attempts))
        first = counter.with_suffix(".first")          # when this requirement first failed
        if not first.is_file():
            first.write_text(str(time.time()))
        spent = time.time() - float(first.read_text())
        if (attempts >= int(opts.get("attempts", 6)) or time.time() >= float(opts.get("deadline", "inf"))
                or spent >= float(opts.get("repair-window", "inf"))):
            print(f"{STOP}: attempt {attempts} for {opts['tag']}; moving on")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
