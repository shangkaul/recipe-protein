# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + TypeScript PWA with a local Flask API. The user previously selected this stack.

## Users

The primary users are the creator's parents. They open the app at home while deciding what to cook
and want to browse familiar meal ideas before entering what is in the kitchen.

## Product Purpose

Protein Pantry helps one household turn available ingredients into practical, higher-protein meal
choices. Success means a parent can find a meal they would genuinely cook in under three minutes,
understand what is available or missing, and compare approximate protein and calories without
nutrition expertise.

## Positioning

Unlike generic recipe search, Protein Pantry combines pantry-fit retrieval with a user-entered
protein target and locally run, source-grounded recipe adaptation. Nutrition remains deterministic
and dietary details are not sent to a cloud AI service.

## Operating Context

- Mobile-first and installable as a PWA, commonly used in the kitchen on a phone.
- Browse-first opening with suggested meals; pantry search is the primary action.
- Typed, natural-language pantry input may mix common Indian English food terms.
- No account, profile, or medical intake.

## Capabilities and Constraints

- Prefer Indian meals while retaining useful global options.
- Exclude beef, pork, lamb, other red meat, and red-meat-derived ingredients.
- Show 20–30 ranked results where the corpus permits.
- Users enter their own per-meal protein target; the product does not prescribe one.
- Nutrition is attributed or deterministically calculated and labelled approximate.
- A local open-weight model may adapt a selected source recipe, but cannot invent nutrition.
- Search remains usable when the local model is unavailable.
- Primary implementation uses React, Flask, BM25 retrieval, and Ollama-compatible local inference.

## Brand Commitments

- Product name: **Protein Pantry**.
- Voice: plain, reassuring, practical, and concise.
- The interface must not resemble a clinical fitness dashboard, a traditional-themed cultural
  treatment, or a playful/gamified product.

## Evidence on Hand

- Approved product specification: `specs/001-protein-pantry-recommendations/spec.md`.
- UniTools World Recipes: 501 recipes under CC BY-SA 4.0 with servings, time, ingredients,
  instructions, protein, calories, cuisine, attribution, and photo licensing metadata.
- A local Recipe1M nutrition subset is available for private retrieval experiments but has no
  servings and contains corrupted fractions; it is not the public MVP nutrition authority.
- BM25 retrieval and ingredient normalization are implemented specifically for Protein Pantry.

## Product Principles

1. Start with appetising choices, not a form wall.
2. Make pantry fit and missing ingredients obvious at a glance.
3. Present nutrition as practical evidence, never judgment.
4. Keep adaptation grounded, local, and optional.
5. Prefer reliable everyday usefulness over feature count.

## Accessibility & Inclusion

The primary journey must support readable type, strong contrast, large touch targets, visible focus,
keyboard operation, reduced motion, and plain-language recovery states. Mobile controls should be
comfortable for older adults without creating a specialised or patronising interface.
