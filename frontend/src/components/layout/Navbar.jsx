import { useState, useRef, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Home, History, LogOut, User, Menu, X } from 'lucide-react';
import './Navbar.css';

const Navbar = () => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [imgError, setImgError] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      if (import.meta.env.DEV) console.error('Failed to log out', error);
    }
  };

  const closeMenus = () => {
    setIsMobileMenuOpen(false);
    setIsDropdownOpen(false);
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Brand */}
        <Link to="/" className="navbar-brand" onClick={closeMenus}>
          <span className="navbar-logo-text gradient-text">NeuralLens</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="navbar-desktop-links">
          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <Home size={18} />
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <History size={18} />
            <span>History</span>
          </NavLink>
        </div>

        {/* Desktop Profile Dropdown */}
        <div className="navbar-desktop-profile" ref={dropdownRef}>
          <button className="profile-btn" onClick={() => setIsDropdownOpen(!isDropdownOpen)}>
            {user?.photoURL && !imgError ? (
              <img 
                src={user.photoURL} 
                alt="Profile" 
                className="profile-avatar"
                referrerPolicy="no-referrer"
                onError={() => setImgError(true)}
              />
            ) : (
              <div className="profile-avatar-fallback">
                <User size={20} />
              </div>
            )}
          </button>

          {isDropdownOpen && (
            <div className="profile-dropdown">
              <div className="dropdown-header">
                <span className="dropdown-name">{user?.displayName || 'User'}</span>
                <span className="dropdown-email">{user?.email}</span>
              </div>
              <div className="dropdown-divider"></div>
              <Link to="/profile" className="dropdown-item" onClick={closeMenus}>
                <User size={16} />
                <span>Profile</span>
              </Link>
              <button className="dropdown-item dropdown-item-danger" onClick={handleLogout}>
                <LogOut size={16} />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>

        {/* Mobile Menu Toggle */}
        <button 
          className="mobile-menu-btn" 
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="mobile-menu page-enter">
          <div className="mobile-menu-header">
            <div className="mobile-user-info">
              {user?.photoURL && !imgError ? (
                <img 
                  src={user.photoURL} 
                  alt="Profile" 
                  className="profile-avatar"
                  referrerPolicy="no-referrer"
                  onError={() => setImgError(true)}
                />
              ) : (
                <div className="profile-avatar-fallback">
                  <User size={24} />
                </div>
              )}
              <div className="mobile-user-text">
                <span className="mobile-user-name">{user?.displayName || 'User'}</span>
                <span className="mobile-user-email">{user?.email}</span>
              </div>
            </div>
          </div>
          <div className="mobile-menu-links">
            <NavLink to="/" className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`} onClick={closeMenus}>
              <Home size={20} />
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/history" className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`} onClick={closeMenus}>
              <History size={20} />
              <span>History</span>
            </NavLink>
            <NavLink to="/profile" className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`} onClick={closeMenus}>
              <User size={20} />
              <span>Profile</span>
            </NavLink>
            <button className="mobile-nav-link danger" onClick={handleLogout}>
              <LogOut size={20} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
