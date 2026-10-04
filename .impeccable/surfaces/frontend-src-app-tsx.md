---
version: 1
slug: "frontend-src-app-tsx"
primary_target: "frontend/src/App.tsx"
related_targets: []
---

# Protein Pantry primary application

## Scope and mode

Primary mobile-first PWA surface. Visitor mode: Operate.

## Audience and job

Parents browsing practical meal ideas at home, then narrowing them with pantry ingredients, a protein target, and available time. The primary action is to move from an appealing idea to a feasible meal without needing nutrition expertise.

## Constraints

Browse-first; large touch targets; readable for older adults; no fitness-dashboard visuals, traditional cultural theming, or playful gamification. Nutrition is approximate and attributed. Local API and local model failures must be clear and recoverable.

## Direction contract

**THESIS:** Treat meal choice as calm mise-en-place: food ideas arrive already sorted into what is ready, what is missing, and what one serving contributes. Refuse the category-default macro dashboard, recipe-card mosaic, and decorative heritage treatment.

**OWN-WORLD:** A light mineral kitchen surface in rice white and cool stone, with curry-leaf green owning primary actions, aubergine ink for text, and tomato coral reserved for missing or attention states. Compact sans typography, ingredient-label density, soft 14px corners only where content is grouped, and fine dividers rather than nested cards. Recipe imagery remains natural and untinted.

**STORY:** The opening offers genuinely browsable meals, then one obvious pantry action. Search reorganizes the same meal language around ingredient coverage and the protein target. Detail reveals quantities, method, nutrition provenance, and optional local adaptation without changing vocabulary.

**FIRST VIEWPORT:** On a 390px phone, a compact app bar sits above “What sounds good?” and a horizontally scrollable category row. One generous lead meal fills most of the width with image, title, cuisine/time, and a two-column protein/calorie footer; the next meal edge signals browsing. Below it, a full-width curry-leaf action opens the pantry sheet inline. Desktop becomes a stable two-column workspace with pantry controls at left and the meal stream at right. The signature move is the prep strip: matched ingredients settle into solid green labels while missing ingredients remain quiet outlined labels, with one short state transition after search.

**FORM:** Grounded direction 7 of the c00747d5 roll: a contemporary mise-en-place counter translated into an Operate surface through type, palette, density, and the prep-strip state change—not kitchen-tool costume.

**FINISH:** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Unresolved decisions

None blocking implementation. Recipe photos come from the selected dataset and retain per-image attribution.
