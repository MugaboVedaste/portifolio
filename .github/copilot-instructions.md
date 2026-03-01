## Purpose

This file gives AI coding agents the minimal, high-value details needed to be productive in this static portfolio project.

## Big Picture

- Single-page static portfolio: the site is implemented as a single HTML entrypoint ([index.html](index.html)) with styling in [style.css](style.css) and interactive behavior in [script.js](script.js).
- Assets live under [assets/](assets/) (profile image expected at [assets/images/profile.jpg](assets/images/profile.jpg)).

## Key Files

- [index.html](index.html): the single-page structure and content. Contact section and project markup are here.
- [style.css](style.css): global styles. Top of file contains CSS variables for brand colors.
- [script.js](script.js): UI interactions and `projectData` object — modify this object to add or edit projects.
- [assets/images](assets/images): images and profile photo.

## Developer Workflows

- No build step required. To preview locally, open [index.html](index.html) in a browser or run a simple static server from the project root:

  - Node: `npx http-server -c-1 .` 
  - Python 3: `python -m http.server 8000`

- Debugging: use browser DevTools. There are no bundlers or transpilers in this repo.

## Project-Specific Conventions

- UI data lives in `projectData` inside [script.js](script.js); prefer editing that object over adding DOM fragments manually.
- Colors are controlled by CSS variables at the top of [style.css](style.css) — change values there for site-wide theming.
- Profile image must be named `profile.jpg` and placed in [assets/images/](assets/images/) for the hero section to load correctly.

## Integration Points

- Contact form in [index.html](index.html) is static — no backend is included. If wiring to a backend, keep changes minimal: the form currently posts nowhere; add an `action` and proper `method` or use fetch in `script.js` to submit.

## Patterns & Examples

- To add a project: update `projectData` in [script.js](script.js). Example shape is present near the top of the file — keep fields consistent (title, description, tags, links).
- Avoid changing the DOM structure in `index.html` except when adding semantic sections; prefer data-driven updates through `script.js`.

## Tests, CI, and Deployment

- There are no automated tests or CI configured. For quick deploys, use GitHub Pages, Netlify, or Vercel — the site is static.

## Merge Guidance

- If merging changes from an AI agent, prefer small, well-scoped edits: update `projectData`, swap `profile.jpg`, or tweak CSS variables. Flag any changes that add a build step or external dependency — these require human approval.

## If You Need More

- If details are missing (e.g., desired project data format or contact backend URL), ask the repository owner before implementing automated integrations.

---
Please review and tell me if you want more examples or to include specific content from `index.html` or `script.js`.
