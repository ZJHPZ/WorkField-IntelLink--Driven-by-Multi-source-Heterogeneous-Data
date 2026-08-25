import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/variables.css'
import './styles/base.css'
import './styles/utilities.css'
import './styles/animations.css'
import './styles/dark-override.css'
import './styles/enterprise.css'
import './styles/markdown.css'
import './styles/tailwind.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
