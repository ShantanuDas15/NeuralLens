import './PageShell.css';

const PageShell = ({ children, className = '' }) => {
  return (
    <main className={`page-shell ${className}`}>
      <div className="page-shell-container page-enter">
        {children}
      </div>
    </main>
  );
};

export default PageShell;
