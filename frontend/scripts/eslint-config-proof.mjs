#!/usr/bin/env node
// lint-frontend must prove it blocks, not only that it passes (D-270 L4 · ISS-211).
//
// From 2026-09-15 to 2026-10-02 this job could not lint anything: ESLint 10 found no
// `eslint.config.*` and crashed before reading a file. A green run proves the config
// loads; it does not prove the gate rejects anything. This script plants each kind of
// failure and requires the gate to go red:
//
//   1. a new React Compiler error in a new file;
//   2. a fourth warning (the workflow allows MAX_WARNINGS=3, measured, ratchet only);
//   3. a stale entry in eslint-suppressions.json (the frozen debt shrinks in both
//      directions: fixing a suppressed error without pruning it is red too);
//   4. each ESLint 10 shim in eslint.config.mjs is still needed. When upstream fixes
//      the cause, the official config stops crashing without the shim, and this script
//      goes red so the shim is removed instead of lingering as dead code.
//
// Run from frontend/:  node scripts/eslint-config-proof.mjs
// Planted files live in a temporary folder under app/ and are always removed.

import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";

import { ESLint } from "eslint";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

import config, { eslint10Shims } from "../eslint.config.mjs";

const CWD = process.cwd();
const ESLINT_BIN = join(CWD, "node_modules", ".bin", "eslint");
const MAX_WARNINGS = process.env.MAX_WARNINGS ?? "3";
const PROBE_DIR = join(CWD, "app", "__eslint_proof__");
const SUPPRESSIONS = join(CWD, "eslint-suppressions.json");

const SET_STATE_IN_EFFECT = `import { useEffect, useState } from "react";
export default function Probe({ value }) {
    const [copy, setCopy] = useState(null);
    useEffect(() => {
        setCopy(value);
    }, [value]);
    return <p>{copy}</p>;
}
`;

const MISSING_DEPENDENCY = `import { useEffect } from "react";
export default function Probe({ value, onChange }) {
    useEffect(() => {
        onChange(value);
    }, []);
    return null;
}
`;

const failures = [];

function check(name, ok, detail) {
    console.log(`${ok ? "✅" : "❌"} ${name}${detail ? ` — ${detail}` : ""}`);
    if (!ok) failures.push(name);
}

function runGate(...targets) {
    const result = spawnSync(
        ESLINT_BIN,
        [...targets, "--ext", ".js,.jsx", "--max-warnings", MAX_WARNINGS],
        { cwd: CWD, encoding: "utf8" },
    );
    return { status: result.status, output: `${result.stdout}\n${result.stderr}` };
}

function plant(fileName, source) {
    mkdirSync(PROBE_DIR, { recursive: true });
    writeFileSync(join(PROBE_DIR, fileName), source);
}

async function lintWith(overrideConfig, source) {
    const eslint = new ESLint({ cwd: CWD, overrideConfigFile: true, overrideConfig });
    try {
        await eslint.lintText(source, { filePath: join(CWD, "app", "ProofProbe.jsx") });
        return null;
    } catch (error) {
        return String(error?.message ?? error);
    }
}

try {
    // 0. The real tree passes — otherwise every planted check below is meaningless.
    const baseline = runGate("app/");
    check("the current tree passes the gate", baseline.status === 0, `exit ${baseline.status}`);

    // 1. A new error is red, and it is the planted rule that fires.
    plant("NewError.jsx", SET_STATE_IN_EFFECT);
    const newError = runGate("app/");
    check(
        "a new set-state-in-effect error is red",
        newError.status === 1 && newError.output.includes("react-hooks/set-state-in-effect"),
        `exit ${newError.status}`,
    );
    rmSync(PROBE_DIR, { recursive: true, force: true });

    // 2. A fourth warning is red: the warning ratchet still bites.
    plant("FourthWarning.jsx", MISSING_DEPENDENCY);
    const fourthWarning = runGate("app/");
    check(
        `a warning past MAX_WARNINGS=${MAX_WARNINGS} is red`,
        fourthWarning.status === 1 && fourthWarning.output.includes("react-hooks/exhaustive-deps"),
        `exit ${fourthWarning.status}`,
    );
    rmSync(PROBE_DIR, { recursive: true, force: true });

    // 3. A stale suppression is red: the frozen debt cannot be carried past its fix.
    const original = readFileSync(SUPPRESSIONS, "utf8");
    try {
        const ledger = JSON.parse(original);
        const [file, rules] = Object.entries(ledger)[0];
        const [rule] = Object.keys(rules);
        ledger[file][rule].count += 1;
        writeFileSync(SUPPRESSIONS, `${JSON.stringify(ledger, null, 2)}\n`);
        const stale = runGate("app/");
        check(
            "a suppression that no longer matches an error is red",
            stale.status !== 0 && /suppressions left that do not occur anymore/i.test(stale.output),
            `exit ${stale.status}`,
        );
    } finally {
        writeFileSync(SUPPRESSIONS, original);
    }

    // 4a. Shim 1 (parser) is still needed: the official config alone crashes on ESLint 10.
    const withoutParserShim = await lintWith(
        [...nextCoreWebVitals, { settings: eslint10Shims.settings }],
        SET_STATE_IN_EFFECT,
    );
    check(
        "shim 1 (parser) is still needed",
        withoutParserShim?.includes("addGlobals") ?? false,
        withoutParserShim ? "official parser still lacks scopeManager.addGlobals" : "the official config now lints without it — remove shim 1",
    );

    // 4b. Shim 2 (React version) is still needed: `detect` still calls a removed API.
    const withoutVersionShim = await lintWith(
        [
            ...nextCoreWebVitals,
            { languageOptions: eslint10Shims.languageOptions, settings: { react: { version: "detect" } } },
        ],
        SET_STATE_IN_EFFECT,
    );
    check(
        "shim 2 (React version) is still needed",
        withoutVersionShim?.includes("getFilename") ?? false,
        withoutVersionShim ? "eslint-plugin-react still calls context.getFilename()" : "`detect` now works — remove shim 2",
    );

    // 5. The shims are what the gate actually runs with, for a real file under app/.
    const effective = await new ESLint({ cwd: CWD }).calculateConfigForFile(
        join(CWD, "app", "components", "CogniForgeApp.jsx"),
    );
    const espree = createRequire(createRequire(import.meta.url).resolve("eslint"))("espree");
    check(
        "the gate parses with ESLint's own parser",
        effective.languageOptions?.parser === espree,
    );
    const reactVersion = JSON.parse(
        readFileSync(createRequire(import.meta.url).resolve("react/package.json"), "utf8"),
    ).version;
    check(
        "the gate pins the installed React version",
        effective.settings?.react?.version === reactVersion,
        effective.settings?.react?.version,
    );
    check("the config is the exported default", config.at(-1) === eslint10Shims);
} finally {
    rmSync(PROBE_DIR, { recursive: true, force: true });
}

if (failures.length > 0) {
    console.log(`\n❌ ${failures.length} proof(s) failed: ${failures.join(" · ")}`);
    process.exit(1);
}
console.log("\n✅ lint-frontend blocks what it claims to block");
