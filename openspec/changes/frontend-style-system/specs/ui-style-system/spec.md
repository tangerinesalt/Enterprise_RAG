## ADDED Requirements

### Requirement: Styles use CSS Modules with design tokens

All component styles SHALL use CSS Modules (`.module.css` files) instead of inline `React.CSSProperties` objects. Shared visual properties SHALL reference CSS custom properties defined in `tokens.css`.

#### Scenario: Component has hover feedback

- **WHEN** user hovers over a clickable row in KbList, SessionList, or file list
- **THEN** the row background changes to a hover color
- **AND** the cursor is a pointer

#### Scenario: Button has focus ring

- **WHEN** user tabs to a primary button
- **THEN** the button shows a visible focus ring

#### Scenario: Token change propagates globally

- **WHEN** the primary color token `--color-primary` in `tokens.css` is updated
- **THEN** all primary buttons and links reflect the new color

### Requirement: Design tokens are defined in a single source

All visual design tokens (colors, spacing, font sizes, border radii, shadows) SHALL be defined as CSS custom properties in `ui/src/styles/tokens.css`. Components SHALL reference these tokens via `var(--token-name)` rather than hardcoded values.

#### Scenario: Token reference consistency

- **WHEN** a component uses a blue color for a primary action
- **THEN** it SHALL use `var(--color-primary)` instead of a hardcoded hex value

### Requirement: Inline style objects are removed

Each component file SHALL have its corresponding `.module.css` file. After migration, the `const btnStyle: React.CSSProperties = {...}` objects SHALL be removed from every component.

#### Scenario: Full migration verified

- **WHEN** a code review checks all 6 component files (NavBar, KbList, KbDetail, SessionList, SessionChat, MarkdownMessage)
- **THEN** no file SHALL contain a top-level `const ... : React.CSSProperties` style definition

### Requirement: CSS Modules work with TypeScript 6

The project SHALL include a type declaration for `.module.css` imports to satisfy TypeScript strict mode.

#### Scenario: Build passes

- **WHEN** running `tsc -b` in the `ui/` directory
- **THEN** it SHALL pass without errors related to CSS Module imports
