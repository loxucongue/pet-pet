# Design System - PetPet Companion Mini Program

## Product Context
- **What this is:** A pet-owner-focused mini program that combines virtual pet growth, daily care tracking, AI medical interpretation, AI Q&A, and a knowledge-sharing forum.
- **Who it's for:** Cat-first pet owners (especially young mobile users) who want emotional companionship plus practical care decisions.
- **Space/industry:** Pet care, consumer health, AI assistant, social community.
- **Project type:** Mobile-first mini program / app-like web product.

## Aesthetic Direction
- **Direction:** Playful + Clinical Trust Hybrid
- **Decoration level:** Intentional
- **Mood:** Warm, friendly, and collectible in growth scenes; calm, clear, and reliable in data/medical scenes. The interface should feel "cute but not childish, professional but not cold."
- **Reference sites:** Not externally researched in this pass; direction is based on design consultation best practices and category conventions.

## Safe vs Risk
- **Safe choices (category baseline):**
- Card-based mobile layout with strong information hierarchy.
- Calm neutral surfaces for health and analytics content.
- Conventional semantic status colors for warnings and abnormal metrics.
- **Risks (brand differentiation):**
- Use a playful accent pair (mint + coral) instead of generic blue/purple health-app tones to make the product memorable.
- Introduce "space room" visual layer (soft gradients, rounded scene frames, collectible props) in growth module while keeping medical pages restrained.
- Use a distinctive Chinese display font for emotional moments (titles/events) but keep body/system content highly legible.

## Typography
- **Display/Hero:** `ZCOOL KuaiLe` - adds personality for growth moments, event banners, and mascot states.
- **Body:** `Noto Sans SC` - highly readable Chinese text rendering for dense mobile reading.
- **UI/Labels:** `Noto Sans SC` Medium/Semibold.
- **Data/Tables:** `JetBrains Mono` (numbers only) + `Noto Sans SC` (labels) - improves metric scanning and date/weight consistency.
- **Code:** `JetBrains Mono`.
- **Loading:** Google Fonts CDN (`Noto Sans SC`, `ZCOOL KuaiLe`, `JetBrains Mono`), with system fallback `PingFang SC`, `Hiragino Sans GB`, `Microsoft YaHei`.
- **Scale (mobile-first):**
- Display XL: 36px / 1.15 / 700
- Display L: 30px / 1.2 / 700
- H1: 24px / 1.25 / 700
- H2: 20px / 1.3 / 700
- H3: 18px / 1.35 / 600
- Body L: 16px / 1.6 / 400
- Body M: 14px / 1.6 / 400
- Body S: 12px / 1.5 / 400
- Caption: 11px / 1.4 / 500

## Color
- **Approach:** Balanced
- **Primary:** `#2A9D8F` (Mint Teal) - primary actions, progression, positive trend.
- **Secondary:** `#E76F51` (Warm Coral) - rewards, collectible highlights, important CTA moments.
- **Support Accent:** `#E9C46A` (Sunlight Gold) - medals, streak badges, premium but friendly emphasis.
- **Neutrals (cool-warm balanced):**
- `#F7F8FA` surface-0
- `#EEF1F4` surface-1
- `#D9DEE5` border-subtle
- `#8A95A6` text-muted
- `#2B3440` text-primary
- `#141A22` text-strong
- **Semantic:**
- success `#3AA675`
- warning `#F4A261`
- error `#D9534F`
- info `#4C8BF5`
- **Dark mode strategy:** keep chroma but reduce saturation by ~15%; raise base surface to deep slate (`#10151C`, `#171E27`), keep text contrast >= WCAG AA, avoid pure-black backgrounds.

## Spacing
- **Base unit:** 4px
- **Density:** Comfortable
- **Scale:** 2xs(2) xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48) 3xl(64)

## Layout
- **Approach:** Hybrid
- **Grid:**
- Mobile (default): 4-column fluid grid, 16px page padding, 12px gutters.
- Tablet/foldable: 8-column, 24px page padding.
- Desktop operations console (if added later): 12-column, max width 1200px.
- **Max content width:** 640px for core mobile content containers.
- **Card strategy:** stack-first, sectional grouping by module (Growth, Data, AI Health, Forum).
- **Border radius hierarchy:** sm 8px, md 12px, lg 16px, xl 24px, full 9999px.

## Motion
- **Approach:** Intentional
- **Easing:** enter `cubic-bezier(0.22, 1, 0.36, 1)`, exit `cubic-bezier(0.4, 0, 1, 1)`, move `cubic-bezier(0.4, 0, 0.2, 1)`
- **Duration:** micro 80ms, short 180ms, medium 280ms, long 480ms
- **Rules:**
- Growth module: subtle bobbing/parallax for pet room elements.
- Data/Medical module: minimal transitions only (expand/collapse, chart update).
- Feedback: every reward interaction gets one celebratory micro-animation (<700ms).

## Module-Specific UI Rules
- **1) Virtual Growth Space**
- Scene cards use warmer gradients and decorative shapes.
- Daily real-pet check-in is the primary habit trigger and must stay one-tap.
- Props inventory should prioritize visual ownership (rarity color + count + recent gain).
- **2) Data Tracking**
- Timeline + calendar dual view: timeline for narrative, calendar for operational reminders.
- Dates and weights should always display in monospaced numerals.
- Critical tasks (deworming, vaccine, unusual weight change) stay pinned at top.
- **3) AI Medical Interpretation**
- Separate "data facts" from "AI interpretation" in different card styles.
- Every AI conclusion includes confidence level and suggested action window.
- Use plain language summaries first, detail-expansion second.
- **4) AI Chat Agent**
- Persistent quick prompts: coughing, vomiting, appetite loss, scratching, litter behavior.
- Always show safety escalation prompts ("seek vet now") with high-contrast treatment.
- Pull recent monitored data as context chips before answer generation.
- **5) Knowledge Forum**
- Category tabs: life, behavior training, medical, nutrition, emotional bonding.
- Post cards show trust signals: author level, pet profile, evidence tags, moderation state.
- Encourage practical formats: checklist posts, before/after logs, symptom diary templates.

## Content Voice
- Friendly, supportive, and evidence-aware.
- Avoid fear-inducing language; prioritize actionable next steps.
- Explain medical terms with one-sentence plain-language gloss.

## Accessibility & UX Guardrails
- Minimum body text size 14px in mobile UI.
- Hit area >= 44x44px for all tappable elements.
- Color is never the only status channel; pair with icon/text labels.
- Core task completion (daily check-in, adding a record, asking AI question) must be <= 3 taps.

## Tokens (Starter Set)
- **Font tokens:** `font-display`, `font-body`, `font-data`
- **Color tokens:** `color-primary`, `color-secondary`, `color-bg`, `color-surface`, `color-text`, `color-success`, `color-warning`, `color-error`, `color-info`
- **Radius tokens:** `radius-sm`, `radius-md`, `radius-lg`, `radius-xl`, `radius-pill`
- **Spacing tokens:** `space-2xs` ... `space-3xl`
- **Motion tokens:** `motion-micro`, `motion-short`, `motion-medium`, `motion-long`

## Implementation Notes for Mini Program
- Prioritize local performance: preload only body font; lazy-load display font for non-critical views.
- Keep animation on transform/opacity only for low-end devices.
- Persist key reminders locally with cloud backup for notification resilience.

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-20 | Initial design system created | Created by /design-consultation based on provided product modules and target user profile |

