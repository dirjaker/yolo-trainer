// Minimal geometric SVG icons for YOLO Trainer menu
import { h } from 'vue'

const Icon = (d, size = 18) => ({
  render() {
    return h('svg', {
      width: size, height: size, viewBox: '0 0 24 24',
      fill: 'none', stroke: 'currentColor', 'stroke-width': '1.6',
      'stroke-linecap': 'round', 'stroke-linejoin': 'round',
      innerHTML: d,
    })
  },
})

// Dashboard — 4-square grid
export const DashboardIcon = Icon(
  '<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/>'
)

// Training — play / start
export const TrainingIcon = Icon(
  '<circle cx="12" cy="12" r="9"/><polygon points="10,8 17,12 10,16" fill="currentColor" stroke="none"/>'
)

// Model — cube
export const ModelIcon = Icon(
  '<path d="M12 2L3 7v10l9 5 9-5V7z"/><path d="M3 7l9 5"/><path d="M21 7l-9 5"/><path d="M12 12v10"/>'
)

// Dataset — layers
export const DatasetIcon = Icon(
  '<path d="M12 2L2 7l10 5 10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>'
)

// Test — target / crosshair
export const TestIcon = Icon(
  '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/>'
)

// Compare — bar chart
export const CompareIcon = Icon(
  '<rect x="3" y="13" width="4" height="8" rx="0.5"/><rect x="10" y="9" width="4" height="12" rx="0.5"/><rect x="17" y="5" width="4" height="16" rx="0.5"/>'
)

// Deploy — rocket / send
export const DeployIcon = Icon(
  '<path d="M12 2l-3 9h6z"/><path d="M9 11l-6 5h18l-6-5"/><path d="M12 22v-6"/>'
)

// Hyperparameter — sliders
export const TuningIcon = Icon(
  '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>'
)

// Team — users
export const TeamIcon = Icon(
  '<path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4-4v2"/><circle cx="8" cy="7" r="4"/><path d="M22 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>'
)

// Activity — clock
export const ActivityIcon = Icon(
  '<circle cx="12" cy="12" r="9"/><polyline points="12 6 12 12 16 16"/>'
)

export const menuIcons = {
  '/': DashboardIcon,
  '/training': TrainingIcon,
  '/models': ModelIcon,
  '/datasets': DatasetIcon,
  '/test': TestIcon,
  '/compare': CompareIcon,
  '/deploy': DeployIcon,
  '/hyperparameter': TuningIcon,
  '/team': TeamIcon,
  '/activity': ActivityIcon,
}
