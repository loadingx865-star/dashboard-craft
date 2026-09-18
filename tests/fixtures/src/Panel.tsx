import { Link } from 'react-router-dom';

export const Panel = () => (
  <div className="bg-slate-900 border-2 border-cyan-400 rounded-xl p-4">
    <span className="text-red-500 text-2xl font-bold">ALARM</span>
    <i style={{ color: "rgb(239 68 68)", fontSize: 22, padding: 16 }} />
    <b className="text-white/70">ok</b>
    <Link to="/detail#face">详情</Link>
  </div>
);
