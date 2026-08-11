import { useEffect, useState } from 'react'
import { API_BASE_URL } from './config.js'

function App() {
  const [health, setHealth] = useState({
    state: 'checking',
    message: '正在检查后端连接…',
  })

  useEffect(() => {
    const controller = new AbortController()

    async function checkBackendHealth() {
      try {
        const response = await fetch(`${API_BASE_URL}/health`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data = await response.json()
        if (data.status !== 'ok') {
          throw new Error('健康检查响应格式不正确')
        }

        setHealth({
          state: 'success',
          message: `后端运行正常：${data.message}`,
        })
      } catch (error) {
        if (error.name !== 'AbortError') {
          setHealth({
            state: 'error',
            message: `后端连接失败：${error.message}`,
          })
        }
      }
    }

    checkBackendHealth()
    return () => controller.abort()
  }, [])

  return (
    <main className="status-card">
      <h1>地图功能demo</h1>
      <p className="frontend-status">前端运行正常</p>
      <p className={`backend-status backend-status--${health.state}`} role="status">
        {health.message}
      </p>
    </main>
  )
}

export default App
