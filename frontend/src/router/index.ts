import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/chart/:ticker',
      name: 'chart',
      component: () => import('@/views/ChartView.vue'),
    },
    {
      path: '/calculator',
      name: 'calculator',
      component: () => import('@/views/CalculatorView.vue'),
    },
    {
      path: '/stock-search',
      name: 'stock-search',
      component: () => import('@/views/StockSearchView.vue'),
    },
    {
      path: '/investment-plans',
      name: 'investment-plans',
      component: () => import('@/views/InvestmentPlanView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (!to.meta.public && !token) {
    return { name: 'login' }
  }
})

export default router
