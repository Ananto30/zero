
import DefaultTheme from 'vitepress/theme'
import './custom.css'

import AdsLayout from '@theme/layouts/AdsLayout.vue'

export default {
    ...DefaultTheme,
    Layout: AdsLayout
}
