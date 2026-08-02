---
name: RegVerdict
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3fd'
  on-secondary-container: '#57657b'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#001d31'
  on-tertiary-container: '#188ace'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d5e3fd'
  secondary-fixed-dim: '#b9c7e0'
  on-secondary-fixed: '#0d1c2f'
  on-secondary-fixed-variant: '#3a485c'
  tertiary-fixed: '#cce5ff'
  tertiary-fixed-dim: '#93ccff'
  on-tertiary-fixed: '#001d31'
  on-tertiary-fixed-variant: '#004b73'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style

The design system is anchored in **Precision Modernism**. It balances the stoic authority of global legal institutions with the streamlined efficiency of high-performance developer tools. The UI must evoke feelings of absolute certainty, security, and meticulousness.

The aesthetic utilizes a refined **Minimalist** approach with a **Corporate Modern** structure. It prioritizes information density without sacrificing clarity, using generous whitespace to frame complex regulatory data. Every interface element is functional; decorative flourishes are avoided in favor of structural integrity and high-order legibility.

**Target Audience:** Compliance officers, legal counsel, and enterprise risk managers who require rapid, accurate interpretations of complex legislation.

## Colors

The palette is designed for high-stakes decision-making. 

- **Primary (Deep Navy):** Used for structural navigation, headers, and primary actions to establish an authoritative "legal" foundation.
- **Secondary (Slate):** Employed for supporting text and UI chrome, providing a professional, neutral backdrop.
- **Accent (Professional Blue):** Reserved for interactive "AI" features, highlighting insights and copilot suggestions.
- **Semantic States:** 
    - **Emerald Green (Compliant):** Signifies a "Pass" or "De-risked" state.
    - **Amber (Review):** Indicates legal ambiguity or a need for human intervention.
    - **Crimson (Non-Compliant):** Signals high risk or regulatory failure.

Backgrounds utilize a clean, high-contrast white or near-white (`#F8FAFC`) to ensure that dense text remains the focus and status colors are immediately identifiable.

## Typography

The typography system uses **Inter** for all primary interfaces to maximize legibility of dense regulatory text across all screens. It is a systematic, utilitarian choice that feels both modern and professional.

- **Headlines:** Use tight letter spacing and semi-bold weights to convey a "journalistic" authority.
- **Body Text:** Designed with generous line-height to prevent fatigue during long reading sessions of legal documents.
- **Monospace (JetBrains Mono):** Introduced for audit trails, version numbers, and technical metadata to signify "data-backed" precision.

Accessibility is paramount: contrast ratios for all body text must exceed 7:1 against the background.

## Layout & Spacing

The design system employs a **Fixed Grid** model for desktop to ensure structured, predictable document reading, transitioning to a **Fluid Grid** for tablet and mobile.

- **Desktop (1280px+):** 12-column grid with 24px gutters. Sidebars for "AI Context" and "Audit Trails" are fixed at 320px.
- **Tablet (768px - 1279px):** 8-column grid with 16px gutters. Contextual panels collapse into bottom sheets or drawers.
- **Mobile (<768px):** 4-column grid with 16px gutters.

Spacing follows a strict 4px/8px baseline rhythm to maintain visual order. Information-dense areas (like data tables) may use the "Compact" spacing tier (4px/8px), while narrative analysis sections use "Standard" spacing (16px/24px) to improve readability.

## Elevation & Depth

This design system avoids heavy shadows in favor of **Tonal Layers** and **Low-Contrast Outlines**. Depth is used sparingly to indicate "active" or "focused" analytical states.

- **Level 0 (Surface):** The main canvas, using `#F8FAFC`.
- **Level 1 (Container):** White (`#FFFFFF`) with a subtle 1px border in `#E2E8F0`. Used for content cards and legal text blocks.
- **Level 2 (Hover/Active):** A very soft, diffused shadow (`0px 4px 12px rgba(15, 23, 42, 0.05)`) combined with a 2px primary color border.
- **Level 3 (Modals/Overlays):** Direct focus elements with a medium-diffused shadow and a 40% opacity Slate backdrop blur to maintain context without visual noise.

Interactions are signaled by elevation shifts rather than just color changes, aiding users with color-vision deficiencies.

## Shapes

The shape language is **Soft (0.25rem)**. This provides a subtle modern touch while maintaining the "sturdy" feel of a professional legal application. 

- **Buttons & Inputs:** Use the base `0.25rem` (4px) radius.
- **Verdict Badges:** Use a pill-shape (`rounded-full`) to differentiate them from standard UI components, making "Compliant" or "Risk" status immediately recognizable as a distinct entity.
- **Data Visualizations:** Graphs and charts should use sharp or minimally rounded corners to emphasize technical accuracy.

## Components

### Verdict Cards
The signature component of the system. A "Verdict" card must feature a thick (4px) left-accent border colored by its status (Green, Amber, or Crimson). It includes a "Rationale" section using `body-sm` and a "Citation" link using the `label-caps` style.

### Buttons
- **Primary:** Deep Navy background, white text. No gradient. Focus state: 2px offset ring in Professional Blue.
- **Secondary:** Transparent background, Slate border (1px).
- **Ghost:** Used for low-priority actions in audit trails.

### Input Fields
Strict, rectangular fields with 1px Slate borders. On focus, the border thickens to 2px in Professional Blue. Error states use Crimson text for helper labels.

### Chips & Tags
Used for "Regulatory Tags" (e.g., GDPR, MiFID II). These use a light Slate tint background with `code-md` typography to indicate they are system-indexed terms.

### Graph Visualizations
Interactive nodes for showing regulatory relationships. Nodes use the "Soft" radius and status colors for their borders. Connection lines should be neutral Slate, thickening and turning Blue when a path is hovered.

### Audit Trail
A vertical timeline component using `jetbrainsMono` for timestamps and `body-sm` for action descriptions. Each entry is separated by a 1px Slate divider.