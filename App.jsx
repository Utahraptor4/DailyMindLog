import React, { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import IncomeSourceManager from './components/IncomeSourceManager'
import DailyLogger from './components/DailyLogger'
import Analytics from './components/Analytics'
import Navigation from './components/Navigation'
import { apiService } from './services/api'

function App() {
  const [currentView, setCurrentView] = useState('dashboard')
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const response = await apiService.getDashboard()
      if (response.success) {
        setDashboardData(response.data)
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const refreshData = () => {
    loadDashboardData()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation currentView={currentView} onViewChange={setCurrentView} />
      
      <main className="container mx-auto px-4 py-8">
        {currentView === 'dashboard' && (
          <Dashboard 
            data={dashboardData} 
            onRefresh={refreshData}
            onNavigate={setCurrentView}
          />
        )}
        
        {currentView === 'sources' && (
          <IncomeSourceManager onUpdate={refreshData} />
        )}
        
        {currentView === 'logger' && (
          <DailyLogger onUpdate={refreshData} />
        )}
        
        {currentView === 'analytics' && (
          <Analytics />
        )}
      </main>
    </div>
  )
}

export default App