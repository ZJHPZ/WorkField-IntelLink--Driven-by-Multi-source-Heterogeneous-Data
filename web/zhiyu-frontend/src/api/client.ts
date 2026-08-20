import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 错误统一处理
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail?.error_message ||
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      '请求失败'
    console.error('[API Error]', message)
    return Promise.reject(
      new Error(typeof message === 'string' ? message : JSON.stringify(message))
    )
  }
)

export default client
