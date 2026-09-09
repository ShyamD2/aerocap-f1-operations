import React, { useState, useEffect, useRef } from 'react';
import { 
  ShieldCheck, Activity, Gauge, Cpu, Radio, Download, 
  Layers, Compass, AlertTriangle, CheckCircle2, TrendingUp
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('3d-aero');
  const [rideHeight, setRideHeight] = useState(19);
  const [shakerFreq, setShakerFreq] = useState(12);
  const [streamlineSpeed, setStreamlineSpeed] = useState(280);
  const [budgetLimit, setBudgetLimit] = useState(400000);
  const [autoclaveLimit, setAutoclaveLimit] = useState(50);
  const [currentTime, setCurrentTime] = useState(new Date().toUTCString());

  // Clock ticker
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date().toUTCString()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Canvas Refs for 3D views
  const canvasVenturiRef = useRef(null);
  const canvasShakerRef = useRef(null);
  const canvasStreamlineRef = useRef(null);
  const canvasCopRef = useRef(null);

  // 1. Render 3D Underfloor Venturi Pressure Map
  useEffect(() => {
    const canvas = canvasVenturiRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let angle = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const cx = canvas.width / 2;
      const cy = canvas.height / 2 + 15;
      
      const isStall = rideHeight < 16;
      angle += 0.015;

      const rows = 18;
      const cols = 18;
      const scaleX = 14;
      const scaleY = 7;

      for (let i = -rows/2; i <= rows/2; i++) {
        for (let j = -cols/2; j <= cols/2; j++) {
          const x = j * scaleX;
          const y = i * scaleY;
          
          const distFromThroat = Math.sqrt((j * 0.3) ** 2 + (i * 0.2) ** 2);
          let suction = -Math.exp(-distFromThroat) * (180 / Math.max(rideHeight, 10));
          
          if (isStall) {
            suction += Math.sin(angle * 8 + j * 0.8) * 12;
          }

          const isoX = cx + (x - y) * Math.cos(0.4);
          const isoY = cy + (x + y) * Math.sin(0.4) + suction;

          const heat = Math.min(Math.abs(suction) / 8, 1);
          ctx.fillStyle = isStall 
            ? `rgba(239, 68, 68, ${0.4 + heat * 0.6})` 
            : `rgba(0, ${Math.floor(180 + heat * 30)}, ${Math.floor(170 + heat * 20)}, ${0.3 + heat * 0.7})`;
          
          ctx.beginPath();
          ctx.arc(isoX, isoY, isStall ? 3.0 : 2.2, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };
    render();

    return () => cancelAnimationFrame(animationFrameId);
  }, [rideHeight]);

  // 2. Render 3D 7-Post Shaker Rig Chassis
  useEffect(() => {
    const canvas = canvasShakerRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;
    let t = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      t += shakerFreq * 0.008;

      const cx = canvas.width / 2;
      const cy = canvas.height / 2;

      const heave = Math.sin(t) * 10;
      const pitch = Math.sin(t * 1.2) * 6;
      const roll = Math.cos(t * 0.8) * 5;

      const points = [
        { x: -80, y: -30 + roll, z: -70 + heave - pitch },
        { x: 80,  y: -30 - roll, z: -70 + heave - pitch },
        { x: 90,  y: -30 - roll, z: 80 + heave + pitch },
        { x: -90, y: -30 + roll, z: 80 + heave + pitch },
        { x: 0,   y: -65,        z: -15 + heave },
      ];

      const projected = points.map(p => ({
        x: cx + p.x * 1.2,
        y: cy + p.z * 0.65 + p.y * 0.55
      }));

      ctx.strokeStyle = '#00D2BE';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(projected[0].x, projected[0].y);
      ctx.lineTo(projected[1].x, projected[1].y);
      ctx.lineTo(projected[2].x, projected[2].y);
      ctx.lineTo(projected[3].x, projected[3].y);
      ctx.closePath();
      ctx.stroke();

      ctx.strokeStyle = '#38BDF8';
      ctx.beginPath();
      ctx.moveTo(projected[0].x, projected[0].y);
      ctx.lineTo(projected[4].x, projected[4].y);
      ctx.lineTo(projected[1].x, projected[1].y);
      ctx.stroke();

      const posts = [projected[0], projected[1], projected[2], projected[3]];
      posts.forEach((p, idx) => {
        const load = 4500 + Math.sin(t + idx) * 1100;
        ctx.strokeStyle = load > 5200 ? '#EF4444' : '#F59E0B';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x, p.y + 50);
        ctx.stroke();

        ctx.fillStyle = '#E2E8F0';
        ctx.font = '10px JetBrains Mono';
        ctx.fillText(`${load.toFixed(0)} N`, p.x - 16, p.y + 65);
      });

      animId = requestAnimationFrame(render);
    };
    render();
    return () => cancelAnimationFrame(animId);
  }, [shakerFreq]);

  // 3. Render 3D Wind Tunnel Streamlines
  useEffect(() => {
    const canvas = canvasStreamlineRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;
    let offset = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      offset += (streamlineSpeed / 280) * 3.5;

      const numLines = 12;
      for (let i = 0; i < numLines; i++) {
        const yBase = 40 + i * 18;
        ctx.beginPath();
        ctx.strokeStyle = i < 3 || i > 8 ? 'rgba(0, 210, 190, 0.3)' : 'rgba(0, 210, 190, 0.75)';
        ctx.lineWidth = 1.5;

        for (let x = 0; x < canvas.width; x += 15) {
          let yDeflect = yBase;
          if (x > 100 && x < 260) {
            const arc = Math.sin((x - 100) / 160 * Math.PI);
            yDeflect -= arc * 25;
          }
          if (x === 0) ctx.moveTo(x, yDeflect);
          else ctx.lineTo(x, yDeflect);
        }
        ctx.stroke();

        const particleX = (offset * 3 + i * 45) % canvas.width;
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.arc(particleX, yBase - (particleX > 100 && particleX < 260 ? Math.sin((particleX - 100) / 160 * Math.PI) * 25 : 0), 2, 0, Math.PI * 2);
        ctx.fill();
      }

      animId = requestAnimationFrame(render);
    };
    render();
    return () => cancelAnimationFrame(animId);
  }, [streamlineSpeed]);

  // 4. Render 3D Center of Pressure (CoP)
  useEffect(() => {
    const canvas = canvasCopRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;

    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(cx, cy - 70);
    ctx.lineTo(cx, cy + 70);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx - 45, cy - 50); ctx.lineTo(cx + 45, cy - 50);
    ctx.moveTo(cx - 50, cy + 50); ctx.lineTo(cx + 50, cy + 50);
    ctx.stroke();

    const copShift = (19 - rideHeight) * 3.0;
    const copY = cy + copShift;

    ctx.strokeStyle = '#00D2BE';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(cx, copY, 15, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = '#00D2BE';
    ctx.beginPath();
    ctx.arc(cx, copY, 3.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#E2E8F0';
    ctx.font = '11px Rajdhani, sans-serif';
    ctx.fillText(`CoP: ${(46.5 - (copShift * 0.15)).toFixed(1)}% Front`, cx + 22, copY + 4);
  }, [rideHeight]);

  const isGateLocked = rideHeight < 16;

  return (
    <div className="app-container">
      
      {/* HEADER */}
      <header className="header-banner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <img 
            src="https://upload.wikimedia.org/wikipedia/commons/f/fb/Mercedes_AMG_Petronas_F1_Logo.svg" 
            alt="Mercedes-AMG F1"
            style={{ width: '48px', height: '48px', objectFit: 'contain' }}
          />
          <div>
            <div style={{ fontSize: '11px', color: '#00D2BE', fontWeight: '700', letterSpacing: '1px', textTransform: 'uppercase' }}>
              Mercedes-AMG PETRONAS Formula One Team
            </div>
            <h1 className="font-title" style={{ fontSize: '24px', color: '#FFFFFF', margin: 0 }}>
              AEROCAP // Correlation Governance & Cost-Cap Platform
            </h1>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span className="badge badge-live">
            <Radio size={12} />
            <span>PIT WALL ONLINE: {currentTime.split(' ')[4] || '12:00:00'} UTC</span>
          </span>
          <span className="badge" style={{ background: '#1E293B', color: '#94A3B8' }}>
            FIA ISSUE 24
          </span>
        </div>
      </header>

      {/* KPI HUD BAR */}
      <section className="kpi-grid">
        <div className="hud-card">
          <div className="kpi-label">Statutory Cost Cap</div>
          <div className="kpi-value">$138.6M</div>
          <div className="kpi-subtext">£109.2M @ 1.2691 (24 Grands Prix)</div>
        </div>

        <div className="hud-card">
          <div className="kpi-label">Net Relevant Costs</div>
          <div className="kpi-value">$127.6M</div>
          <div className="kpi-subtext">£100.5M (Article 2.2 Audited)</div>
        </div>

        <div className="hud-card">
          <div className="kpi-label">Certified Headroom</div>
          <div className="kpi-value" style={{ color: '#00D2BE' }}>$11.0M</div>
          <div className="kpi-subtext">✅ Article 6.10(a) Compliant (+7.9%)</div>
        </div>

        <div className="hud-card warning">
          <div className="kpi-label">Test Rig Availability</div>
          <div className="kpi-value">4 / 5 Ready</div>
          <div className="kpi-subtext" style={{ color: '#F59E0B' }}>⚠️ STR-04 On Hold • 92.4% Cell OEE</div>
        </div>
      </section>

      {/* NAVIGATION TABS */}
      <nav className="tab-bar">
        {[
          { id: '3d-aero', label: '01 // 3D Aerodynamics & Rig Suite' },
          { id: 'pareto', label: '02 // Pareto Upgrade Optimizer' },
          { id: 'telemetry', label: '03 // Silverstone Track Telemetry' },
          { id: 'compliance', label: '04 // FIA Statutory Audit Pack' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* TAB 1: 3D AERODYNAMICS */}
      {activeTab === '3d-aero' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
            <div>
              <h2 className="font-title" style={{ fontSize: '18px', color: '#FFFFFF', marginBottom: '4px' }}>
                Underfloor Aerodynamics & Dynamic Rig Visualization
              </h2>
              <p style={{ fontSize: '12px', color: '#94A3B8' }}>
                Addresses simulation-to-track correlation disconnects prior to composite tooling release.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: '#10141C', padding: '8px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <span style={{ fontSize: '11px', color: '#94A3B8', fontFamily: 'JetBrains Mono' }}>RIDE HEIGHT:</span>
              <input 
                type="range" min="10" max="35" value={rideHeight} 
                onChange={(e) => setRideHeight(Number(e.target.value))}
                style={{ width: '120px' }}
              />
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#FFFFFF', width: '45px', fontFamily: 'JetBrains Mono' }}>
                {rideHeight}mm
              </span>
              <span className={`badge ${isGateLocked ? 'badge-locked' : 'badge-approved'}`}>
                {isGateLocked ? '🚨 GATE 3 LOCKED: DETACHMENT' : '✅ GATE 3 AUTHORIZED'}
              </span>
            </div>
          </div>

          <div className="three-d-grid">
            <div className="hud-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span className="kpi-label">3D Layout 1 // Underfloor Venturi Pressure Profile (Cp)</span>
              </div>
              <div className="canvas-container">
                <canvas ref={canvasVenturiRef} width={520} height={280} />
              </div>
              <p style={{ fontSize: '11px', color: '#94A3B8', marginTop: '10px' }}>
                Visualizes dynamic throat suction. Dropping ride height below 16mm induces aerodynamic detachment and porpoising bouncing.
              </p>
            </div>

            <div className="hud-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span className="kpi-label">3D Layout 2 // 7-Post Shaker Dynamic Chassis Heave Mesh</span>
                <span style={{ fontSize: '11px', color: '#00D2BE', fontFamily: 'JetBrains Mono' }}>{shakerFreq} Hz</span>
              </div>
              <div className="canvas-container">
                <canvas ref={canvasShakerRef} width={520} height={280} />
              </div>
              <p style={{ fontSize: '11px', color: '#94A3B8', marginTop: '10px' }}>
                Models dynamic chassis pitch, roll, and heave deflections with contact patch hydraulic actuator readouts in Newtons.
              </p>
            </div>

            <div className="hud-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span className="kpi-label">3D Layout 3 // Wind Tunnel 60% Scale Streamlines</span>
                <span style={{ fontSize: '11px', color: '#00D2BE', fontFamily: 'JetBrains Mono' }}>280 km/h</span>
              </div>
              <div className="canvas-container">
                <canvas ref={canvasStreamlineRef} width={520} height={280} />
              </div>
              <p style={{ fontSize: '11px', color: '#94A3B8', marginTop: '10px' }}>
                Airspeed velocity vectors passing over front wing outwash cascades and sidepod undercuts.
              </p>
            </div>

            <div className="hud-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span className="kpi-label">3D Layout 4 // Dynamic Center of Pressure (CoP) Map</span>
              </div>
              <div className="canvas-container">
                <canvas ref={canvasCopRef} width={520} height={280} />
              </div>
              <p style={{ fontSize: '11px', color: '#94A3B8', marginTop: '10px' }}>
                Tracks aerodynamic balance forward/rearward migration during high-speed compression.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PARETO OPTIMIZER */}
      {activeTab === 'pareto' && (
        <div className="hud-card">
          <h2 className="font-title" style={{ fontSize: '18px', color: '#FFFFFF', marginBottom: '6px' }}>
            Multi-Objective Pareto Frontier Upgrade Strategy
          </h2>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '20px' }}>
            Identifies non-dominated packages balancing Downforce Points vs Cost Cap Spend vs Autoclave Hours.
          </p>

          <table className="data-table">
            <thead>
              <tr>
                <th>Package Code</th>
                <th>Target Component</th>
                <th>Downforce Gain</th>
                <th>Lap Delta</th>
                <th>Cost (£)</th>
                <th>Cost/ms (£/ms)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {[
                { code: 'UPG-W16-FL-B', comp: 'Slotted Edge Floor', df: '+12.0 pts', lap: '-0.14s', cost: '£190,000', cpms: '£1,357', status: 'PARETO OPTIMAL' },
                { code: 'UPG-W16-FW-01', comp: 'Aggressive Inwash Wing', df: '+9.5 pts', lap: '-0.10s', cost: '£140,000', cpms: '£1,400', status: 'PARETO OPTIMAL' },
                { code: 'UPG-W16-SUSP-A', comp: 'Anti-Dive Pushrod Geom.', df: '+8.0 pts', lap: '-0.11s', cost: '£160,000', cpms: '£1,454', status: 'PARETO OPTIMAL' },
                { code: 'UPG-W16-DIFF-1', comp: 'Expanded Throat Diffuser', df: '+14.0 pts', lap: '-0.16s', cost: '£260,000', cpms: '£1,625', status: 'PARETO OPTIMAL' },
                { code: 'UPG-W16-FL-A', comp: 'Underfloor Venturi V2', df: '+18.5 pts', lap: '-0.22s', cost: '£380,000', cpms: '£1,727', status: 'PARETO OPTIMAL' },
                { code: 'UPG-W16-SIDE-A', comp: 'Undercut Sidepod (Sub-opt)', df: '+7.0 pts', lap: '-0.07s', cost: '£310,000', cpms: '£4,428', status: 'DOMINATED' },
              ].map((r, i) => (
                <tr key={i}>
                  <td style={{ color: '#FFFFFF', fontWeight: '700' }}>{r.code}</td>
                  <td>{r.comp}</td>
                  <td style={{ color: '#00D2BE' }}>{r.df}</td>
                  <td style={{ color: '#38BDF8' }}>{r.lap}</td>
                  <td>{r.cost}</td>
                  <td style={{ color: '#F59E0B', fontWeight: '700' }}>{r.cpms}</td>
                  <td>
                    <span className={`badge ${r.status === 'PARETO OPTIMAL' ? 'badge-approved' : 'badge-locked'}`}>
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 3: TELEMETRY */}
      {activeTab === 'telemetry' && (
        <div className="hud-card">
          <h2 className="font-title" style={{ fontSize: '18px', color: '#FFFFFF', marginBottom: '6px' }}>
            On-Track Telemetry // Silverstone Grand Prix
          </h2>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '20px' }}>
            George Russell Qualifying Lap Data (Copse, Maggotts-Becketts, Stowe)
          </p>

          <div className="kpi-grid" style={{ marginBottom: '20px' }}>
            <div className="hud-card">
              <div className="kpi-label">Top Speed</div>
              <div className="kpi-value">331.4 km/h</div>
            </div>
            <div className="hud-card">
              <div className="kpi-label">Peak Aero Downforce</div>
              <div className="kpi-value" style={{ color: '#00D2BE' }}>28.6 kN</div>
            </div>
            <div className="hud-card">
              <div className="kpi-label">Min Dynamic Ride Height</div>
              <div className="kpi-value" style={{ color: '#F59E0B' }}>11.8 mm</div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: COMPLIANCE */}
      {activeTab === 'compliance' && (
        <div className="hud-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 className="font-title" style={{ fontSize: '18px', color: '#FFFFFF', marginBottom: '4px' }}>
                FIA Issue 24 Statutory Cost Cap Reconciliation
              </h2>
              <p style={{ fontSize: '12px', color: '#94A3B8' }}>
                Formal audit reconciliation under Articles 2, 3, 4, TD017, and Appendix 3.
              </p>
            </div>
            <button 
              onClick={() => alert('Official FIA Compliance PDF generated and downloaded!')}
              className="tab-btn active"
            >
              <Download size={14} />
              <span>Download Official FIA Compliance PDF</span>
            </button>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Statutory Line Item</th>
                <th>USD ($)</th>
                <th>GBP (£ @ 1.2691)</th>
                <th>Regulatory Article</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Gross Ledger Total Expenses</td>
                <td>$155,000,000</td>
                <td>£122,133,795</td>
                <td>Audited Financial Accounts</td>
              </tr>
              <tr>
                <td style={{ color: '#00D2BE' }}>Less: Article 3.1 Excluded Costs</td>
                <td style={{ color: '#00D2BE' }}>($38,000,000)</td>
                <td style={{ color: '#00D2BE' }}>(£29,942,478)</td>
                <td>Articles 3.1(a)–(y)</td>
              </tr>
              <tr>
                <td>Add: Used Inventory (Current Car)</td>
                <td>+$14,000,000</td>
                <td>£11,031,439</td>
                <td>Art. 4.1(f)(i)(A)</td>
              </tr>
              <tr>
                <td style={{ color: '#F59E0B' }}>Add: Redundant Inventory Written Off</td>
                <td style={{ color: '#F59E0B' }}>+$1,800,000</td>
                <td style={{ color: '#F59E0B' }}>£1,418,327</td>
                <td>Art. 4.1(f)(i)(C) / TD017</td>
              </tr>
              <tr>
                <td style={{ color: '#38BDF8' }}>Less: Unused Inventory Carried Forward</td>
                <td style={{ color: '#38BDF8' }}>($5,200,000)</td>
                <td style={{ color: '#38BDF8' }}>(£4,097,391)</td>
                <td>Art. 4.1(f)(i)(B)</td>
              </tr>
              <tr style={{ background: '#131A24', borderTop: '2px solid #00D2BE' }}>
                <td style={{ color: '#FFFFFF', fontWeight: '700' }}>NET RELEVANT COSTS</td>
                <td style={{ color: '#00D2BE', fontWeight: '800', fontSize: '15px' }}>$127,600,000</td>
                <td style={{ color: '#00D2BE', fontWeight: '800', fontSize: '15px' }}>£100,543,692</td>
                <td style={{ color: '#00D2BE', fontWeight: '700' }}>Article 2.2</td>
              </tr>
              <tr>
                <td style={{ fontWeight: '700' }}>FIA Statutory Cost Cap Ceiling</td>
                <td style={{ fontWeight: '700' }}>$138,600,000</td>
                <td style={{ fontWeight: '700' }}>£109,211,252</td>
                <td>Art. 2.3 & 4.1(l)</td>
              </tr>
              <tr style={{ background: 'rgba(0, 210, 190, 0.08)' }}>
                <td style={{ color: '#00D2BE', fontWeight: '700' }}>Certified Headroom Remaining</td>
                <td style={{ color: '#00D2BE', fontWeight: '800' }}>$11,000,000</td>
                <td style={{ color: '#00D2BE', fontWeight: '800' }}>£8,667,559</td>
                <td style={{ color: '#00D2BE', fontWeight: '700' }}>FULLY COMPLIANT</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* FOOTER */}
      <footer style={{ marginTop: '40px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', color: '#64748B', fontSize: '11px', fontFamily: 'JetBrains Mono' }}>
        <div>Mercedes-AMG PETRONAS Formula One Team • Brackley, UK</div>
        <div>AEROCAP v2.4 • FIA Financial Regulations Issue 24</div>
      </footer>

    </div>
  );
}
