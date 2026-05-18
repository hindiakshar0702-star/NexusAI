---
version: "alpha"
name: "Marcus Reed - Systems Architect"
description: "Marcus Reed Pricing Section is designed for comparing plans and supporting conversion decisions. Key features include plan comparison blocks and conversion-oriented actions. It is suitable for subscription pricing pages and plan comparison experiences."
colors:
  primary: "#1A3B5C"
  secondary: "#EA4313"
  tertiary: "#0B3B8C"
  neutral: "#1A1A1A"
  background: "#F4F1EB"
  surface: "#1A3B5C"
  text-primary: "#1A1A1A"
  text-secondary: "#1A3B5C"
  border: "#1A1A1A"
  accent: "#1A3B5C"
typography:
  display-lg:
    fontFamily: "Inter"
    fontSize: "288px"
    fontWeight: 700
    lineHeight: "288px"
    letterSpacing: "-0.05em"
    textTransform: "uppercase"
  body-md:
    fontFamily: "JetBrains Mono"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: "19.5px"
spacing:
  base: "4px"
  sm: "2px"
  md: "4px"
  lg: "8px"
  xl: "12px"
  gap: "2px"
  card-padding: "8px"
  section-padding: "32px"
---

## Overview

- **Composition cues:**
  - Layout: Grid
  - Content Width: Full Bleed
  - Framing: Open
  - Grid: Strong

## Colors

The color system uses light mode with #1A3B5C as the main accent and #1A1A1A as the neutral foundation.

- **Primary (#1A3B5C):** Main accent and emphasis color.
- **Secondary (#EA4313):** Supporting accent for secondary emphasis.
- **Tertiary (#0B3B8C):** Reserved accent for supporting contrast moments.
- **Neutral (#1A1A1A):** Neutral foundation for backgrounds, surfaces, and supporting chrome.

- **Usage:** Background: #F4F1EB; Surface: #1A3B5C; Text Primary: #1A1A1A; Text Secondary: #1A3B5C; Border: #1A1A1A; Accent: #1A3B5C

## Typography

Typography pairs Inter for display hierarchy with JetBrains Mono for supporting content and interface copy.

- **Display (`display-lg`):** Inter, 288px, weight 700, line-height 288px, letter-spacing -0.05em, uppercase.
- **Body (`body-md`):** JetBrains Mono, 12px, weight 400, line-height 19.5px.

## Layout

Layout follows a grid composition with reusable spacing tokens. Preserve the grid, full bleed structural frame before changing ornament or component styling. Use 4px as the base rhythm and let larger gaps step up from that cadence instead of introducing unrelated spacing values.

Treat the page as a grid / full bleed composition, and keep that framing stable when adding or remixing sections.

- **Layout type:** Grid
- **Content width:** Full Bleed
- **Base unit:** 4px
- **Scale:** 2px, 4px, 8px, 12px, 16px, 24px, 32px, 48px
- **Section padding:** 32px, 48px, 64px
- **Card padding:** 8px, 10px, 12px, 16px
- **Gaps:** 2px, 4px, 8px, 16px

## Elevation & Depth

Depth is communicated through elevated, border contrast, and reusable shadow or blur treatments. Keep those recipes consistent across hero panels, cards, and controls so the page reads as one material system.

Surfaces should read as elevated first, with borders, shadows, and blur only reinforcing that material choice.

- **Surface style:** Elevated
- **Borders:** 1px #1A1A1A; 2px #1A3B5C; 2px #EA4313; 1px #EA4313
- **Shadows:** rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgb(26, 26, 26) 4px 4px 0px 0px

## Shapes

Shapes rely on a tight radius system anchored by 9999px and scaled across cards, buttons, and supporting surfaces. Icon geometry should stay compatible with that soft-to-controlled silhouette.

Use the radius family intentionally: larger surfaces can open up, but controls and badges should stay within the same rounded DNA instead of inventing sharper or pill-only exceptions.

- **Corner radii:** 9999px
- **Icon treatment:** Linear
- **Icon sets:** Solar

## Components

Component styling should inherit the shared button, icon, spacing, and surface rules instead of inventing one-off treatments. Favor a small family of repeatable patterns for actions, content containers, and fields.

### Iconography
- **Treatment:** Linear.
- **Sets:** Solar.

## Do's and Don'ts

Use these constraints to keep future generations aligned with the current system instead of drifting into adjacent styles.

### Do
- Do use the primary palette as the main accent for emphasis and action states.
- Do keep spacing aligned to the detected 4px rhythm.
- Do reuse the Elevated surface treatment consistently across cards and controls.
- Do keep corner radii within the detected 9999px family.

### Don't
- Don't introduce extra accent colors outside the core palette roles unless the page needs a new semantic state.
- Don't mix unrelated shadow or blur recipes that break the current depth system.
- Don't exceed the detected minimal motion intensity without a deliberate reason.

## Motion

Motion stays restrained and interface-led across text, layout, and scroll transitions. Timing clusters around 150ms. Easing favors ease and cubic-bezier(0.4.

**Motion Level:** minimal

**Durations:** 150ms

**Easings:** ease, cubic-bezier(0.4, 0, 0.2, 1)
