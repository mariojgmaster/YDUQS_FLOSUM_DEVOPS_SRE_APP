# Enterprise Design System

**Status:** Foundation / v0.1
**Inspiração arquitetural:** Salesforce Lightning Design System 2
**Objetivo:** aplicações enterprise, SaaS, CRM, backoffice, portais, operações e produtos orientados a dados.

---

# 1. Visão do Design System

Este Design System deve servir como uma camada comum entre:

**Design → Produto → Engenharia → Acessibilidade → Marca**

Ele não deve ser somente uma biblioteca de componentes.

A arquitetura deve possuir seis camadas:

```text
┌──────────────────────────────────────────────┐
│ 6. Product Patterns                         │
│ CRM, Search, Record Page, Workflow, etc.     │
├──────────────────────────────────────────────┤
│ 5. Components                               │
│ Button, Input, Table, Modal, Card...         │
├──────────────────────────────────────────────┤
│ 4. Primitives                               │
│ Stack, Grid, Box, Text, Icon...              │
├──────────────────────────────────────────────┤
│ 3. Semantic Tokens                          │
│ text-primary, surface-raised, danger...      │
├──────────────────────────────────────────────┤
│ 2. Foundation Tokens                        │
│ palette, spacing, radius, typography...      │
├──────────────────────────────────────────────┤
│ 1. Brand / Theme Layer                      │
│ Default, Dark, High Contrast, Customer...    │
└──────────────────────────────────────────────┘
```

Princípios:

1. **Composição antes de customização ad hoc**
2. **Semântica antes de valores físicos**
3. **Acessibilidade por padrão**
4. **Enterprise density sem sacrificar legibilidade**
5. **Progressive disclosure**
6. **Consistência de interação**
7. **Keyboard-first**
8. **Responsividade por componente**
9. **Tema independente da estrutura**
10. **API previsível entre componentes**
11. **Estados assíncronos tratados como parte do componente**
12. **Zero hardcoded design values no produto**

---

# 2. Arquitetura de Tokens

A arquitetura deve abandonar o modelo:

```css
color: #0176d3;
padding: 16px;
border-radius: 4px;
```

e adotar:

```css
color: var(--ds-color-text-link);
padding: var(--ds-spacing-4);
border-radius: var(--ds-radius-medium);
```

## 2.1 Hierarquia

```text
Primitive Token
      ↓
Semantic Token
      ↓
Component Token
      ↓
Component
```

Exemplo:

```text
blue-600
   ↓
color-action-primary
   ↓
button-primary-background
   ↓
<Button variant="primary">
```

Nunca faça:

```text
Button → blue-600
```

Isso cria acoplamento entre componente e marca.

---

# 3. Color System

## 3.1 Primitive Palette

Criar escalas:

```text
neutral-0
neutral-50
neutral-100
neutral-200
neutral-300
neutral-400
neutral-500
neutral-600
neutral-700
neutral-800
neutral-900
neutral-950

brand-50 → brand-950
blue-50 → blue-950
green-50 → green-950
yellow-50 → yellow-950
orange-50 → orange-950
red-50 → red-950
purple-50 → purple-950
```

A paleta primitiva **não deve ser usada diretamente nas aplicações**.

## 3.2 Semantic Colors

### Text

```css
--ds-color-text-primary
--ds-color-text-secondary
--ds-color-text-tertiary
--ds-color-text-disabled
--ds-color-text-placeholder
--ds-color-text-inverse

--ds-color-text-link
--ds-color-text-link-hover

--ds-color-text-success
--ds-color-text-warning
--ds-color-text-danger
--ds-color-text-info
```

### Surface

```css
--ds-color-surface-page
--ds-color-surface-primary
--ds-color-surface-secondary
--ds-color-surface-tertiary
--ds-color-surface-raised
--ds-color-surface-overlay
--ds-color-surface-selected
--ds-color-surface-hover
--ds-color-surface-disabled
--ds-color-surface-inverse
```

### Borders

```css
--ds-color-border-default
--ds-color-border-subtle
--ds-color-border-strong
--ds-color-border-interactive
--ds-color-border-selected
--ds-color-border-disabled
```

### Interactive

```css
--ds-color-action-primary
--ds-color-action-primary-hover
--ds-color-action-primary-active

--ds-color-action-secondary
--ds-color-action-secondary-hover

--ds-color-focus
```

### Feedback

```css
--ds-color-success
--ds-color-success-surface
--ds-color-success-border

--ds-color-warning
--ds-color-warning-surface
--ds-color-warning-border

--ds-color-danger
--ds-color-danger-surface
--ds-color-danger-border

--ds-color-info
--ds-color-info-surface
--ds-color-info-border
```

---

# 4. Tipografia

Não tornar Salesforce Sans uma dependência do sistema.

Recomendação default:

```css
--ds-font-family-sans:
  Inter,
  ui-sans-serif,
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  Roboto,
  Helvetica,
  Arial,
  sans-serif;

--ds-font-family-mono:
  "SFMono-Regular",
  Consolas,
  "Liberation Mono",
  monospace;
```

Caso exista uma fonte corporativa licenciada:

```css
--ds-font-family-brand
```

## 4.1 Typography Scale

### Display

```text
Display Large    40 / 48
Display Medium   32 / 40
Display Small    28 / 36
```

### Heading

```text
Heading XL       24 / 32
Heading LG       20 / 28
Heading MD       18 / 24
Heading SM       16 / 24
Heading XS       14 / 20
```

### Body

```text
Body LG          16 / 24
Body MD          14 / 20
Body SM          13 / 18
Body XS          12 / 16
```

### Label

```text
Label LG         14 / 20 — 600
Label MD         13 / 18 — 600
Label SM         12 / 16 — 600
```

## 4.2 Font Weights

```css
--ds-font-weight-regular: 400;
--ds-font-weight-medium: 500;
--ds-font-weight-semibold: 600;
--ds-font-weight-bold: 700;
```

Evitar usar peso 700 indiscriminadamente em interfaces densas.

---

# 5. Spacing System

Base de **4px**.

```text
0    0px
1    4px
2    8px
3    12px
4    16px
5    20px
6    24px
8    32px
10   40px
12   48px
16   64px
20   80px
24   96px
```

Tokens:

```css
--ds-spacing-0
--ds-spacing-1
--ds-spacing-2
...
--ds-spacing-24
```

Tokens semânticos adicionais:

```css
--ds-spacing-component-inline
--ds-spacing-component-block
--ds-spacing-container
--ds-spacing-section
--ds-spacing-page
```

---

# 6. Density

Sistemas enterprise precisam operar em diferentes densidades.

Criar três modos:

```text
Comfortable
Default
Compact
```

Exemplo:

| Elemento  | Compact | Default | Comfortable |
| --------- | ------: | ------: | ----------: |
| Input     |    32px |    40px |        48px |
| Button    |    32px |    40px |        48px |
| Table row |    32px |    40px |        48px |
| Menu item |    32px |    40px |     44–48px |

Implementação:

```html
<body data-density="compact">
```

Tokens:

```css
--ds-control-height
--ds-row-height
--ds-menu-item-height
```

---

# 7. Radius

```css
--ds-radius-none: 0;
--ds-radius-small: 4px;
--ds-radius-medium: 8px;
--ds-radius-large: 12px;
--ds-radius-xl: 16px;
--ds-radius-full: 9999px;
```

Semântica:

```css
--ds-radius-control
--ds-radius-card
--ds-radius-dialog
--ds-radius-pill
```

---

# 8. Elevation

Evitar sombras excessivas.

```text
Elevation 0 — página
Elevation 1 — card
Elevation 2 — sticky content
Elevation 3 — dropdown / popover
Elevation 4 — modal
Elevation 5 — notification / critical overlay
```

Tokens:

```css
--ds-shadow-xs
--ds-shadow-sm
--ds-shadow-md
--ds-shadow-lg
--ds-shadow-xl
```

---

# 9. Borders

```css
--ds-border-width-0
--ds-border-width-1
--ds-border-width-2

--ds-border-default
--ds-border-strong
```

A separação visual deve priorizar:

```text
spacing → background → border → shadow
```

nesta ordem.

---

# 10. Motion

Motion deve comunicar relação espacial ou mudança de estado.

## Durations

```text
Instant      0ms
Fast         100ms
Normal       160ms
Moderate     240ms
Slow         320ms
```

## Easing

```css
--ds-easing-standard
--ds-easing-enter
--ds-easing-exit
```

Respeitar:

```css
@media (prefers-reduced-motion: reduce)
```

Nunca depender exclusivamente de animação para transmitir estado.

---

# 11. Z-Index Architecture

Não permitir números arbitrários.

```text
base             0
sticky           100
dropdown         300
popover          400
overlay          500
modal            600
toast            700
tooltip          800
critical         900
```

---

# 12. Breakpoints

```text
xs     0
sm     480px
md     768px
lg     1024px
xl     1280px
2xl    1440px
```

Preferir **Container Queries** para componentes autocontidos.

---

# 13. Icons

Manter a filosofia de categorização do SLDS, mas com ativos próprios.

## Categorias

### Utility Icons

Ícones monocromáticos funcionais.

Exemplos:

```text
search
close
settings
edit
delete
add
remove
filter
sort
download
upload
refresh
copy
check
chevron
menu
more
```

### Object Icons

Entidades de negócio.

```text
account
contact
lead
opportunity
case
invoice
contract
product
order
shipment
campaign
employee
organization
```

Equivalente conceitual aos Standard Icons.

### Action Icons

```text
call
email
schedule
create
approve
reject
share
assign
merge
convert
archive
```

### File Type Icons

```text
pdf
doc
xls
ppt
csv
zip
image
video
audio
code
unknown
```

### Status Icons

```text
success
warning
error
information
pending
offline
locked
verified
```

## Sizes

```text
xxs   12
xs    16
sm    20
md    24
lg    32
xl    48
2xl   64
```

## API

```jsx
<Icon
  name="search"
  size="sm"
  tone="neutral"
/>
```

Ícones decorativos:

```html
aria-hidden="true"
```

Ícones que representam uma ação precisam de nome acessível no botão.

---

# 14. Grid System

Inspirado na flexibilidade do SLDS, mas modernizado com Grid + Flexbox.

## Grid

```jsx
<Grid columns={12} gap="4">
```

## Column

```jsx
<Column span={12} md={6} lg={4}>
```

## Stack

```jsx
<Stack
  direction="vertical"
  gap="4"
/>
```

## Inline

```jsx
<Inline
  gap="2"
  align="center"
/>
```

## Cluster

Agrupa elementos que quebram automaticamente:

```text
badges
actions
filters
tags
```

## Container

```text
sm
md
lg
xl
fluid
```

## Layout primitives

Implementar:

```text
Box
Container
Stack
Inline
Cluster
Grid
Column
Center
Sidebar
Split
Spacer
Divider
Scrollable
AspectRatio
VisuallyHidden
```

---

# 15. Data Display

## Data Table

Variantes:

```text
Default
Compact
Comfortable
Striped
Bordered
Tree Table
Editable
Selectable
Virtualized
```

Capacidades:

```text
sorting
multi-sort
column resize
column reorder
column visibility
sticky header
sticky column
row selection
bulk actions
inline editing
keyboard navigation
loading
empty state
pagination
infinite scrolling
virtualization
export
```

Estados obrigatórios:

```text
loading
loaded
empty
error
partial-error
disabled
selected
editing
saving
```

Para datasets grandes:

```text
pagination server-side
ou
virtualização
```

Nunca renderizar milhares de linhas diretamente no DOM.

---

# 16. Card

Anatomia:

```text
┌────────────────────────────┐
│ Icon Title       Actions   │
│ Subtitle                   │
├────────────────────────────┤
│                            │
│ Content                    │
│                            │
├────────────────────────────┤
│ Footer                     │
└────────────────────────────┘
```

Variantes:

```text
Default
Raised
Interactive
Selectable
Compact
Metric
Record
Media
```

---

# 17. Badge

Variantes:

```text
Neutral
Brand
Success
Warning
Danger
Info
```

Casos:

```text
status
category
count
attribute
```

Não utilizar apenas cor para representar status.

---

# 18. Avatar

Tipos:

```text
Person
Organization
Object
Group
Bot
```

Tamanhos:

```text
XS
SM
MD
LG
XL
```

Fallback:

```text
image → initials → generic icon
```

Suportar:

```text
presence
status
badge
```

---

# 19. Tile

Estrutura compacta de entidade:

```text
Avatar/Icon
Title
Metadata
Attributes
Actions
```

Ideal para:

```text
search results
record selection
recent items
related records
```

---

# 20. List

Criar:

```text
List
ListItem
DescriptionList
MetadataList
ActionList
SelectableList
VirtualList
```

---

# 21. Tree

Capacidades:

```text
expand/collapse
nested selection
keyboard navigation
lazy loading
single/multi select
drag-and-drop opcional
```

ARIA:

```text
role="tree"
role="treeitem"
aria-expanded
aria-level
```

---

# 22. Accordion

Variantes:

```text
Single-open
Multiple-open
Contained
Borderless
```

Obrigatório:

```text
keyboard accessible
aria-expanded
aria-controls
```

---

# 23. Panel

Tipos:

```text
Side Panel
Inspector Panel
Details Panel
Filter Panel
Context Panel
```

Pode ser:

```text
persistent
collapsible
overlay
resizable
```

---

# 24. Visual Picker

Usar para opções relativamente pequenas e de alto valor visual:

```text
plan
template
integration
payment method
configuration profile
```

Suportar:

```text
single
multi
disabled
recommended
```

---

# 25. Additional Data Display

Adicionar além do escopo inicial:

```text
Stat / Metric
KPI Card
Description List
Timeline
Feed
Calendar
Calendar Event
Code Block
JSON Viewer
Key-Value
Empty State
Skeleton
Carousel
Image
Thumbnail
File Preview
Record Summary
Property Grid
Diff Viewer
Log Viewer
Chart Container
```

---

# 26. Form Architecture

Todo campo deve seguir:

```text
Label
Required Indicator
Control
Supporting Text
Validation Message
Character Counter
```

API conceitual:

```jsx
<Input
  label="Nome"
  value={value}
  required
  description="Nome exibido aos usuários."
  error="Informe um nome válido."
/>
```

---

# 27. Input

Tipos:

```text
text
email
password
number
currency
percentage
telephone
url
search
```

Estados:

```text
default
hover
focus
filled
invalid
disabled
readonly
loading
```

Elementos opcionais:

```text
prefix
suffix
leading icon
trailing icon
clear button
character count
```

---

# 28. Textarea

Recursos:

```text
fixed
auto-grow
resizable
max-length
character counter
```

---

# 29. Checkbox

Tipos:

```text
Checkbox
Checkbox Group
Indeterminate Checkbox
```

Use `indeterminate` especialmente em seleção de tabelas/árvores.

---

# 30. Radio Group

Orientações:

```text
vertical
horizontal
card-style
```

Evitar radios para listas muito grandes.

---

# 31. Select

Uso:

```text
listas pequenas
conteúdo estático
seleção simples
```

Não utilizar Select quando a lista possui centenas de elementos.

---

# 32. Combobox

Tipos:

```text
Autocomplete
Searchable Select
Multi-select
Creatable
Async
Entity Lookup
```

Suportar:

```text
keyboard navigation
typeahead
loading
no results
grouped options
recent items
```

---

# 33. Lookup

Componente enterprise de primeira classe.

```text
Input
Recent Records
Search
Result List
Entity Icon
Metadata
Create New
Advanced Search
```

Este deve existir separadamente de um Combobox genérico.

---

# 34. Slider

Tipos:

```text
Single
Range
Discrete
Continuous
```

Sempre fornecer alternativa de input numérico quando precisão for importante.

---

# 35. Toggle

Use para configuração que:

```text
On / Off
```

e cujo efeito normalmente é imediato.

Não usar como substituto visual de checkbox em formulários submetidos em lote.

---

# 36. Date & Time

Criar separadamente:

```text
Date Input
Date Picker
Date Range Picker
Time Picker
DateTime Picker
Month Picker
```

Considerar:

```text
locale
timezone
first day of week
DST
format
keyboard
```

Nunca manipular data corporativa sem política explícita de timezone.

---

# 37. File Selector

Modos:

```text
Button upload
Drag & drop
Multi-file
Image upload
Attachment manager
```

Estados:

```text
uploading
processing
complete
failed
cancelled
virus-scanning
```

---

# 38. Form Components Adicionais

```text
Field
Fieldset
Form Section
Input Group
Number Input
Search Input
Password Input
Color Input
OTP Input
Pin Input
Segmented Control
Rating
Tag Input
Rich Text Input
Address Input
Phone Input
Currency Input
Percentage Input
Masked Input
Entity Lookup
```

---

# 39. Buttons

## Variants

```text
Primary
Secondary
Neutral
Outline
Ghost
Destructive
Destructive Outline
Link
Inverse
```

Correspondências conceituais:

```text
Brand        → Primary
Neutral      → Secondary/Neutral
Destructive  → Destructive
```

## Sizes

```text
XS
SM
MD
LG
```

## States

```text
default
hover
focus
active
disabled
loading
success
```

Nunca remover estado de foco.

---

# 40. Icon Button

Tipos:

```text
Default
Bare
Bordered
Filled
Inverse
Destructive
```

Todo botão somente com ícone deve possuir:

```text
aria-label
ou
tooltip + accessible name
```

---

# 41. Button Group

Tipos:

```text
Grouped actions
Segmented actions
Split button
Toolbar
```

---

# 42. Menu Button

```text
Primary action
        ↓
 ┌────────────┐
 │ New        │
 │ Duplicate  │
 │ Import     │
 └────────────┘
```

Variantes:

```text
Menu Button
Split Button
Icon Menu
```

---

# 43. Stateful Button

Exemplos:

```text
Follow / Following
Favorite
Like
Pin
Subscribe
```

Estado nunca deve depender exclusivamente de cor.

---

# 44. Dual Listbox

Usar para conjuntos pequenos/médios.

Para milhares de opções, substituir por uma experiência de busca + seleção.

---

# 45. Path / Process Stepper

Inspirado no Salesforce Path.

Tipos:

```text
Linear Stepper
Interactive Stepper
Process Path
Status Path
```

Estados:

```text
complete
current
upcoming
error
disabled
```

Bom para:

```text
sales stage
onboarding
approval
fulfillment
case lifecycle
```

---

# 46. Navigation

## Tabs

Tipos:

```text
Default
Underline
Contained
Scrollable
Vertical
```

Suportar:

```text
keyboard arrow navigation
Home
End
```

---

# 47. Breadcrumbs

Evitar em hierarquias rasas.

No mobile:

```text
colapsar níveis intermediários
```

---

# 48. Vertical Navigation

Suportar:

```text
sections
icons
badges
nested items
collapsed mode
```

---

# 49. Global Navigation

Estrutura:

```text
Logo
App Switcher
Navigation
Global Search
Quick Actions
Notifications
Help
Profile
```

---

# 50. Pill Navigation

Adequada para:

```text
filters
views
categories
segments
```

Não substituir Tabs quando existe relação de painel/tab semântica.

---

# 51. Pagination

Tipos:

```text
Page numbers
Previous/Next
Cursor Pagination
Load More
Infinite
```

Para aplicações enterprise, preferir server-side pagination em dados volumosos.

---

# 52. Navigation Tree

Adequado para:

```text
files
configuration
documentation
product hierarchy
administration
```

---

# 53. App Launcher

Estrutura:

```text
Search
Pinned Apps
Recent Apps
All Apps
```

Suportar:

```text
favorites
reordering
roles/permissions
```

---

# 54. Contextual Navigation

Muda conforme:

```text
module
record
workspace
permission
```

Não esconder caminhos críticos exclusivamente em menus contextuais.

---

# 55. Page Header

Tipos:

```text
Record Header
Object Header
List Header
Workspace Header
Detail Header
```

Anatomia:

```text
Breadcrumb
Icon
Eyebrow
Title
Metadata
Status
Primary Action
Secondary Actions
More Menu
Tabs optional
```

---

# 56. Navigation Adicional

```text
Side Navigation
Bottom Navigation
Command Palette
Mega Menu
Anchor Navigation
Skip Navigation
Back Link
Stepper Navigation
Subnav
Workspace Switcher
```

---

# 57. Alerts

Hierarquia:

```text
Info
Success
Warning
Danger
```

Podem ser:

```text
Global
Page
Section
Inline
```

---

# 58. Toast

Variantes:

```text
Info
Success
Warning
Error
Loading
```

Anatomia:

```text
Icon
Title
Message
Optional Action
Close
```

Boas práticas:

```text
não desaparecer rapidamente em mensagens importantes
não usar toast para erros que exigem correção no formulário
```

---

# 59. Spinner

Tamanhos:

```text
XS
SM
MD
LG
```

Nunca usar spinner indefinidamente sem feedback complementar.

Após períodos prolongados:

```text
Spinner
→ mensagem
→ opção retry/cancel
```

---

# 60. Progress Bar

Tipos:

```text
Determinate
Indeterminate
Segmented
```

---

# 61. Progress Ring

Ideal para:

```text
completion
small tasks
dashboard indicators
```

Não utilizar como gráfico de negócio genérico.

---

# 62. Scoped Notification

Vinculada semanticamente ao conteúdo que afeta.

Exemplo:

```text
Card
 ├─ Notification
 └─ Content
```

---

# 63. Empty State

Estrutura:

```text
Illustration
Title
Explanation
Primary Action
Optional Secondary Action
```

Tipos:

```text
First Use
No Data
No Results
No Permission
Configuration Needed
Error
Offline
```

---

# 64. Skeleton

Adicionar ao sistema.

Tipos:

```text
Text
Avatar
Card
Table Row
Record Detail
```

Preferível ao spinner para conteúdo cuja estrutura já é conhecida.

---

# 65. Feedback Banner

Usar para:

```text
beta feature
survey
service feedback
product announcement
```

---

# 66. Welcome / Onboarding

Não limitar ao Welcome Mat.

Criar:

```text
Welcome Mat
Onboarding Checklist
Guided Tour
Coach Mark
Getting Started Panel
Contextual Hint
```

---

# 67. Modal

Tamanhos:

```text
SM
MD
LG
XL
Fullscreen
```

Estrutura:

```text
Header
Body
Footer
```

Comportamento:

```text
focus trap
Escape
focus restoration
scroll locking
aria-modal
```

Nunca empilhar vários modais.

---

# 68. Popover

Tipos:

```text
Default
Rich
Interactive
Confirmation
```

Popover ≠ Tooltip.

Popover pode conter interação.

Tooltip normalmente não.

---

# 69. Tooltip

Uso apenas para informação complementar curta.

Não colocar:

```text
form fields
links
complex instructions
essential content
```

dentro de tooltip.

---

# 70. Dropdown Menu

Itens:

```text
Action
Checkbox Item
Radio Item
Submenu
Divider
Header
Destructive Action
```

Com teclado:

```text
Arrow Up
Arrow Down
Home
End
Escape
Enter
```

---

# 71. Drawer

Adicionar como padrão de primeira classe.

Tipos:

```text
Left
Right
Bottom
```

Variantes:

```text
Modal
Non-modal
Persistent
```

---

# 72. Action Sheet

Especialmente para touch/mobile.

Utilizar para conjunto pequeno de ações contextuais.

---

# 73. Lookup Dialog

Busca avançada:

```text
Search
Filters
Table/List
Recent
Selection
Pagination
Create Record
```

---

# 74. Split View

Estrutura:

```text
┌──────────────┬─────────────────────┐
│ Record List  │ Record Detail       │
│              │                     │
│              │                     │
└──────────────┴─────────────────────┘
```

Excelente para:

```text
CRM
email
support
administration
master/detail
```

---

# 75. Docked Components

Criar:

```text
Utility Bar
Docked Composer
Docked Chat
Docked Task
Mini Player
```

Precisam de gerenciamento centralizado de:

```text
position
collision
minimize/maximize
z-index
focus
```

---

# 76. Feedback / Overlay Adicional

```text
Confirmation Dialog
Alert Dialog
Prompt
Coach Mark
Spotlight
Command Palette
Context Menu
Inline Confirmation
Loading Overlay
Blocking Screen
```

---

# 77. Productivity Components

## Activity Timeline

Tipos de evento:

```text
call
email
task
meeting
note
status
system event
custom event
```

Permitir:

```text
filter
group by date
expand/collapse
quick actions
pagination
```

---

# 78. Global Search

Fluxo:

```text
Query
↓
Recent Searches
↓
Autocomplete
↓
Suggested Entities
↓
Results grouped by object
↓
Full Search
```

Implementar:

```text
keyboard navigation
debounce
async cancellation
recent items
search history
highlighted terms
```

---

# 79. Feed

Componentes:

```text
Feed
Feed Item
Comment
Composer
Reaction
Attachment
Mention
```

---

# 80. Publisher / Quick Create

Permite criação rápida de:

```text
task
note
event
record
post
call
email
```

Arquitetura plugin-based:

```text
Publisher
 ├─ Action Plugin
 ├─ Action Plugin
 └─ Action Plugin
```

---

# 81. File Manager

Criar:

```text
File List
File Card
File Preview
File Metadata
Upload
Version History
Download
Share
Permissions
```

---

# 82. Rich Text Editor

Barra modular:

```text
bold
italic
underline
heading
list
link
image
table
code
mention
```

Sanitização HTML obrigatória.

---

# 83. Email Composer

Estrutura:

```text
From
To
CC/BCC
Subject
Rich Text Body
Attachments
Templates
Merge Fields
Schedule
Send
```

Estados:

```text
draft
saving
saved
sending
sent
failed
```

---

# 84. Task List

Recursos:

```text
complete
due date
priority
owner
filter
bulk action
inline edit
drag reorder opcional
```

---

# 85. Notes

Tipos:

```text
Plain
Rich
Pinned
Collaborative
```

---

# 86. Productivity Adicional

```text
Command Palette
Quick Actions
Recent Items
Favorites
Clipboard
Keyboard Shortcuts
Saved Views
List Views
Filter Builder
Query Builder
Kanban
Calendar
Scheduler
Inbox
Notification Center
Activity Composer
Record History
Audit Timeline
```

---

# 87. List View

Deve ser um Product Pattern, não apenas Data Table.

Anatomia:

```text
Page Header
View Selector
Search
Filters
Display Mode
Sort
Bulk Actions
Table
Pagination
```

Variantes:

```text
Table
Cards
Kanban
Split View
```

---

# 88. Record Page

Pattern fundamental para aplicações CRM.

```text
Record Header

┌──────────────────────────────────────────┐
│ Highlights / Key Fields                 │
├───────────────────────┬──────────────────┤
│ Main Content          │ Context Sidebar  │
│                       │                  │
│ Tabs / Sections       │ Related Info     │
└───────────────────────┴──────────────────┘
```

Incluir:

```text
details
related records
activity
files
history
actions
```

---

# 89. Record Form

Modos:

```text
View
Edit
Create
Quick Edit
Inline Edit
```

Arquitetura baseada em metadata quando possível:

```json
{
  "field": "customerName",
  "type": "text",
  "required": true
}
```

---

# 90. Filter Builder

Suportar:

```text
Field
Operator
Value
AND
OR
Nested Groups
```

Modelo:

```text
Status = Active
AND
(
  Revenue > 100000
  OR
  Priority = High
)
```

---

# 91. Kanban

Estrutura:

```text
Board
Column
Card
Drop Zone
Column Total
```

Considerar:

```text
keyboard alternatives to drag-and-drop
virtualização
permission
optimistic updates
```

---

# 92. Utilities

O Design System deve possuir utilities, mas não permitir que elas substituam componentes.

Namespace:

```text
ds-
```

## Spacing

```text
ds-m-*
ds-mx-*
ds-my-*
ds-mt-*
ds-mr-*
ds-mb-*
ds-ml-*

ds-p-*
ds-px-*
ds-py-*
```

## Display

```text
ds-block
ds-inline
ds-inline-block
ds-flex
ds-grid
ds-hidden
```

## Flex

```text
ds-flex-row
ds-flex-column
ds-items-start
ds-items-center
ds-items-end
ds-justify-start
ds-justify-between
ds-justify-center
ds-flex-wrap
ds-flex-1
```

## Alignment

```text
ds-text-left
ds-text-center
ds-text-right
```

## Sizing

```text
ds-w-full
ds-h-full
ds-min-w-0
ds-max-w-full
```

## Overflow

```text
ds-overflow-auto
ds-overflow-hidden
ds-overflow-x-auto
ds-overflow-y-auto
```

## Typography

```text
ds-font-regular
ds-font-medium
ds-font-semibold
ds-font-bold

ds-truncate
ds-line-clamp-2
ds-line-clamp-3
ds-break-word
```

## Visibility

```text
ds-sr-only
ds-visible
ds-hidden
```

Responsivas:

```text
md:ds-hidden
lg:ds-flex
```

## Borders

```text
ds-border
ds-border-top
ds-border-bottom
ds-rounded-sm
ds-rounded-md
ds-rounded-lg
```

## Position

```text
ds-relative
ds-absolute
ds-fixed
ds-sticky
```

---

# 93. Component State Model

Todos os componentes interativos devem considerar:

```text
default
hover
focus-visible
active
selected
checked
expanded
disabled
readonly
loading
invalid
success
warning
dragging
drop-target
```

Isso deve existir no Design System antes do desenvolvimento.

---

# 94. Interaction State Architecture

Para evitar CSS inconsistente:

```html
data-state="open"
data-selected="true"
data-disabled
data-invalid
```

Preferível a classes arbitrárias:

```html
class="open selected red ..."
```

---

# 95. Accessibility

Target mínimo:

**WCAG 2.2 AA**

Obrigatório:

```text
keyboard navigation
visible focus
screen reader labels
semantic HTML
ARIA somente quando necessário
contrast
reduced motion
zoom 200%
high contrast compatibility
touch targets
error identification
focus management
```

## Focus Ring

```css
outline: 2px solid var(--ds-color-focus);
outline-offset: 2px;
```

Nunca:

```css
outline: none;
```

sem substituição acessível.

---

# 96. Keyboard Interaction Standards

Padronizar globalmente:

### Menus

```text
↑ ↓       navegar
Enter     executar
Escape    fechar
Home/End  extremos
```

### Tabs

```text
← →       navegar
Home/End  extremos
```

### Dialogs

```text
Tab       ciclo de foco
Escape    fechar quando permitido
```

### Combobox

```text
↑ ↓       opções
Enter     selecionar
Escape    fechar
```

---

# 97. Responsive Behavior

Não reduzir simplesmente desktop.

Definir comportamento por componente.

Exemplo Data Table:

```text
Desktop
→ tabela

Tablet
→ tabela horizontal scroll / colunas prioritárias

Mobile
→ cards ou lista estruturada
```

Exemplo Modal:

```text
Desktop → centered dialog
Mobile  → fullscreen ou bottom sheet
```

---

# 98. Internationalization

Todos os componentes devem suportar:

```text
LTR
RTL
locale
plural rules
currency
dates
numbers
timezones
long translations
```

Não utilizar:

```css
margin-left
padding-right
```

quando propriedades lógicas resolvem:

```css
margin-inline-start
padding-inline-end
```

---

# 99. Theming

Arquitetura:

```html
<html data-theme="light">
```

```html
<html data-theme="dark">
```

```html
<html data-theme="customer-a">
```

Tokens permanecem iguais.

Somente valores mudam.

```css
[data-theme="light"] {
  --ds-color-surface-page: ...;
}

[data-theme="dark"] {
  --ds-color-surface-page: ...;
}
```

---

# 100. Branding

Separar:

```text
Design System
≠
Brand Theme
```

O componente:

```jsx
<Button variant="primary">
```

não deve conhecer a cor da marca.

O tema define:

```css
--ds-color-action-primary
```

---

# 101. Component API Standard

Todos os componentes devem usar convenções consistentes.

Exemplo:

```tsx
<Button
  variant="primary"
  size="md"
  disabled={false}
  loading={false}
  iconStart="plus"
>
  Criar
</Button>
```

Evitar APIs diferentes:

```text
kind
mode
type
appearance
styleType
buttonStyle
```

para representar a mesma coisa.

Standard:

```text
variant
size
tone
state
orientation
density
```

---

# 102. Composition

Preferir:

```jsx
<Card>
  <Card.Header />
  <Card.Body />
  <Card.Footer />
</Card>
```

a:

```jsx
<Card
  title=""
  subtitle=""
  footer=""
  content=""
  button=""
  ...
/>
```

quando o componente possuir estrutura complexa.

---

# 103. Controlled vs Uncontrolled

Componentes complexos devem aceitar ambos quando aplicável:

```tsx
<Tabs value={tab} onValueChange={setTab} />
```

ou:

```tsx
<Tabs defaultValue="details" />
```

---

# 104. Async Components

Padronizar:

```text
loading
error
retry
empty
success
```

Exemplo:

```tsx
<Combobox
  loading={isLoading}
  error={error}
  onRetry={retry}
/>
```

---

# 105. Data Attributes

Expor para testes:

```html
data-component="button"
data-variant="primary"
data-state="loading"
```

Não depender de classes CSS internas para automação.

---

# 106. CSS Architecture

Recomendação:

```text
CSS Custom Properties
+
CSS Modules / component scope
+
utility layer
```

Não permitir override interno:

```css
.ds-button span > svg {
   ...
}
```

Consumidores devem usar API pública ou tokens documentados.

---

# 107. Package Architecture

```text
@company/design-tokens
@company/icons
@company/primitives
@company/components
@company/patterns
@company/css
@company/react
@company/web-components
@company/eslint-plugin
@company/testing
```

Se apenas React for necessário inicialmente:

```text
@company/tokens
@company/icons
@company/ui
```

começar simples.

---

# 108. Token Distribution

Source of truth:

```text
tokens/
├── primitive.json
├── semantic.json
├── component.json
├── themes/
│   ├── light.json
│   └── dark.json
```

Build:

```text
JSON
 ↓
Token Compiler
 ↓
CSS Variables
TypeScript
Android
iOS
Figma
```

---

# 109. CSS Output

```css
:root {
  --ds-spacing-1: 0.25rem;
  --ds-spacing-2: 0.5rem;
  --ds-spacing-4: 1rem;

  --ds-color-text-primary: ...;
  --ds-color-surface-page: ...;
}
```

---

# 110. Design / Figma Architecture

Estrutura da biblioteca:

```text
00 Foundations
01 Icons
02 Primitives
03 Forms
04 Navigation
05 Data Display
06 Feedback
07 Overlays
08 Productivity
09 Patterns
10 Templates
```

Cada componente deve possuir:

```text
variants
states
sizes
density
theme examples
content guidelines
accessibility annotations
```

---

# 111. Documentation Standard

Cada componente deve documentar:

```text
Overview
When to use
When not to use
Anatomy
Variants
Sizes
States
Behavior
Content rules
Accessibility
Keyboard interaction
Responsive behavior
Theming
API
Examples
Do / Don't
Known limitations
Changelog
```

---

# 112. Design System Website

Estrutura:

```text
Getting Started

Foundations
 ├── Color
 ├── Typography
 ├── Spacing
 ├── Layout
 ├── Motion
 ├── Elevation
 ├── Accessibility
 └── Icons

Components
 ├── Actions
 ├── Forms
 ├── Data Display
 ├── Navigation
 ├── Feedback
 └── Overlays

Patterns
 ├── Search
 ├── Record Page
 ├── List View
 ├── Forms
 ├── Filtering
 ├── CRUD
 ├── Bulk Actions
 └── Errors

Develop
Design
Content
Accessibility
Releases
```

---

# 113. Storybook

Para desenvolvimento web:

**Storybook** é adequado como ambiente de documentação e teste.

Cada componente:

```text
Overview
Playground
Variants
States
Interactions
Accessibility
Visual Regression
```

---

# 114. Testing Strategy

## Unit

```text
Vitest/Jest
```

## DOM / accessibility

```text
Testing Library
axe-core
```

## Interaction

```text
Playwright
```

## Visual Regression

```text
Chromatic
ou
Playwright screenshots
```

## Token Validation

CI deve bloquear:

```text
hardcoded colors
hardcoded spacing
invalid tokens
deprecated tokens
```

---

# 115. ESLint / Stylelint

Criar regras:

```text
no-hardcoded-color
no-hardcoded-spacing
no-private-component-import
require-accessible-icon-button
require-form-label
no-deprecated-component
```

---

# 116. Versioning

Semantic Versioning:

```text
PATCH
correção sem mudança de API

MINOR
novo componente / variante compatível

MAJOR
breaking API
```

Componentes deprecated:

```text
Active
↓
Deprecated
↓
Migration Period
↓
Removed
```

---

# 117. Governance

Papéis:

```text
Design System Core Team
Design Representative
Frontend Representative
Accessibility Owner
Product Representative
Contributors
```

Processo:

```text
RFC
↓
Design Review
↓
API Review
↓
Accessibility Review
↓
Implementation
↓
Testing
↓
Documentation
↓
Release
```

---

# 118. Contribution Model

Para novo componente, exigir:

```text
problema recorrente
≥ 2 casos reais
API reutilizável
acessibilidade definida
comportamento responsivo
design aprovado
testes
documentação
owner
```

Não adicionar componente simplesmente porque uma única página precisa dele.

---

# 119. Enterprise Patterns

Além dos componentes, criar padrões explícitos para:

```text
Create Record
Edit Record
Delete Record
Bulk Edit
Bulk Delete
Approval
Assignment
Search
Filtering
Sorting
Pagination
Import
Export
File Upload
Record Selection
Multi-select
Confirmation
Error Recovery
Unsaved Changes
Permissions
Empty State
Loading
Offline
Optimistic Updates
Long-running Job
Notifications
Audit History
```

---

# 120. Permissions Pattern

Aplicações enterprise precisam distinguir:

```text
hidden
disabled
readonly
not authorized
```

Eles não possuem a mesma semântica.

Exemplo:

```text
Usuário não conhece funcionalidade
→ hidden pode ser aceitável

Usuário conhece funcionalidade mas não pode executá-la
→ disabled + explanation

Acesso explicitamente bloqueado
→ permission state
```

---

# 121. Error Architecture

Tipos:

```text
Field Error
Form Error
Section Error
Page Error
Request Error
Permission Error
Network Error
System Error
Partial Failure
```

Estratégia:

```text
Onde ocorreu?
↓
O usuário consegue corrigir?
↓
Qual ação está disponível?
```

Evitar:

```text
Something went wrong.
```

Sempre que o sistema souber mais.

---

# 122. Loading Architecture

Hierarquia:

```text
<300ms
→ normalmente nenhum loader

300ms–2s
→ skeleton/spinner

>2s
→ feedback adicional

long-running operation
→ progresso + possibilidade de continuar trabalhando
```

---

# 123. Content Design

Tom:

```text
direto
conciso
humano
orientado a ação
sem linguagem técnica desnecessária
```

Botões:

```text
Salvar
Criar oportunidade
Enviar e-mail
Excluir contato
```

Evitar:

```text
OK
Confirmar
Executar
Enviar
```

quando a ação pode ser específica.

---

# 124. Destructive Actions

Hierarquia:

```text
Reversible
↓
Soft destructive
↓
Irreversible
```

Para irreversível:

```text
explicar impacto
nomear objeto
confirmar ação
```

Exemplo:

```text
Excluir oportunidade
```

em vez de:

```text
Confirmar
```

---

# 125. Analytics

Componentes complexos podem expor eventos sem acoplar analytics diretamente.

Exemplo:

```text
ds:interaction
ds:open
ds:close
ds:select
ds:submit
```

A aplicação conecta isso ao provedor de analytics.

O Design System não deve importar diretamente:

```text
GA
Segment
Adobe
Mixpanel
```

---

# 126. Observability

Erros de componentes críticos devem poder ser observados.

Especialmente:

```text
Upload
Rich Text
Data Table
Lookup
Search
File Preview
DateTime
Virtualized Lists
```

---

# 127. Security

## Rich Text

Sanitização obrigatória contra XSS.

## URL

Validar protocolos permitidos.

## File Upload

Validar:

```text
MIME
extension
size
malware scanning
permissions
```

## SVG

Não aceitar SVG arbitrário sem sanitização.

## HTML

Evitar APIs equivalentes a:

```text
dangerouslySetInnerHTML
```

como mecanismo normal do Design System.

---

# 128. Performance Budgets

Cada pacote deve ser tree-shakeable.

Evitar:

```tsx
import { Everything } from "@company/ui";
```

internamente.

Permitir:

```tsx
import { Button } from "@company/ui/button";
```

Metas:

```text
no unnecessary runtime CSS-in-JS
lazy load heavyweight components
virtualize large collections
code split editors/viewers
```

---

# 129. Heavy Components

Carregar sob demanda:

```text
Rich Text Editor
Data Grid avançado
Charts
Calendar
File Viewer
Code Editor
Map
```

---

# 130. Component Classification

## Tier 0 — Foundations

```text
Tokens
Typography
Icons
Layout
Accessibility
```

## Tier 1 — Primitives

```text
Box
Stack
Grid
Text
Icon
Divider
```

## Tier 2 — Core Components

```text
Button
Input
Checkbox
Select
Card
Badge
Modal
Tabs
Toast
```

## Tier 3 — Advanced Components

```text
Combobox
Data Table
Tree
Date Picker
Rich Text
File Upload
```

## Tier 4 — Product Patterns

```text
Global Search
Record Page
List View
Activity Timeline
Email Composer
App Launcher
```

---

# 131. Priority de Implementação

## Phase 1 — Foundation

```text
Tokens
Color
Typography
Spacing
Radius
Elevation
Icons
Grid
Accessibility
```

## Phase 2 — Core

```text
Button
Icon Button
Link
Input
Textarea
Checkbox
Radio
Select
Badge
Avatar
Card
Tooltip
Spinner
Alert
```

## Phase 3 — Application

```text
Tabs
Breadcrumb
Navigation
Dropdown
Modal
Drawer
Toast
Accordion
Pagination
Page Header
```

## Phase 4 — Enterprise Data

```text
Combobox
Lookup
Date Picker
Data Table
Tree
Filter Builder
List View
Split View
```

## Phase 5 — Productivity

```text
Global Search
Activity Timeline
File Manager
Rich Text
Email Composer
Publisher
Kanban
Record Page
```

---

# 132. Core Component Inventory

O catálogo inicial completo deve conter aproximadamente:

```text
Accordion
Action Sheet
Alert
App Launcher
Avatar
Badge
Breadcrumb
Button
Button Group
Calendar
Card
Carousel
Checkbox
Checkbox Group
Combobox
Command Palette
Context Menu
Data Table
Date Picker
Date Range Picker
DateTime Picker
Description List
Divider
Drawer
Dropdown
Dual Listbox
Empty State
File Preview
File Selector
Filter Builder
Form
Form Field
Icon
Icon Button
Inline Edit
Input
Input Group
Kanban
Link
List
Lookup
Menu
Modal
Navigation
Notification
Page Header
Pagination
Panel
Popover
Progress Bar
Progress Ring
Radio
Radio Group
Rich Text Editor
Scoped Notification
Search
Select
Skeleton
Slider
Spinner
Split Button
Split View
Stepper
Tab
Table
Tag
Task List
Textarea
Tile
Timeline
Toast
Toggle
Toolbar
Tooltip
Tree
Tree Table
Visual Picker
Welcome Mat
```

---

# 133. Product Pattern Inventory

```text
Activity Timeline
App Shell
Approval Flow
Audit History
Bulk Operations
Command Center
Create Record
Dashboard
Email Composer
Entity Lookup
Error Recovery
Filter & Search
Global Navigation
Global Search
Import Wizard
List View
Notification Center
Onboarding
Quick Create
Record Detail
Record Edit
Record Header
Record Page
Saved Views
Search Results
Settings
Split Workspace
Task Management
Upload Flow
Wizard
```

---

# 134. Component Quality Checklist

Antes de um componente ser considerado estável:

* [ ] Possui casos de uso documentados
* [ ] Possui anatomy
* [ ] Possui todas as variantes necessárias
* [ ] Possui estados de loading
* [ ] Possui estado empty quando aplicável
* [ ] Possui estado error quando aplicável
* [ ] Funciona apenas com teclado
* [ ] Funciona com screen reader
* [ ] Possui focus visible
* [ ] Possui RTL
* [ ] Possui dark mode
* [ ] Possui reduced motion
* [ ] Funciona em 200% zoom
* [ ] Possui mobile behavior
* [ ] Possui density compact/default
* [ ] Não contém design values hardcoded
* [ ] Possui testes unitários
* [ ] Possui interaction tests
* [ ] Possui accessibility tests
* [ ] Possui visual regression
* [ ] Possui documentação
* [ ] Possui API TypeScript
* [ ] Possui changelog

---

# 135. Naming

Não copiar namespace `slds-`.

Utilizar namespace próprio.

Exemplo:

```text
acme-
core-
enterprise-
ds-
```

Recomendação genérica:

```text
ds-
```

Componentes:

```text
DsButton
DsInput
DsModal
```

ou simplesmente:

```text
Button
Input
Modal
```

quando o pacote já provê namespace:

```tsx
import { Button } from "@company/ui";
```

---

# 136. O que preservar do modelo Salesforce

Preservar conceitualmente:

```text
Design foundations
Semantic styling
Strong data components
Record-centric patterns
Productivity components
Structured navigation
Rich state handling
Enterprise density
Icon categorization
Utility system
Component blueprints
Accessibility-first behaviors
```

---

# 137. O que não copiar

Não copiar diretamente:

```text
Salesforce Sans
Salesforce logo
Salesforce cloud identity
Salesforce brand blue
Salesforce illustrations
Salesforce proprietary icons
Salesforce-specific object semantics
SLDS class names
Salesforce-specific interaction quirks
```

O objetivo é herdar a **maturidade arquitetural**, não produzir uma réplica visual.

---

# 138. Evoluções além do SLDS

O novo sistema deve tratar como first-class:

```text
Dark Mode
High Contrast
Container Queries
CSS Logical Properties
Reduced Motion
Virtualization
Command Palette
Skeletons
Drawers
Async Combobox
Filter Builder
Permission States
Audit Interfaces
Responsive Data Tables
AI Interactions
```

---

# 139. AI Components

Para produtos modernos, acrescentar:

```text
AI Prompt Input
AI Response
Streaming Response
AI Thinking/Processing State
Suggestion
Citation
Source Card
AI Feedback
Regenerate
Stop Generation
Model/Mode Selector
AI Disclaimer
AI Action Confirmation
```

Regra fundamental:

```text
AI suggestion ≠ system fact
```

Visualmente distinguir:

```text
Generated
Suggested
Confirmed
Executed
```

---

# 140. AI Action Safety

Quando IA puder executar ações:

```text
Proposal
↓
Preview
↓
User Confirmation
↓
Execution
↓
Result
↓
Audit Log
```

Especialmente para:

```text
delete
financial operations
user permissions
communication
CRM updates
bulk actions
```

---

# 141. Design System Architecture Final

```text
                    PRODUCT
                       │
              ┌────────▼─────────┐
              │ Product Patterns│
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │   Components    │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │    Primitives   │
              └────────┬─────────┘
                       │
       ┌───────────────▼────────────────┐
       │       Semantic Tokens         │
       └───────────────┬────────────────┘
                       │
       ┌───────────────▼────────────────┐
       │       Primitive Tokens        │
       └───────────────┬────────────────┘
                       │
              ┌────────▼─────────┐
              │ Theme / Branding │
              └──────────────────┘
```

---

# 142. Recomendação Arquitetural

O Design System deve ser construído como uma **plataforma de produto interna**, e não como um pacote isolado de componentes.

A implementação recomendada é:

```text
Design Tokens
+
Headless interaction primitives quando fizer sentido
+
Accessible UI Components
+
Enterprise Product Patterns
+
Icons próprios
+
Utility CSS pequena e controlada
+
Storybook / documentação
+
Figma Library
+
Automated Testing
+
Design System Governance
```

A influência do Salesforce deve estar principalmente em:

```text
completude
consistência
enterprise UX
tratamento de dados
navegação
produtividade
acessibilidade
tokens
patterns
governança
```

e não na reprodução exata de sua identidade visual.

Isso permite criar uma experiência com a robustez conceitual de um sistema como SLDS, mas com identidade, arquitetura técnica e evolução independentes.