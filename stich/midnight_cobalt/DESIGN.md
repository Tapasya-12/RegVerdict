---
name: Midnight Cobalt
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#c6c6cd'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#909097'
  outline-variant: '#45464d'
  surface-tint: '#bec6e0'
  primary: '#bec6e0'
  on-primary: '#283044'
  primary-container: '#0f172a'
  on-primary-container: '#798098'
  inverse-primary: '#565e74'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#dec29a'
  on-tertiary: '#3e2d11'
  tertiary-container: '#231500'
  on-tertiary-container: '#957d5a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#fcdeb5'
  tertiary-fixed-dim: '#dec29a'
  on-tertiary-fixed: '#271901'
  on-tertiary-fixed-variant: '#574425'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
  compliant: '#10b981'
  review: '#f59e0b'
  non-compliant: '#ef4444'
  surface-elevated: '#1e293b'
  border-subtle: '#334155'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  code-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  container-max: 1440px
---

## Brand & Style

This design system is engineered for high-stakes legal-tech environments where data density and clarity are paramount. The brand personality is one of **modern authority**—combining the traditional trust of legal institutions with the efficiency of a high-growth technology platform.

The visual direction follows a **Corporate / Modern** aesthetic, utilizing a deep, sophisticated "Midnight" foundation. It prioritizes functional clarity and high-contrast accessibility to reduce cognitive load during extended audit sessions. The style avoids unnecessary decorative elements, favoring a "data-first" approach where color is used strategically for status and hierarchy rather than mere ornamentation.

## Colors

The palette is anchored by **Imperial Blue (#0f172a)**, providing a deep, stable background that reduces eye strain. **Vibrant Cobalt (#3b82f6)** serves as the primary action color, ensuring high visibility against the dark base.

### Color Logic
- **Primary Surface:** Used for the main application background and global navigation.
- **Accent:** Reserved for primary calls-to-action, active selection states, and interactive links.
- **Semantic Hierarchy:** The status colors (**Emerald, Amber, Rose**) are non-negotiable indicators of regulatory health. They should be used consistently to represent Compliant, Review, and Non-Compliant states respectively.
- **Tonal Stepping:** Use lighter variations of the primary blue (e.g., #1e293b) to define cards and modals, creating a sense of depth without relying on heavy shadows.

## Typography

The system utilizes **Inter** exclusively to ensure maximum legibility across dense data tables and complex legal documents. 

- **Weight Strategy:** Use `600` (Semi-bold) for section headers and `700` (Bold) for page titles to create clear visual entry points.
- **Readability:** Body text is optimized at `14px` (body-md) for data density, while `16px` (body-lg) is used for long-form textual analysis or legal commentary.
- **Letter Spacing:** Headlines use a slight negative tracking (-0.02em) for a more compact, modern feel. Labels use increased tracking (+0.05em) and uppercase styling to distinguish them from interactive text.

## Layout & Spacing

This design system uses a **fixed grid** model for the main content area to maintain line-length readability for legal documents, centered within the viewport.

- **Grid Model:** A 12-column grid on desktop with 16px gutters.
- **Rhythm:** A 4px baseline grid governs all spacing. Vertical rhythm should follow multiples of 4 (8px, 16px, 24px, 32px).
- **Density:** For data-heavy views (Audit Tables), utilize "Compact" spacing (8px cell padding). For "Overview" dashboards, utilize "Comfortable" spacing (16px - 24px padding).
- **Breakpoints:**
  - **Mobile:** < 600px (1 column, 16px margins)
  - **Tablet:** 600px - 1024px (6 columns, 24px margins)
  - **Desktop:** > 1024px (12 columns, 32px margins)

## Elevation & Depth

Hierarchy is established primarily through **Tonal Layers** rather than heavy shadows, reflecting a modern, tech-forward interface.

- **Level 0 (Base):** Imperial Blue (#0f172a). Used for the application background.
- **Level 1 (Surface):** Lighter Blue (#1e293b). Used for primary content cards and table containers.
- **Level 2 (Overlay):** Even lighter blue (#334155). Used for modals, dropdown menus, and hovered states.
- **Outlines:** Use low-contrast borders (1px solid #334155) to define boundaries between Level 1 elements. Shadows should be kept minimal: deep, highly diffused, and tinted with the primary blue to maintain the "Midnight" aesthetic.

## Shapes

The system follows a **Soft** geometry (4px / 0.25rem), which strikes a balance between the precision of professional legal tools and the approachability of modern SaaS.

- **Standard Elements:** Buttons, input fields, and tags use the base 4px radius.
- **Containers:** Large cards and modals may scale up to `rounded-lg` (8px) to soften the overall interface.
- **Strictness:** Do not use fully rounded pill shapes for buttons, as this deviates from the "Professional Legal" aesthetic.

## Components

### Buttons
- **Primary:** Vibrant Cobalt background, white text. 4px border radius.
- **Secondary:** Transparent background with a 1px border of Vibrant Cobalt.
- **Ghost:** No background or border; Cobalt text. Used for low-priority actions in tables.

### Input Fields
- **Default State:** Background #1e293b, 1px border #334155.
- **Focus State:** 1px border #3b82f6 with a subtle outer glow of the same color.
- **Error State:** 1px border #ef4444.

### Status Chips (Audit Badges)
- High-contrast badges used to denote compliance.
- **Compliant:** Emerald text on a 10% opacity Emerald background.
- **Review:** Amber text on a 10% opacity Amber background.
- **Non-Compliant:** Rose text on a 10% opacity Rose background.

### Cards & Lists
- Cards should use Level 1 surface coloring. List items should have a 1px bottom border (#334155) and a subtle hover state change to Level 2.

### Data Tables
- Header row: Level 2 surface background, uppercase labels (label-md).
- Alternating rows (Zebra striping): Optional, using a 2% lighter tint of Level 1 for high-density readability.