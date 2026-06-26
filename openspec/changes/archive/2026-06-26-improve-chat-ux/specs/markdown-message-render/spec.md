## ADDED Requirements

### Requirement: Markdown rendering for chat messages
The frontend SHALL render all assistant chat messages as Markdown, supporting standard GFM (GitHub Flavored Markdown) syntax and code syntax highlighting.

#### Scenario: Basic markdown formatting
- **WHEN** an assistant message contains Markdown formatting (headings `##`, bold `**`, italic `*`, lists `-`, links `[text](url)`, tables `| col | col |`, blockquotes `>`)
- **THEN** the message SHALL be rendered as formatted HTML, not raw Markdown text

#### Scenario: Code block with syntax highlighting
- **WHEN** an assistant message contains a fenced code block with a language identifier, e.g. ` ```python ` / ` ```javascript ` / ` ```bash `
- **THEN** the code block SHALL be rendered with syntax highlighting appropriate to the specified language
- **THEN** the code block SHALL have a copy-to-clipboard button

#### Scenario: Long code block with scroll
- **WHEN** a code block exceeds 20 lines or 80 characters per line
- **THEN** the code block SHALL be scrollable (vertical and horizontal as needed) without breaking the message layout

#### Scenario: Inline code
- **WHEN** an assistant message contains inline code ( `` `code` `` )
- **THEN** the inline code SHALL be rendered in a monospace font with a subtle background highlight

#### Scenario: Safe HTML sanitization
- **WHEN** an assistant message contains HTML tags (e.g., `<script>`, `<img>`)
- **THEN** the Markdown renderer SHALL sanitize the HTML to prevent XSS — only allow safe tags (`<code>`, `<pre>`, `<a>`, `<table>`, etc.)

#### Scenario: User messages as plain text
- **WHEN** displaying a user message
- **THEN** it SHALL be rendered as plain text (no Markdown processing)
