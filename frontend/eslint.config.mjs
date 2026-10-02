// ESLint flat config — the official `eslint-config-next/core-web-vitals`, plus two
// compatibility shims for ESLint 10 (ISS-211).
//
// Why this file exists: ESLint 10 (installed 2026-09-15) no longer reads `.eslintrc.*`,
// so `lint-frontend` crashed before checking a single line ("couldn't find an
// eslint.config.* file") on every commit that touched `frontend/`.
//
// Both shims are measured, not guessed. Each one has a proof in
// `scripts/eslint-config-proof.mjs` that turns `lint-frontend` red once the shim is no
// longer needed, so a fix upstream retires the shim instead of leaving dead code behind.
//
// `.eslintrc.json` is still on disk but ESLint 10 does not read it, and Next 16 no longer
// lints during `next build`. It stays because a change may not delete files (D-277); this
// file is the only ESLint configuration in effect.

import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

const requireHere = createRequire(import.meta.url);

// Shim 1 — the parser. `eslint-config-next` sets its own parser, which returns a scope
// manager without `addGlobals`; ESLint 10 calls it on every file
// (`TypeError: scopeManager.addGlobals is not a function`). Espree is the parser ESLint
// ships with, resolved from ESLint's own location, so it always matches the installed
// ESLint and adds no dependency. It parses JSX; this tree has no TypeScript under `app/`.
const espree = createRequire(requireHere.resolve("eslint"))("espree");

// Shim 2 — the React version. `eslint-plugin-react` detects the version through
// `context.getFilename()`, which ESLint 10 removed
// (`contextOrFilename.getFilename is not a function`). Detection only runs for
// `version: "detect"`; the installed version, read from React itself, skips it and stays
// correct when React is upgraded.
const reactVersion = JSON.parse(
    readFileSync(requireHere.resolve("react/package.json"), "utf8"),
).version;

export const eslint10Shims = {
    languageOptions: {
        parser: espree,
        parserOptions: {
            ecmaVersion: "latest",
            sourceType: "module",
            ecmaFeatures: { jsx: true },
        },
    },
    settings: { react: { version: reactVersion } },
};

const config = [
    { ignores: [".next/**", "out/**", "build/**", "node_modules/**", "next-env.d.ts"] },
    ...nextCoreWebVitals,
    eslint10Shims,
];

export default config;
