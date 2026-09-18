export const Panel = () => (
  <div className="bg-surface text-primary rounded-md">
    <span style={{ color: 'var(--color-status-alarm)', fontSize: 'var(--font-size-metric)' }}>ok</span>
    <span style={{ borderWidth: 1 }}>发丝线，允许</span> {/* hardcode-ok: 1px 发丝线不属于设计刻度 */}
    <a href="#section">锚点跳转，不是颜色</a>
  </div>
);
