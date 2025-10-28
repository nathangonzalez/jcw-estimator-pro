import React, { useState } from 'react';
import { Calculator, TrendingUp, Database, Brain } from 'lucide-react';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [formData, setFormData] = useState({
    area_sf: '',
    project_type: 'residential',
    finish_quality: 'standard',
    design_complexity: 'moderate',
    bedrooms: '3',
    bathrooms: '2',
    garage_bays: '2',
    windows: '',
    doors: '',
    special_features: []
  });

  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  // Fetch stats on mount
  React.useEffect(() => {
    fetch(`${API_URL}/stats`)
      .then(res => res.json())
      .then(setStats)
      .catch(console.error);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/estimate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          area_sf: parseFloat(formData.area_sf),
          bedrooms: parseInt(formData.bedrooms) || 0,
          bathrooms: parseInt(formData.bathrooms) || 0,
          garage_bays: parseInt(formData.garage_bays) || 0,
          windows: parseInt(formData.windows) || 0,
          doors: parseInt(formData.doors) || 0
        })
      });

      const data = await response.json();
      setEstimate(data);
    } catch (error) {
      alert('Error getting estimate: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <h1><Calculator size={32} /> JCW Cost Estimator Pro</h1>
          <p>AI-Powered Construction Cost Estimation</p>
        </div>
      </header>

      {stats && (
        <div className="stats-banner">
          <div className="container stats-grid">
            <div className="stat-card">
              <Database size={24} />
              <div>
                <h3>{stats.total_projects}</h3>
                <p>Training Projects</p>
              </div>
            </div>
            <div className="stat-card">
              <TrendingUp size={24} />
              <div>
                <h3>{stats.avg_cost_per_sf ? `$${stats.avg_cost_per_sf.toFixed(2)}/SF` : 'N/A'}</h3>
                <p>Avg Cost per SF</p>
              </div>
            </div>
            <div className="stat-card">
              <Brain size={24} />
              <div>
                <h3>±6.5%</h3>
                <p>Model Accuracy</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <main className="container main-content">
        <div className="form-section">
          <h2>Project Details</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label>Total Area (SF) *</label>
                <input
                  type="number"
                  value={formData.area_sf}
                  onChange={(e) => setFormData({ ...formData, area_sf: e.target.value })}
                  required
                  placeholder="5000"
                />
              </div>

              <div className="form-group">
                <label>Project Type *</label>
                <select
                  value={formData.project_type}
                  onChange={(e) => setFormData({ ...formData, project_type: e.target.value })}
                >
                  <option value="residential">Residential</option>
                  <option value="commercial">Commercial</option>
                </select>
              </div>

              <div className="form-group">
                <label>Finish Quality *</label>
                <select
                  value={formData.finish_quality}
                  onChange={(e) => setFormData({ ...formData, finish_quality: e.target.value })}
                >
                  <option value="economy">Economy</option>
                  <option value="standard">Standard</option>
                  <option value="premium">Premium</option>
                  <option value="luxury">Luxury</option>
                </select>
              </div>

              <div className="form-group">
                <label>Design Complexity *</label>
                <select
                  value={formData.design_complexity}
                  onChange={(e) => setFormData({ ...formData, design_complexity: e.target.value })}
                >
                  <option value="simple">Simple</option>
                  <option value="moderate">Moderate</option>
                  <option value="complex">Complex</option>
                  <option value="luxury">Luxury</option>
                </select>
              </div>

              <div className="form-group">
                <label>Bedrooms</label>
                <input
                  type="number"
                  value={formData.bedrooms}
                  onChange={(e) => setFormData({ ...formData, bedrooms: e.target.value })}
                  placeholder="3"
                />
              </div>

              <div className="form-group">
                <label>Bathrooms</label>
                <input
                  type="number"
                  value={formData.bathrooms}
                  onChange={(e) => setFormData({ ...formData, bathrooms: e.target.value })}
                  placeholder="2"
                />
              </div>

              <div className="form-group">
                <label>Garage Bays</label>
                <input
                  type="number"
                  value={formData.garage_bays}
                  onChange={(e) => setFormData({ ...formData, garage_bays: e.target.value })}
                  placeholder="2"
                />
              </div>

              <div className="form-group">
                <label>Windows</label>
                <input
                  type="number"
                  value={formData.windows}
                  onChange={(e) => setFormData({ ...formData, windows: e.target.value })}
                  placeholder="Auto"
                />
              </div>
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Calculating...' : 'Get Estimate'}
            </button>
          </form>
        </div>

        {estimate && (
          <div className="results-section">
            <h2>Cost Estimate</h2>
            
            <div className="estimate-card primary">
              <h3>Recommended Estimate</h3>
              <div className="estimate-value">
                {formatCurrency(estimate.ensemble_estimate.total_cost)}
              </div>
              <p className="estimate-detail">
                {formatCurrency(estimate.ensemble_estimate.cost_per_sf)}/SF
              </p>
              <span className={`confidence-badge ${estimate.confidence}`}>
                {estimate.confidence.toUpperCase()} CONFIDENCE
              </span>
            </div>

            <div className="estimates-grid">
              <div className="estimate-card">
                <h4>Rule-Based Model</h4>
                <div className="estimate-value small">
                  {formatCurrency(estimate.rule_based_estimate.total_cost)}
                </div>
                <p>{formatCurrency(estimate.rule_based_estimate.cost_per_sf)}/SF</p>
                <div className="breakdown">
                  <div>Hard Costs: {formatCurrency(estimate.rule_based_estimate.hard_costs)}</div>
                  <div>Soft Costs: {formatCurrency(estimate.rule_based_estimate.soft_costs)}</div>
                </div>
              </div>

              {estimate.ml_estimate && (
                <div className="estimate-card">
                  <h4>ML Model</h4>
                  <div className="estimate-value small">
                    {formatCurrency(estimate.ml_estimate.total_cost)}
                  </div>
                  <p>{formatCurrency(estimate.ml_estimate.cost_per_sf)}/SF</p>
                  <div className="ml-badge">{estimate.ml_estimate.confidence} confidence</div>
                </div>
              )}
            </div>

            <div className="info-box">
              <p><strong>Method:</strong> {estimate.ensemble_estimate.method}</p>
              <p><strong>Training Projects:</strong> {estimate.ensemble_estimate.training_projects}</p>
              <p className="small-text">
                This estimate is based on {estimate.ensemble_estimate.training_projects} completed projects
                with an average accuracy of ±6.5%. The model improves with every project added.
              </p>
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <div className="container">
          <p>&copy; 2025 JCW Cost Estimator Pro | Professional Construction Estimation</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
