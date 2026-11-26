import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertCircle, Download, Bell, BookOpen, Building2, Calendar,
  BarChart3, Check, ChevronDown, ChevronRight, ClipboardList,
  CreditCard, Clock, FileText, GraduationCap, LayoutDashboard, Lock,
  LogOut, Menu, Pencil, Plus, Search, Shield, ShieldCheck, Trash2,
  UserCog, Users, Wallet, X, Briefcase, GitBranch
} from 'lucide-react';
import { api, clearToken, getToken, setToken } from './api';
import FinancePortal from './FinancePortal';

const NAV = [
  { title: 'OVERVIEW', items: [{ id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard }] },
  { title: 'INSTITUTION SETUP', items: [
    { id: 'institutions', label: 'Institutions', icon: Building2 },
    { id: 'academic-years', label: 'Academic Years', icon: Calendar },
    { id: 'courses', label: 'Courses / Programmes', icon: GraduationCap },
    { id: 'departments', label: 'Departments', icon: Briefcase },
    { id: 'batches', label: 'Batches', icon: Users },
    { id: 'semesters', label: 'Semesters / Years', icon: BookOpen },
  ]},
  { title: 'ACCESS CONTROL', items: [
    { id: 'users', label: 'User Management', icon: UserCog },
    { id: 'roles', label: 'Role Management', icon: Shield },
    { id: 'permissions', label: 'Permissions', icon: Lock },
    { id: 'role-permissions', label: 'Role Permissions', icon: ShieldCheck },
    { id: 'portal-access', label: 'Portal Access', icon: ShieldCheck },
  ]},
  { title: 'WORKFLOW & COMMUNICATION', items: [
    { id: 'approval-workflows', label: 'Approval Workflows', icon: GitBranch },
    { id: 'notification-configs', label: 'Notifications', icon: Bell },
  ]},
  { title: 'INSTITUTION-WIDE VIEW', items: [
    { id: 'students', label: 'Students', icon: GraduationCap },
    { id: 'employees', label: 'Employees', icon: Briefcase },
    { id: 'audit-logs', label: 'Audit Logs', icon: Clock },
    { id: 'reports', label: 'Institution Reports', icon: BarChart3 },
  ]},
];

const META = {
  institutions: { title: 'Institution Master', subtitle: 'Manage KMCT institutions and their status.', singular: 'Institution', fields: [
    ['code','Institution Code','text',true], ['name','Institution Name','text',true], ['address','Address','textarea'], ['is_active','Active','boolean']
  ], columns: ['code','name','address','is_active'] },
  'academic-years': { title: 'Academic Year Master', subtitle: 'Configure academic years for each institution.', singular: 'Academic Year', fields: [
    ['institution_id','Institution','reference',false,{resource:'institutions',label:'name'}], ['label','Academic Year','text',true], ['start_date','Start Date','date'], ['end_date','End Date','date'], ['is_current','Current Year','boolean'], ['is_active','Active','boolean']
  ], columns: ['label','institution_id','start_date','end_date','is_current','is_active'] },
  courses: { title: 'Course / Programme Master', subtitle: 'Maintain programmes offered by each institution.', singular: 'Course', fields: [
    ['institution_id','Institution','reference',false,{resource:'institutions',label:'name'}], ['code','Course Code','text',true], ['name','Course Name','text',true], ['programme_type','Programme Type','text'], ['duration_years','Duration (years)','number'], ['is_active','Active','boolean']
  ], columns: ['code','name','programme_type','duration_years','institution_id','is_active'] },
  departments: { title: 'Department Master', subtitle: 'Manage institution-wise departments.', singular: 'Department', fields: [
    ['institution_id','Institution','reference',false,{resource:'institutions',label:'name'}], ['code','Department Code','text',true], ['name','Department Name','text',true], ['is_active','Active','boolean']
  ], columns: ['code','name','institution_id','is_active'] },
  batches: { title: 'Batch Master', subtitle: 'Map batches to the relevant institution and course.', singular: 'Batch', fields: [
    ['institution_id','Institution','reference',false,{resource:'institutions',label:'name'}], ['course_id','Course','reference',false,{resource:'courses',label:'name'}], ['label','Batch Name / Label','text',true], ['start_year','Start Year','number'], ['end_year','End Year','number'], ['is_active','Active','boolean']
  ], columns: ['label','course_id','start_year','end_year','institution_id','is_active'] },
  semesters: { title: 'Semester / Year Master', subtitle: 'Configure semester or year sequences for courses.', singular: 'Semester / Year', fields: [
    ['course_id','Course','reference',false,{resource:'courses',label:'name'}], ['label','Semester / Year Label','text',true], ['sequence','Sequence','number'], ['is_active','Active','boolean']
  ], columns: ['label','course_id','sequence','is_active'] },
  users: { title: 'User Management', subtitle: 'Create users and assign their institution and system role.', singular: 'User', fields: [
    ['username','Username','text',true], ['full_name','Full Name','text',true], ['email','Email','email',true], ['password','Temporary Password','password',true], ['institution_id','Institution (blank for central user)','reference',false,{resource:'institutions',label:'name'}], ['role_id','Role','reference',true,{resource:'roles',label:'name'}], ['is_active','Active','boolean']
  ], columns: ['username','full_name','email','role_name','institution_id','is_active'] },
  roles: { title: 'Role Management', subtitle: 'Define roles used across the ERP portals.', singular: 'Role', fields: [
    ['key','Role Key','text',true], ['name','Role Name','text',true], ['description','Description','textarea'], ['is_system','System Role','boolean']
  ], columns: ['key','name','description','is_system'] },
  permissions: { title: 'Permission Management', subtitle: 'Maintain permission keys and the modules they govern.', singular: 'Permission', fields: [
    ['key','Permission Key','text',true], ['name','Permission Name','text',true], ['module','Module','text',true], ['description','Description','textarea']
  ], columns: ['key','name','module','description'] },
  'role-permissions': { title: 'Role Permission Mapping', subtitle: 'Assign system permissions to roles.', singular: 'Role Permission', fields: [
    ['role_id','Role','reference',true,{resource:'roles',label:'name'}], ['permission_id','Permission','reference',true,{resource:'permissions',label:'name'}], ['is_granted','Granted','boolean']
  ], columns: ['role_name','permission_name','role_id','permission_id','is_granted'] },
  'portal-access': { title: 'Portal Access Configuration', subtitle: 'Configure a user’s allowed actions in each portal.', singular: 'Portal Access Rule', fields: [
    ['user_id','User','reference',true,{resource:'users',label:'username'}], ['portal_key','Portal','select',true,['STUDENT','ADMIN','FACULTY','HR_ADMIN','FINANCE_ADMIN','MAIN_ADMIN']], ['can_view','View','boolean'], ['can_create','Create','boolean'], ['can_update','Update','boolean'], ['can_delete','Delete','boolean']
  ], columns: ['username','user_id','portal_key','can_view','can_create','can_update','can_delete'] },
  'approval-workflows': { title: 'Approval Workflow Configuration', subtitle: 'Configure the approval levels for institutional processes.', singular: 'Approval Workflow', fields: [
    ['institution_id','Institution','reference',false,{resource:'institutions',label:'name'}], ['name','Workflow Name','text',true], ['module','Module','select',true,['HR','FINANCE','ACADEMIC','ADMIN']], ['level1_role','Level 1 Approver Role','text',true], ['level2_role','Level 2 Approver Role','text',true], ['is_active','Active','boolean']
  ], columns: ['name','module','level1_role','level2_role','institution_id','is_active'] },
  'notification-configs': { title: 'Notification Configuration', subtitle: 'Choose which system events send email and in-app notifications.', singular: 'Notification Rule', fields: [
    ['institution_id','Institution (blank for all)','reference',false,{resource:'institutions',label:'name'}], ['event_key','Event Key','text',true], ['channel_email','Email','boolean'], ['channel_in_app','In-app','boolean'], ['enabled','Enabled','boolean']
  ], columns: ['event_key','institution_id','channel_email','channel_in_app','enabled'] },
};

const TITLE_MAP = Object.fromEntries(NAV.flatMap(g => g.items.map(x => [x.id, x.label])));
const money = (n) => new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(Number(n || 0));
const nice = (s='') => String(s).replaceAll('_',' ').replace(/\b\w/g, c => c.toUpperCase());

function Login({ onLogin }) {
  const [username,setUsername] = useState('admin');
  const [password,setPassword] = useState('');
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError('');
    try { const result = await api('/api/auth/login',{method:'POST',body:JSON.stringify({username,password})}); setToken(result.access_token); onLogin(result.user); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  return <div className="login-screen"><div className="login-card">
    <div className="brand-mark large">KMCT <span>ERP</span></div>
    <div className="eyebrow">SECURE PORTAL ACCESS</div>
    <h1>Welcome back</h1><p className="muted">Sign in to your authorised KMCT ERP portal.</p>
    <form onSubmit={submit} className="login-form">
      <label>Username<input autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)} required /></label>
      <label>Password<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} required /></label>
      {error && <div className="error-line"><AlertCircle size={16}/>{error}</div>}
      <button className="primary-btn full" disabled={busy}>{busy?'Signing in…':'Sign in'} <ChevronRight size={17}/></button>
    </form>
    <div className="login-foot">KMCT ERP · Centralised institution management</div>
  </div></div>;
}

function App() {
  const [authenticated,setAuthenticated] = useState(Boolean(getToken()));
  const [user,setUser] = useState(null);
  const [active,setActive] = useState('dashboard');
  const [sidebarOpen,setSidebarOpen] = useState(false);
  const [refreshKey,setRefreshKey] = useState(0);
  const [toast,setToast] = useState('');
  const refresh = useCallback(()=>setRefreshKey(x=>x+1),[]);
  useEffect(()=>{
    if (!authenticated) return;
    api('/api/auth/me').then(setUser).catch(()=>{clearToken();setAuthenticated(false);});
  },[authenticated]);
  useEffect(()=>{ if(!toast) return; const id=setTimeout(()=>setToast(''),3200); return ()=>clearTimeout(id); },[toast]);
  const logout = () => { clearToken(); setAuthenticated(false); setUser(null); setActive('dashboard'); };
  if (!authenticated) return <Login onLogin={(u)=>{setUser(u);setAuthenticated(true);}}/>;
  if (user?.role === 'FINANCE_ADMIN') return <FinancePortal user={user} onLogout={logout}/>;
  const selected = NAV.flatMap(g=>g.items).find(x=>x.id===active);
  const pageTitle = active==='dashboard'?'Main dashboard':(META[active]?.title || selected?.label || 'Dashboard');
  return <div className="app-shell">
    <aside className={`sidebar ${sidebarOpen?'open':''}`}>
      <div className="brand"><div className="brand-mark">KMCT <span>ERP</span></div><div className="brand-sub">Central Administration</div><button className="mobile-close" onClick={()=>setSidebarOpen(false)}><X size={18}/></button></div>
      <div className="institution-chip"><span className="institution-dot"/> <span><b>All Institutions</b><small>Central view</small></span><ChevronDown size={14}/></div>
      <nav className="nav-list">{NAV.map(group=><div className="nav-group" key={group.title}><div className="nav-heading">{group.title}</div>{group.items.map(item=>{const Icon=item.icon;return <button key={item.id} className={`nav-item ${active===item.id?'active':''}`} onClick={()=>{setActive(item.id);setSidebarOpen(false);}}><Icon size={17}/><span>{item.label}</span>{active===item.id&&<span className="active-indicator"/>}</button>;})}</div>)}</nav>
      <div className="sidebar-bottom"><div className="secure-note"><ShieldCheck size={15}/><span>Secure admin session</span></div><div className="profile-row"><div className="avatar">{(user?.full_name||'A').slice(0,1).toUpperCase()}</div><div className="profile-copy"><b>{user?.full_name||'Super Admin'}</b><small>SUPERADMIN</small></div><button className="icon-btn logout-btn" title="Sign out" onClick={logout}><LogOut size={17}/></button></div></div>
    </aside>
    {sidebarOpen&&<button className="sidebar-backdrop" aria-label="Close menu" onClick={()=>setSidebarOpen(false)}/>}
    <main className="main-area">
      <header className="topbar"><div className="topbar-left"><button className="mobile-menu icon-btn" onClick={()=>setSidebarOpen(true)}><Menu size={20}/></button><div className="breadcrumb">KMCT ERP <ChevronRight size={14}/> <b>{pageTitle}</b></div></div><div className="topbar-right"><span className="topbar-institution">National College of Pharmacy <span className="topbar-sep">·</span> All institutions</span><button className="icon-btn" title="Notifications" onClick={()=>setActive('notification-configs')}><Bell size={18}/></button><div className="top-avatar">{(user?.full_name||'A').slice(0,1).toUpperCase()}</div></div></header>
      <div className="page-wrap">
        {active==='dashboard' ? <Dashboard refreshKey={refreshKey} onNavigate={setActive}/> : active==='audit-logs' ? <AuditPage refreshKey={refreshKey}/> : active==='reports' ? <ReportsPage refreshKey={refreshKey}/> : active==='students'||active==='employees' ? <ReadOnlyPage resource={active} refreshKey={refreshKey}/> : <ResourcePage resource={active} refreshKey={refreshKey} onChanged={(message)=>{refresh();setToast(message);}}/>}
        <footer className="page-footer">© {new Date().getFullYear()} KMCT ERP <span>·</span> Super Admin Portal <span className="footer-status"><i/> API connected when backend is available</span></footer>
      </div>
    </main>
    {toast&&<div className="toast"><Check size={17}/>{toast}</div>}
  </div>;
}

function PageHeader({title,subtitle,actions}) { return <div className="page-header"><div><div className="eyebrow">KMCT ERP · SUPER ADMIN</div><h1>{title}</h1><p>{subtitle}</p></div>{actions&&<div className="header-actions">{actions}</div>}</div>; }

function Dashboard({refreshKey,onNavigate}) {
  const [data,setData]=useState(null); const [error,setError]=useState('');
  useEffect(()=>{api('/api/admin/dashboard').then(setData).catch(e=>setError(e.message));},[refreshKey]);
  const cards = data ? [
    {label:'Students',value:data.students,icon:GraduationCap,color:'blue',hint:'Across institutions'},
    {label:'Total billed',value:money(data.billed),icon:Wallet,color:'violet',hint:'Assigned fee amount'},
    {label:'Fees collected',value:money(data.collected),icon:CreditCard,color:'green',hint:'Successful payments'},
    {label:'Outstanding',value:money(data.outstanding),icon:FileText,color:'amber',hint:'Billed less collected'},
    {label:'Employees',value:data.employees,icon:Briefcase,color:'blue',hint:'Employee master'},
    {label:'Present today',value:data.present_today,icon:Check,color:'green',hint:'Attendance records'},
    {label:'Pending leave requests',value:data.pending_leaves,icon:Calendar,color:'amber',hint:'Awaiting approval'},
    {label:'Audit entries',value:data.audit_entries,icon:Activity,color:'violet',hint:'Recorded system actions'},
  ] : [];
  const maxAmount=Math.max(1,...(data?.monthly_collection||[]).map(x=>x.amount));
  return <>
    <PageHeader title="Main dashboard" subtitle="Institution-wide overview of academic, financial and HR operations." actions={<button className="secondary-btn" onClick={()=>onNavigate('audit-logs')}><Clock size={16}/> View audit trail</button>}/>
    {error&&<div className="banner error-banner"><AlertCircle size={17}/>{error} <button onClick={()=>location.reload()}>Retry</button></div>}
    <div className="section-row"><div><h2>Institution overview</h2><p>Key operational indicators across KMCT institutions</p></div><span className="live-pill"><i/> Live data</span></div>
    <div className="stats-grid">{cards.map((c,i)=>{const Icon=c.icon;return <div className="stat-card" key={c.label}><div className={`stat-icon ${c.color}`}><Icon size={18}/></div><div className="stat-label">{c.label}</div><div className="stat-value">{c.value}</div><div className="stat-hint">{c.hint}</div></div>;})}</div>
    <div className="dashboard-grid">
      <section className="panel chart-panel"><div className="panel-head"><div><h3>Monthly fee collection</h3><p>Successful payments received by month</p></div><span className="panel-chip">Last 6 months</span></div>
        <div className="chart-area">{(data?.monthly_collection||[]).map((m)=>{const height=Math.max(3,(m.amount/maxAmount)*100);return <div className="chart-column" key={m.month}><div className="chart-amount">{money(m.amount)}</div><div className="chart-bar-wrap"><div className="chart-bar" style={{height:`${height}%`}} title={money(m.amount)} /></div><div className="chart-month">{m.label}</div></div>;})}</div>
        {data?.monthly_collection?.every(x=>x.amount===0)&&<div className="empty-chart-note">No payment records yet. Monthly collections will appear here when successful payments are recorded.</div>}
      </section>
      <section className="panel quick-panel"><div className="panel-head"><div><h3>Quick access</h3><p>Common central administration tasks</p></div></div><div className="quick-links">
        {[['institutions','Institution master',Building2],['users','Manage users',UserCog],['approval-workflows','Approval workflows',GitBranch],['reports','Institution reports',BarChart3]].map(([id,label,Icon])=><button key={id} onClick={()=>onNavigate(id)}><span><Icon size={17}/></span>{label}<ChevronRight size={16}/></button>)}
      </div></section>
    </div>
    <section className="panel audit-preview"><div className="panel-head"><div><h3>Recent audit activity</h3><p>Latest recorded actions across the ERP</p></div><button className="text-btn" onClick={()=>onNavigate('audit-logs')}>View all <ChevronRight size={15}/></button></div><AuditTable rows={data?.recent_audit||[]} compact/></section>
  </>;
}

function AuditTable({rows,compact=false}) {
  if(!rows.length) return <div className="empty-state"><div className="empty-icon"><Clock size={22}/></div><b>No audit activity yet</b><span>Changes and actions will be listed here once users start working in the system.</span></div>;
  return <div className="table-scroll"><table><thead><tr><th>TIME</th><th>USER</th><th>ACTION</th><th>ENTITY</th><th>DETAIL</th></tr></thead><tbody>{rows.map(r=><tr key={r.id}><td className="time-cell">{r.created_at?new Date(r.created_at).toLocaleString('en-IN'): '—'}</td><td>{r.actor_name}</td><td><span className={`action-pill ${String(r.action).toLowerCase()}`}>{r.action}</span></td><td>{nice(r.entity)}</td><td className="detail-cell">{typeof r.details==='object'?JSON.stringify(r.details):String(r.details||'—')}</td></tr>)}</tbody></table></div>;
}

function AuditPage({refreshKey}) {
  const [rows,setRows]=useState([]);const [error,setError]=useState('');const [entity,setEntity]=useState('');const [query,setQuery]=useState('');
  useEffect(()=>{api(`/api/admin/audit-logs?limit=250${entity?`&entity=${entity}`:''}`).then(setRows).catch(e=>setError(e.message));},[refreshKey,entity]);
  const filtered=rows.filter(r=>`${r.actor_name} ${r.action} ${r.entity} ${JSON.stringify(r.details)}`.toLowerCase().includes(query.toLowerCase()));
  return <><PageHeader title="Audit logs" subtitle="A traceable record of system activity, approvals and administrative changes." actions={<button className="secondary-btn" onClick={()=>downloadCsv('kmct-audit-logs.csv',filtered)}><Download size={16}/> Export CSV</button>}/>
    {error&&<div className="banner error-banner"><AlertCircle size={17}/>{error}</div>}
    <section className="panel list-panel"><div className="list-toolbar"><div className="search-box"><Search size={16}/><input placeholder="Search audit activity…" value={query} onChange={e=>setQuery(e.target.value)}/></div><select className="filter-select" value={entity} onChange={e=>setEntity(e.target.value)}><option value="">All entities</option>{['USER','INSTITUTION','ACADEMIC-YEARS','COURSES','DEPARTMENTS','BATCHES','SEMESTERS','ROLES','PERMISSIONS','PORTAL-ACCESS','APPROVAL-WORKFLOWS','NOTIFICATION-CONFIGS'].map(x=><option key={x}>{x}</option>)}</select><span className="result-count">{filtered.length} entries</span></div><AuditTable rows={filtered}/></section>
  </>;
}

function ReportsPage({refreshKey}) {
  const [rows,setRows]=useState([]);const [error,setError]=useState('');
  useEffect(()=>{api('/api/admin/institution-reports').then(setRows).catch(e=>setError(e.message));},[refreshKey]);
  return <><PageHeader title="Institution-wise reports" subtitle="A central view of student, employee and financial indicators by institution." actions={<button className="secondary-btn" onClick={()=>downloadCsv('kmct-institution-reports.csv',rows)}><Download size={16}/> Export CSV</button>}/>{error&&<div className="banner error-banner"><AlertCircle size={17}/>{error}</div>}
    <div className="report-cards">{rows.map(r=><div className="panel report-card" key={r.institution_id}><div className="report-card-head"><span className="code-chip">{r.code}</span><span className="status-dot-label"><i/> Institution</span></div><h3>{r.institution}</h3><div className="report-metrics"><div><span>Students</span><b>{r.students}</b></div><div><span>Employees</span><b>{r.employees}</b></div><div><span>Billed</span><b>{money(r.billed)}</b></div><div><span>Collected</span><b>{money(r.collected)}</b></div></div><div className="report-outstanding"><span>Outstanding</span><b>{money(r.outstanding)}</b></div></div>)}</div>
    {!rows.length&&!error&&<div className="panel empty-state"><Building2 size={24}/><b>No institutions configured</b><span>Add an institution to start seeing reports.</span></div>}
  </>;
}

function ReadOnlyPage({resource,refreshKey}) {
  const [rows,setRows]=useState([]);const [error,setError]=useState('');const [query,setQuery]=useState('');
  useEffect(()=>{api(`/api/admin/${resource}`).then(setRows).catch(e=>setError(e.message));},[resource,refreshKey]);
  const columns=resource==='students'?['student_no','full_name','course','batch','institution_id','status']:['employee_no','full_name','department','designation','institution_id','status'];
  const filtered=rows.filter(r=>columns.some(c=>String(r[c]??'').toLowerCase().includes(query.toLowerCase())));
  return <><PageHeader title={resource==='students'?'Student overview':'Employee overview'} subtitle={`Institution-wide, read-only ${resource} view. Record ownership remains with the ${resource==='students'?'Admin':'HR Admin'} portal.`}/>{error&&<div className="banner error-banner"><AlertCircle size={17}/>{error}</div>}
    <section className="panel list-panel"><div className="list-toolbar"><div className="search-box"><Search size={16}/><input placeholder={`Search ${resource}…`} value={query} onChange={e=>setQuery(e.target.value)}/></div><span className="result-count">{filtered.length} records · Read only</span></div><DataTable rows={filtered} columns={columns} readOnly/></section>
  </>;
}

function ResourcePage({resource,refreshKey,onChanged}) {
  const meta=META[resource];const [rows,setRows]=useState([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('');const [query,setQuery]=useState('');const [modal,setModal]=useState(null);const [saving,setSaving]=useState(false);
  const load=useCallback(()=>{setLoading(true);api(`/api/admin/${resource}`).then(setRows).catch(e=>setError(e.message)).finally(()=>setLoading(false));},[resource]);
  useEffect(()=>{load();},[load,refreshKey]);
  const filtered=useMemo(()=>rows.filter(r=>JSON.stringify(r).toLowerCase().includes(query.toLowerCase())),[rows,query]);
  async function save(formData) {
    setSaving(true);setError('');
    try {
      const path=modal.id?`/api/admin/${resource}/${modal.id}`:`/api/admin/${resource}`;
      await api(path,{method:modal.id?'PATCH':'POST',body:JSON.stringify(formData)});
      setModal(null);await load();onChanged(`${meta.singular} ${modal.id?'updated':'created'} successfully.`);
    } catch(e){setError(e.message);} finally{setSaving(false);}
  }
  async function remove(row) {
    if(!window.confirm(`Delete this ${meta.singular.toLowerCase()}? This action will be recorded in the audit log.`))return;
    try{await api(`/api/admin/${resource}/${row.id}`,{method:'DELETE'});await load();onChanged(`${meta.singular} deleted.`);}catch(e){setError(e.message);}
  }
  const isReadOnly=resource==='roles'&&rows.length>0;
  return <><PageHeader title={meta.title} subtitle={meta.subtitle} actions={<button className="primary-btn" onClick={()=>setModal({})}><Plus size={17}/> Add {meta.singular}</button>}/>
    {error&&<div className="banner error-banner"><AlertCircle size={17}/>{error}<button onClick={()=>setError('')}><X size={15}/></button></div>}
    <section className="panel list-panel"><div className="list-toolbar"><div className="search-box"><Search size={16}/><input placeholder={`Search ${meta.singular.toLowerCase()}…`} value={query} onChange={e=>setQuery(e.target.value)}/></div><span className="result-count">{filtered.length} records</span></div>
      {loading?<div className="loading-state">Loading records…</div>:<DataTable rows={filtered} columns={meta.columns} onEdit={row=>setModal(row)} onDelete={remove} resource={resource}/ >}
    </section>
    {modal&&<RecordModal meta={meta} initial={modal} saving={saving} onClose={()=>setModal(null)} onSave={save}/>}
  </>;
}

function DataTable({rows,columns,onEdit,onDelete,resource,readOnly=false}) {
  if(!rows.length)return <div className="empty-state"><div className="empty-icon"><ClipboardList size={22}/></div><b>No records found</b><span>{readOnly?'Records created in their owning portal will appear here.':'Create a record to get started.'}</span></div>;
  return <div className="table-scroll"><table><thead><tr>{columns.map(c=><th key={c}>{nice(c)}</th>)}{!readOnly&&<th className="actions-col">ACTIONS</th>}</tr></thead><tbody>{rows.map(row=><tr key={row.id}>{columns.map(c=><td key={c}>{renderValue(c,row[c])}</td>)}{!readOnly&&<td className="actions-cell"><button className="row-icon edit" title="Edit" onClick={()=>onEdit(row)}><Pencil size={15}/></button><button className="row-icon delete" title="Delete" onClick={()=>onDelete(row)}><Trash2 size={15}/></button></td>}</tr>)}</tbody></table></div>;
}
function renderValue(key,value){if(value===null||value===undefined||value==='')return <span className="muted">—</span>;if(typeof value==='boolean')return <span className={`status-label ${value?'enabled':'disabled'}`}><i/>{value?'Yes':'No'}</span>;if(key==='amount'||key==='billed'||key==='collected'||key==='outstanding')return money(value);if(typeof value==='string'&&/^\d{4}-\d\d-\d\d/.test(value))return new Date(value).toLocaleDateString('en-IN');if(key==='action'||key==='status')return <span className="action-pill neutral">{nice(value)}</span>;return String(value);}

function RecordModal({meta,initial,saving,onClose,onSave}) {
  const [values,setValues]=useState(()=>{const v={...(initial.id?initial:{})};meta.fields.forEach(([key,,type])=>{if(v[key]===undefined)v[key]=type==='boolean'?false:'';});return v;});
  const [localError,setLocalError]=useState('');
  const [referenceOptions,setReferenceOptions]=useState({});
  useEffect(()=>{
    let active=true;
    const refs=meta.fields.filter(([, ,type])=>type==='reference');
    Promise.all(refs.map(async ([key,,type,required,config])=>{
      try { const result=await api(`/api/admin/${config.resource}`); return [key,result]; }
      catch { return [key,[]]; }
    })).then(entries=>{if(active)setReferenceOptions(Object.fromEntries(entries));});
    return ()=>{active=false;};
  },[meta]);
  function update(key,value){setValues(v=>({...v,[key]:value}));}
  function submit(e){e.preventDefault();setLocalError('');const data={};meta.fields.forEach(([key,,type])=>{let value=values[key];if(type==='number'){if(value===''&&(key==='duration_years'||key==='sequence'))return;value=value===''?null:Number(value);}if(type==='boolean')value=Boolean(value);if(type==='password'&&!value)return;if(value!==undefined)data[key]=value;});if(!initial.id&&meta.fields.some(([key,,type,required])=>required&&(data[key]===undefined||data[key]===''))){setLocalError('Please complete all required fields.');return;}if(data.institution_id==='')data.institution_id=null;onSave(data);}
  return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}><div className="modal-card"><div className="modal-head"><div><div className="eyebrow">{initial.id?'UPDATE RECORD':'NEW RECORD'}</div><h2>{initial.id?`Edit ${meta.singular}`:`Add ${meta.singular}`}</h2></div><button className="icon-btn" onClick={onClose}><X size={19}/></button></div>
    <form onSubmit={submit}><div className="form-grid">{meta.fields.map(([key,label,type,required,options])=>type==='boolean'?<label className="toggle-field" key={key}><span>{label}</span><input type="checkbox" checked={Boolean(values[key])} onChange={e=>update(key,e.target.checked)}/></label>:<label className={`field ${type==='textarea'?'span-two':''}`} key={key}>{label}{required&&<em>*</em>}{type==='select'?<select value={values[key]??''} onChange={e=>update(key,e.target.value)} required={Boolean(required)}><option value="">Select {label}</option>{options.map(o=><option key={o} value={o}>{nice(o)}</option>)}</select>:type==='reference'?<select value={values[key]??''} onChange={e=>update(key,e.target.value===''?'':Number(e.target.value))} required={Boolean(required&&!initial.id)}><option value="">{required?`Select ${label}`:'All / central'}</option>{(referenceOptions[key]||[]).map(o=><option key={o.id} value={o.id}>{o[options.label]||o.name||o.username||`Record ${o.id}`}</option>)}</select>:type==='textarea'?<textarea rows="3" value={values[key]??''} onChange={e=>update(key,e.target.value)}/>:<input type={type} value={values[key]??''} required={Boolean(required&&!initial.id)} onChange={e=>update(key,e.target.value)} placeholder={type==='password'&&initial.id?'Leave blank to keep existing password':''} min={type==='number'?0:undefined}/>}</label>)}</div>
      {localError&&<div className="error-line"><AlertCircle size={15}/>{localError}</div>}
      <div className="modal-actions"><button type="button" className="secondary-btn" onClick={onClose}>Cancel</button><button className="primary-btn" disabled={saving}>{saving?'Saving…':initial.id?'Save changes':'Create record'} <Check size={16}/></button></div>
    </form>
  </div></div>;
}

function downloadCsv(filename,rows){if(!rows?.length)return;const headers=Object.keys(rows[0]);const csv=[headers.join(','),...rows.map(row=>headers.map(h=>`"${String(typeof row[h]==='object'?JSON.stringify(row[h]):row[h]??'').replaceAll('"','""')}"`).join(','))].join('\n');const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;a.click();URL.revokeObjectURL(url);}

export default App;
