# ZeroBuzz UI & Design System Specification

## 1. Design Language
- **Style**: Minimalist, clean, monochromatic with luminous violet/cyan accent highlights.
- **Surface**: Frosted off-white `#F7F7FA` canvas with clean white card surfaces (`#FFFFFF`).
- **Typography**: Clean sans-serif with negative letter spacing (`-0.02`) on bold headers.

---

## 2. Color Palette Tokens (`colors.xml`)

| Token | Hex | Role |
| :--- | :--- | :--- |
| `canvas` | `#F7F7FA` | Primary window background |
| `surface` | `#FFFFFF` | Card backgrounds |
| `surface_border` | `#E2E4EC` | Subtle card outline (1dp) |
| `primary` | `#181829` | Deep midnight slate for active states, headers, primary buttons |
| `accent_violet` | `#7C3AED` | Soft luminous violet (silenced indicator / logo accent) |
| `accent_cyan` | `#06B6D4` | Neon cyan (allowed indicator / logo accent) |
| `text_primary` | `#0F172A` | Primary readable text |
| `text_secondary` | `#475569` | Secondary descriptive text |
| `text_muted` | `#94A3B8` | Hints, timestamps, and inactive nav icons |

---

## 3. Launcher Adaptive Icon Specs
- **Canvas Size**: 108dp x 108dp (432px at xxxhdpi).
- **Safe Zone**: Central 72dp circle/squircle.
- **Emblem**: Audio waveform resolving into a zero circle.
- **Safe Zone Rule**: The emblem occupies 64% of the canvas width, perfectly centered so Samsung One UI squircles and standard circular masks clip with comfortable breathing room.
- **Background**: Seamless frosted gradient from `#FFFFFF` to `#EFF0F5`.

---

## 4. Navigation & Screens

1. **Whitelist Screen**:
   - Search bar (`bg_search_input`) with shield icon.
   - RecyclerView of all launchable packages with real app icons and names.
   - MaterialSwitch for instant zero-latency bypass.
2. **Activity Screen**:
   - Filter buttons: `All`, `Unbuzz`, `Buzz`.
   - Card feed of intercepted notifications with app icon, title, text, and single-tap silence toggle (`btnToggleSilence`).
3. **Settings Screen**:
   - Master engine card: "Want buzz in your life" with enable/disable switch.
   - App information card: Version 1.0.0.
   - Developer credit card: Redirect to `https://github.com/hereisswapnil`.
